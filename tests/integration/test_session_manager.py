import time

from tests.utils import RequestGenerator
from tests.utils.requisition import ClientRequisition


# As duas rotas públicas desta API, com o status que cada uma responde.
#
# Estão escritas aqui à mão de propósito, como os cabeçalhos de segurança
# em test_healthcheck.py: o teste cobra o contrato pela rede e não importa
# nada de src/. Se ele lesse a mesma lista que a aplicação usa, uma rota
# removida de lá sumiria daqui junto, sem ninguém reclamar.
#
# O que interessa nelas, neste arquivo, é que NENHUMA usa banco.
PUBLIC_ROUTES = [
    ("/", 200),
    ("/health_check", 204),
]

# Um status que não existe na tabela de status.
#
# O filtro do /sample_entities aceita qualquer texto (é `str`, não uma
# lista fechada), e lá dentro a busca por um status inexistente estoura.
# É o único jeito, pela rede, de pedir uma requisição que explode DEPOIS
# de já ter falado com o banco — que é exatamente o caminho que o
# middleware da sessão precisa cobrir.
UNKNOWN_STATUS = "status_que_nao_existe"

INTERNAL_ERROR_CODE = "QIT000500"

# Quantas vezes o par explode/funciona se repete. O pool de conexões tem
# 5 (o pool_size lá em src/database.py), então 6 voltas garantem que
# alguma conexão já usada por uma requisição que falhou seja reaproveitada
# por uma que precisa dar certo.
POOL_CYCLES = 6

# Quantas requisições seguidas o teste do vazamento dispara.
#
# O pool tem 5 conexões (o pool_size lá em src/database.py) mais o
# max_overflow padrão do SQLAlchemy, que são 10: 15 no total. Por isso 20:
# é preciso passar de 15 pra que a próxima requisição precise de uma
# conexão que já devia ter voltado.
REQUESTS_BEYOND_THE_POOL = 20

# Quanto uma requisição destas pode demorar antes de o teste chamar de
# problema.
#
# O número tem folga enorme dos dois lados, de propósito, porque teste que
# olha relógio é a receita mais conhecida de teste instável. Este projeto
# mediu as duas situações, com a API recém-subida:
#
#     desenho atual        -> as 20 requisições, 0,0s cada
#     sessão não devolvida -> as 15 primeiras 0,0s, a DÉCIMA SEXTA 15,3s
#
# Cinco segundos ficam 100 vezes acima do caso bom e 3 vezes abaixo do
# caso ruim. Não há como cair no meio por acaso.
MAX_SECONDS_PER_REQUEST = 5.0


