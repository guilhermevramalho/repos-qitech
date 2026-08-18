# Bootcamp QI Tech — projeto base da API

Projeto base do Bootcamp: uma API REST em **Python + FastAPI**, com banco
**PostgreSQL**, rodando em **Docker**.

Você não precisa saber programar para começar. E não precisa instalar
Python, banco de dados nem nada disso na sua máquina: **o Docker faz
tudo** — inclusive rodar os testes.

---

## 0. O que você precisa ter instalado

São duas coisas. Só duas.

| O quê | Para quê | Como conferir |
|---|---|---|
| **Docker** (com o Docker Desktop no Mac/Windows) | roda a API, o banco e os testes | `docker compose version` |
| **Git** | trazer o projeto para o seu computador | `git --version` |

Abra o terminal e rode os dois comandos da coluna da direita. Se ambos
responderem um número de versão, você está pronto.

> **`docker compose version` deu erro?** Sua instalação do Docker é
> antiga demais (ou o Docker não está ligado). No Mac e no Windows,
> abra o **Docker Desktop** e espere a baleia parar de se mexer. Se o
> comando continuar falhando, reinstale pelo site oficial —
> o `docker compose` (com **espaço**) vem junto desde 2022.

Nada mais é necessário. Se em algum momento este projeto pedir que você
instale outra coisa, é um bug do projeto — avise a gente.

---

## 1. Rodando pela primeira vez

```bash
docker compose up
```

Um comando. Só isso, e não precisa criar nem copiar arquivo nenhum
antes: as configurações já vêm com valor padrão dentro do
`docker-compose.yml`.

O Docker baixa o Python, sobe o banco, cria as tabelas e liga a API. Na
primeira vez demora alguns minutos; depois é quase instantâneo.

Quando aparecer `Application startup complete`, abra no navegador:

### 👉 http://localhost:3000/docs

Essa página é o **Swagger**. Ela não foi escrita por ninguém: o FastAPI
gera a documentação lendo o próprio código. Cada rota tem um botão
**Try it out** que dispara a requisição de verdade, ali mesmo, sem
Postman e sem `curl`.

Comece por ela. É o jeito mais rápido de entender o que a API faz.

Para desligar tudo: `Ctrl+C` no terminal e depois

```bash
docker compose down
```

---

## 2. Rodando os testes

**Um comando, em outro terminal, dentro da pasta do projeto:**

```bash
docker compose run --rm tests
```

Não precisa ter a API de pé antes: se ela não estiver, este mesmo
comando sobe o banco, sobe a API, espera os dois responderem e só então
roda a suíte. Não precisa de Python instalado, nem de `pip`, nem de
cliente de banco — tudo isso vive dentro do container de testes.

O resultado sai assim:

```
tests/integration/test_healthcheck.py::TestHealthCheck::test_home PASSED
...
============================== 14 passed in 0.62s ==============================
```

Para rodar só um arquivo (ou só um teste), acrescente o caminho:

```bash
docker compose run --rm tests pytest -v tests/integration/test_healthcheck.py
```

Os testes conversam com a API **por HTTP**, exatamente como um cliente de
verdade faria. Eles não espiam o código por dentro — não sabem que existe
FastAPI, nem SQLAlchemy. Só sabem: "mandei isso, tem que voltar aquilo".

Isso tem uma consequência bonita: **este projeto inteiro já foi reescrito
de um framework para outro, e nenhum teste precisou mudar.** Quando o
teste descreve o combinado em vez de descrever o código, ele sobrevive à
reforma.

> **Escreveu um teste novo?** Rode o mesmo comando. O `tests/` da sua
> máquina está montado dentro do container: o que você salva agora vale
> no próximo comando, sem reconstruir imagem nenhuma.

### Atalho para quem já tem Python 3.11 (opcional)

Roda um pouco mais rápido, e o erro aparece direto no seu editor. Exige
Python na sua máquina — por isso é atalho, não o caminho principal:

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v
```

Só aqui o `.env` **é** obrigatório: fora do Docker ninguém preenche as
variáveis por você. Além dele, a API precisa estar de pé (`docker
compose up` em outro terminal), e o `DATABASE_URL` do `.env` precisa
apontar para a porta em que o banco está publicado na sua máquina.

---

## 3. Quando dá errado

Os três tropeços mais comuns, com a mensagem que você vai ver:

### `port is already allocated`

```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

Outro programa da sua máquina já usa aquela porta (é comum ter um
Postgres instalado ocupando a 5432). Não precisa descobrir qual: escolha
outras portas livres. É pra isto que serve o `.env` —

```bash
cp .env.example .env
```

— e, dentro dele, tire o `#` da frente destas duas linhas e troque os
números:

```
API_PORT=3001
DB_PORT=5433
```

Suba de novo. Agora a API atende em http://localhost:3001/docs.

### `failed to connect to the docker API`

```
failed to connect to the docker API at unix:///var/run/docker.sock;
check if the path is correct and if the daemon is running
```

O Docker não está ligado. Abra o **Docker Desktop** (Mac/Windows) e
espere ficar verde. No Linux: `sudo systemctl start docker`.

### `Nao consegui falar com a API` / `Nao consegui falar com o banco`

Só aparece no atalho local (fora do Docker). Quer dizer que a API ou o
banco não estão de pé, ou que a porta no seu `.env` não é a que eles
estão usando. Suba com `docker compose up` e confira as portas.

