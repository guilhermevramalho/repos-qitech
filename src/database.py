from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from constants import DATABASE_URL


engine = create_engine(DATABASE_URL, pool_size=5, pool_recycle=600, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db(request: Request) -> Session:
    """Entrega à rota a sessão de banco desta requisição.

    A rota pede do mesmo jeito de sempre, e é de propósito que esta
    linha não mudou:

        def minha_rota(db: Session = Depends(get_db)):

    ────────────────────────────────────────────────────────────────
    "Esta função não era maior?"
    ────────────────────────────────────────────────────────────────
    Era. Ela abria a sessão, entregava com `yield`, fazia `rollback` se
    a rota explodisse e `close` no `finally`: o ciclo de vida inteiro
    morava aqui. E a docstring que ficava neste lugar defendia, com
    todas as letras, que sessão de banco NÃO deveria ser um middleware.

    O projeto mudou de ideia, e vale contar por quê — porque o motivo
    não é técnico. O desenho antigo funcionava.

    A favor da dependency havia um argumento honesto: só ela consegue
    ENTREGAR um objeto para a rota, e a rota que não pedisse não abria
    conexão nenhuma.

    Contra ela, um argumento mais forte: "onde a sessão de banco nasce
    e morre?" é uma pergunta que se responde olhando a lista de
    middlewares. É lá que as pessoas procuram, é assim que a maioria
    dos serviços faz — e um projeto de estudo que ensina um jeito
    diferente do que se vai encontrar no trabalho ensina uma coisa a
    mais pra desaprender depois.

    Ganhou o padrão conhecido. Hoje quem cuida do ciclo é
    src/middlewares/session_manager.py, e esta função virou o balcão de
    retirada: a sessão desta requisição está no `request.state`, e ela
    a devolve.

    Repare que o argumento a favor da dependency não foi jogado fora —
    ele foi dividido em dois. **Entregar** continua sendo tarefa desta
    função, porque middleware não consegue passar objeto pra rota. E
    **não abrir à toa** continua valendo por causa do `if` aqui
    embaixo: a sessão só nasce quando alguém pede. É essa preguiça que
    mantém o /health_check sem conexão nenhuma — e a docstring do
    middleware conta, com o 500 medido, o que acontece com quem esquece
    que ela pode não existir.

    ────────────────────────────────────────────────────────────────
    O QUE A MUDANÇA CUSTOU
    ────────────────────────────────────────────────────────────────
    Três coisas, e nenhuma é de graça:

    • **A sessão passou a morar num canto compartilhado.** Antes ela
      era uma variável local desta função, e ninguém mais alcançava.
      Agora ela está no `request.state`, que é um saco aberto onde
      qualquer camada pode mexer. O combinado que substitui a garantia
      perdida é curto: `request.state.db` é assunto destas linhas e do
      middleware, de mais ninguém.

    • **Duas peças precisam concordar.** O middleware zera o
      `request.state.db` antes de a requisição entrar, e esta função
      conta com isso. Tire a linha dele do src/app.py e o erro aparece
      AQUI, num AttributeError, longe do que você apagou.

    • **O ciclo ficou mais curto do que era.** A dependency fechava a
      sessão depois de a resposta estar pronta; o middleware fecha
      assim que a rota devolve. Para esta API dá no mesmo — toda
      resposta daqui é montada inteira antes de sair. Uma rota que
      devolvesse um fluxo lendo do banco aos poucos sentiria a
      diferença, e é o tipo de rota que pediria outro desenho.

    O segundo custo é de propósito. Dava pra escrever esta função de um
    jeito que sobrevivesse sem o middleware — e aí, sem ninguém pra
    fechar, a API abriria sessões até o banco recusar a próxima
    conexão, em silêncio, provavelmente num horário ruim. Entre falhar
    alto na primeira requisição e falhar baixo na milésima, este
    projeto escolhe a primeira.
    """
    if request.state.db is None:
        request.state.db = SessionLocal()

    return request.state.db
