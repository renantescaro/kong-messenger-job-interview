SafePay Stream - Async Payment API
Projeto demonstrativo de um sistema de pagamentos assíncrono utilizando FastAPI, Kong Gateway, RabbitMQ e MySQL.

🛠️ Tecnologias e Infraestrutura
- API Gateway: Kong (Modo DB-less) para Rate Limiting e Correlation ID.
- Backend: FastAPI (Python 3.10+).
- Mensageria: RabbitMQ (Broker de mensagens).
- Banco de Dados: MySQL 8.0 (Persistência de estado e Idempotência).

🚀 Como Executar
1. Subir a Infraestrutura (Docker)
Este comando inicia o Kong, RabbitMQ e MySQL.

```PowerShell
docker-compose up -d
```
2. Preparar o Banco de Dados
Acesse o MySQL (Porta 3307) e execute o script de criação:
```SQL
CREATE DATABASE IF NOT EXISTS safepay;
USE safepay;

CREATE TABLE payments (
    correlation_id VARCHAR(36) PRIMARY KEY,
    amount DECIMAL(10,2),
    status VARCHAR(20),
    idempotency_key VARCHAR(100) UNIQUE,
    kind VARCHAR(50)
);
```

3. Rodar a Aplicação Python
Certifique-se de que o FastAPI está ouvindo em 0.0.0.0 para ser visível pelo Docker.

```PowerShell
uvicorn main:app --host 0.0.0.0 --port 5000
```

4. Atualizar Configurações do Gateway
Sempre que alterar o arquivo kong.yml, reinicie o container:

```PowerShell
docker-compose restart kong
```

📊 Monitoramento e Acesso
RabbitMQ Management: http://localhost:15672 (User/Pass: guest)

Kong Admin API: http://localhost:8001

Konga Dashboard: http://localhost:1337

MySQL: localhost:3307 (User: root | Pass: root)

📬 Requests (Via Kong - Porta 8000)
Criar Pagamento
O Kong injeta o correlation_id e aplica rate-limiting.

```PowerShell
curl --request POST \
  --url http://localhost:8000/pagar \
  --header 'Content-Type: application/json' \
  --header 'idempotency-key: wdwqd2' \
  --data '{
    "amount": 550.00,
    "kind": "RENOVACAO"
}'
```

Consultar Status
Substitua pelo UUID retornado na criação.

```PowerShell
curl --request GET \
  --url http://localhost:8000/pagamento/d4383c63-2b3f-4fc2-81d6-0764536932
```
