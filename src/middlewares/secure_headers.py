from fastapi import FastAPI, Request


# Cabeçalhos que instruem o navegador a se proteger.
# São baratos de ligar e evitam uma família inteira de ataques.
SECURITY_HEADERS = {
    # Não revela qual servidor está rodando: informação de menos
    # para quem estiver procurando uma versão com falha conhecida.
    "Server": "undisclosed",
    # Proíbe colocar esta página dentro de um iframe de outro site.
    "x-frame-options": "SAMEORIGIN",
    "x-xss-protection": "1; mode=block",
    # Impede o navegador de "adivinhar" o tipo do arquivo.
    "x-content-type-options": "nosniff",
    # Exige HTTPS nas próximas visitas.
    "strict-transport-security": "max-age=63072000; includeSubdomains",
    # Só carrega script/estilo vindos do próprio domínio.
    "content-security-policy": "default-src 'self'",
}


def register_secure_headers_middleware(application: FastAPI) -> None:
    @application.middleware("http")
    async def add_secure_headers(request: Request, call_next):
        response = await call_next(request)

        for header_name, header_value in SECURITY_HEADERS.items():
            response.headers[header_name] = header_value

        return response
