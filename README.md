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

O Docker baixa o Python, sobe o banco, sobe a fila, cria as tabelas e
liga a API — mais o **consumer**, um segundo programa deste projeto que
não atende requisição nenhuma: ele só olha a fila e trabalha no que
encontra (seção 1, exemplo 7). Na primeira vez demora alguns minutos;
depois é quase instantâneo.

São quatro coisas de pé, e vale saber o nome de cada uma:

| Serviço | O que é |
|---|---|
| `api` | a API que responde às suas requisições |
| `db` | o banco de dados (PostgreSQL) |
| `localstack` | a **fila**. Em produção a QI Tech usa o SQS, da Amazon; aqui o localstack faz o papel dele dentro do seu Docker — sem conta na Amazon, sem cartão |
| `consumer` | quem tira as mensagens da fila e faz o trabalho |

Quando aparecer `Application startup complete`, a API está no ar. Abra
no navegador:

### 👉 http://localhost:3000

Você vai ver isto:

```json
{"service":"bootcamp-api","id":"8"}
```

Pouca coisa, e de propósito: essa rota só diz "estou viva, e eu sou este
serviço". Mas você acabou de fazer uma **requisição HTTP** — a mesma
coisa que o navegador faz ao abrir qualquer site.

### Agora as outras rotas

Elas não abrem no navegador, porque exigem um cabeçalho: o
`INTERNAL-TOKEN`, que é a senha da API (seção 6). Para mandar um
cabeçalho a gente usa o `curl`, um programa de linha de comando que já
vem instalado no Mac, no Linux e no Windows.

**Abra um segundo terminal** — o primeiro está ocupado rodando a API — e
cole um comando de cada vez.

> **No Windows**, use o **Git Bash**: ele veio junto com o Git da seção
> 0. No PowerShell estes comandos não funcionam, porque lá `curl` é o
> apelido de outro programa, com outra sintaxe.

#### 1. Criar uma entidade

```bash
curl -X POST http://localhost:3000/sample_entity \
  -H "INTERNAL-TOKEN: default_token" \
  -H "Content-Type: application/json" \
  -d '{"hello": "world"}'
```

```json
{"sample_entity_key":"3fbf83e9-e5fc-4e0f-8427-db6a1a50f964"}
```

Esse `sample_entity_key` é o endereço da entidade que você acabou de
criar. **Copie o seu** — ele nasce diferente a cada vez, e nos comandos
abaixo você troca o que está escrito aqui pelo seu.

#### 2. Buscar a entidade

```bash
curl http://localhost:3000/sample_entity/3fbf83e9-e5fc-4e0f-8427-db6a1a50f964 \
  -H "INTERNAL-TOKEN: default_token"
```

```json
{"hello":"world","status":"pending","sample_entity_key":"3fbf83e9-e5fc-4e0f-8427-db6a1a50f964","counter":0}
```

Você mandou um campo e voltaram quatro. Os outros três a API inventou
sozinha: o endereço, o status inicial e um contador zerado.

#### 3. Listar as entidades

```bash
curl http://localhost:3000/sample_entities \
  -H "INTERNAL-TOKEN: default_token"
```

```json
{"data":[{"hello":"world","status":"pending","sample_entity_key":"3fbf83e9-e5fc-4e0f-8427-db6a1a50f964","counter":0}],"limit":10,"page":0,"is_last_page":true}
```

Vêm de dez em dez. Para pedir outra quantidade ou outra página,
acrescente `?limit=2&page=0` ao endereço. O `is_last_page` já responde a
pergunta seguinte — "tem mais?" — sem custar uma segunda requisição.

#### 4. Somar 1 no contador

```bash
curl -i -X PUT http://localhost:3000/webhook/sample_entity/3fbf83e9-e5fc-4e0f-8427-db6a1a50f964/increment_counter \
  -H "INTERNAL-TOKEN: default_token"
```

```
HTTP/1.1 204 No Content
```

Esta rota não responde nada — por isso o `-i`, que manda o `curl`
mostrar também o **status** da resposta. `204` quer dizer "deu certo e
não tenho nada a dizer". Repita o comando 2: o `counter` agora é `1`.

#### 5. Mudar o status

```bash
curl -X PUT http://localhost:3000/sample_entity/3fbf83e9-e5fc-4e0f-8427-db6a1a50f964 \
  -H "INTERNAL-TOKEN: default_token" \
  -H "Content-Type: application/json" \
  -d '{"status": "success"}'
```

```json
{"sample_entity_key":"3fbf83e9-e5fc-4e0f-8427-db6a1a50f964"}
```

Repita o comando 2: o `status` virou `success`. E rode este comando 5
mais uma vez — agora a API recusa:

