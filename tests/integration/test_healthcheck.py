from tests.utils import INTERNAL_TOKEN
from tests.utils.requisition import ClientRequisition


# Os cabeçalhos de segurança que TODA resposta desta API carrega.
#
# Estão escritos aqui à mão de propósito: o teste cobra o contrato pela
# rede, sem importar nada de src/ — se ele lesse a mesma constante que a
# aplicação usa, um erro de digitação lá passaria despercebido aqui.
# Cabeçalho novo em src/middlewares/secure_headers.py entra nesta lista,
# e os dois testes que a usam passam a cobrar.
SECURITY_HEADERS = {
    "Server": "undisclosed",
    "x-frame-options": "SAMEORIGIN",
    "x-xss-protection": "1; mode=block",
    "x-content-type-options": "nosniff",
    "strict-transport-security": "max-age=63072000; includeSubdomains",
    "content-security-policy": "default-src 'self'",
}


def assert_has_security_headers(response):
    headers = response.response.headers

    for header_name, header_value in SECURITY_HEADERS.items():
        assert header_name in headers, f"faltou o cabecalho de seguranca {header_name}"
        assert headers[header_name] == header_value, f"o cabecalho {header_name} veio com outro valor"


class TestHealthCheck:
    def test_home(self):
        response = ClientRequisition.send("GET", "/")
        assert response.response_status == 200

    def test_health_check(self):
        response = ClientRequisition.send("GET", "/health_check")
        assert response.response_status == 204

    def test_no_token(self):
        response = ClientRequisition.send("PUT", "/sample")
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000002"

    def test_sink(self):
        response = ClientRequisition.send(
            "PUT",
            "/sample",
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
        )
        assert response.response_status == 404
        assert response.response_json["code"] == "QIT000404"

    def test_method_not_allowed(self):
        response = ClientRequisition.send("PUT", "/health_check")
        assert response.response_status == 405
        assert response.response_json["code"] == "QIT000405"

    def test_secure_headers_middleware(self):
        response = ClientRequisition.send("GET", "/health_check")
        assert response.response_status == 204
        assert_has_security_headers(response)

    def test_secure_headers_on_forbidden(self):
        """Cabeçalho de segurança também na resposta que NÃO chega na rota.

        Este teste guarda a ordem dos middlewares em src/app.py, e é o par
        do teste acima — os dois juntos é que fecham o assunto.

        O de cima manda em /health_check, que é rota pública: a requisição
        atravessa a pilha inteira e volta. Ele prova que os cabeçalhos
        existem, mas não prova ONDE a camada que os coloca está na pilha.

        Este manda sem token. O middleware de token responde 403 na hora e
        a requisição nunca chega na rota — então os cabeçalhos só aparecem
        se a camada de segurança for MAIS EXTERNA que a de token. Inverta
        as duas linhas de src/app.py e este teste fica vermelho enquanto o
        de cima segue verde: o 403 sai pelado, e é justo a resposta que um
        atacante recebe.
        """
        response = ClientRequisition.send("PUT", "/sample")
        assert response.response_status == 403
        assert_has_security_headers(response)
