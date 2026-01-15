from typing import Optional
from sqlmodel import Field, SQLModel


class Payments(SQLModel, table=True):
    correlation_id: Optional[str] = Field(default=None, primary_key=True)
    amount: float
    status: str = Field(max_length=20)
    idempotency_key: str = Field(max_length=100, unique=True)
    kind: str = Field(max_length=50)

    def to_json(self):
        return {
            "correlation_id": self.correlation_id,
            "amount": self.amount,
            "status": self.status,
            "idempotency_key": self.idempotency_key,
        }
