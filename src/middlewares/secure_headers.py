from fastapi import FastAPI, Request


# Cabecalhos que instruem o navegador a se proteger.
# Sao baratos de ligar e evitam uma familia inteira de ataques.
SECURITY_HEADERS = {
    # Nao revela qual servidor esta rodando: informacao de menos
    # para quem estiver procurando uma versao com falha conhecida.
    "Server": "undisclosed",
    # Proibe colocar esta pagina dentro de um iframe de outro site.
    "x-frame-options": "SAMEORIGIN",
    "x-xss-protection": "1; mode=block",
    # Impede o navegador de "adivinhar" o tipo do arquivo.
    "x-content-type-options": "nosniff",
    # Exige HTTPS nas proximas visitas.
    "strict-transport-security": "max-age=63072000; includeSubdomains",
    # So carrega script/estilo vindos do proprio dominio.
    "content-security-policy": "default-src 'self'",
}


def register_secure_headers_middleware(application: FastAPI) -> None:
    @application.middleware("http")
    async def add_secure_headers(request: Request, call_next):
        response = await call_next(request)

        for header_name, header_value in SECURITY_HEADERS.items():
            response.headers[header_name] = header_value

        return response
