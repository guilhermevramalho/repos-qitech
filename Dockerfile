# Imagem oficial e publica do Python. Qualquer pessoa consegue baixar.
FROM python:3.11-slim AS base

# Roda a aplicacao com um usuario sem privilegios, nunca como root.
RUN adduser --system --no-create-home user

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copiar so o requirements primeiro faz o Docker reaproveitar o cache:
# enquanto as dependencias nao mudam, ele nao reinstala tudo de novo.
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip && pip install -r /requirements.txt

WORKDIR /app
COPY src /app

FROM base AS api
RUN chown -R user /app
USER user

# --no-server-header: o uvicorn nao anuncia a propria versao.
# Quem responde o cabecalho Server e o nosso middleware de seguranca.
CMD uvicorn app:app --host 0.0.0.0 --port 3000 --no-server-header


# Imagem que roda os testes — usada por:
#
#     docker compose run --rm tests
#
# Ela existe pra que ninguem precise instalar Python, pytest ou psql na
# propria maquina: o Docker ja tem tudo dentro. Esta imagem NUNCA sobe
# pra producao — as dependencias de teste ficam so aqui.
FROM base AS tests
COPY requirements-dev.txt /requirements-dev.txt
RUN pip install -r /requirements-dev.txt

WORKDIR /workspace
COPY tests /workspace/tests
COPY database /workspace/database

# Aqui tambem sem privilegios: assim o container nunca cria arquivo de
# root dentro da sua pasta (o tests/ da sua maquina esta montado aqui).
USER user

CMD ["pytest", "-v"]
