from typing import Optional
import pika, json
from main.database.database import Database, select
from main.database.models.payments import Payments

# Simulação de Cache de Idempotência TODO: Redis
cache_idempotencia = set()

def _get_payment(ikey: str) -> Optional[Payments]:
    query = select(Payments).where(Payments.idempotency_key == ikey)
    return Database().get_one(query)

def execute(ch, method, properties, body):
    data = json.loads(body)
    ikey = data['idempotency_key']

    # checa idempotência
    if ikey in cache_idempotencia:
        print(f"Pedido {ikey} já processado. Ignorando...")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        payment = _get_payment(ikey)

        if payment and payment.status not in ["ERRO", "PENDENTE"]:
            print(f"Pedido {ikey} já processado anteriormente. Ignorando...")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # simula integração crítica (Sistemas Heterogêneos)
        print(f"Processando {data['kind']} de R$ {data['amount']}")
        
        # simula erro aleatório para testar Retry/DLQ
        if data['amount'] > 1000:
            raise ValueError("Valor muito alto para sistema legado")

        # sucesso
        payment.status = "APROVADO"
        Database().save(payment)

        cache_idempotencia.add(ikey)
        ch.basic_ack(delivery_tag=method.delivery_tag) # Manual Ack
        print("Sucesso!")

    except Exception as e:
        payment = _get_payment(ikey)

        payment.status = "ERRO"
        Database().save(payment)

        # troubleshooting e resiliência
        print(f"Erro: {e}. Enviando para análise/DLQ.")
        # nack com requeue=False joga a mensagem para a DLQ configurada
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.basic_consume(queue='payment_queue', on_message_callback=execute)
channel.start_consuming()
