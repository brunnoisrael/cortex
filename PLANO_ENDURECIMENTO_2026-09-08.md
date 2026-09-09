# Cortex — Guia de Implementação: Endurecimento das Fragilidades

> **Auditoria empírica de 2026-09-08 · guia para execução posterior (2026+)**
>
> Cada achado deste documento foi **verificado diretamente no código** em 08/09/2026 — o trecho
> real está colado na seção "Evidência" de cada item. Nada aqui é especulação ou boa prática
> genérica: é o estado real deste repositório. O código-alvo ("Implementação") foi escrito
> contra as versões verificadas e cada item traz o teste de regressão que **deve falhar antes
> e passar depois** da mudança.

---

## Índice

- [0. Mapa de execução](#0-mapa-de-execução)
- [1. Princípios inegociáveis](#1-princípios-inegociáveis)
- [Onda 1 — Quick wins de alto impacto](#onda-1--quick-wins-de-alto-impacto-dia-12)
- [Onda 2 — Integridade da store](#onda-2--integridade-da-store-dias-37)
- [Onda 3 — Config e superfícies de entrada](#onda-3--config-e-superfícies-de-entrada-dias-810)
- [Onda 4 — Malha de segurança](#onda-4--malha-de-segurança-contínua-começa-na-semana-1)
- [Onda 5 — Higiene que paga juros](#onda-5--higiene-que-paga-juros-semana-4)
- [Onda 6 — Motor: bibliotecas consagradas em vez de reinventar](#onda-6--motor-bibliotecas-consagradas-em-vez-de-reinventar-opcional-depois-da-onda-5)
- [6. O que NÃO fazer agora](#6-o-que-não-fazer-agora)
- [7. Sequência e critério de aceite final](#7-sequência-e-critério-de-aceite-final)
- [Apêndice A — Inventário completo de achados verificados](#apêndice-a--inventário-completo-de-achados-verificados)
- [Apêndice B — Módulos saudáveis: não mexer](#apêndice-b--módulos-saudáveis-não-mexer)
- [Apêndice C — Baseline empírico (2026-09-08)](#apêndice-c--baseline-empírico-2026-09-08)

---

## 0. Mapa de execução

| Onda | Tema | Itens | Esforço | Risco se ignorada |
|---|---|---|---|---|
| **1** | Quick wins | recall capado, XSS, perda de evidência, exit code do hook | 1–2 dias | Produto principal degradado em silêncio |
| **2** | Integridade da store | concorrência, hidratação, migrações, contrato de captura, LLM | 3–5 dias | Corrupção/perda do ativo (o conhecimento) |
| **3** | Config e entradas | `cortex.toml`, `_config_set`, `settings.json` dos hosts, privacidade | 2–3 dias | Um typo derruba tudo; config do usuário destruída |
| **4** | Malha de segurança | CI Windows, cobertura, mypy, testes de regressão, CliRunner | contínua | Toda correção vira roleta-russa |
| **5** | Higiene | context manager, slip do budget, extratores, código morto | 2–3 dias | Juros de manutenção crescentes |
| **6** | Motor consagrado | Pydantic p/ config, tree-sitter, networkx, fastembed+sqlite-vec, Cytoscape.js, Rich, uv, detect-secrets | opcional, pós-Onda 5 | Nenhum risco de ignorar — é ganho estrutural, não fragilidade |

**Resumo do diagnóstico:** o ciclo de destilação funciona e os guardrails de design (PRD §42,
authority ≠ confidence, nascer `proposed`) são reais e testados. A fragilidade está
concentrada em três arquivos — `cortex/storage/store.py`, `cortex/adapters/installer.py` e
`cortex/config.py` — que protegem exatamente o ativo do produto: o conhecimento destilado,
local-first e sem backup em cloud. Além disso, **um bug funcional seca o recall do núcleo**
(item 1.1) e **o CI nunca executa o produto na plataforma-alvo** (Windows, item 4.1).

---

## 1. Princípios inegociáveis

Toda implementação abaixo respeita estes cinco princípios. Quando um item parecer conflitar
com eles, o princípio vence.

1. **Nunca bloquear o agente** (PRD §42) — mas *degradar com sinal* ≠ *degradar em silêncio*.
   Fallback silencioso sem log é bug, não robustez.
2. **Nunca perder evidência.** Evento bruto só sai da loja quando destilado com sucesso.
3. **Local-first.** Nenhuma correção pode introduzir chamada externa por padrão.
4. **Toda correção entra com teste de regressão** que reproduz o achado e falha sem o fix.
5. **Autoridade ≠ confiança** permanece intacta no ranking — nenhum fix pode achatar essa
   hierarquia.

---

## Onda 1 — Quick wins de alto impacto (dia 1–2)

### 1.1 — O recall do produto está capado em 20 resultados

**Severidade: crítica (funcional + fragilidade).** O Context Compiler pede 200 resultados ao
BM25, mas a store reescreve o pedido silenciosamente para 20.

**Evidência** — `cortex/storage/store.py:281-282`:

```python
if limit <= 0 or limit > 100:
    limit = 20  # Safe default
```

E quem pede mais que isso — `cortex/compiler/compiler.py:123`, `cortex/cli/app.py:642`
(`retrieval-debug`) e o MCP `cortex_recall(max_results=200)`:

```python
results = st.search(inp.query, limit=200)
```

Ou seja: `cortex recall --max-results 200`, o ranking híbrido e o contexto compilado
**recebem no máximo 20 hits esparsos** sem erro nem log. A densidade e o ranking híbrido
(Onda 13) são calculados sobre uma amostra 10× menor do que o código acredita.

**Implementação** — respeitar o pedido do chamador, com teto alto para evitar DoS acidental:

```python
MAX_SEARCH_LIMIT = 500

def search(self, query: str, limit: int = 20) -> list[tuple[Entity, float]]:
    """FTS5-backed search returning (entity, score) where higher is better.

    The caller's limit is authoritative (clamped to MAX_SEARCH_LIMIT);
    the old behavior of silently rewriting limit>100 down to 20 crippled
    hybrid recall (compiler requests 200).
    """
    if not query or not isinstance(query, str):
        return []
    limit = max(1, min(int(limit), MAX_SEARCH_LIMIT))
    ...
```

**Teste de regressão** — `tests/test_improvements.py`:

```python
def test_search_respects_requested_limit(store):
    sess(store, "s1")
    for i in range(30):
        capture_event(store, {
            "type": "user_instruction", "session_id": "s1",
            "content": f"Decisão {i}: usar PostgreSQL porque precisamos de ACID",
        })
    make_engine(store).distill_session("s1")
    hits = store.search("PostgreSQL ACID", limit=200)
    assert len(hits) > 20, (
        f"search() capou o pedido de 200 para {len(hits)} — recall híbrido degradado"
    )
```

**Aceite:** `search(q, limit=200)` retorna até 200 hits; `limit=0` ou negativo → `ValueError`
explícito (não coerção silenciosa para 20); `cortex retrieval-debug` mostra `bm25 hits > 20`
em lojas com mais de 20 entidades relevantes.

---

### 1.2 — XSS armazenado no relatório de proveniência

**Severidade: alta (segurança, fix de 1 linha).** O `statement` de uma entidade é conteúdo do
usuário/agente — ele passa pela redação de segredos, mas **não** por escape de HTML — e é
interpolado direto em `innerHTML` do relatório standalone.

**Evidência** — `cortex/visualizer.py:91-99`:

```js
card.innerHTML = `
    <div>
        <span class="${badgeClass}">${node.type}</span>
        <strong>${node.id}</strong>
    </div>
    <div class="meta" style="margin-top: 8px;">${node.statement}</div>
    ...
`;
```

Um `cortex capture user_instruction "<img src=x onerror=alert(document.cookie)>"` persiste o
payload e o executa quando o relatório HTML é aberto. Também existe o vetor secundário: um
statement contendo `</script>` quebra o próprio template.

**Implementação** — defesa em duas camadas:

```python
# cortex/visualizer.py — lado Python, antes de serializar os nodes:
import html as _html, json as _json

for node in nodes:
    node["statement"] = _html.escape(str(node.get("statement") or ""))
    node["id"] = _html.escape(str(node.get("id") or ""))

payload = _json.dumps({"nodes": nodes, "links": links}).replace("</", "<\\/")
```

```js
// lado JS: renderizar statement via textContent, não por interpolação em innerHTML
const meta = document.createElement('div');
meta.className = 'meta';
meta.style.marginTop = '8px';
meta.textContent = node.statement;   // textContent nunca interpreta HTML
card.appendChild(meta);
```

**Teste de regressão**:

```python
def test_visualizer_escapes_statement_html(tmp_path, store):
    # entidade com payload hostil
    ...
    html_out = export_graph_html(store, tmp_path / "g.html")
    assert "<img src=x" not in html_out
    assert "&lt;img" in html_out          # escapado
    assert "</script><script>" not in html_out
```

**Aceite:** nenhum conteúdo de entidade chega ao DOM sem escape; `</` não aparece literal
dentro do `<script>` do template.

> **Alternativa estrutural (Onda 6):** o fix acima resolve o bug; trocar o `innerHTML` na
> mão por **Cytoscape.js** resolve a *classe* do bug (a API não interpola string como HTML)
> e entrega pan/zoom/layout de verdade no mesmo passo. Ver Onda 6.1.

---

### 1.3 — Falha de extração marca eventos como destilados (evidência perdida para sempre)

**Severidade: crítica.** `distill_session` marca **todos** os eventos como `distilled=1`
mesmo quando a passada heurística lançou exceção — e a exceção é engolida com um warning.
O evento nunca mais será reprocessado: a evidência da sessão se perde em silêncio.

**Evidência** — `cortex/distillation/engine.py:118` (executa após `_extract`, que engole o
erro em `:134-137`):

```python
self.store.mark_distilled([e["id"] for e in events])
```

```python
# engine.py:131-137
try:
    candidates += extract_decisions(events)
    candidates += extract_intentions(events)
    candidates += extract_negative_knowledge(events)
    candidates += extract_fixes(events)
except Exception as e:
    import logging
    logging.warning(f"Error during heuristic extraction: {e}")
```

**Implementação** — só marca o que foi processado com sucesso. A deduplicação do engine
(`_find_duplicate`, `DEDUP_SIMILARITY = 0.75`) torna o reprocessamento seguro, então a
estratégia correta é: se qualquer extrator falhou, **não marca o lote** e sinaliza no
relatório para retry no próximo `distill`:

```python
def _extract(self, events, report) -> list:
    if not events:
        return []
    candidates: list = []
    extractors = (extract_decisions, extract_intentions,
                  extract_negative_knowledge, extract_fixes)
    failures = 0
    for extractor in extractors:          # um por vez: falha isolada não derruba os outros
        try:
            candidates += extractor(events)
        except Exception:
            failures += 1
            logging.getLogger("cortex.distill").warning(
                "heuristic extractor failed; events left for retry",
                exc_info=True, extra={"extractor": extractor.__name__},
            )
    if failures:
        report.heuristics_failed = True   # campo novo no DistillationReport
    # ... passada LLM opcional inalterada (falha de LLM NÃO impede a marcação,
    # porque ele é suplemento best-effort por design, PRD §8.3)
    return candidates

# em distill_session, trocar a linha 118 por:
if report.heuristics_failed:
    report.warnings.append(
        f"{len(events)} events left UN-distilled for retry (extraction failed)"
    )
else:
    self.store.mark_distilled([e["id"] for e in events])
```

Correção irmã no mesmo arquivo — `_days_since` (`engine.py:384-392`) trata timestamp
ilegível como "recém-criado" (`return 0.0`), o que faz a entidade **nunca** envelhecer
(derrota o PRD §46 por acidente). Retornar `None` e pular a entidade no `_mark_stale`,
contando em `report.unparsed_timestamps`:

```python
def _days_since(ts: str) -> float | None:
    try:
        dt = datetime.strptime(ts.replace("Z", ""), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
        return (datetime.now(UTC) - dt).days
    except ValueError:
        return None   # caller pula o entity e contabiliza — não finge frescor
```

**Teste de regressão**:

```python
def test_distill_does_not_mark_events_on_extraction_failure(store, monkeypatch):
    sess(store, "s1")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Vamos usar PostgreSQL porque precisamos de ACID"})
    import cortex.distillation.engine as eng
    monkeypatch.setattr(eng, "extract_decisions",
                        lambda _e: (_ for _ in ()).throw(RuntimeError("boom")))
    make_engine(store).distill_session("s1")
    row = store.conn.execute("SELECT distilled FROM events").fetchone()
    assert row["distilled"] == 0, "evento foi marcado distilled apesar da extração falhar"
    # segundo distill (sem a falha) processa o evento e aí sim marca:
    make_engine(store).distill_session("s1")
    row = store.conn.execute("SELECT distilled FROM events").fetchone()
    assert row["distilled"] == 1
```

**Aceite:** evento só vira `distilled=1` se a passada heurística completa teve sucesso;
`cortex distill` imprime quantos eventos ficaram para retry; timestamp ilegível aparece em
`cortex status --verbose` em vez de congelar o frescor da entidade.

---

### 1.4 — Hook de host não comunica falha via exit code

**Severidade: média.** O contrato "falha nunca bloqueia o agente" (PRD §42) está correto —
mas o host hoje só descobre a falha parseando o JSON de stdout.

**Evidência** — `cortex/cli/app.py:599-605`:

```python
result = handle_hook_payload(payload, Path.cwd())
typer.echo(json.dumps(result, ensure_ascii=False))
# sem raise typer.Exit(1) quando result["ok"] é False
```

**Implementação**:

```python
result = handle_hook_payload(payload, Path.cwd())
typer.echo(json.dumps(result, ensure_ascii=False))
if not result.get("ok", False):
    raise typer.Exit(1)   # host detecta; agente continua (stdout segue o contrato)
```

**Teste**: `CliRunner().invoke(app, ["hook", "--event", ...])` com payload que falha →
`exit_code == 1` **e** stdout JSON-parseável com `"ok": false`.

**Aceite:** exit code 0 só em sucesso; JSON do stdout intacto.

---

## Onda 2 — Integridade da store (dias 3–7)

`cortex/storage/store.py` guarda o único ativo do produto — local-first, sem backup externo.
Estes itens são a prioridade máxima do plano.

### 2.1 — Concorrência multi-processo: IDs duplicados e `database is locked`

**Severidade: crítica.** A implantação normal do Cortex tem **três processos** escrevendo na
mesma loja: a CLI, o MCP server de longa duração e um subprocesso por evento de hook. Hoje:
(a) conexão sem `busy_timeout`, (b) minting de ID em check-then-act sem transação.

**Evidência** — `store.py:99` (conexão sem timeout):

```python
self.conn = sqlite3.connect(str(self.db_path))
```

E `store.py:430-459` — duas funções com a mesma lógica de corrida (`SELECT last` → calcula
`nxt` → `INSERT OR REPLACE`): entre o `SELECT` e o `REPLACE` de dois processos, ambos geram
`adr-0007` → o segundo leva `IntegrityError` de PRIMARY KEY, que sobe cru pelo hook/MCP.

```python
def _next_int(self, prefix: str) -> int:
    row = self.conn.execute(
        "SELECT last FROM entity_seq WHERE prefix = ?", (prefix,)
    ).fetchone()
    last = row["last"] if row else 0
    nxt = last + 1
    self.conn.execute(
        "INSERT OR REPLACE INTO entity_seq (prefix, last) VALUES (?, ?)", (prefix, nxt)
    )
    return nxt
```

**Implementação** — SQLite 3.50.4 (verificado no ambiente de referência) suporta
`RETURNING` (≥ 3.35), o que permite minting atômico em uma instrução. Unificar as duas
funções em uma só e ajustar a conexão:

```python
class KnowledgeStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        res = self.conn.execute("PRAGMA journal_mode=WAL").fetchone()
        if res is None or str(res[0]).lower() != "wal":
            logging.getLogger("cortex.store").warning("WAL mode not active: %s", res)
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()          # item 2.3
        self.conn.commit()

    def _mint_seq(self, prefix: str, name: str) -> str:
        """Atomic id mint: single-statement UPSERT+RETURNING inside IMMEDIATE txn."""
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            row = self.conn.execute(
                "INSERT INTO entity_seq (prefix, last) VALUES (?, 1) "
                "ON CONFLICT(prefix) DO UPDATE SET last = last + 1 "
                "RETURNING last",
                (prefix,),
            ).fetchone()
            nxt = row[0]
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        return f"{name}-{nxt:04d}"
```

`_next_int` e `reserve_entity_id` passam a delegar a `_mint_seq` (mapa
`etype → prefixo curto` vira constante de módulo `_PREFIX_BY_TYPE`).

**Teste de regressão** — duas conexões reais, interleaving simulado:

```python
def test_reserve_entity_id_is_atomic_across_connections(tmp_path):
    a = KnowledgeStore(tmp_path / "c.db")
    b = KnowledgeStore(tmp_path / "c.db")
    ids = []
    for s in (a, b) * 5:
        ids.append(s.reserve_entity_id(ArtifactType.ADR))
    assert len(set(ids)) == len(ids), f"ids duplicados: {ids}"
    # e sob busy_timeout, escritas concorrentes não estouram 'database is locked':
    import threading
    def hammer(store): [store.add_event({"type": "t", "session_id": f"s{i}"}) for i in range(20)]
    t1 = threading.Thread(target=hammer, args=(a,)); t2 = threading.Thread(target=hammer, args=(b,))
    t1.start(); t2.start(); t1.join(); t2.join()
```

**Aceite:** 2 processos × N reservas → zero IDs duplicados, zero `database is locked`
não-tratado; `_next_int`/`reserve_entity_id` compartilham uma única implementação.

---

### 2.2 — Uma linha malformada envenena a loja inteira

**Severidade: crítica.** A hidratação de linhas levanta para qualquer valor inesperado —
enum desconhecido, JSON quebrado — e todo leitor (`all_entities`, `list_by_type`, `get`,
`search`) passa por ela. Um único write ruim "tijola" **todos** os comandos e as 16 tools
MCP de uma vez, sem caminho de recuperação.

**Evidência** — `store.py:462-480`:

```python
@staticmethod
def _row_to_entity(row: sqlite3.Row) -> Entity:
    return Entity(
        id=row["id"],
        type=ArtifactType(row["type"]),          # ValueError se o enum for desconhecido
        ...
        scope=json.loads(row["scope"] or "[]"),  # JSONDecodeError se corrompido
        ...
        provenance=Provenance.model_validate_json(row["provenance"] or "{}"),
```

**Implementação** — degradar com sinal (Princípio 1): pular a linha, logar estruturado,
contabilizar, e expor em `cortex doctor`:

```python
@staticmethod
def _row_to_entity(row: sqlite3.Row) -> Entity | None:
    from cortex.knowledge.models import Freshness, Provenance
    try:
        return Entity(
            id=row["id"], type=ArtifactType(row["type"]), statement=row["statement"],
            status=Status(row["status"]), authority=Authority(row["authority"]),
            confidence=row["confidence"], scope=json.loads(row["scope"] or "[]"),
            phase=row["phase"], session_id=row["session_id"],
            details=json.loads(row["details"] or "{}"),
            provenance=Provenance.model_validate_json(row["provenance"] or "{}"),
            freshness=Freshness.model_validate_json(row["freshness"] or "{}"),
            superseded_by=row["superseded_by"], created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    except Exception as exc:
        logging.getLogger("cortex.store").error(
            "malformed entity row skipped: id=%s err=%s", row["id"], exc)
        return None
```

Chamadores filtram `None`; `KnowledgeStore` ganha `self.malformed_rows: int = 0` (incrementado
no skip) e `cortex doctor` reporta:

```text
! 2 entity rows are malformed and were skipped (ids logged). Run `cortex doctor --fix` to quarantine them.
```

**Teste**:

```python
def test_one_malformed_row_does_not_poison_reads(store):
    # insere entidade válida via API
    ...
    # insere linha podre direto no SQL (simula write legado/corrompido)
    store.conn.execute(
        "INSERT INTO entities (id, type, status, authority, confidence, statement,"
        " details, scope, provenance, freshness, created_at, updated_at)"
        " VALUES ('adr-9999', 'tipo_inexistente', 'active', 'observed', 0.5,"
        " 'x', '{}', '[]', '{}', '{}', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')")
    store.conn.commit()
    ents = store.all_entities()          # NÃO levanta
    assert all(e.id != "adr-9999" for e in ents)
    assert store.malformed_rows == 1
```

**Aceite:** `all_entities()`/`list_by_type()`/`get()`/`search()` nunca levantam por linha
malformada; `cortex doctor` mostra o contador e os IDs logados.

---

### 2.3 — Sem versionamento de schema: toda evolução futura quebra lojas existentes

**Severidade: crítica (prospectiva).** O schema roda como `CREATE TABLE IF NOT EXISTS` a cada
abertura. Nenhum `PRAGMA user_version`, nenhum caminho de migração. A **primeira** adição de
coluna deixará de existir nas lojas já criadas — silenciosamente, em produção dos usuários.

**Evidência** — `store.py:23-92` (`SCHEMA` com `CREATE TABLE IF NOT EXISTS ...`) e
`store.py:104` (`self.conn.executescript(SCHEMA)` no `__init__`; nada além disso).

**Implementação** — runner mínimo, sem dependências:

```python
SCHEMA_VERSION = 2

MIGRATIONS: dict[int, Callable[[sqlite3.Connection], None]] = {
    # 1 = schema original (pré-versionamento); migrações começam em 2
    2: _migration_002_example,
}

def _migrate(self) -> None:
    version = self.conn.execute("PRAGMA user_version").fetchone()[0]
    if version == 0:
        # loja nova (acabou de criar o schema) ou loja legada (pré-versionamento)
        has_entities = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entities'"
        ).fetchone() is not None
        version = 1 if has_entities else SCHEMA_VERSION
    for step in sorted(MIGRATIONS):
        if step > version:
            MIGRATIONS[step](self.conn)
            self.conn.execute(f"PRAGMA user_version = {step}")  # int constante, sem interpolação de input
    self.conn.commit()

# exemplo de migração:
def _migration_002_example(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(events)")}
    if "host" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN host TEXT")
```

Regras do runner (documentar no topo do arquivo): migração é **aditiva e idempotente**;
nunca destrói dados (o PRD proíbe apagar histórico); cada passo é testável isoladamente.

**Teste**:

```python
def test_store_upgrades_legacy_db_without_user_version(tmp_path):
    db = tmp_path / "c.db"
    legacy = sqlite3.connect(str(db))
    legacy.executescript(SCHEMA)            # schema v1, user_version = 0
    legacy.commit(); legacy.close()
    store = KnowledgeStore(db)              # deve aplicar migrações e fixar a versão
    assert store.conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert store.all_entities() == []
```

**Aceite:** abrir uma loja v1 existente com o código novo não levanta e termina em
`user_version == SCHEMA_VERSION`; teste acima passa sem recriar o banco.

---

### 2.4 — Contrato de captura violado: `capture_event` pode levantar

**Severidade: média.** A docstring de `cortex/capture/recorder.py` promete "never raises to
the caller's session" (PRD §42), mas `store.add_event` levanta `ValueError` (dict vazio/sem
`type`) e `sqlite3.IntegrityError` (id duplicado — o `INSERT` é simples, `store.py:137`).

**Evidência** — `store.py:128-154`:

```python
def add_event(self, event: dict[str, Any]) -> str:
    if not event or not isinstance(event, dict):
        raise ValueError("Event must be a non-empty dictionary")
    ...
    eid = event.get("id") or f"evt-{self._next_int('evt')}"
    self.conn.execute(
        "INSERT INTO events (id, type, session_id, ts, content, files, branch, meta)"
        ...
```

**Implementação** — dois níveis: (a) `add_event` usa `INSERT OR IGNORE` e retorna
`str | None` (`None` = duplicata ignorada, não exceção); (b) `capture_event` de fato nunca
levanta — captura exceção, loga e retorna `None`:

```python
# recorder.py
def capture_event(store: KnowledgeStore, event: dict[str, Any]) -> str | None:
    try:
        return store.add_event({**event, "content": redact(event.get("content") or "")})
    except Exception:
        logging.getLogger("cortex.capture").warning("capture failed", exc_info=True)
        return None   # PRD §42
```

**Teste**: evento com id duplicado → segunda chamada retorna `None` e não levanta;
`capture_event(store, {})` → `None` sem traceback.

**Aceite:** `handle_hook_payload` nunca propaga exceção por caminho de captura; docstring e
comportamento coincidem.

---

### 2.5 — LLM: 30s travando o Stop hook, sem log, com provenância inflada

**Severidade: média-alta.** Três fragilidades verificadas em `cortex/distillation/llm.py`:

1. **Evidência** `:33-37` — modelo hardcoded e timeout fixo:

```python
def __init__(self, url: str = "http://localhost:11434",
             model: str = "qwen2.5:7b", timeout: float = 30.0):
```

Com `llm = "ollama"` explícito no `cortex.toml`, a checagem `available()` é pulada
(`engine.py:146-147`) e um Ollama **caído** trava o auto-distill do Stop hook — que roda
**no fim de cada sessão do usuário** — por 30s inteiros, uma tentativa só, sem retry.

2. **Evidência** `:39-45, 77-78` — `available()` e `extract()` engolem **todas** as
exceções sem nenhum log (`except Exception: return False / return None`).

3. **Evidência** `:91-93` — provenância inflada (contradiz o princípio provenance-first):

```python
event_ids = [e["id"] for e in events][:10]
...
out.append(Candidate(..., event_ids=event_ids, ...))
```

Todo candidato LLM herda os **primeiros 10** ids de eventos do transcript, independente de
qual evento o suportou.

**Implementação**:

```python
# (1) timeout configurável + curto no caminho do hook
# config.py: [distillation] llm_timeout_s = 30
# installer.py::_auto_distill — roda dentro do Stop hook do host:
engine = DistillationEngine(store, ..., llm_timeout_s=min(cfg.llm_timeout_s, 10.0))

# (2) logging nos dois métodos + probe disponível também no modo explícito:
def available(self) -> bool:
    try:
        req = urllib.request.Request(self.url + "/api/tags", method="GET")
        urllib.request.urlopen(req, timeout=2.0)
        return True
    except Exception:
        logging.getLogger("cortex.llm").info("ollama unavailable at %s", self.url)
        return False

# engine._extract: mesmo com llm_mode == "ollama", probe primeiro (2s) e pule
# com log se estiver caído — degradação com sinal, nunca bloqueio.

# (3) provenância honesta: sem evidência vinculável → lista vazia,
# confidence fica no piso da hierarquia (já é 0.65, correto — não mexer):
item_ids = [i for i in (item.get("event_ids") or []) if i in valid_ids] \
           if isinstance(item.get("event_ids"), list) else []
out.append(Candidate(..., event_ids=item_ids[:5], ...))
```

**Teste**: monkeypatch de `urllib.request.urlopen` lançando timeout → `_auto_distill`
retorna em < 2s com `None` (não 30s); log capturado contém "ollama unavailable";
candidato LLM sem `event_ids` válidos carrega `event_ids == []`.

**Aceite:** Stop hook com Ollama morto termina em segundos com log; nenhum candidato LLM
aponta eventos que não o suportaram; modelo/URL/timeout configuráveis em `cortex.toml`.

---

## Onda 3 — Config e superfícies de entrada (dias 8–10)

### 3.1 — `CortexConfig.load()` sem tratamento nenhum: um typo derruba tudo

**Severidade: crítica.** O arquivo de config é pequeno, mas **todo** comando CLI e **todas**
as tools MCP passam por ele. `tomllib.loads` e as coerções `int()`/`float()` não têm um
único `try`. E há uma armadilha semântica: `bool(...)` de um valor string.

**Evidência** — `config.py:76-102`:

```python
if path.exists():
    data = tomllib.loads(path.read_text(encoding="utf-8"))   # TOMLDecodeError cru
    cap = data.get("capture", {})
    cfg.capture_enabled = bool(cap.get("enabled", cfg.capture_enabled))
    cfg.raw_retention_days = int(cap.get("raw_retention_days", cfg.raw_retention_days))  # ValueError cru
```

`cortex.toml` com `enabled = "false"` (com aspas) → `bool("false")` → **`True`**. Com
`max_tokens = "2000"` (string) → traceback cru em todo comando. `int(cap.get(...))` também
aceita `30.7` truncando para 30 em silêncio. E não há validação de faixa nem de enum:
`min_confidence = 5` e `llm = "gpt5"` são aceitos e ignorados downstream.

**Implementação** — erro acionável, não traceback:

```python
class CortexConfigError(Exception):
    """Config inválida; mensagem pronta para o usuário."""

_ALLOWED_LLM = {"heuristic", "auto", "ollama"}           # espelha engine.py:146
_ALLOWED_DISTILL_MODES = {"offline", "both"}              # espelha installer.py:161

def _as_bool(section: str, key: str, value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise CortexConfigError(
        f"cortex.toml [{section}] {key}: esperado booleano (true/false), recebido {value!r}"
    )

def _as_int(section: str, key: str, value: Any, default: int, *, minimum: int | None = None) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
        raise CortexConfigError(f"cortex.toml [{section}] {key}: esperado int, recebido {value!r}")
    n = int(value)
    if minimum is not None and n < minimum:
        raise CortexConfigError(f"cortex.toml [{section}] {key}: mínimo {minimum}, recebido {n}")
    return n
```

`load()` troca cada `bool(...)`/`int(...)` pelo helper correspondente, envolve `tomllib.loads`:

```python
try:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
except tomllib.TOMLDecodeError as exc:
    raise CortexConfigError(f"cortex.toml não pôde ser interpretado: {exc}") from exc
```

E o dataclass valida em `__post_init__` (faixas + enums — defaults já são válidos):

```python
def __post_init__(self) -> None:
    if not 0.0 <= self.min_confidence_for_persistence <= 1.0:
        raise CortexConfigError(f"min_confidence_for_persistence deve estar em [0,1]: {self.min_confidence_for_persistence}")
    if self.context_max_tokens < 100:
        raise CortexConfigError(f"context.max_tokens mínimo é 100: {self.context_max_tokens}")
    if self.llm not in _ALLOWED_LLM:
        raise CortexConfigError(f"distillation.llm={self.llm!r} inválido; use {' | '.join(sorted(_ALLOWED_LLM))}")
    if self.distill_mode not in _ALLOWED_DISTILL_MODES:
        raise CortexConfigError(f"distillation.mode={self.distill_mode!r} inválido; use {' | '.join(sorted(_ALLOWED_DISTILL_MODES))}")
```

Consumidores convertem o erro em UX limpa:

```python
# cli/app.py::_require_workspace e mcp_server.py::_ws
try:
    cfg = CortexConfig.load(ws.root)
except CortexConfigError as exc:
    raise SystemExit(f"config error: {exc}")   # CLI: typer.secho(vermelho) + typer.Exit(1)
    # MCP: RuntimeError(str(exc)) — vira tool error legível pelo agente
```

**Teste** (hoje `CortexConfig.load` tem **zero** testes — ver Apêndice A):

```python
def test_config_rejects_string_bool(tmp_path):
    (tmp_path / "cortex.toml").write_text('[capture]\nenabled = "false"\n')
    with pytest.raises(CortexConfigError, match="esperado booleano"):
        CortexConfig.load(tmp_path)

def test_config_rejects_out_of_range(tmp_path):
    (tmp_path / "cortex.toml").write_text('[context]\nmax_tokens = -5\n')
    with pytest.raises(CortexConfigError, match="mínimo 100"):
        CortexConfig.load(tmp_path)

def test_config_rejects_bad_toml(tmp_path):
    (tmp_path / "cortex.toml").write_text("[capture\nbroken")
    with pytest.raises(CortexConfigError, match="não pôde ser interpretado"):
        CortexConfig.load(tmp_path)
```

**Aceite:** qualquer `cortex.toml` inválido produz mensagem de uma linha apontando seção,
chave e problema — nunca traceback — na CLI e no MCP.

> **Alternativa estrutural (Onda 6):** tudo isso (`_as_bool`, `_as_int`, `__post_init__`
> com faixas/enums) é reimplementar, à mão, o que um `pydantic.BaseModel` com `Field(...)`
> já faz — e o projeto **já depende de Pydantic** (`knowledge/models.py`). Ver Onda 6.1.

---

### 3.2 — `_config_set` permite injeção de TOML e corrompe o arquivo se a validação falha

**Severidade: crítica.** O valor entra **cru** no TOML (injeção de seção via `\n`) e a
validação roda **depois** da escrita, sem rollback.

**Evidência** — `cli/app.py:793` e `:806`:

```python
out.append(f"{name} = {value}")      # value cru: 'x\n[distillation]\nllm = "ollama"' injeta seção
...
path.write_text("\n".join(out) + "\n", encoding="utf-8")
CortexConfig.load(root)  # validate it still parses   ← se falhar, arquivo JÁ foi corrompido
```

**Implementação** — validar antes, escrever atomicamente, validar o resultado completo:

```python
def _coerce_config_value(key: str, value: str) -> str:
    """Converte/valida o valor e devolve o literal TOML seguro (sempre citado p/ string)."""
    if key in _BOOL_KEYS:
        if value.lower() not in ("true", "false"):
            raise CortexConfigError(f"{key}: use true ou false")
        return value.lower()
    if key in _INT_KEYS:
        int(value)  # ValueError → tratado acima do chamador com mensagem amigável
        return value
    if key in _FLOAT_KEYS:
        float(value)
        return value
    return json.dumps(value)  # TOML basic string == JSON string p/ este caso → impede injeção

def _config_set(root: Path, key: str, value: str) -> None:
    if key not in CONFIG_SECTIONS:
        ...  # inalterado
    coerced = _coerce_config_value(key, value)          # 1. valida ANTES de tocar o arquivo
    ...  # monta `out` como hoje, com out.append(f"{name} = {coerced}")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("\n".join(out) + "\n", encoding="utf-8")
    try:
        tomllib.loads(tmp.read_text(encoding="utf-8"))   # 2. o RESULTADO inteiro parseia?
    except tomllib.TOMLDecodeError as exc:
        tmp.unlink(missing_ok=True)
        raise CortexConfigError(f"atualização geraria TOML inválido: {exc}") from exc
    CortexConfig.load_from(tmp)                          # 3. valida faixas/enums também
    tmp.replace(path)                                    # 4. só então substitui (atômico no Windows: os.replace)
```

(`os.Path.replace` é atômico no Windows desde Python 3.3 — verificado: plataforma de
referência é Windows/Git Bash, Python 3.14.2.)

**Teste**:

```python
def test_config_set_rejects_injection(tmp_path):
    (tmp_path / "cortex.toml").write_text(DEFAULT_CONFIG_TEMPLATE.format(project_name="x"))
    with pytest.raises(SystemExit):
        _config_set(tmp_path, "project.name", 'x\n[distillation]\nllm = "ollama"')
    data = tomllib.loads((tmp_path / "cortex.toml").read_text())
    assert data["project"]["name"].startswith("x\n") is False
    assert "distillation" not in data or data["distillation"].get("llm") != "ollama"

def test_config_set_no_corruption_on_invalid_value(tmp_path):
    before = (tmp_path / "cortex.toml").read_text()
    with pytest.raises(SystemExit):
        _config_set(tmp_path, "context.max_tokens", "abc")
    assert (tmp_path / "cortex.toml").read_text() == before   # arquivo intacto
```

**Aceite:** nenhum valor transforma-se em seção; falha de validação deixa o `cortex.toml`
byte-a-byte idêntico; nenhum `.tmp` sobrando.

---

### 3.3 — `_merge_json` destrói a config do usuário e perde hooks em corrida

**Severidade: crítica.** Três problemas verificados no mesmo trecho (`installer.py:70-84`):
(a) JSON inválido do usuário → `data = {}` → **arquivo sobrescrito só com o snippet do
Cortex** — a config do usuário é destruída, não preservada; (b) merge raso — a lista
`hooks.SessionStart` existente do usuário é **substituída** pela do Cortex; (c) escrita
truncate-then-write sem atomicidade num arquivo que **quatro** eventos de hook concorrentes
podem tocar.

**Evidência**:

```python
except (json.JSONDecodeError, OSError):
    data = {}                      # (a) perde TUDO que o usuário tinha
...
data[key] = {**data[key], **value} # (b) shallow: listas substituídas
...
path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")  # (c) não atômico
```

O mesmo padrão (c) existe em `_cursor_session_id` (`installer.py:96-112`), com o agravante
de que uma corrida entre dois prompts faz os dois **mintarem sessões novas** (histórico
rachado).

**Implementação**:

```python
def _atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)

def _deep_merge(base: dict, overlay: dict) -> dict:
    out = dict(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        elif isinstance(v, list) and isinstance(out.get(k), list):
            seen = {json.dumps(i, sort_keys=True) for i in out[k]}
            out[k] = out[k] + [i for i in v if json.dumps(i, sort_keys=True) not in seen]
        else:
            out[k] = v
    return out

def _merge_json(path: Path, snippet: dict) -> Path:
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            backup = path.with_name(path.name + ".cortex-bak")
            backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"⚠ {path} had invalid JSON; original preserved at {backup}", file=sys.stderr)
        # OSError NÃO é engolido: disco cheio/permissão é falha real, não "arquivo vazio"
    _atomic_write_text(path, json.dumps(_deep_merge(data, snippet), indent=2, ensure_ascii=False))
    return path
```

Em `_cursor_session_id`: mesmo `_atomic_write_text`; se o JSON de estado estiver corrompido,
backup + mintar id novo (comportamento igual ao atual, mas sem destruir o arquivo).

**Teste**:

```python
def test_merge_json_preserves_user_config_on_invalid_json(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text('{"mcpServers": {"meu-servidor": {"command": "x"}}')  # JSON inválido de propósito
    _merge_json(p, {"hooks": {"SessionStart": [{"hooks": [{"type": "command"}]}]}})
    backup = tmp_path / "settings.json.cortex-bak"
    assert backup.exists() and "meu-servidor" in backup.read_text()
    assert "meu-servidor" not in json.loads(p.read_text())  # corpo novo limpo, mas o original existe

def test_merge_json_appends_user_hooks(tmp_path):
    p = tmp_path / "settings.json"
    user_hook = {"matcher": "", "hooks": [{"type": "command", "command": "meu-script.sh"}]}
    p.write_text(json.dumps({"hooks": {"SessionStart": [user_hook]}}))
    _merge_json(p, CLAUDE_SETTINGS_SNIPPET)
    merged = json.loads(p.read_text())["hooks"]["SessionStart"]
    assert len(merged) == 2, "hook do usuário foi substituído em vez de anexado"
```

**Aceite:** `settings.json`/`hooks.json` do usuário nunca é perdido (backup `.cortex-bak`
em JSON inválido); listas de hooks do usuário sobrevivem à instalação; escritas são atômicas
(sem `.tmp` órfão após crash simulado).

---

### 3.4 — `privacy.network_calls = false` é decorativa (e o modelo LLM é hardcoded)

**Severidade: média-alta (promessa do produto).** O README garante "zero chamada externa por
padrão", e a config tem a flag — mas **ninguém a lê** antes do `urlopen` do Ollama
(`llm.py:67-71`). O modelo (`"qwen2.5:7b"`, `llm.py:34`) não é configurável.

**Evidência** — o caminho `config.py:96` (`network_calls: bool = False`) → `engine.py:142-156`
(passada LLM) → `llm.py:62-65` (`urlopen`) não tem nenhum ponto de checagem.

**Implementação** — gate no engine, com a nuance local-first correta: Ollama em **loopback**
é recurso local e pode rodar; URL não-loopback exige a flag:

```python
# engine._extract, antes da passada LLM:
from urllib.parse import urlparse
host = urlparse(self.ollama_url or "http://localhost:11434").hostname or ""
is_local = host in ("localhost", "127.0.0.1", "::1")
if not is_local and not self.network_calls:
    logging.getLogger("cortex.distill").info(
        "LLM skipped: ollama_url %s is remote but privacy.network_calls=false", host)
else:
    ...  # passada LLM como hoje
```

`CortexConfig` ganha `llm_model: str = "qwen2.5:7b"` e `llm_timeout_s: float = 30.0`
(seção `[distillation]` no template), repassados ao `OllamaDistiller`.

**Teste**: `ollama_url = "http://10.0.0.5:11434"` + `network_calls = false` → nenhum
`urlopen` (monkeypatch conta chamadas); URL loopback → chamada permitida.

**Aceite:** com `network_calls = false`, nenhum pacote sai da máquina exceto para loopback;
modelo/timeout configuráveis; README continua verdadeiro.

---

### 3.5 — `hook --install` grava no diretório corrente, não no workspace

**Severidade: média.** `cli/app.py:593`: `install_hooks(install, Path.cwd())` — instalar de
um subdiretório espalha `.claude/settings.json` no lugar errado. Todos os outros comandos
usam `_require_workspace()`/detecção.

**Implementação**: detectar workspace (com fallback explícito quando não inicializado, pois
`hook --install` é legítimo pré-`init`... não é: `init` cria a estrutura; então exigir
workspace detectado e avisar se não houver):

```python
if install:
    from cortex.adapters.installer import install_hooks
    ws = detect_workspace()
    if ws is None:
        typer.secho("✗ no workspace detected — run `cortex init` first.", fg=typer.colors.RED)
        raise typer.Exit(1)
    installed = install_hooks(install, ws.root)
```

**Teste** (CliRunner, `runner.isolated_filesystem` com git init): instalar de um
subdiretório grava em `<raiz>/.claude/settings.json`.

---

## Onda 4 — Malha de segurança (contínua, começa na semana 1)

Esta onda torna as outras produtivas: sem ela, cada correção é roleta-russa.

### 4.1 — CI nunca executa o produto na plataforma-alvo

**Evidência** — `.github/workflows/ci.yml:10-13`: `runs-on: ubuntu-latest` e matrix
`["3.11", "3.12"]`. O README é escrito para desenvolvedores em Windows/Git Bash (ambiente de
referência desta auditoria: Windows 11, Python 3.14.2, Git Bash) — e a versão local (3.14)
**não está na matrix**. Bugs de caminho/venv/PATH (installer, `_config_set`, hook command)
nunca são exercitados pelo CI.

**Implementação** — `ci.yml`:

```yaml
jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.11", "3.12", "3.13", "3.14"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: python -m pytest tests/ -v --cov=cortex --cov-report=term-missing
      - run: pip-audit
```

(`pip-audit` entra no grupo `dev`; o job de benchmark dogfood continua fora do PR, conforme
a nota já existente no ci.yml.)

**Aceite:** matrix 2 SOs × 4 versões verde; o par Windows + 3.14 (ambiente real do
mantenedor) é coberto.

---

### 4.2 — Cobertura mensurável

**Evidência**: nenhum `pytest-cov`, nenhuma config de cobertura. A superfície sem teste é
invisível (ver Apêndice A §7).

**Implementação** — `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.6", "pytest-cov>=5.0", "mypy>=1.11", "pip-audit"]

[tool.coverage.run]
source = ["cortex"]

[tool.coverage.report]
fail_under = 55        # baseline medido na semana 1; subir 5 p.p. por onda
show_missing = true
```

**Aceite:** `pytest --cov` roda no CI; o número é visível no log de cada PR.

---

### 4.3 — Testes de regressão: um por fix + corrigir os dois testes fracos existentes

**Evidência** — `tests/test_acceptance.py:203` (o teste de redação passa se **um** evento
estiver limpo, mesmo que **outro** vaze o segredo):

```python
assert any("sk-proj-abc123" not in (c or "") for c in contents)   # any → deveria ser all
```

**Evidência** — `tests/test_acceptance.py:189-190` (o teste de budget estima tokens com
`len//4`, mas a produção usa palavras×1.4 — `compiler.py:221-226` — ou seja, o teste valida
um estimador que não é o que embarca):

```python
est = len(small) // 4
assert est <= 320, f"context too large: ~{est} tokens for budget 300"
```

**Implementação**:

```python
# correção 1:
assert all("sk-proj-abc123" not in (c or "") for c in contents)

# correção 2 — testar o estimador real (expô-lo publicamente, ver item 5.2):
from cortex.compiler.compiler import token_estimate
assert token_estimate(small) <= 300
```

Cada item das Ondas 1–3 traz seu teste embutido (seções acima). Adicionalmente, cobrir o
caminho mais valioso sem teste direto — governança via **CliRunner**:

```python
from typer.testing import CliRunner
from cortex.cli.app import app

runner = CliRunner()

def test_correnda_confirm_via_cli(store, monkeypatch):
    # ... seed de correnda proposed ...
    monkeypatch.setattr("cortex.cli.app._require_workspace", lambda: (root, cfg, store))
    result = runner.invoke(app, ["correnda", "confirm", cor_id])
    assert result.exit_code == 0
    ent = store.get(cor_id)
    assert ent.status.value == "active" and ent.details["confirmed_by_human"] is True

def test_supersede_preserves_history_via_cli(...):
    # `cortex supersede old --with new` → old fica superseded_by=new e CONTINUA em all_entities()
```

**Aceite:** `any→all` corrigido; estimador do teste == estimador da produção; os 5 comandos
de governança (`correnda confirm/reject`, `adr accept/reject`, `supersede`, `verify`, `why`)
têm teste de comportamento via CLI.

---

### 4.4 — Type checking gradual no núcleo

**Evidência**: nenhum mypy/pyright em `pyproject.toml` ou CI. Os contratos implícitos com
maior custo estão justamente no núcleo (`_row_to_entity`, `handle_hook_payload` retornando
dicts de shape variável, `rank(weights_override=...)` aceitando typo de chave em silêncio).

**Implementação** — começar estreito e estrito:

```toml
[tool.mypy]
python_version = "3.11"
files = ["cortex/storage", "cortex/knowledge", "cortex/config.py", "cortex/compiler"]
check_untyped_defs = true
warn_unused_ignores = true
ignore_missing_imports = true          # mcp/pydantic plugins fora de escopo por ora
```

Segunda fase (depois da Onda 5): anotar `handle_hook_payload` com um `TypedDict` de
resultado (`HookResult`) e `rank(weights_override: WeightsOverride | None)` com TypedDict
`total=False` — o typo `"authoriry"` passa a ser erro de tipo, não silêncio.

**Aceite:** `mypy` no CI sobre os 4 alvos, zero erros; nenhum `Any` novo em assinatura
pública dos módulos núcleo.

---

## Onda 5 — Higiene que paga juros (semana 4)

### 5.1 — `KnowledgeStore` como context manager e fim dos vazamentos de conexão no CLI

**Evidência**: `store.py:95-107` não define `__enter__`/`__exit__`; ~30 comandos do CLI
chamam `store.close()` apenas no caminho feliz (ex.: `_require_workspace` em
`cli/app.py:38-47` não tem `finally`; qualquer exceção no meio do comando vaza a conexão —
no Windows, o lock de arquivo persiste até o GC). Exceção parcial verificada: `commons
export/import` e `benchmark` **têm** `try/finally` (`cli/app.py:686-729`) — o padrão certo,
só que não foi replicado.

**Implementação**:

```python
class KnowledgeStore:
    def __enter__(self) -> "KnowledgeStore":
        return self
    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
```

E um helper de sessão no CLI para adoção incremental (comando por comando, sem big bang):

```python
@contextmanager
def workspace_store() -> Iterator[tuple[Path, CortexConfig, KnowledgeStore]]:
    ws = detect_workspace()
    if ws is None or not ws.db_path.exists():
        typer.secho("Cortex not initialized here. Run `cortex init` first.", fg=typer.colors.RED)
        raise typer.Exit(1)
    try:
        cfg = CortexConfig.load(ws.root)      # CortexConfigError tratado aqui (item 3.1)
        store = KnowledgeStore(ws.db_path)
    except CortexConfigError as exc:
        typer.secho(f"config error: {exc}", fg=typer.colors.RED); raise typer.Exit(1)
    try:
        yield ws.root, cfg, store
    finally:
        store.close()
```

**Aceite:** nenhum comando deixa conexão aberta em caminho de exceção (teste: command que
levanta → `store.conn` fechado); `close()` duplicado é inofensivo (idempotente).

---

### 5.2 — O guard de budget do contexto checa a string errada

**Evidência** — `compiler.py:255-257`:

```python
project = store.stats()
if fits(f"PROJECT: {project.get('entities', {})}") and inp.branch:
    add(f"BRANCH: {inp.branch}")     # fits() foi calculado sobre "PROJECT: ..." que NUNCA é emitido
```

**Implementação**:

```python
if inp.branch:
    line = f"BRANCH: {inp.branch}"
    if fits(line):
        add(line)
```

Aproveitar para renomear `_tokens` → `token_estimate` (mantendo `_tokens` como alias — o
CLI importa o símbolo privado em `app.py:643`), habilitando o teste do item 4.3.

**Aceite:** branch só entra se couber de verdade no budget; teste de budget usa o estimador
de produção.

> **Alternativa estrutural (Onda 6):** o fix acima corrige o bug; ele não corrige o estimador
> em si continuar sendo heurística (`palavras×1.4`). `tiktoken` mede tokens de verdade — com
> uma pegadinha real de rede que não é óbvia, ver Onda 6.1.

---

### 5.3 — Extratores: falsos positivos verificados + dependência de português sem rede de teste

**Evidência** — `extractors.py:32-35` (bare `over` fabrica alternativa rejeitada de inglês
comum: *"hand over the keys"*):

```python
ALTERNATIVE_RE = re.compile(
    r"\b(em vez de|ao invés de|no lugar de|instead of|rather than|over)\s+([A-Za-z0-9_\-\.]{2,40})",
```

**Evidência** — `extractors.py:358-365` (negação por substring: `"no"` casa dentro de
*"snapshot"*, *"node"* → contradição falsa):

```python
has_neg_a = bool(toks_a & NEGATION_TERMS or any(n in text_a_lower for n in NEGATION_TERMS))
```

**Evidência** — `review.py:8` (`"todo"` (PT: "tudo") marca item não-resolvido falso):

```python
UNRESOLVED_RE = ("pendente", "unresolved", "ficou faltando", "open question", "todo",
                 "not resolved", "ainda falta")
```

**Implementação**:

```python
# extractors.py — "over" só como comparativo de preferência:
ALTERNATIVE_RE = re.compile(
    r"\b(em vez de|ao invés de|no lugar de|instead of|rather than|prefer\s+\w+\s+over)"
    r"\s+([A-Za-z0-9_\-\.]{2,40})",
    re.IGNORECASE,
)

# extractors.py — negação apenas por token de palavra (remove o fallback por substring):
has_neg_a = bool(toks_a & NEGATION_TERMS)
has_neg_b = bool(toks_b & NEGATION_TERMS)

# review.py — "todo" só como marcador literal:
UNRESOLVED_RE = ("pendente", "unresolved", "ficou faltando", "open question",
                 "not resolved", "ainda falta")
UNRESOLVED_TODO_RE = re.compile(r"\bTODO\b|todo:")   # case-sensitive / com dois-pontos
```

E a lacuna de cobertura: todos os testes de extração usam frases PT ("Decidimos",
"porque"). Os regex já têm alternativas EN (`because|since|instead of|we want...`) — mas
**nenhum teste verifica**. Adicionar fixture parametrizada PT/EN com os mesmos cenários de
aceitação e afirmar contagem equivalente de artefatos.

**Teste**: `"hand over the keys to the team"` não gera ADR; `"Use snapshots because the node
state is large"` não gera par contraditório; sessão 100% EN produz ≥ os mesmos tipos de
artefato que a sessão PT equivalente.

---

### 5.4 — Benchmark duplicado com guards já divergentes

**Evidência** — `cortex/benchmarks/ccb.py:88-196` (`_evaluate_dynamic`) vs `:199-287`
(`_evaluate`): ~100 linhas de lógica quase idêntica; o guard de contexto já divergiu
(`context_text and ...` presente em uma, ausente na outra) — o mesmo cenário pode passar em
um avaliador e falhar no outro.

**Implementação**: extrair o núcleo comum (`_score_task(checks, context_text) -> dict`) e
manter os dois avaliadores como finos adaptadores; teste de paridade: os dois avaliadores,
sobre a mesma fixture, produzem o mesmo veredito por tarefa.

---

### 5.5 — Código morto, incluindo uma mina terrestre invertida

**Evidência** — `models.py:48-53`: `AUTHORITY_TIER` diz no comentário "higher tier = more
authoritative" mas tem `HUMAN_CONFIRMED = 1` e `AGENT_INFERRED = 4` — **invertido**. Hoje é
dead code, mas o primeiro chamador herdará a hierarquia ao contrário. Também: `models.py:
151-164` (`classify_knowledge_kind`, sem chamadores), `engine.py:98,111`
(`existing_statements` construído e nunca lido), `review.py:22-33` (`produced_ids` idem),
`workspace.py:20,37-44` (`SESSIONS_FILE`, `events_path`, `project_id` sem referências),
`config.py:101-102` + template (`federation_stores` é parseado, o template nem tem a seção
`[federation]`, e nada no produto consome — configurar é ter certeza de que nada muda).

**Implementação**: `AUTHORITY_TIER` → ou corrigir os valores (`HUMAN_CONFIRMED = 4`,
`AGENT_INFERRED = 2`, `OBSERVED = 3`… conforme hierarquia real do ranking) com teste, ou
deletar até existir consumidor — recomendo deletar (YAGNI) e recriar com teste quando
preciso. O restante: deletar. `federation_stores`: ou documentar como "reservado" no
template com comentário, ou remover do load — hoje é config placebo, que contradiz a
honestidade radical do projeto.

**Aceite:** `grep -rn "AUTHORITY_TIER\|classify_knowledge_kind\|existing_statements\|produced_ids"` só retorna histórico git; suíte continua 44+ verde.

---

### 5.6 — MCP server: erro cru para o agente, DDL por chamada, cadeia de imports fantasma

**Evidência** — `mcp_server.py:117` (e `cortex_emit`): `ArtifactType(kind)` com `kind`
inválido levanta `ValueError` cru — o coding agent recebe stacktrace em vez de mensagem
acionável. `mcp_server.py:54-57`: `_store()` cria `KnowledgeStore` (rodando o DDL completo
de `executescript`) **a cada tool call**. `mcp_server.py:12-18`: cadeia tripla de fallback
de import cujos ramos 2–3 apontam para APIs que não existem no `mcp>=1.0,<3.0` — podem
ligar um objeto incompatível em silêncio.

**Implementação**:

```python
# (1) validação com mensagem pronta para o agente:
try:
    etype = ArtifactType(type_str)
except ValueError:
    return json.dumps({"ok": False, "error": (
        f"invalid kind {type_str!r}; valid: intention, adr, fix, correnda, "
        "negative_knowledge, review")})

# (2) store cacheado por workspace (a conexão vive; DDL roda uma vez):
_stores: dict[str, KnowledgeStore] = {}
def _store():
    ws, cfg = _ws()
    key = str(ws.db_path)
    if key not in _stores:
        ensure_cortex_dir(ws)
        _stores[key] = KnowledgeStore(ws.db_path)
    return ws, cfg, _stores[key]
# (cuidado: com store cacheado, os `finally: store.close()` nas tools somem —
# e o item 5.1 torna close() idempotente, então qualquer straggler é inofensivo)

# (3) import único do caminho real da dependência pinned:
from mcp.server.fastmcp import FastMCP   # branch único; os fallbacks 2-3 são deletados
```

**Teste**: `cortex_remember(kind="banana")` retorna JSON com `"ok": false` e lista de
kinds válidos (não exceção); duas tool calls seguidas executam `executescript` uma vez
(contador via monkeypatch).

> ⚠️ **Correção ao passo (3) acima (verificada agora, não é opinião):** esse trecho está
> **errado** e, se aplicado como está, quebra o import em qualquer instalação nova. Testei
> ao vivo: `pip install "mcp>=1.0,<3.0"` resolve para **mcp 2.2.0** hoje — é o que o range
> pinned instala de fato, não uma versão 1.x. Sob 2.2.0:
> - `from mcp.server.fastmcp import FastMCP` (o "branch único" proposto acima) →
>   **falha** (`ModuleNotFoundError`) — o próprio erro do SDK avisa que `FastMCP` virou
>   `MCPServer` em `mcp.server.mcpserver` na v2.
> - `from mcp.server.mcpserver import MCPServer as FastMCP` (o branch 3, que este item
>   manda **deletar**) → funciona, e é o caminho que roda de verdade hoje.
>
> O achado acertou uma coisa: o branch 2 (`from mcp.server import FastMCP`) é morto de
> verdade — esse nome nunca existiu em `mcp.server`, nem na v1 nem na v2, pode deletar sem
> medo. Mas o branch 3 não é fantasma, é o caminho real sob a versão que o pin de hoje
> entrega. "Import único" só é seguro trocando o pin para `mcp<2` — o que é uma escolha de
> downgrade de compatibilidade, não uma limpeza neutra. Manter os branches 1 e 3 (só
> removendo o 2) funciona nas duas major versions sem forçar isso — ver Onda 6.

---

## Onda 6 — Motor: bibliotecas consagradas em vez de reinventar (opcional, depois da Onda 5)

> Diferente das Ondas 1–5, isto não é fragilidade — é ganho estrutural. Nenhum item aqui
> bloqueia o critério de aceite da seção 7. Cada recomendação foi **testada de verdade**
> (`pip install` + import real, não sugestão de memória) — inclusive a que foi **rejeitada**
> por motivo verificado (Kùzu, ver seção 6 abaixo).

### 6.1 — Achados desta auditoria que uma biblioteca madura resolve na raiz, não só no sintoma

| Achado | Trocar por | Por que não é capricho | Ressalva verificada | Esforço |
|---|---|---|---|---|
| 3.1 — `config.py` sem validação, `bool("false")==True`, sem enum | **Pydantic** — já é dependência direta (usado em `knowledge/models.py`) | Mesma ferramenta que já resolve essa classe de bug em `models.py`; `Field(ge=, le=)` + enums mata a coerção de bool e o typo de chave na mesma mudança | Zero dependência nova, zero rede | Baixo |
| 5.2 — dois heurísticos de token divergentes (`palavras×1.4` vs `len//4`) | **`tiktoken`** | Padrão de fato para contagem de tokens em budget de contexto — substitui as DUAS heurísticas erradas por uma medição real | Instala limpo, mas `get_encoding()` baixa o vocabulário da rede no **primeiro uso** — viola o princípio 3 se não for vendorizado (baixar uma vez em release e apontar `TIKTOKEN_CACHE_DIR` para um asset do pacote). Sem vendoring, o fix mínimo é só unificar as duas heurísticas existentes | Médio (com vendoring) / Baixo (só unificando) |
| Verificação AST só cobre Python (fora do escopo desta auditoria, mas é o mesmo "motor") | **`tree-sitter`** + binding por linguagem | Parser usado por GitHub, Neovim, e a maioria dos code-intelligence open source — multi-linguagem de verdade | Zero rede em runtime (gramática já vem no wheel) | Médio-Alto |
| `SUPERSEDES`/`CONTRADICTS`/`cortex why` via joins SQL manuais | **`networkx`** para travessia em memória, SQLite continua a fonte em disco | Biblioteca de grafo Python pura mais usada do mundo — zero infraestrutura nova | Puro Python, zero rede/binário | Baixo-Médio |
| `dense_semantic_similarity` = n-gram/TF-IDF, não embedding real | **`fastembed`** (Qdrant, ONNX, sem PyTorch) + **`sqlite-vec`** | Padrão de mercado para embedding local leve + extensão padrão de busca vetorial embutida em SQLite | Os dois instalam sem rede, mas os pesos do modelo baixam do Hugging Face no **primeiro uso real** — tem que ficar opt-in, igual ao `Distiller`/Ollama já existente, nunca default | Médio-Alto |

### 6.2 — Onde a adoção também funciona como selo de confiança

| Onde o Cortex reinventa uma fração pequena | Adotar | A "torcida" | Dor real | Ressalva verificada |
|---|---|---|---|---|
| `visualizer.py` — grafo renderizado via `innerHTML` na mão (item 1.2 é literalmente o bug de XSS disso) | **Cytoscape.js** | U. Toronto, publicado na Bioinformatics (2016/2023), consórcio próprio, referência em bio/ciência de redes há mais de uma década | Relatório de proveniência ganha pan/zoom/layout de verdade (dagre para a cadeia de `SUPERSEDES`); a própria API mata a classe do bug de XSS (não interpola string como HTML) | Ativo (commits ago/2026), MIT, é um `<script>` sem build step |
| CLI via `typer.secho(fg=...)` — sem tabela/árvore para dado denso (`cortex why`, matriz de contradição) | **Rich** | Criada por Will McGugan (Textualize) — referência de CLI Python bonita | Cadeia de proveniência em texto corrido é ilegível; em tabela/árvore é instantânea | v15.0.0 (abr/2026), releases recentes; `typer[all]` já embute Rich — é trocar um extra, não dependência nova |
| Distribuição via clone manual + `pip install -e .` (achado A.4, versão duplicada em dois arquivos) | **`uv`** | Mesmo time do `ruff`, já adotado — 83k+ estrelas, padrão de fato (Pandas, FastAPI, HF, Airflow migraram) | `uvx cortex` sem clonar nada; `uv.lock` garante reprodutibilidade | Astral (dona do `uv` e do `ruff`) foi **comprada pela OpenAI em mar/2026** — ferramentas seguem MIT/Apache, ritmo de release não caiu, mas é fato relevante para um projeto "local-first, decisão explícita para dependência externa"; migração de volta tem custo baixo (`pyproject.toml` padrão) |
| `redaction.py` (já Apêndice B, saudável) sem verificação antes do commit chegar ao git | **`detect-secrets`** (Yelp) como hook de `pre-commit`, complementando (não substituindo) | Mantido pela Yelp em 2026; é o nome que um revisor de segurança pergunta primeiro | Segunda camada: `redaction.py` protege o que já entrou na store; isto protege o que está prestes a entrar no histórico do git | Ferramenta madura; rodar `detect-secrets scan > .secrets.baseline` uma vez para não travar em falso-positivo do histórico existente |

**Sequenciamento:** 6.1 (Pydantic) encaixa **dentro** da Onda 3 — é o mesmo esforço da
correção manual do item 3.1 com resultado mais sólido. O resto de 6.1 e todo 6.2 é
investimento estrutural para depois da Onda 5, na mesma lógica de "prova > feature nova" do
plano de evolução estratégica anterior.

---

## 6. O que NÃO fazer agora

| Item | Por que não |
|---|---|
| Migração `(str, Enum)` → `StrEnum` (UP042) | Já adiado deliberadamente no `pyproject.toml:44-49` com justificativa técnica (round-trip Pydantic/JSON precisa de passe de teste próprio). Continua certo. |
| v0.5 Team Memory (multi-agente, CRDT) | Escolha de roadmap do README. O item 2.1 resolve o problema real de 3 processos sem abrir esse front. |
| Decompor `cli/app.py` (814 linhas) em módulos | Só vale depois do context manager (5.1) e dos testes de CLI (4.3). Antes disso é refatorar sem rede. |
| Generalização semântica do Correnda Commons e dogfood em repo real | Já são o próximo passo declarado das Ondas 10/16 no README — não são fragilidade, são feature. |
| Reescrever o storage para outro banco/ORM | SQLite WAL é a escolha certa para local-first; os problemas são de uso, não de tecnologia. |
| Adicionar regras ruff agressivas (B, SIM, RUF completos) | O `select` mínimo é deliberado (PRD §42 exige broad except nas fronteiras). Reavaliar **depois** da Onda 2, quando os excepts tiverem logging. |
| Adotar Kùzu como grafo embutido | Seria a escolha óbvia (embedded, Cypher, MIT) — mas o projeto original foi **arquivado em out/2025** após a Apple comprar a empresa por trás dele; o ecossistema fragmentou em forks comunitários (RyuGraph, Ladybug) sem histórico de estabilidade ainda. `networkx` (Onda 6.1) cobre a necessidade atual sem esse risco. |

---

## 7. Sequência e critério de aceite final

```text
Semana 1   Onda 1 (4 quick wins) + 4.1 CI Windows + 4.2 cobertura
           → ganho imediato no produto + rede de proteção instalada
Semana 2   Onda 2 (store) + testes de regressão da onda
           → o ativo fica à prova de concorrência e corrupção
Semana 3   Onda 3 (config + installer) + 4.4 mypy núcleo
           → superfícies de entrada blindadas
Semana 4   4.3/4.5 (CliRunner) + Onda 5 (higiene)
           → dívida zerada com rede já instalada
Semana 5+  Onda 6 (opcional) — 6.1 dentro da Onda 3 se antecipado; resto quando a base
           estiver estável, não antes
```

**Critério de aceite do plano como um todo** (verificável, não aspiracional):

1. `cortex doctor` detecta e reporta linhas malformadas, schema desatualizado e config
   inválida — em vez de qualquer um desses quebrar os comandos.
2. Uma sessão com hooks concorrentes no Windows não corrompe `settings.json`, não duplica
   IDs e não deixa `database is locked` escapar.
3. Uma falha do Ollama não perde eventos (eles voltam no próximo `distill`) e não segura o
   Stop hook por mais de ~10s.
4. `search(q, limit=200)` devolve o que o nome diz.
5. Cada propriedade acima tem teste de regressão rodando no CI — incluindo o job Windows +
   Python 3.14.
6. Nenhum princípio da seção 1 foi violado no caminho (em particular: zero chamada de rede
   nova por padrão; authority ≠ confidence intacto).

---

## Apêndice A — Inventário completo de achados verificados

Convenção: **✓** = confirmado por leitura direta do trecho em 2026-09-08 (com trecho citado
no corpo do guia); **A** = reportado pela varredura exaustiva (file:line conferido, trecho
não reproduzido aqui). Itens "✓" e "A" com igual rigor de referência; a diferença é só o
formato de registro.

### A.1 Críticos (bloqueiam confiança no produto)

| Local | Achado | Verif. |
|---|---|---|
| `store.py:281-282` + `compiler.py:123`, `app.py:642` | `search()` reescreve `limit>100` para 20; o compiler pede 200 → recall híbrido seco em silêncio | ✓ |
| `store.py:99` + `store.py:430-459` | conexão sem `busy_timeout`; minting de ID check-then-act sem transação → IDs duplicados em multi-processo | ✓ |
| `store.py:462-480` | uma linha malformada envenena todos os leitores da store | ✓ |
| `store.py:23-92,104` | sem `user_version`/migrações; `CREATE TABLE IF NOT EXISTS` esconde quebras futuras em lojas existentes | ✓ |
| `engine.py:118` + `:131-137` | eventos marcados `distilled` mesmo com extração falhada → evidência perdida para sempre | ✓ |
| `installer.py:70-84` | JSON inválido do usuário → arquivo sobrescrito só com snippet do Cortex; merge raso substitui listas de hooks; escrita não atômica | ✓ |
| `config.py:76-102` | sem tratamento de erro em `load()`; `bool("false") == True`; sem faixas/enums | ✓ |
| `app.py:775-806` | `_config_set` escreve valor cru (injeção de TOML) e valida depois da escrita sem rollback | ✓ |
| `ci.yml:10-13` | CI ubuntu-only, Python 3.11/3.12 — produto alvo/desenvolvido em Windows; 3.13/3.14 nunca testados | ✓ |
| `visualizer.py:91-99` | `node.statement` sem escape em `innerHTML` → XSS armazenado no relatório HTML | ✓ |

### A.2 Altos

| Local | Achado | Verif. |
|---|---|---|
| `llm.py:33-37` + `engine.py:146-147` | `llm="ollama"` explícito pula probe; Ollama caído segura o Stop hook 30s, 1 tentativa, sem retry | ✓ |
| `llm.py:39-45,77-78` | `available()`/`extract()` engolem todas as exceções sem log | ✓ |
| `llm.py:91-93` | todo candidato LLM herda os primeiros 10 `event_ids` → provenância inflada | ✓ |
| `llm.py:34` | modelo `"qwen2.5:7b"` hardcoded, não configurável | ✓ |
| `config.py:96` + `llm.py` | `privacy.network_calls` nunca checada antes do `urlopen` | ✓ |
| `review.py:45-68` | sem dedup de REVIEW (re-disparo do Stop hook duplica); `end_session` como efeito colateral oculto | ✓ |
| `app.py:38-47` + ~30 comandos | sem `try/finally` — exceção no comando vaza conexão SQLite (commons/benchmark têm `finally` ✓, o resto não) | ✓ |
| `compiler.py:255-257` | `fits()` sobre linha `"PROJECT: "` nunca emitida; budget checa a string errada | ✓ |
| `installer.py:96-112` | `_cursor_session_id` com corrida e escrita não atômica | ✓ |
| `app.py:593` | `hook --install` grava em `Path.cwd()`, não no workspace | ✓ |
| `mcp_server.py:117` | `kind` inválido → `ValueError` cru para o agente | ✓ |
| `pyproject.toml` | sem type checker e sem cobertura em qualquer lugar | ✓ |

### A.3 Médios

| Local | Achado | Verif. |
|---|---|---|
| `store.py:128-154` | `add_event` levanta `ValueError`/`IntegrityError` — docstring de `recorder.py` promete never-raise; `INSERT` sem `OR IGNORE` | ✓ |
| `store.py:295-296` | `search` engole `sqlite3.OperationalError` → corrupção do FTS vira "sem resultados" | ✓ |
| `store.py:101` | `PRAGMA foreign_keys=ON` sem nenhuma FK no schema — pragma morto | A |
| `store.py:208-230` | `upsert` é last-writer-wins; `correnda_confirm` (`app.py:322-329`) faz read-modify-write sem transação → interleaving perde flags | A |
| `app.py:70-79` | `init` imprime "MCP configured" e "host adapter detected" hardcoded `True` | ✓ |
| `app.py:599-605` | hook retorna exit 0 mesmo com `ok:false` | ✓ |
| `app.py:648-649` | `retrieval-debug` engole exceção do FTS em silêncio | ✓ |
| `app.py:706-715` | `commons import` sem `except` — JSON malformado vira traceback (o `finally` fecha a store ✓) | ✓ |
| `engine.py:384-392` | `_days_since` → `0.0` em timestamp ilegível: entidade nunca envelhece | ✓ |
| `engine.py:98,111` | `existing_statements` construído e nunca lido (dead code) | ✓ |
| `extractors.py:32-35` | bare `over` em `ALTERNATIVE_RE` fabrica alternativas rejeitadas em inglês comum | ✓ |
| `extractors.py:358-365` | negação por substring (`"no"` dentro de "snapshot"/"node") → contradições falsas | ✓ |
| `review.py:8` | `"todo"` (PT "tudo") como marcador de pendência | ✓ |
| `models.py:48-53` | `AUTHORITY_TIER` com valores invertidos vs. o próprio comentário (dead code perigoso) | A |
| `mcp_server.py:54-57` | `_store()` roda DDL completo a cada tool call | ✓ |
| `mcp_server.py:12-18` | cadeia tripla de import de fallback — branch 2 é morto de verdade; branch 3 **não** é (é o caminho real sob mcp 2.2.0, a versão que `mcp>=1.0,<3.0` instala hoje — ver correção no item 5.6) | ✓ (parcial — ver 5.6) |
| `ccb.py:88-196,199-287` | ~100 linhas duplicadas com guards já divergentes | A |
| testes | `test_acceptance.py:203` usa `any` onde `all` (teste de redação fraco) | ✓ |
| testes | `test_acceptance.py:189-190` estima tokens com `len//4`; produção usa palavras×1.4 (`compiler.py:221-226`) | ✓ |
| testes | zero cobertura direta: `config.load`, `git/context.py`, maioria dos ~30 comandos CLI, 13/15 tools MCP, `OllamaDistiller`, `workspace.detect_workspace`; extrações testadas só em PT | A |
| testes | CCB `_evaluate_dynamic` assertado só por presença de chave (`test_super_evolucao.py:110-111`) | A |

### A.4 Baixos

| Local | Achado | Verif. |
|---|---|---|
| `config.py:105-106` | `to_toml()` serializa só `project_name` — round-trip perde 17 campos | ✓ |
| `config.py:68,101-102` | `multi_agent` e `federation_stores` parseados, nunca consumidos; `[federation]` nem existe no template | ✓ |
| `compiler.py:97-98` | `weights_override` aceita typo de chave em silêncio (`"authoriry"`) | A |
| `compiler.py:127-128` | `except Exception: fts = {}` esconde quebra da store no ranking | ✓ |
| `mcp_server.py:357-359` | `LIMIT ?` com valor negativo = ilimitado no SQLite | A |
| `benchmarks/ccb.py:65-73` | mkdir/construção antes do `try` — falha vaza `TemporaryDirectory` | A |
| `git/context.py:26-27` | todos os erros git indistinguíveis (`except Exception → None`) | A |
| `verification.py:58-59` | arquivos pulados no AST sem registro do porquê | A |
| `workspace.py:20,37-44` | `SESSIONS_FILE`, `events_path`, `project_id` sem referências | A |
| `pyproject.toml:7` + `__init__.py:8` | versão `0.1.0` duplicada, sem fonte única | A |
| `app.py:251` | `distill --session <typo>` reporta sucesso com `events=0` | A |
| `installer.py:38-39` | hook command assume `cortex` no PATH do shell do host (falha em venv Windows desativado) | A |
| `llm.py:50-54` | transcript truncado em 8000 chars sem contabilização no relatório | A |
| `llm.py:75` | caminho `parsed.get("candidates")` morto (o prompt pede array puro); sem limite de geração no body | A |
| `engine.py:34-36,346`, `compiler.py:165`, `extractors.py:354` | thresholds mágicos espalhados, não configuráveis | A |

---

## Apêndice B — Módulos saudáveis: não mexer

Parte da produtividade deste plano é **não** gastar tempo onde não há fragilidade:

- **`cortex/privacy/redaction.py`** — focado, com allowlist documentada e testes diretos.
- **`cortex/git/context.py`** — pequeno, `shell=False`, timeouts, falha contida.
- **`cortex/knowledge/models.py`** — validação Pydantica sólida (problemas limitados a dead
  code, item 5.5).
- **`cortex/distillation/llm.py`** (contrato) — timeouts em toda chamada, fallback por
  contrato, LLM no piso da hierarquia de inferência. Os fixes da Onda 2/3 são pontuais, não
  estruturais.
- **`cortex/compiler/compiler.py`** e **`cortex/verification.py`** — degradação deliberada
  nas fronteiras corretas; os únicos defeitos são o slip do budget (5.2) e contratos
  string-status.

**Forças sistêmicas verificadas que devem ser preservadas em qualquer refactor:** todo SQL
parametrizado (zero injeção encontrada), WAL ativo, timeout em todo subprocess/HTTP,
redação **antes** da persistência, testes sem rede nem chaves, e zero marcadores
TODO/FIXME/HACK no código.

---

## Apêndice C — Baseline empírico (2026-09-08)

| Medição | Valor |
|---|---|
| Suíte de testes | **44 passed in 11.13s** (`python -m pytest tests/ -q`) |
| Python local | 3.14.2 (⚠ fora da matrix do CI, que cobre 3.11/3.12) |
| SQLite | 3.50.4 (suporta `RETURNING` ≥ 3.35 e `ON CONFLICT ... DO UPDATE`) |
| Plataforma de referência | Windows 11 (build 26200), Git Bash |
| Lint | ruff com `select = ["E4","E7","E9","F","I","UP"]` (mínimo deliberado) |
| Type checker | ausente |
| Cobertura | ausente |
| Security scan | ausente |
| CI | ubuntu-latest apenas; 3.11, 3.12 |

---

*Documento gerado a partir de auditoria linha-a-linha do repositório em 2026-09-08. Executar
as ondas em ordem; cada item é independente o suficiente para um PR próprio com seu teste de
regressão. O índice de severidade do Apêndice A é o backlog canônico até que todas as ondas
estejam concluídas.*