### Nada disso resolveu?

Este comando desliga e limpa **este** projeto (containers, rede e o
banco com tudo dentro) para você recomeçar do zero:

```bash
docker compose down -v
docker compose up
```

Para ver o que a API está dizendo enquanto roda: `docker compose logs -f api`.

---

## 4. As pastas

```
src/
  app.py           ← liga tudo: rotas, middlewares e tratamento de erro
  database.py      ← a conexão com o banco
  constants.py     ← as configurações, lidas do ambiente

  routers/         ← recebe a requisição HTTP e devolve a resposta
  schemas/         ← o formato do JSON que entra (e o que é inválido)
  controllers/     ← as regras de negócio: o que pode e o que não pode
  repositories/    ← as conversas com o banco
  models/          ← as tabelas, descritas em Python
  dtos/            ← monta o formato do JSON que sai
  errors/          ← os erros da API, cada um com seu código
  middlewares/     ← o que acontece com TODA requisição

database/
  database.sql     ← as tabelas, em SQL puro

tests/             ← os testes
```

### Por que tanta pasta?

Porque cada uma tem **um trabalho só**, e só conversa com a vizinha:

```
requisição → router → controller → repository → banco
                ↑          ↑
            valida o    decide o
             formato    que pode
```

O router não sabe SQL. O repository não sabe o que é uma regra de
negócio. Quando você precisa trocar o banco, mexe numa pasta. Quando a
regra muda, mexe na outra. É isso que permite um time inteiro trabalhar
no mesmo projeto sem pisar no pé um do outro.

Isso responde ao "por quê". Falta a outra metade — **"onde eu mexo
quando quero fazer X?"** —, e ela está em
**[docs/como-o-projeto-e-organizado.md](docs/como-o-projeto-e-organizado.md)**:
o caminho de uma requisição arquivo por arquivo, o que cada pasta pode e
não pode, e uma tabela de "quero fazer isto → mexo aqui". São dez
minutos de leitura, feitos para um momento com calma — não para o meio
da aula.

---

## 5. Configuração e senhas

Toda configuração entra por **variável de ambiente** — nunca escrita no
meio do código.

- **valor padrão** → escrito no `docker-compose.yml`, na forma
  `${VARIAVEL:-padrao}`. É por causa dele que o `docker compose up`
  funciona sem preparo nenhum.
- `.env` → **opcional**, fica só na sua máquina e **nunca** vai para o
  Git. Serve para sobrescrever um padrão (porta ocupada, outro token).
- `.env.example` → vai para o Git, e é a cópia de onde você parte. Só
  tem valor de mentirinha.

Essa separação não é frescura. Senha commitada em repositório é uma das
formas mais comuns de vazamento de dados no mundo real, e não tem
desfazer: uma vez no histórico, está lá para sempre.

Uma ressalva honesta: valor padrão de senha em arquivo versionado só
vale porque aqui é um projeto de estudo, sem dado de ninguém. Em
sistema de verdade, segredo não tem padrão — ele falta, e a aplicação
se recusa a subir sem ele.

---

## 6. Autenticação

As rotas de negócio pedem um cabeçalho:

```
INTERNAL-TOKEN: default_token
```

Sem ele, a API responde **403**. `default_token` é o valor padrão; para
trocar, ponha `INTERNAL_TOKEN=outra_coisa` no seu `.env`.

Ficam abertas, de propósito: a rota raiz, o `/health_check` e o `/docs`.

---

## 7. Os códigos de erro

Todo erro da API responde no mesmo formato, com um código próprio:

```json
{
  "title": "Bad Request",
  "description": "Field required in hello",
  "translation": "Payload Invalido",
  "code": "QIT000001"
}
```

| Código      | Quando acontece                                  |
|-------------|--------------------------------------------------|
| `QIT000001` | o JSON enviado está fora do formato              |
| `QIT000002` | faltou o `INTERNAL-TOKEN`, ou ele está errado    |
| `QIT000010` | um parâmetro do endereço está inválido           |
| `QIT000404` | essa rota não existe                             |
| `QIT000405` | a rota existe, mas não aceita esse método        |
| `QIT000500` | erro inesperado (o time é avisado)               |
| `QIT001001` | a entidade procurada não existe                  |
| `QIT001002` | a entidade já está num status final              |

Um código estável vale mais que uma mensagem bonita: quem integra com a
API programa em cima do código, não do texto.

Os números não são sorteados. Eles vêm em duas faixas:

- **`QIT000…`** — os erros que **toda** API tem: JSON errado, sem token,
  rota inexistente. Estão em `src/errors/base_error.py` e você não
  precisa mexer neles.
- **`QIT001…`** — os erros das **regras deste projeto**. Estão em
  `src/errors/custom_errors.py`, e é aí que os seus entram: o próximo
  livre é o `QIT001003`.

Não repita um número. Se repetir, a API **não sobe** — tem uma checagem
no start (`error_verification`, em `src/errors/base_error.py`) que
procura código repetido e derruba a aplicação de propósito. Parecer
chato agora é melhor que dois erros diferentes chegarem ao cliente com o
mesmo código.

---

## 8. A licença

Este projeto é **MIT** — pode usar, copiar, modificar e levar para o seu
portfólio, inclusive em trabalho pago. O único pedido é manter o arquivo
`LICENSE` junto quando você distribuir o código.
