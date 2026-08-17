import subprocess
from os import environ
from urllib.parse import urlparse, unquote


RESET_QUERIES = [
    "DROP SCHEMA public CASCADE;",
    "CREATE SCHEMA public;",
    "GRANT ALL ON SCHEMA public TO CURRENT_USER;",
    "GRANT ALL ON SCHEMA public TO public;",
]


class DbUtils:
    """Limpa o banco entre os testes e recria as tabelas do zero.

    Cada teste comeca com o banco vazio: assim um teste nunca depende
    do que outro deixou pra tras.
    """

    @staticmethod
    def connection_settings() -> dict:
        url = urlparse(environ["DATABASE_URL"])
        return {
            "host": url.hostname,
            "port": str(url.port or 5432),
            "user": unquote(url.username or ""),
            "password": unquote(url.password or ""),
            "database": (url.path or "/").lstrip("/"),
        }

    @staticmethod
    def run_psql(settings: dict, arguments: list) -> None:
        command = [
            "psql",
            "-h",
            settings["host"],
            "-p",
            settings["port"],
            "-U",
            settings["user"],
            settings["database"],
        ]
        command.extend(arguments)
        subprocess.run(command, env={"PGPASSWORD": settings["password"], "PATH": environ.get("PATH", "")}, check=True)

    @staticmethod
    def rollback() -> None:
        settings = DbUtils.connection_settings()

        for query in RESET_QUERIES:
            DbUtils.run_psql(settings, ["--command", query])

        DbUtils.run_psql(settings, ["-f", "database/database.sql"])
