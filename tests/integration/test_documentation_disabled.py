from tests.utils import INTERNAL_TOKEN
from tests.utils.requisition import ClientRequisition


DOCUMENTATION_ENDPOINTS = ["/docs", "/redoc", "/openapi.json"]


class TestDocumentationDisabled:
    """Guarda uma decisao de produto: esta API nao serve documentacao automatica.

    O FastAPI monta /docs, /redoc e /openapi.json sozinho. Aqui os tres estao
    desligados de proposito, em src/app.py — quem quiser saber o que a API
    responde manda uma requisicao, com os exemplos prontos do README. Um
    FastAPI() distraido reabre os tres em silencio, e desfazer a decisao sem
    ninguem ver e exatamente o que estes dois testes impedem.

    Repare no INTERNAL-TOKEN do primeiro teste: sem ele os tres enderecos
    respondem 403, e 403 nao prova nada sobre documentacao. O middleware de
    token e mais externo que o roteamento, entao ele barra a requisicao antes
    de alguem perguntar se a rota existe. Com token a requisicao chega ao
    roteamento, e a resposta vira 404: a rota nao existe mesmo.
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
