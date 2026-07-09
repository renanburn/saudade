-- saudade · esquema mínimo de memória com invalidação bi-temporal
-- 3 tabelas. SQLite puro, sem extensão, sem dependência.
--
-- A regra que o schema inteiro serve: NUNCA se apaga. Fato que deixou de ser
-- verdade é SUPERADO por um evento novo; aresta que deixou de valer é INVALIDADA
-- com data e motivo. O estado atual é derivado dos eventos, não guardado.
--
-- Nota sobre o índice idx_rel_ativa: ele é ÚNICO e PARCIAL (só arestas vigentes).
-- É o que permite a mesma aresta morrer e renascer em janelas diferentes.
-- UNIQUE de tabela quebraria isso: a linha morta ocuparia a chave pra sempre.

CREATE TABLE IF NOT EXISTS entities (
    name TEXT PRIMARY KEY, entity_type TEXT NOT NULL DEFAULT 'tema',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_name TEXT NOT NULL REFERENCES entities(name),
    content TEXT NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    tipo TEXT, ts TEXT, supersedes_id INTEGER, cold INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL REFERENCES entities(name),
    target TEXT NOT NULL REFERENCES entities(name),
    relation_type TEXT NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    valid_from TEXT, invalidated_at TEXT, invalid_reason TEXT, invalidated_by TEXT);
CREATE INDEX IF NOT EXISTS idx_obs_entity ON observations(entity_name);
CREATE INDEX IF NOT EXISTS idx_obs_tipo ON observations(tipo);
CREATE INDEX IF NOT EXISTS idx_obs_ts ON observations(ts);
CREATE INDEX IF NOT EXISTS idx_obs_supersedes ON observations(supersedes_id);
CREATE INDEX IF NOT EXISTS idx_obs_cold ON observations(cold);
CREATE INDEX IF NOT EXISTS idx_rel_source ON relations(source);
CREATE INDEX IF NOT EXISTS idx_rel_target ON relations(target);
CREATE INDEX IF NOT EXISTS idx_rel_inval ON relations(invalidated_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ent_canon ON entities(lower(name));
CREATE UNIQUE INDEX IF NOT EXISTS idx_rel_ativa
    ON relations(source, target, relation_type) WHERE invalidated_at IS NULL;
