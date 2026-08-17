# Bootcamp QI Tech — API boilerplate

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
cp .env.example .env
docker compose up
```

É isso. O Docker baixa o Python, sobe o banco, cria as tabelas e liga a
API. Na primeira vez demora alguns minutos; depois é quase instantâneo.

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
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v
```

Aqui a API **precisa** estar de pé (`docker compose up` em outro
terminal), e o `DATABASE_URL` do seu `.env` precisa apontar para a porta
em que o banco está publicado na sua máquina.

---

## 3. Quando dá errado

Os quatro tropeços mais comuns, com a mensagem que você vai ver:

### `port is already allocated`

```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

Outro programa da sua máquina já usa aquela porta (é comum ter um
Postgres instalado ocupando a 5432). Não precisa descobrir qual: abra o
`.env` e escolha outras portas livres —

```
API_PORT=3001
DB_PORT=5433
```

— e suba de novo. Agora a API atende em http://localhost:3001/docs.
As duas linhas já estão no seu `.env`, comentadas: basta tirar o `#`.

### `failed to connect to the docker API`

```
failed to connect to the docker API at unix:///var/run/docker.sock;
check if the path is correct and if the daemon is running
```

O Docker não está ligado. Abra o **Docker Desktop** (Mac/Windows) e
espere ficar verde. No Linux: `sudo systemctl start docker`.

### `env file ... .env not found`

Faltou o primeiro comando do passo 1:

```bash
cp .env.example .env
```

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

---

## 5. Configuração e senhas

Toda configuração entra por **variável de ambiente** — nunca escrita no
meio do código.

- `.env.example` → vai para o Git. Só tem valor de mentirinha.
- `.env` → fica só na sua máquina. **Nunca** vai para o Git.

Essa separação não é frescura. Senha commitada em repositório é uma das
formas mais comuns de vazamento de dados no mundo real, e não tem
desfazer: uma vez no histórico, está lá para sempre.

---

## 6. Autenticação

As rotas de negócio pedem um cabeçalho:

```
INTERNAL-TOKEN: default_token
```

(o valor está no seu `.env`). Sem ele, a API responde **403**.

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
| `BAP000001` | a entidade procurada não existe                  |
| `BAP000002` | a entidade já está num status final              |

Um código estável vale mais que uma mensagem bonita: quem integra com a
API programa em cima do código, não do texto.
