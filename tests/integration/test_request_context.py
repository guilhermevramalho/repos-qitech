import re

from tests.utils import INTERNAL_TOKEN
from tests.utils.requisition import ClientRequisition


# O cabeçalho que carrega o identificador da requisição, escrito aqui à
# mão de propósito — como os cabeçalhos de segurança em
# test_healthcheck.py. O teste cobra o contrato pela rede e não importa
# nada de src/: se ele lesse a mesma constante que a aplicação usa, um
# erro de digitação lá passaria despercebido aqui.
REQUEST_ID_HEADER = "X-Request-ID"

# O formato do identificador que a API inventa quando o cliente não
# manda um: um UUID versão 4, no formato 8-4-4-4-12.
UUID_FORMAT = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")

# Valores que a API NÃO deve aceitar de quem chama, todos legais de
# trafegar em HTTP e todos ruins de cair num arquivo de log:
#   • comprido demais (65 caracteres, um a mais que o limite);
#   • com espaço, vírgula e barra — pontuação que atrapalha quem depois
#     for separar as colunas do log.
UNSAFE_REQUEST_IDS = [
    "a" * 65,
    "tem espaco no meio",
    "tem,virgula",
    "tem/barra",
    "",
]


def get_request_id(response) -> str:
    return response.response.headers.get(REQUEST_ID_HEADER)


class TestRequestContext:
    """Toda requisição sai com um nome próprio, e ele serve pra achá-la no log.

    O middleware que faz isso é src/middlewares/request_context.py. Estes
    testes cobram as três coisas que ele promete: que o identificador
    sempre existe, que o de quem chamou é respeitado quando dá, e que ele
    aparece até quando a requisição é recusada na porta.
    """

    def test_request_id_is_created_when_the_client_sends_none(self):
        """Cliente que não pede nada ganha um identificador mesmo assim.

        Esta é a rota pública, sem token: até ela é nomeada. O middleware
        do identificador é o único do projeto sem lista de exceção, e é
        de propósito — requisição sem nome é requisição que você não acha
        no log depois.
        """
        response = ClientRequisition.send("GET", "/")

        assert response.response_status == 200

        request_id = get_request_id(response)
        assert request_id is not None, f"a resposta veio sem o cabecalho {REQUEST_ID_HEADER}"
        assert UUID_FORMAT.fullmatch(request_id), f"o identificador {request_id} nao tem o formato de um UUID"

    def test_request_id_sent_by_the_client_comes_back(self):
        """O identificador de quem chamou é respeitado, e volta igual.

        É isto que permite seguir um mesmo pedido atravessando vários
        sistemas: o serviço que chamou esta API já tinha um nome pro que
        estava fazendo, e os dois logs passam a contar a mesma história
        com o mesmo nome.
        """
        sent_request_id = "id-de-quem-chamou-1234"

        response = ClientRequisition.send(
            "GET",
            "/health_check",
            headers={REQUEST_ID_HEADER: sent_request_id},
        )

        assert response.response_status == 204
        assert get_request_id(response) == sent_request_id

    def test_each_request_gets_its_own_id(self):
        """Duas requisições, dois identificadores diferentes.

        Parece óbvio e não é: se o identificador fosse guardado numa
        variável comum em vez de num ContextVar, ele seria UM só pro
        programa inteiro — e duas pessoas usando a API ao mesmo tempo
        teriam o log embaralhado. Este teste é o que denuncia isso.
        """
        first_response = ClientRequisition.send("GET", "/")
        second_response = ClientRequisition.send("GET", "/")

        assert get_request_id(first_response) != get_request_id(second_response)

    def test_unsafe_request_id_is_replaced(self):
        """Identificador fora do formato é descartado, não é ecoado.

        O que se defende aqui tem nome: log injection. O cabeçalho é
        texto que qualquer pessoa escreve, e ele vai parar no arquivo de
        log — quem conseguisse ecoar o que quisesse escreveria linhas
        inteiras, inventadas, dentro do seu log. Um identificador que não
        passa na peneira é trocado por um novo, e a requisição segue
        normalmente: recusar o valor não é recusar o cliente.
        """
        for unsafe_request_id in UNSAFE_REQUEST_IDS:
            response = ClientRequisition.send(
                "GET",
                "/",
                headers={REQUEST_ID_HEADER: unsafe_request_id},
            )

            assert response.response_status == 200

            request_id = get_request_id(response)
            assert request_id != unsafe_request_id, f"a API ecoou o identificador invalido {unsafe_request_id!r}"
            assert UUID_FORMAT.fullmatch(request_id), f"o identificador {request_id} nao tem o formato de um UUID"

    def test_request_id_on_forbidden_response(self):
        """Identificador também na resposta que NÃO chega na rota.

        Este teste guarda a ordem dos middlewares em src/app.py, do mesmo
        jeito que test_secure_headers_on_forbidden guarda a dele.

        A requisição vai sem token: o middleware de token responde 403 na
        hora, e ela nunca chega na rota. O identificador só aparece nessa
        resposta se a camada que o cria for MAIS EXTERNA que a de token.
        Desça a linha do request_context para baixo da linha do
        internal_token em src/app.py e este teste fica vermelho — e o
        403, que é a resposta que um atacante recebe, sai sem nome
        nenhum pra você procurar no log depois.
        """
        response = ClientRequisition.send("PUT", "/sample")

        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000002"

        request_id = get_request_id(response)
        assert request_id is not None, "o 403 do middleware de token veio sem identificador"
        assert UUID_FORMAT.fullmatch(request_id), f"o identificador {request_id} nao tem o formato de um UUID"

    def test_request_id_on_not_found_response(self):
        """E também na resposta que nasce lá dentro, num exception handler.

        O par do teste acima. O 403 nasce num middleware, com a
        requisição ainda a caminho da rota; o 404 nasce bem mais pra
        dentro, depois do roteamento. São dois caminhos de volta
        diferentes, e um não prova o outro.
        """
        response = ClientRequisition.send(
            "PUT",
            "/sample",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )

        assert response.response_status == 404
        assert response.response_json["code"] == "QIT000404"

        request_id = get_request_id(response)
        assert request_id is not None, "o 404 veio sem identificador"
        assert UUID_FORMAT.fullmatch(request_id), f"o identificador {request_id} nao tem o formato de um UUID"
