from tests.utils import INTERNAL_TOKEN
from tests.utils.requisition import ClientRequisition


DOCUMENTATION_ENDPOINTS = ["/docs", "/redoc", "/openapi.json"]


class TestDocumentationDisabled:
    """Guarda uma decisão de produto: esta API não serve documentação automática.

    O FastAPI monta /docs, /redoc e /openapi.json sozinho. Aqui os três estão
    desligados de propósito, em src/app.py — quem quiser saber o que a API
    responde manda uma requisição, com os exemplos prontos do README. Um
    FastAPI() distraído reabre os três em silêncio, e desfazer a decisão sem
    ninguém ver é exatamente o que estes dois testes impedem.

    Repare no INTERNAL-TOKEN do primeiro teste: sem ele os três endereços
    respondem 403, e 403 não prova nada sobre documentação. O middleware de
    token é mais externo que o roteamento, então ele barra a requisição antes
    de alguém perguntar se a rota existe. Com token a requisição chega ao
    roteamento, e a resposta vira 404: a rota não existe mesmo.
    """

    def test_documentation_endpoints_are_not_served(self):
        for endpoint in DOCUMENTATION_ENDPOINTS:
            response = ClientRequisition.send(
                "GET",
                endpoint,
                headers={"INTERNAL-TOKEN": INTERNAL_TOKEN},
            )
            assert response.response_status == 404
            assert response.response_json["code"] == "QIT000404"

    def test_documentation_endpoints_are_not_public(self):
        for endpoint in DOCUMENTATION_ENDPOINTS:
            response = ClientRequisition.send("GET", endpoint)
            assert response.response_status == 403
            assert response.response_json["code"] == "QIT000002"
