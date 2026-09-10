"""Onde a sessão de banco mora, e como ela chega em quem precisa dela.

────────────────────────────────────────────────────────────────────
"Este arquivo não tinha um `get_db`?"
────────────────────────────────────────────────────────────────────
Tinha, e a história dele é a melhor coisa que este arquivo tem para
ensinar — porque são três desenhos, cada um trocando um problema por
outro, e nenhum de graça.

**Primeiro desenho: a dependency.** O `get_db` abria a sessão, entregava
com `yield`, fazia `rollback` se a rota explodisse e `close` no
`finally`. O ciclo de vida inteiro morava aqui, e a rota pedia assim:

    def minha_rota(db: Session = Depends(get_db)):

A favor: a rota DECLARAVA que usava banco, e quem não pedisse não abria
conexão nenhuma.

**Segundo desenho: o ciclo virou middleware.** "Onde a sessão nasce e
morre?" é uma pergunta que se responde olhando a lista de middlewares —
é lá que as pessoas procuram. O `get_db` encolheu para um balcão de
retirada: a sessão ficava no `request.state`, e ele a devolvia.

**Terceiro desenho, que é o de hoje: o `get_db` acabou.** A rota não
pede mais nada; quem pede é o controller, ao ser construído.

────────────────────────────────────────────────────────────────────
O QUE MUDOU DE VERDADE — "entregar" virou "deixar onde dá pra achar"
────────────────────────────────────────────────────────────────────
A defesa do desenho anterior era esta frase: *middleware não consegue
passar objeto pra rota, só a dependency consegue*. A frase continua
verdadeira, e mesmo assim o `get_db` morreu. Vale entender por quê,
porque é a ideia inteira deste arquivo.

Middleware continua sem conseguir **entregar** nada. O que ele consegue
é **deixar num lugar onde quem vier depois sabe procurar** — e esse
lugar é o `contextvars`, o mesmo mecanismo que o `request_id` deste
projeto já usava antes (src/utils/request_context.py). Não é um
truque novo: é o caminho que você já viu funcionando no bloco do log.

Entregar é empurrar; deixar no contexto é pousar. Para quem recebe, dá
no mesmo — e o middleware sabe fazer o segundo.

────────────────────────────────────────────────────────────────────
O QUE ISSO CUSTA — três coisas, e nenhuma é de graça
────────────────────────────────────────────────────────────────────
• **A sessão virou ambiente.** Antes, a assinatura da rota dizia em voz
  alta "eu uso banco". Agora a sessão está no ar, e qualquer código, em
  qualquer camada, alcança o banco chamando `get_session()` — inclusive
  um DTO, que não deveria. Isso é uma perda real de legibilidade, e não
  há como impedir por código: o combinado é que **só o controller
  chama `get_session()`**, e é curto de propósito, pra caber na cabeça.

• **Duas peças precisam concordar.** Quem prepara o contexto é o
  middleware (numa requisição) ou o consumer (numa mensagem). Se um dos
  dois não rodar, o `get_session` levanta. Isto aqui MELHOROU em relação
  ao desenho anterior, que quebrava com um `AttributeError` seco longe
  do crime: agora a mensagem diz qual peça faltou e onde ela mora.

• **O ciclo é mais curto que o da dependency.** A dependency fechava a
  sessão depois de a resposta estar pronta; o middleware fecha assim que
  a rota devolve. Para esta API dá no mesmo — toda resposta daqui é
  montada inteira antes de sair. Uma rota que devolvesse um fluxo lendo
  do banco aos poucos encontraria a sessão já fechada, e é o tipo de
  rota que pediria outro desenho.

────────────────────────────────────────────────────────────────────
UMA CONTA QUE ESTE PROJETO JÁ ERROU
────────────────────────────────────────────────────────────────────
Por muito tempo estava escrito aqui que a preguiça do `if` (só abrir a
sessão quando alguém pede) era o que mantinha "o /health_check sem
conexão nenhuma". Isso era **falso**, e vale corrigir em voz alta em vez
de apagar em silêncio.

`SessionLocal()` não conecta no banco. O SQLAlchemy só tira uma conexão
do pool no primeiro comando SQL de verdade. Medido, com o pool a
descoberto:

    depois de SessionLocal()   -> 0 conexões em uso
    depois do PRIMEIRO SQL     -> 1 conexão em uso
    depois do close()          -> 0 conexões em uso

Ou seja: o /health_check não abriria conexão nenhuma de qualquer jeito,
porque ele não emite SQL. A preguiça não economiza conexão.

O que ela compra, então? Duas coisas menores e uma grande. As menores:
um objeto Python que não é criado, e a garantia de que uma rota que não
fala com o banco não **dependa** do banco estar de pé. A grande é a
lição: enquanto a sessão for opcional, todo `close` e todo `rollback`
precisa perguntar antes de agir — e é essa pergunta que o
tests/integration/test_session_manager.py cobra.

Ensinar um custo que não existe é pior do que não ensinar nada.
"""

