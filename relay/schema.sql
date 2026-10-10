-- ============================================================
-- relay - the delivery attempt log
-- F-Keys | www.f-keys.com
-- ------------------------------------------------------------
-- One row per inbound event, one row per delivery attempt. The
-- two are separate tables because an event is received once and
-- delivered many times, and conflating them loses the retry
-- history that is the entire reason a relay exists.
--
-- COLUMN COUNT IS LOAD BEARING HERE. D1 binds at most 100
-- parameters per query, so a write of N rows costs
-- ceil(N / floor(100 / columns_bound)) round trips. attempts
-- binds eight columns, so the ceiling is floor(100/8) = 12 rows
-- a statement and the code takes 11, one short of it.
--
-- That number is DERIVED from the limit, never typed beside it.
-- A ninth column here drops the ceiling to 11 and the safe
-- figure to 10, and nothing anywhere would say so. Typing 40
-- next to a limit of 100 is the bug that failed f-keys-datapipe
-- silently on every run for months.
--
-- Apply:  npx wrangler d1 execute f-keys-relay --remote --file schema.sql
-- ============================================================

-- An event as it arrived. Stored once, verified before it got here.
CREATE TABLE IF NOT EXISTS events (
  id            TEXT PRIMARY KEY,         -- our id, not theirs
  source        TEXT NOT NULL,            -- which endpoint received it
  sender_id     TEXT,                     -- the sender's own event id, for dedupe
  received_at   TEXT NOT NULL,            -- ISO 8601, UTC
  signature_ok  INTEGER NOT NULL,         -- 1 verified, 0 rejected
  reject_reason TEXT,                     -- why, when signature_ok = 0
  body_bytes    INTEGER NOT NULL,
  body          TEXT                      -- NULL once archived to R2
);

-- Deliveries are looked up by endpoint and by time far more often
-- than by id, and a relay with no index here is a relay that gets
-- slower every day it runs.
CREATE INDEX IF NOT EXISTS idx_events_source_time
  ON events (source, received_at DESC);

-- The sender's id is what dedupe tests. KV holds the hot path; this
-- index is what makes the cold check possible after a KV TTL expires.
CREATE INDEX IF NOT EXISTS idx_events_sender
  ON events (source, sender_id);

-- One row per attempt, not per event. A 500 followed by a retry that
-- succeeds is two rows and both are true.
CREATE TABLE IF NOT EXISTS attempts (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id      TEXT NOT NULL,
  destination   TEXT NOT NULL,
  attempt_no    INTEGER NOT NULL,
  started_at    TEXT NOT NULL,
  duration_ms   INTEGER,
  status        INTEGER,                  -- HTTP status, NULL if it never connected
  error         TEXT,                     -- transport error, NULL on an HTTP answer
  FOREIGN KEY (event_id) REFERENCES events (id)
);

CREATE INDEX IF NOT EXISTS idx_attempts_event
  ON attempts (event_id, attempt_no);

CREATE INDEX IF NOT EXISTS idx_attempts_dest_time
  ON attempts (destination, started_at DESC);

-- Endpoints are configured, not discovered. An unknown endpoint is a
-- 404 and not an implicit create, because a relay that accepts
-- anything is an open proxy.
CREATE TABLE IF NOT EXISTS endpoints (
  slug          TEXT PRIMARY KEY,
  destination   TEXT NOT NULL,            -- where verified events go
  secret_name   TEXT NOT NULL,            -- which binding holds the shared secret
  scheme        TEXT NOT NULL,            -- how the sender signs: 'hmac-sha256-hex'
  tolerance_s   INTEGER NOT NULL DEFAULT 300,
  active        INTEGER NOT NULL DEFAULT 1,
  created_at    TEXT NOT NULL
);
