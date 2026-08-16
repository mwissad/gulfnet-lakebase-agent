-- GulfNet Care Copilot — Lakebase schema
-- Run against database `gulfnet` (CREATE DATABASE gulfnet first).

CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- Optional: vector / Lakebase Search. Seed works without embeddings.
DO $$ BEGIN
  CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'vector extension not available: %', SQLERRM;
END $$;
-- Lakebase Search (beta). Uncomment when enabled on the workspace:
-- CREATE EXTENSION IF NOT EXISTS lakebase_vector;
-- CREATE EXTENSION IF NOT EXISTS lakebase_text;

CREATE SCHEMA IF NOT EXISTS gulfnet;

-- ---------------------------------------------------------------------------
-- OLTP: subscribers, plans, usage, tickets, network
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gulfnet.plans (
    plan_id         TEXT PRIMARY KEY,
    name_en         TEXT NOT NULL,
    name_ar         TEXT,
    type            TEXT NOT NULL CHECK (type IN ('prepaid', 'postpaid', 'enterprise')),
    monthly_fee_aed NUMERIC(10, 2) NOT NULL,
    data_gb         NUMERIC(10, 2),
    voice_minutes   INT,
    roaming_gcc     BOOLEAN DEFAULT FALSE,
    roaming_intl    BOOLEAN DEFAULT FALSE,
    description_en  TEXT,
    description_ar  TEXT
);

CREATE TABLE IF NOT EXISTS gulfnet.subscribers (
    account_id      TEXT PRIMARY KEY,
    msisdn          TEXT UNIQUE NOT NULL,
    full_name       TEXT NOT NULL,
    segment         TEXT NOT NULL CHECK (segment IN ('VIP', 'SME', 'prepaid', 'enterprise', 'tourist')),
    plan_id         TEXT REFERENCES gulfnet.plans(plan_id),
    emirate         TEXT NOT NULL,
    language_pref   TEXT DEFAULT 'en',
    channel_pref    TEXT DEFAULT 'sms',
    arpu_aed        NUMERIC(10, 2),
    churn_risk      TEXT DEFAULT 'low',
    status          TEXT DEFAULT 'active',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gulfnet.usage_daily (
    id              BIGSERIAL PRIMARY KEY,
    account_id      TEXT REFERENCES gulfnet.subscribers(account_id),
    usage_date      DATE NOT NULL,
    data_gb         NUMERIC(10, 3) DEFAULT 0,
    voice_minutes   INT DEFAULT 0,
    roaming_data_gb NUMERIC(10, 3) DEFAULT 0,
    roaming_country TEXT,
    UNIQUE (account_id, usage_date)
);

CREATE TABLE IF NOT EXISTS gulfnet.tickets (
    ticket_id       TEXT PRIMARY KEY,
    account_id      TEXT REFERENCES gulfnet.subscribers(account_id),
    category        TEXT NOT NULL,
    priority        TEXT DEFAULT 'medium',
    status          TEXT DEFAULT 'open',
    summary         TEXT NOT NULL,
    details         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gulfnet.network_events (
    event_id        BIGSERIAL PRIMARY KEY,
    emirate         TEXT NOT NULL,
    cell_area       TEXT NOT NULL,
    severity        TEXT NOT NULL CHECK (severity IN ('info', 'degraded', 'outage')),
    started_at      TIMESTAMPTZ NOT NULL,
    ended_at        TIMESTAMPTZ,
    description     TEXT NOT NULL,
    affected_tech   TEXT DEFAULT '5G'
);

-- ---------------------------------------------------------------------------
-- Knowledge base for Lakebase Search / hybrid retrieval
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gulfnet.kb_documents (
    doc_id          TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    category        TEXT NOT NULL,
    language        TEXT DEFAULT 'en',
    source_uri      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gulfnet.kb_chunks (
    chunk_id        BIGSERIAL PRIMARY KEY,
    doc_id          TEXT REFERENCES gulfnet.kb_documents(doc_id) ON DELETE CASCADE,
    chunk_index     INT NOT NULL,
    content         TEXT NOT NULL,
    content_tsv     TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    -- Prefer VECTOR(1024) when pgvector is installed; TEXT fallback stores base64 later.
    embedding       TEXT,
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS kb_chunks_tsv_idx ON gulfnet.kb_chunks USING GIN (content_tsv);
-- HNSW / lakebase_vector index when embeddings are populated:
-- CREATE INDEX IF NOT EXISTS kb_chunks_embedding_idx ON gulfnet.kb_chunks
--   USING hnsw (embedding vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- Orchestration: Postgres task queue (CLA / Lakebase orchestration pattern)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gulfnet.tasks (
    task_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type           TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'enqueued'
                            CHECK (status IN ('enqueued', 'processing', 'completed', 'failed', 'cancelled')),
    priority            INT NOT NULL DEFAULT 50,
    payload             JSONB NOT NULL DEFAULT '{}',
    result              JSONB,
    locked_by           TEXT,
    lease_expires_at    TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    error_message       TEXT
);

CREATE TABLE IF NOT EXISTS gulfnet.task_attempts (
    attempt_id          BIGSERIAL PRIMARY KEY,
    task_id             UUID REFERENCES gulfnet.tasks(task_id) ON DELETE CASCADE,
    attempt_number      INT NOT NULL,
    run_id              TEXT,
    mlflow_trace_id     TEXT,
    status              TEXT NOT NULL DEFAULT 'started',
    cost_metadata       JSONB DEFAULT '{}',
    started_at          TIMESTAMPTZ DEFAULT NOW(),
    finished_at         TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS tasks_status_priority_idx
    ON gulfnet.tasks (status, priority DESC, created_at);

CREATE INDEX IF NOT EXISTS tasks_lease_idx
    ON gulfnet.tasks (lease_expires_at)
    WHERE status = 'processing';

-- NOTIFY on task status changes for SSE dashboards
CREATE OR REPLACE FUNCTION gulfnet.notify_task_change() RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify(
        'gulfnet_tasks',
        json_build_object(
            'task_id', NEW.task_id,
            'status', NEW.status,
            'task_type', NEW.task_type,
            'updated_at', NEW.updated_at
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tasks_notify ON gulfnet.tasks;
CREATE TRIGGER tasks_notify
    AFTER INSERT OR UPDATE OF status ON gulfnet.tasks
    FOR EACH ROW EXECUTE FUNCTION gulfnet.notify_task_change();

-- ---------------------------------------------------------------------------
-- Long-term memory mirror (agent also uses LangGraph AsyncDatabricksStore)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gulfnet.user_memory (
    user_id         TEXT NOT NULL,
    memory_key      TEXT NOT NULL,
    memory_value    JSONB NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, memory_key)
);
