# Como o projeto é organizado

Dentro de `src/` tem dez pastas. Para um programa que responde oito
endereços, parece muita pasta — e no começo assusta mesmo.

Este texto explica por que elas existem, o que cada uma pode e não pode
fazer, e principalmente: **onde você mexe quando quer fazer alguma
coisa**.

Não precisa decorar. Leia uma vez para pegar o mapa e volte quando
estiver perdido.

---

## 1. O caminho de uma requisição

Toda requisição atravessa as mesmas camadas, sempre na mesma ordem.
Este é o `POST /sample_entity`, que cria uma entidade:

```
  requisição chega
        ↓
  src/middlewares/     confere o INTERNAL-TOKEN. Sem ele, para aqui (403)
        ↓
  src/routers/         que endereço é esse? quem cuida dele?
        ↓              (antes da 1ª linha da rota rodar, src/schemas/
        ↓               confere o JSON. Torto, para aqui: 400)
        ↓
  src/controllers/     pode fazer isso? é aqui que mora a regra
        ↓
  src/repositories/    a conversa com o banco — só aqui existe consulta
        ↓
  src/models/          a tabela, descrita em Python
        ↓
      banco
        ↓
  src/dtos/            traduz o objeto do banco no JSON da resposta
        ↓
  resposta sai
```

Repare no que isso compra: quando o código chega no **controller**, o
JSON já foi conferido. Quando chega no **repository**, a decisão já foi
tomada. Cada camada confia no trabalho da anterior e só cuida do seu
pedaço.

Abra os arquivos e siga o caminho uma vez. Vale mais que ler três vezes
este texto.

---

## 2. O que cada pasta pode e não pode

| Pasta | Pode | Não pode |
|---|---|---|
| `routers/` | receber a requisição, chamar **um** controller, devolver a resposta | saber SQL, decidir regra de negócio |
| `schemas/` | dizer qual JSON é aceito na entrada, e recusar o que não é | falar com banco, decidir regra |
| `controllers/` | decidir o que pode e o que não pode, chamar repositories, salvar (`commit`) | escrever consulta, saber que existe HTTP |
| `repositories/` | buscar, criar e atualizar no banco | decidir se aquilo era permitido |
| `models/` | descrever as tabelas em Python | ter regra dentro |
| `dtos/` | transformar o objeto do banco no dicionário que vira a resposta | buscar coisa no banco, decidir regra |
| `errors/` | definir cada erro: código, mensagem e status HTTP | ter regra de negócio dentro |
| `middlewares/` | fazer algo em **toda** requisição (token, log, cabeçalho) | conhecer uma rota específica |
| `connectors/` | chamar um serviço de fora: endereço, timeout e o desembrulho da resposta | decidir regra de negócio, falar com o nosso banco |
| `utils/` | ferramenta de uso geral — aqui, só o logger | virar o depósito do que não se sabe onde pôr |

Um exemplo do que isso significa na prática: em
`src/controllers/sample_entity_controller.py` você lê
`if old_status != "pending": raise SampleEntityFinalStatus(...)`. Essa
frase é a regra do negócio, e ela mora no controller. Em
`src/repositories/sample_entity_repository.py` não existe nenhuma frase
dessas: o único `if` de lá decide se a busca leva um filtro a mais, e
isso não é regra — é jeito de buscar.

---

## 3. Onde eu mexo quando quero...

| Quero... | Mexo em | Na ordem |
|---|---|---|
| **aceitar um campo novo** no JSON de entrada | `src/schemas/sample_entity.py` | se o campo vai para o banco, também `database/database.sql` e `src/models/` |
| **mudar o que a resposta devolve** | `src/dtos/sample_entity_dto.py` | é o único lugar; se o campo ainda não existe no banco, antes disso `database/database.sql` e `src/models/` |
| **criar uma rota nova** numa entidade que já existe | `src/routers/sample_entity.py` | e o método no controller, se a regra for nova |
| **mudar uma regra** ("não pode X") | `src/controllers/sample_entity_controller.py` | e um erro novo em `src/errors/custom_errors.py`, se precisar |
| **consultar o banco de outro jeito** (filtrar, ordenar, contar) | `src/repositories/sample_entity_repository.py` | o controller chama o método novo |
| **criar uma tabela** | `database/database.sql` | depois `src/models/` e o `__init__.py` da pasta |
| **criar uma entidade inteira** (rota + regra + tabela) | um arquivo em cada pasta | `database.sql` → `models/` → `repositories/` → `controllers/` → `schemas/` → `routers/` → registrar em `src/app.py` |
| **fazer algo em toda requisição** | `src/middlewares/` | registrar em `src/app.py` |
| **chamar outro serviço** | `src/connectors/` | quem chama o connector é o controller, nunca o router |

