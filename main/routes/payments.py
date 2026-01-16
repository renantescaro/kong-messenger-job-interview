from fastapi import APIRouter, Depends, Header, HTTPException, status

from typing import Optional
from fastapi.responses import JSONResponse
import pika, json, uuid
from sqlalchemy.exc import IntegrityError
from main.database.database import Database, select
from main.database.models.payments import Payments

router = APIRouter(prefix="/pay")

@router.post("")
async def pay(body: dict, idempotency_key: str = Header(...)):
    cid = body.get("correlation_id", str(uuid.uuid4()))

    try:
        Database().save(
            Payments(
                correlation_id=cid,
                idempotency_key=idempotency_key,
                amount=float(body["amount"]),
                kind=body["kind"],
                status="PENDENTE",
            )
        )
    except IntegrityError as e:
        print(f'Erro de integridade, valores repetidos: {e}')

        query = select(Payments).where(Payments.idempotency_key == idempotency_key)
        payments: Payments = Database().get_one(query)

        status_code = 200 if payments.status != "ERRO" else 409

        return JSONResponse(
            status_code=status_code,
            content={
                "correlation_id": cid,
                "status": payments.status,
                "amount": payments.amount,
                "kind": payments.kind,
            }
        )

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', socket_timeout=5))
    channel = connection.channel()
    
    # DLQ
    channel.exchange_declare(exchange='dlx_exchange', exchange_type='direct')
    channel.queue_declare(queue='payment_queue_dlq', durable=True)
    channel.queue_bind(exchange='dlx_exchange', queue='payment_queue_dlq', routing_key='dead_letter')

    # vincula DQL a fila payment_queue
    args = {
        "x-dead-letter-exchange": "dlx_exchange", 
        "x-dead-letter-routing-key": "dead_letter"
    }
    channel.queue_declare(queue='payment_queue', durable=True, arguments=args)

    payload = {
        "correlation_id": cid,
        "idempotency_key": idempotency_key,
        **body
    }

    # Publicação Persistente (Garante que não se perca no Broker)
    channel.basic_publish(
        exchange='',
        routing_key='payment_queue',
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    
    connection.close()
    return {"status": "Processando", "correlation_id": cid}

@router.get("/{cid}")
async def get_payment(cid: str):
    query = select(Payments).where(Payments.correlation_id == cid)
    payments: Optional[Payments] = Database().get_one(query)

    if not payments:
        raise HTTPException(
            status_code=404,
            detail="Correlation ID não encontrado.",
        )

    status_code = 200 if payments.status != "ERRO" else 409

    return JSONResponse(
        status_code=status_code,
        content={
            "correlation_id": cid,
            "status": payments.status,
            "amount": payments.amount,
            "kind": payments.kind,
        }
    )
