# Como o projeto é organizado

Dentro de `src/` tem nove pastas. Para um programa que responde sete
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
  src/dtos/            monta o JSON que volta
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
| `schemas/` | dizer qual JSON é aceito, e recusar o que não é | falar com banco, decidir regra |
| `controllers/` | decidir o que pode e o que não pode, chamar repositories, salvar (`commit`) | escrever consulta, saber que existe HTTP |
| `repositories/` | buscar, criar e atualizar no banco | decidir se aquilo era permitido |
| `models/` | descrever as tabelas em Python | ter regra dentro |
| `dtos/` | montar o dicionário que vira a resposta | buscar coisa no banco |
| `errors/` | definir cada erro: código, mensagem e status HTTP | ter regra de negócio dentro |
| `middlewares/` | fazer algo em **toda** requisição (token, log, cabeçalho) | conhecer uma rota específica |
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
| **mudar o que a resposta devolve** | `src/dtos/sample_entity_dto.py` | — |
| **criar uma rota nova** numa entidade que já existe | `src/routers/sample_entity.py` | e o método no controller, se a regra for nova |
| **mudar uma regra** ("não pode X") | `src/controllers/sample_entity_controller.py` | e um erro novo em `src/errors/custom_errors.py`, se precisar |
| **consultar o banco de outro jeito** (filtrar, ordenar, contar) | `src/repositories/sample_entity_repository.py` | o controller chama o método novo |
| **criar uma tabela** | `database/database.sql` | depois `src/models/` e o `__init__.py` da pasta |
| **criar uma entidade inteira** (rota + regra + tabela) | um arquivo em cada pasta | `database.sql` → `models/` → `repositories/` → `controllers/` → `schemas/` → `routers/` → registrar em `src/app.py` |
| **fazer algo em toda requisição** | `src/middlewares/` | registrar em `src/app.py` |

Duas armadilhas que pegam quase todo mundo:

**Criou um arquivo e o Python diz que não existe?** Cada pasta tem um
`__init__.py` que lista o que ela oferece. Abra o da pasta (por exemplo
`src/repositories/__init__.py`) e acrescente a sua linha.

**Mexeu no `database/database.sql` e nada mudou?** Aquele arquivo roda
uma vez só: quando o banco **nasce**. Para recriar do zero — apagando
tudo que estava lá dentro:

```bash
docker compose down -v
docker compose up
```

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

## 5. Uma costura à mostra

Honestidade sobre o código que você tem na mão: `schemas/` e `dtos/`
falam os dois de formato — o primeiro é o que o FastAPI conhece (valida
a entrada e monta o `/docs`), o segundo é o dicionário que o nosso
código monta na saída. Só que a resposta do `POST /sample_entity` está
descrita **nos dois**: em `SampleEntityKeyResponse` (`schemas/`) e em
`only_obj_key` (`dtos/`).

Não é erro, e não precisa consertar. Guarde como sintoma: quando duas
pastas descrevem a mesma coisa, um dia alguém muda uma e esquece a
outra. Perceber isso já é trabalho de gente que programa.
