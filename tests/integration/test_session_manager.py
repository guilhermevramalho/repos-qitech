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


class TestSessionManager:
    """A sessão de banco nasce e morre no middleware, e nunca salva sozinha.

    Quem cuida do ciclo é src/middlewares/session_manager.py; quem entrega
    a sessão para a rota é o `get_db`, em src/database.py.

    Os 16 testes dos outros arquivos já cobram a parte fácil: se a sessão
    não chegasse na rota, todos eles ficariam vermelhos de uma vez. Estes
    dois cobram o que eles não veem — o que acontece nas rotas SEM banco,
    e o que acontece quando uma requisição explode no meio.
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
