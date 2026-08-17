# Bootcamp QI Tech — API boilerplate

Projeto base do Bootcamp: uma API REST em **Python + FastAPI**, com banco
**PostgreSQL**, rodando em **Docker**.

Você não precisa saber programar para começar. Precisa ter o Docker
instalado e vontade de mexer.

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

> Se a porta 3000 ou a 5432 já estiver ocupada na sua máquina, abra o
> `.env` e defina `API_PORT` / `DB_PORT` com portas livres.

---

## 2. Rodando os testes

Com a API de pé, em **outro terminal**:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -v
```

Os testes conversam com a API **por HTTP**, exatamente como um cliente de
verdade faria. Eles não espiam o código por dentro — não sabem que existe
FastAPI, nem SQLAlchemy. Só sabem: "mandei isso, tem que voltar aquilo".

Isso tem uma consequência bonita: **este projeto inteiro já foi reescrito
de um framework para outro, e nenhum teste precisou mudar.** Quando o
teste descreve o combinado em vez de descrever o código, ele sobrevive à
reforma.

---

## 3. As pastas

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

## 4. Configuração e senhas

Toda configuração entra por **variável de ambiente** — nunca escrita no
meio do código.

- `.env.example` → vai para o Git. Só tem valor de mentirinha.
- `.env` → fica só na sua máquina. **Nunca** vai para o Git.

Essa separação não é frescura. Senha commitada em repositório é uma das
formas mais comuns de vazamento de dados no mundo real, e não tem
desfazer: uma vez no histórico, está lá para sempre.

---

## 5. Autenticação

As rotas de negócio pedem um cabeçalho:

```
INTERNAL-TOKEN: default_token
```

(o valor está no seu `.env`). Sem ele, a API responde **403**.

Ficam abertas, de propósito: a rota raiz, o `/health_check` e o `/docs`.

---

## 6. Os códigos de erro

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