class TestSessionManager:
    """A sessão de banco nasce e morre no middleware, e nunca salva sozinha.

    Quem cuida do ciclo é src/middlewares/session_manager.py; quem entrega
    a sessão a quem pede é o `get_session`, em src/database.py — chamado
    pelo BaseController, não mais pela rota.

    Os 29 testes dos outros arquivos já cobram a parte fácil: se a sessão
    não chegasse no controller, todos eles ficariam vermelhos de uma vez.
    Estes três cobram o que eles não veem — o que acontece nas rotas SEM
    banco, o que acontece quando uma requisição explode no meio, e se cada
    requisição devolve a conexão que pegou emprestada.
    """

    def test_public_routes_answer_without_a_session(self):
        """Rota que não usa banco responde normalmente. Este teste tem história.

        Parece o teste mais bobo do projeto, e é o que guarda o erro mais
        caro. Enquanto este middleware era desenhado, uma das versões
        fechava a sessão sem antes perguntar se havia uma:

            finally:
                request.state.db.close()

        O resultado medido foi este:

            GET /                    -> 500
            GET /health_check        -> 500
            GET /sample_entities     -> 200
            POST /sample_entity      -> 201

        Repare na ordem. A mudança era na SESSÃO DE BANCO, e quem quebrou
        foi justamente quem NÃO usa banco — as rotas que qualquer pessoa
        conferiria primeiro ficaram verdes. O 500 foi parar no
        /health_check, que é o endereço que o Docker consulta pra decidir
        se o container está vivo: em produção, isso não é uma rota com
        erro, é o serviço inteiro sendo reiniciado em laço.

        A causa é sempre a mesma, em qualquer desenho: se a sessão pode
        não existir, todo `close` e todo `rollback` precisa perguntar
        antes de agir. Tire uma das duas perguntas
        `if request.state.db is not None` do middleware e este teste fica
        vermelho — enquanto os outros 16 seguem verdes, dizendo que está
        tudo bem.
        """
        for route, expected_status in PUBLIC_ROUTES:
            response = ClientRequisition.send("GET", route)

            assert response.response_status == expected_status, (
                f"a rota publica {route} respondeu {response.response_status}: "
                "o middleware da sessao provavelmente mexeu numa sessao que nunca foi aberta"
            )

    def test_a_request_that_blows_up_does_not_break_the_next_one(self):
        """Depois de um erro no meio da transação, a API continua atendendo.

        Um 500 acontece com a requisição já dentro do banco: a conexão foi
        emprestada, a transação começou, e aí alguma coisa estourou. Se
        essa conexão voltasse pro pool do jeito que estava, a PRÓXIMA
        requisição a pegá-la herdaria uma transação abortada — e falharia
        por um erro que não é dela. Esse é o bug mais confuso que este
        middleware existe pra impedir: o sintoma aparece numa requisição
        inocente, minutos depois, e não tem nada a ver com ela.

        O par se repete algumas vezes de propósito. Uma volta só poderia
        pegar sempre a mesma conexão do pool e não provar nada; com mais
        voltas que o tamanho do pool, alguma conexão usada por uma
        requisição que falhou é necessariamente reaproveitada por uma que
        precisa dar certo.

        Uma honestidade sobre o alcance deste teste: ele cobra o
        RESULTADO (a API segue de pé e o erro não vaza pra frente), não a
        linha do `rollback`. O `close` do middleware já desfaz a
        transação sozinho, então o `rollback` explícito é uma declaração
        de intenção — está lá pra que o combinado continue escrito no dia
        em que alguém trocar o que vem depois. A docstring do middleware
        diz isso com todas as letras.
        """
        for _cycle in range(POOL_CYCLES):
            status, response = RequestGenerator.GET_sample_entities({"status": UNKNOWN_STATUS})
            assert status == 500
            assert response["code"] == INTERNAL_ERROR_CODE

            status, response = RequestGenerator.GET_sample_entities()
            assert status == 200, "a requisicao seguinte herdou a transacao abortada da anterior"

    def test_every_request_gives_its_connection_back(self):
        """Vinte requisições seguidas, e nenhuma fica esperando conexão.

        Este teste nasceu junto com o desenho atual, e cobre um erro que
        antes era impossível cometer.

        Enquanto a sessão morava no `request.state`, quem a fechava era o
        mesmo objeto que a guardava: não havia como errar. Agora ela mora
        no contexto — e o jeito mais natural de escrever isso é o jeito
        errado, porque o contexto só viaja num sentido.

        Guardar a sessão DIRETO no contexto parece limpo e não funciona:
        a rota faria `.set()` numa cópia do contexto, e o `finally` do
        middleware, lá em cima, continuaria enxergando `None`. Ninguém
        fecharia nada.

        Repare em COMO isso aparece, porque não é como se imagina. Este
        projeto rodou o erro de propósito e mediu, requisição a
        requisição:

            req  1 a 15  ->  200, 0,0s cada
            req      16  ->  200, 15,3s
            req 17 a 20  ->  200, 0,0s cada

        Nenhum erro. Nenhum 500. Todas as vinte respondem 200 — e é por
        isso que as duas asserções abaixo existem. As 15 primeiras gastam
        o pool inteiro (5 + 10 de overflow); a décima sexta fica parada
        esperando uma conexão que ninguém devolveu, até o Python recolher
        as sessões abandonadas e liberar tudo de uma vez.

        Com a API já castigada por requisições anteriores, o mesmo erro
        aparece com outra cara: a espera passa dos 30 segundos que o pool
        aguenta e a resposta vira 500. É o mesmo defeito nas duas medições,
        e é por isso que o teste cobra o status E o relógio — sozinho,
        nenhum dos dois pega as duas formas.

        Em produção a primeira forma é a mais cara, justamente por ser a
        mais silenciosa: não é uma página de erro, é a API "ficando
        estranha" de vez em quando, sem nada no log.
        """
        for _request in range(REQUESTS_BEYOND_THE_POOL):
            started_at = time.monotonic()
            status, _response = RequestGenerator.GET_sample_entities()
            elapsed_seconds = time.monotonic() - started_at

            assert status == 200

            assert elapsed_seconds < MAX_SECONDS_PER_REQUEST, (
                f"uma requisicao levou {elapsed_seconds:.1f}s: "
                + "alguma sessao nao esta sendo devolvida pro pool de conexoes"
            )