```json
{"title":"Entity cannot change status","description":"Entity with status success cannot update to success.","translation":"Essa entidade não pode ser atualizada.","code":"QIT001002"}
```

Isso é uma **regra de negócio**, não um erro de digitação: entidade que
já terminou não volta atrás. A frase que decide isso mora em
`src/controllers/sample_entity_controller.py`, e você pode ir ler.

#### 6. Mandar um JSON torto

```bash
curl -X POST http://localhost:3000/sample_entity \
  -H "INTERNAL-TOKEN: default_token" \
  -H "Content-Type: application/json" \
  -d '{}'
```

```json
{"title":"Bad Request","description":"Field required in hello","translation":"Payload Inválido","code":"QIT000001"}
```

**400**, e nada foi criado. O `hello` é obrigatório, e quem recusou não
foi a regra de negócio: foi o `src/schemas/`, antes da primeira linha da
rota rodar. Pedido torto não chega a custar uma consulta ao banco.

#### 7. Pedir um processamento — e ver acontecer depois

Este exemplo é diferente de todos os anteriores, e é o mais importante
deles.

Ele precisa de uma entidade **nova**: a que você vem usando já virou
`success` no comando 5, e entidade que terminou não muda mais. Rode o
comando 1 outra vez e use a chave nova nos dois comandos abaixo.

```bash
curl -i -X POST http://localhost:3000/sample_entity/SUA_CHAVE_NOVA/process \
  -H "INTERNAL-TOKEN: default_token"
```

```
HTTP/1.1 202 Accepted
{"sample_entity_key":"a1b2c3d4-..."}
```

**202**, não 200. A diferença é o coração do assunto: `200` quer dizer
"pronto, feito"; `202` quer dizer **"aceitei o seu pedido e vou fazer"**.
Quando essa resposta chegou até você, o trabalho ainda não havia
acontecido — a API só deixou um recado na fila e foi embora atender
outra pessoa.

Agora repita o comando 2:

```json
{"hello":"world","status":"success","sample_entity_key":"a1b2c3d4-...","counter":0}
```

O status virou `success`, e **não foi a API que virou**: foi o consumer,
o outro programa, que pegou o recado na fila e fez o trabalho. Dá para
assistir:

```bash
docker compose logs consumer
```

```
[INFO] bootcamp-consumer.consumer - Recebi a mensagem process_sample_entity: {'sample_entity_key': 'a1b2c3d4-...'}
[INFO] bootcamp-consumer.consumer - Mensagem processada e apagada da fila
```

Aqui isso leva meio segundo, então talvez você nem pegue o meio do
caminho. Num sistema de verdade o trabalho pode levar minutos — gerar um
relatório, falar com um banco, mandar mil e-mails — e é justamente por
isso que ele não acontece dentro da requisição: ninguém, nem uma pessoa
nem outro sistema, fica com o telefone na orelha esperando dez minutos.

**Por que isso importa tanto?** Porque muda o que pode dar errado. A
mensagem já foi aceita, mas o trabalho pode falhar depois — e aí alguém
precisa tentar de novo. Quem cuida disso, e como, está explicado com
calma nos comentários de **`src/consumer.py`**. Vale a leitura: é uma
das coisas que separa código de estudo de código de produção.

Para olhar a fila por dentro, sem instalar nada:

```bash
docker compose exec localstack awslocal sqs list-queues
```

#### Esqueceu o `-H "INTERNAL-TOKEN: ..."`?

A API responde **403** e nem chega a olhar o resto:

```json
{"title":"Forbidden","description":"Request must be internal","translation":"Requisição precisa ser interna","code":"QIT000002"}
```

#### Toda resposta vem com um número de protocolo

Repare no `-i` deste comando: ele mostra os **cabeçalhos** da resposta,
não só o corpo.

```bash
curl -i "http://localhost:3000/sample_entities?limit=1" \
  -H "INTERNAL-TOKEN: default_token"
```

```
HTTP/1.1 200 OK
content-type: application/json
x-request-id: 8f3c1e42-1b0d-4f77-9a55-2e4c9d1f0abc
server: undisclosed
...
```

Esse `x-request-id` é o **número de protocolo** da sua requisição: um
nome único, criado no instante em que ela chegou. Copie o seu e procure
por ele no log:

```bash
docker compose logs api | grep 8f3c1e42
```

```
[INFO] bootcamp-api.middlewares.request_logger [8f3c1e42-...] - ENTROU GET /sample_entities?limit=1
[INFO] bootcamp-api.middlewares.request_logger [8f3c1e42-...] - SAIU 200 GET /sample_entities - 2.9 ms
```

