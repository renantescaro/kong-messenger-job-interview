from sqlalchemy import Table
from sqlmodel.sql.expression import SelectOfScalar, Select
from sqlmodel import SQLModel, Session, create_engine, select, func, desc, or_, and_
from typing import Any, List, Optional
from main.helpers.enums.dot_env import DotEnvEnum
from main.helpers.settings import Settings


engine = create_engine(
    url=Settings.get(
        DotEnvEnum.DATABASE_URI,
    ),
    max_overflow=0,
    pool_size=10,
    pool_recycle=10,
    # TODO: pegar essa informação do INI, é referente ao log de queries
    echo=False,
)
SQLModel.metadata.create_all(engine)


class Database:
    def __init__(self) -> None: ...

    def get_one(
        self,
        statement: SelectOfScalar | Select,
    ) -> Any:
        try:
            with Session(engine) as session:
                return session.exec(statement).first()
        except Exception as e:
            print(f"'Database' error in 'get_one': {e}")

    def get_all(
        self,
        statement: SelectOfScalar | Select,
    ) -> Optional[List[Any]]:
        try:
            with Session(engine) as session:
                return session.exec(statement).all()

        except Exception as e:
            print(f"'Database' error in 'get_all': {e}")

    def save(
        self,
        object_model: Any,
        refresh: bool = True,
    ) -> Any:
        try:
            with Session(engine) as session:
                session.add(object_model)
                session.commit()

                if refresh:
                    session.refresh(object_model)

                return object_model
        except Exception as e:
            print(f"'Database' error in 'save': {e}")

    def delete(self, object_model) -> None:
        with Session(engine) as session:
            session.delete(object_model)
            session.commit()

    def execute_sql(self, sql_command: str) -> Optional[List[Any]]:
        try:
            with Session(engine) as session:
                result = session.exec(sql_command)
                session.commit()

                if not result.returns_rows:
                    return

                field_names = result.keys()
                results_dict = [
                    dict(zip(field_names, row)) for row in result.fetchall()
                ]

                return results_dict
        except Exception as e:
            print(f"'Database' error in 'execute_sql': {e}")