from contextvars import ContextVar
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from constants import DATABASE_URL


engine = create_engine(DATABASE_URL, pool_size=5, pool_recycle=600, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


class SessionHolder:
    """O balcão de um trabalho: começa vazio, e só abre a sessão se pedirem.

    Por que um objeto, e não a sessão guardada direto no contexto? Porque
    o contexto só viaja num sentido. Quem cria a task filha (o middleware)
    passa uma CÓPIA do contexto pra baixo: a rota enxerga o que o
    middleware pôs, mas um `.set()` feito na rota é invisível lá em cima.
    Este projeto mediu:

        rota enxerga o que o middleware pôs         -> sim
        middleware enxerga o `.set()` feito na rota -> NAO
        middleware enxerga a MUTAÇÃO deste objeto   -> sim

    A leitura do meio é a que decide o desenho. Com a sessão guardada
    direto no contexto, quem a criasse seria a rota — e o `finally` do
    middleware acharia `None` pra sempre, fechando nada. Uma conexão
    vazada por requisição, em silêncio, até a décima sexta pendurar por 30
    segundos e virar 500.

    Guardando um objeto MUTÁVEL, as duas pontas olham o MESMO balcão: a
    rota mexe no atributo, o middleware lê o atributo. É o mesmo mecanismo
    do `request.state` de antes — um saco compartilhado —, só que este
    também serve a quem não tem requisição nenhuma, como o consumer.
    """

    def __init__(self) -> None:
        self.session: Optional[Session] = None

    def get_or_create_session(self) -> Session:
        if self.session is None:
            self.session = SessionLocal()

        return self.session


_session_holder: ContextVar[Optional[SessionHolder]] = ContextVar("db_session_holder", default=None)


def open_session_context() -> SessionHolder:
    """Prepara o lugar da sessão deste trabalho e devolve o balcão.

    Chamada em DOIS lugares, e só nestes dois:

      • src/middlewares/session_manager.py, no começo de cada requisição;
      • src/consumer.py, no começo de cada mensagem da fila.

    São os dois pontos de entrada da aplicação — os dois lugares onde um
    trabalho começa. Quem chama isto é quem também vai fechar a sessão no
    fim; abrir sem fechar é vazar conexão.
    """
    holder = SessionHolder()
    _session_holder.set(holder)

    return holder


def clear_session_context() -> None:
    """Tira o balcão do contexto. Chamada pelos mesmos dois lugares, no fim.

    Sem esta linha, fora de um trabalho o `get_session` devolveria o balcão
    do trabalho ANTERIOR, com a sessão já fechada. E sessão fechada do
    SQLAlchemy não reclama: ela reabre sozinha na próxima query, tomando
    uma conexão que ninguém mais fecharia.

    Na API isso quase não apareceria — cada requisição chega num contexto
    novo. No consumer, que é um processo só num laço eterno, apareceria
    sempre.
    """
    _session_holder.set(None)


def get_session() -> Session:
    """Devolve a sessão deste trabalho, abrindo-a se ninguém pediu ainda.

    Quem chama é o BaseController, ao ser construído. É esta função que
    substituiu o `db: Session = Depends(get_db)` que ficava na assinatura
    de cada rota.

    O `if` lá do `get_or_create_session` é a preguiça de sempre: a sessão só nasce
    quando alguém pede. Rota que não constrói controller nenhum — o `/` e
    o /health_check — não chega aqui, e por isso não depende do banco
    estar de pé.
    """
    holder = _session_holder.get()

    if holder is None:
        raise Exception(
            "Nao existe sessao de banco neste contexto. "
            + "Quem prepara o contexto de uma requisicao e o middleware "
            + "src/middlewares/session_manager.py; quem prepara o de uma mensagem da fila "
            + "e o src/consumer.py. Se voce chegou aqui, um dos dois nao rodou."
        )

    return holder.get_or_create_session()
