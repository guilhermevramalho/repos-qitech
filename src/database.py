from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from constants import DATABASE_URL


engine = create_engine(DATABASE_URL, pool_size=5, pool_recycle=600, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db() -> Session:
    """Entrega uma conversa aberta com o banco e fecha no fim da requisicao.

    Quem precisa do banco escreve, na rota:

        def minha_rota(db: Session = Depends(get_db)):

    O FastAPI chama esta funcao, guarda o que vem depois do `yield` pra
    executar quando a resposta ja tiver sido enviada, e fecha a conexao
    sozinho — mesmo se a rota der erro no meio.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
