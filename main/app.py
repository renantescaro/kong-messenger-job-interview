from typing import Optional
from fastapi import FastAPI, Header, HTTPException
import pika, json, uuid

from main.database.database import Database, select
from main.database.models.payments import Payments

app = FastAPI()

@app.get("/ping")
async def ping():
    return "pong"

@app.post("/pay")
async def pay(body: dict, idempotency_key: str = Header(...)):
    cid = body.get("correlation_id", str(uuid.uuid4()))

    Database().save(
        Payments(
            correlation_id=cid,
            idempotency_key=idempotency_key,
            amount=float(body["amount"]),
            kind=body["kind"],
            status="PENDENTE",
        )
    )

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', socket_timeout=5))
    channel = connection.channel()
    
    # garante que a fila existe e tem DLQ vinculada
    args = {"x-dead-letter-exchange": "dlx_exchange", "x-dead-letter-routing-key": "dead_letter"}
    channel.queue_declare(queue='payment_queue', arguments=args)

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

@app.get("/pay/{cid}")
async def get_payment(cid: str):
    query = select(Payments).where(Payments.correlation_id == cid)
    payments: Optional[Payments] = Database().get_one(query)

    if not payments:
        raise HTTPException(
            status_code=404,
            detail="Correlation ID não encontrado.",
        )

    return {
        "correlation_id": cid,
        "status": payments.status,
        "amount": payments.amount,
        "kind": payments.kind,
    }
