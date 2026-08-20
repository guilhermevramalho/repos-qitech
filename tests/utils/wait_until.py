import time


TIMEOUT_SECONDS = 10.0
INTERVAL_SECONDS = 0.2

TIMEOUT_MESSAGE = (
    "Esperei {timeout:.0f} segundos e isto nao aconteceu: {description}.\n"
    "\n"
    "Quem faz esse trabalho nao e a API: e o consumer, num container\n"
    "separado. Confira se ele esta de pe e o que ele andou fazendo:\n"
    "\n"
    "  docker compose ps consumer\n"
    "  docker compose logs consumer"
)


def wait_until(condition, description: str, timeout_seconds: float = TIMEOUT_SECONDS) -> None:
    """Fica perguntando ate a resposta mudar — ou desiste e explica.

    Testar coisa assincrona tem um jeito proprio: quando a requisicao
    responde, o trabalho ainda nao aconteceu. Nao da pra conferir na
    linha seguinte, e tambem nao se resolve com um `sleep` fixo — o
    numero certo pra ele nao existe: pequeno demais e o teste falha sem
    motivo; grande demais e a suite fica lenta pra sempre.

    O jeito e este: pergunta de novo a cada `INTERVAL_SECONDS`, para no
    instante em que a resposta chega e desiste depois de
    `TIMEOUT_SECONDS`. No caminho normal isto custa menos de um segundo;
    os 10 segundos existem so pra maquina de alguem num dia ruim.
    """
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        if condition():
            return

        time.sleep(INTERVAL_SECONDS)

    raise AssertionError(TIMEOUT_MESSAGE.format(timeout=timeout_seconds, description=description))