Três armadilhas que pegam quase todo mundo. As duas últimas custam caro
pelo mesmo motivo: a mensagem de erro aponta para o sintoma, não para a
causa.

**Criou um arquivo e o Python diz que não existe?** Cada pasta tem um
`__init__.py` que lista o que ela oferece. Abra o da pasta (por exemplo
`src/repositories/__init__.py`) e acrescente a sua linha.

**E a ORDEM das linhas do `src/models/__init__.py` importa.** Abra
`src/models/sample_entity.py` e repare no `from models import
SampleEntityStatus`: o arquivo importa de dentro do próprio pacote em
que ele mora. Isso só funciona porque o `__init__.py` lista o
`SampleEntityStatus` **antes** do `SampleEntity` — quando a linha do
`SampleEntity` roda, o status já foi carregado.

Inverta as duas linhas e o Python responde:

```
ImportError: cannot import name 'SampleEntityStatus' from partially
initialized module 'models' (most likely due to a circular import)
```

A mensagem culpa uma "importação circular", que não é bem o que
aconteceu — e você vai procurar um ciclo que não existe. A regra é
simples: **entidade nova que se relaciona com outra entra no
`__init__.py` depois daquela de que ela depende.**

**Mexeu no `database/database.sql` e nada mudou?** Aquele arquivo roda
uma vez só: **quando o banco nasce**. Depois disso o Postgres nunca mais
olha para ele — nem no `docker compose up` seguinte, nem num
`docker compose restart db`. O sintoma aparece longe daí, na resposta da
API ou no log:

```
psycopg2.errors.UndefinedTable: relation "minha_tabela" does not exist
```

Ela não diz "seu SQL não rodou": diz que a tabela não existe. Dá vontade
de reler o SQL procurando erro de digitação, e não tem nenhum.

Para o banco nascer de novo, com o schema novo:

```bash
docker compose down -v
docker compose up
```

O `-v` é o que apaga o volume, o disco do banco — e **ele leva junto
tudo que você criou na mão** até aqui. Não tem meio-termo: ou o banco
nasce de novo com o schema novo, ou continua com o antigo. Em sistema de
verdade ninguém apaga o banco, claro: lá a mudança de schema entra por
um comando aplicado no deploy, e é por isso que este projeto guarda o
schema num arquivo versionado em vez de deixá-lo só dentro do banco.

---

## 4. A regra que explica todas as outras

A seta anda num sentido só:

```
routers → controllers → repositories → models
```

Um router pode chamar um controller. Um controller pode chamar um
repository. **O contrário nunca acontece** — repository não chama
controller, model não sabe que existe rota.

Por que isso importa, em três respostas concretas:

- **Você acha o problema mais rápido.** Erro no formato do JSON? É
  `schemas/`. Salvou o que não devia? É `controllers/`. Você já começa
  a procurar no lugar certo.
- **Trocar uma peça não derruba as outras.** Este projeto já foi
  reescrito de um framework para outro, e os testes não mudaram — porque
  quem conhecia o framework era só uma camada.
- **Três pessoas trabalham juntas sem colidir.** Uma mexe na regra,
  outra na consulta, outra na rota. Arquivos diferentes, sem pisar no pé
  um do outro.

Quando você estiver com pressa, vai dar vontade de escrever a consulta
direto no router. Funciona. E é exatamente assim que um projeto vira
aquele em que ninguém mais encontra nada.

---

## 5. Schemas e DTOs: o que entra e o que sai

Duas pastas falam de formato, e é fácil confundi-las. A divisão é a
direção: **o `schemas/` cuida do que ENTRA, o `dtos/` cuida do que
SAI.**

- `src/schemas/sample_entity.py` descreve o JSON que o cliente manda.
  Quem lê isso é o Pydantic, antes da primeira linha da rota rodar:
  campo faltando, tipo errado ou campo a mais viram 400 ali mesmo.
- `src/dtos/sample_entity_dto.py` faz o caminho de volta. O repository
  entrega o objeto do banco; o DTO devolve um dicionário simples, e é
  esse dicionário que vira o JSON da resposta.

Abra os dois ao lado de `src/models/sample_entity.py` e a diferença
fica óbvia. Na **tabela**, o `hello` está escondido dentro de uma
coluna JSON e o status é um número apontando para outra tabela. Na
**resposta**, os dois são campos planos, com nome de gente. Quem faz
essa travessia é o DTO, e é por isso que ele existe.

Campo novo na resposta? Acrescente no `dtos/`. Nenhum outro arquivo
precisa saber.

Uma consequência que vale conhecer: **o que o DTO monta é exatamente o
que sai.** Não existe ninguém depois dele conferindo a forma — se um
campo interno entrar naquele dicionário, ele vai para o cliente do
mesmo jeito. Quando aparecer na resposta um dado que você não queria
mostrar, comece procurando aqui.
