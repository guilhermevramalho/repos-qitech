from os import environ
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError


RESET_QUERIES = [
    "DROP SCHEMA public CASCADE;",
    "CREATE SCHEMA public;",
    "GRANT ALL ON SCHEMA public TO CURRENT_USER;",
    "GRANT ALL ON SCHEMA public TO public;",
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_FILE = PROJECT_ROOT / "database" / "database.sql"

MISSING_DATABASE_URL = (
    "A variavel DATABASE_URL nao esta definida.\n"
    "Copie o arquivo de exemplo antes de rodar os testes:  cp .env.example .env"
)

DATABASE_OFFLINE = (
    "Nao consegui falar com o banco em {host}:{port}.\n"
    "Ele precisa estar de pe pros testes rodarem. Suba com:  docker compose up\n"
    "Se ele ja esta de pe, confira a porta na DATABASE_URL do seu .env."
)


class DbUtils:
    """Limpa o banco entre os testes e recria as tabelas do zero.

    Cada teste comeca com o banco vazio: assim um teste nunca depende
    do que outro deixou pra tras.

    A limpeza acontece pela mesma conexao que a aplicacao usa (a
    DATABASE_URL), e nao por um programa externo: quem tem Docker
    rodando ja tem tudo que precisa.
    """

    @staticmethod
    def database_url() -> str:
        url = environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError(MISSING_DATABASE_URL)

        return url

    @staticmethod
    def rollback() -> None:
        engine = create_engine(DbUtils.database_url(), isolation_level="AUTOCOMMIT")

        try:
            with engine.connect() as connection:
                for query in RESET_QUERIES:
                    connection.exec_driver_sql(query)

                connection.exec_driver_sql(SCHEMA_FILE.read_text())
        except OperationalError:
            message = DATABASE_OFFLINE.format(host=engine.url.host, port=engine.url.port)
            raise RuntimeError(message) from None
        finally:
            engine.dispose()