Duas linhas, o mesmo nome nas duas — e nenhuma outra requisição usa esse
nome. Serve para o dia em que alguém disser "deu erro por volta das
14h30": sem o número, você abre o log e encontra mil linhas parecidas, de
mil requisições diferentes, embaralhadas, porque a API atende várias ao
mesmo tempo e o log é um só. Com o número, achar a agulha é um `grep`.

Se quem chamou já mandar um `x-request-id`, a API **respeita o que veio**
e usa o mesmo — é assim que se segue um único pedido atravessando vários
sistemas:

```bash
curl -i "http://localhost:3000/sample_entities?limit=1" \
  -H "INTERNAL-TOKEN: default_token" \
  -H "X-Request-ID: meu-teste-1"
```

Experimente mandar um valor esquisito nesse cabeçalho — com espaços, ou
bem comprido. A API não devolve o que você mandou: ela troca por um novo.
O porquê está em `src/utils/request_context.py`, e é uma das poucas
lições de segurança que cabem em cinco linhas.

> Só o `/` e o `/health_check` não aparecem no log: o Docker consulta o
> health check a cada três segundos, e sem essa exceção o log seria
> quase só isso. Eles ganham o `x-request-id` como todo mundo — o que
> não ganham é a linha de log.

### Todas as rotas

Oito endereços — este é o mapa inteiro da API:

| Método e rota | O que faz | Responde |
|---|---|---|
| `GET /` | diz qual serviço é este | `200` + nome e id |
| `GET /health_check` | diz se a API está de pé | `204`, sem corpo |
| `POST /sample_entity` | cria uma entidade | `201` + o `sample_entity_key` |
| `GET /sample_entity/{key}` | busca uma entidade | `200` + a entidade |
| `GET /sample_entities` | lista, de dez em dez (`?limit=&page=&status=`) | `200` + a página |
| `PUT /sample_entity/{key}` | muda o status (`success` ou `failed`) | `202` + o `sample_entity_key` |
| `POST /sample_entity/{key}/process` | põe o processamento na fila; quem faz é o consumer | `202` + o `sample_entity_key` |
| `PUT /webhook/sample_entity/{key}/increment_counter` | soma 1 no contador | `204`, sem corpo |

As seis de baixo exigem o `INTERNAL-TOKEN` (seção 6). As duas de cima
são abertas — a primeira você já usou: foi ela que respondeu no
navegador.

Para desligar tudo: `Ctrl+C` no terminal da API e depois

```bash
docker compose down
```

---

## 2. Rodando os testes

**Um comando, em outro terminal, dentro da pasta do projeto:**

```bash
docker compose run --rm tests
```

Não precisa ter nada de pé antes: se não estiver, este mesmo comando
sobe o banco, a fila, a API e o consumer, espera todos responderem e só
então roda a suíte. Não precisa de Python instalado, nem de `pip`, nem de
cliente de banco — tudo isso vive dentro do container de testes.

O resultado sai assim:

```
tests/integration/test_documentation_disabled.py::TestDocumentationDisabled::test_documentation_endpoints_are_not_served PASSED
...
============================== 31 passed in 1.50s ==============================
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

Um deles tem um problema a mais para resolver:
`tests/integration/test_sample_entity_process.py` testa o fluxo da fila,
onde a resposta chega **antes** do trabalho acontecer — não dá para
conferir na linha seguinte. E também não se resolve com um `sleep`: o
número certo para ele não existe. O jeito é perguntar de novo até a
resposta mudar, e é o que o `wait_until` faz (em
`tests/utils/wait_until.py`).

> **Escreveu um teste novo?** Rode o mesmo comando. O `tests/` da sua
> máquina está montado dentro do container: o que você salva agora vale
> no próximo comando, sem reconstruir imagem nenhuma.

### Atalho para quem já tem Python 3.11 (opcional)

Roda um pouco mais rápido, e o erro aparece direto no seu editor. Exige
Python na sua máquina — por isso é atalho, não o caminho principal.

Rode os comandos **na raiz do projeto** — a pasta onde está este
README. É de lá que o `pytest` encontra a suíte inteira:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v
```

**O atalho é só do Python: o Docker continua obrigatório.** Os testes
batem numa API de verdade, que grava num banco de verdade e manda
recado por uma fila de verdade — e nada disso roda na sua máquina.
Deixe `docker compose up` de pé em outro terminal: não basta a API, o
banco e o consumer também precisam estar no ar (sem alguém consumindo
a fila, o teste do fluxo assíncrono espera para sempre).

Aqui o `.env` é **opcional**: sem ele, os testes procuram a API em
`0.0.0.0:3000` e o banco em `localhost:5432` — exatamente onde o
`docker compose up` publica os dois. Ele volta a ser necessário quando
você mudou alguma porta ou o token, e é o lugar de dizer isso:

```bash
cp .env.example .env
```

---

## 3. Quando dá errado

Os tropeços mais comuns, com a mensagem que você vai ver:

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

Suba de novo. Agora a API atende em http://localhost:3001 — e nos
comandos `curl` da seção 1 você troca `3000` por `3001`.

### `failed to connect to the docker API`

```
failed to connect to the docker API at unix:///var/run/docker.sock;
check if the path is correct and if the daemon is running
```

O Docker não está ligado. Abra o **Docker Desktop** (Mac/Windows) e
espere ficar verde. No Linux: `sudo systemctl start docker`.

### `Não consegui falar com a API` / `Não consegui falar com o banco`

Só aparece no atalho local (fora do Docker). Quer dizer que a API ou o
banco não estão de pé, ou que a porta no seu `.env` não é a que eles
estão usando. Suba com `docker compose up` e confira as portas.

### `relation "..." does not exist`

```
psycopg2.errors.UndefinedTable: relation "minha_tabela" does not exist
```

Você mexeu no `database/database.sql`, e o banco não ficou sabendo.
Aquele arquivo roda **uma vez só: quando o banco nasce.** Depois disso o
Postgres nunca mais olha para ele — subir de novo com `docker compose
up` não adianta, e `docker compose restart db` também não.

Repare no que a mensagem faz com você: ela não diz "seu SQL não rodou",
diz que a tabela não existe. Você vai reler o seu SQL procurando um erro
de digitação que não está lá.

Para o banco nascer de novo, já com o schema novo:

```bash
docker compose down -v
docker compose up
```

O `-v` é o que apaga o volume — o disco do banco. **Ele leva junto tudo
que você tinha criado na mão**, as entidades dos `curl` da seção 1. Não
tem meio-termo: ou o banco nasce de novo com o schema novo, ou continua
com o antigo. (Em sistema de verdade é outra história — lá ninguém apaga
o banco, e a mudança de schema entra por um comando aplicado no deploy.)

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
  consumer.py      ← o outro programa: tira mensagens da fila e trabalha
  database.py      ← onde a sessão de banco mora (quem cuida do ciclo
                     dela é middlewares/session_manager.py)
  sqs.py           ← a conexão com a fila
  constants.py     ← as configurações, lidas do ambiente

  routers/         ← recebe a requisição HTTP e devolve a resposta
  schemas/         ← o formato do JSON que entra
  controllers/     ← as regras de negócio: o que pode e o que não pode
  repositories/    ← as conversas com o banco
  models/          ← as tabelas, descritas em Python
  dtos/            ← traduz o objeto do banco no JSON que sai
  errors/          ← os erros da API, cada um com seu código
  middlewares/     ← o que acontece com TODA requisição
  connectors/      ← as conversas com outros serviços

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

O `consumer.py` entra por outra porta e chega no mesmo lugar:

```
mensagem na fila → consumer → controller → repository → banco
```

Ele não tem router nem schema — não existe requisição HTTP para validar.
Do controller em diante, é o **mesmo caminho**: a regra de negócio é uma
só, não importa se o pedido chegou por uma requisição ou por uma
mensagem. Regra duplicada é regra que vai divergir.

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

### E aquela chave da Amazon no `docker-compose.yml`?

Você vai ver isto lá:

```yaml
AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:-test}
```

Chave de nuvem em arquivo versionado é exatamente o que o parágrafo
acima proíbe — e aqui está tudo bem, por um motivo específico: **essa
chave não abre nada.** Quem responde do outro lado é o `localstack`, na
sua máquina, e ele não confere o valor. Não existe conta na Amazon neste
projeto, e não há o que vazar.

Repare no que isso ensina: o que decide se um valor é segredo não é o
nome dele, é o que ele abre. `AWS_ACCESS_KEY_ID` **parece** perigoso e
não é; o `DATABASE_URL` de um banco de produção **não parece** e é.

---

## 6. Autenticação

As rotas de negócio pedem um cabeçalho:

```
INTERNAL-TOKEN: default_token
```

Sem ele, a API responde **403**. `default_token` é o valor padrão; para
trocar, ponha `INTERNAL_TOKEN=outra_coisa` no seu `.env`.

Ficam abertas, de propósito, só duas: a rota raiz e o `/health_check`
— esta última porque quem a consulta é o próprio Docker, que não tem
como mandar cabeçalho.

---

## 7. Os códigos de erro

Todo erro da API responde no mesmo formato, com um código próprio:

```json
{
  "title": "Bad Request",
  "description": "Field required in hello",
  "translation": "Payload Inválido",
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
