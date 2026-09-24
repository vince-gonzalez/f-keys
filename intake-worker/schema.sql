-- ============================================================
-- f-keys intake - the state behind a website enquiry
-- F-Keys | www.f-keys.com
-- ------------------------------------------------------------
-- One rule, the same one the epistemend schema runs on: nothing
-- is ever silently lost. A submission that arrived and produced
-- no email is a row that says so, not an absence.
--
-- The row is written BEFORE any email is attempted, so a missing
-- mail key costs a notification, never the intake.
--
--   wrangler d1 execute f-keys-intake --remote --file=schema.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS submissions (
  id            TEXT PRIMARY KEY,        -- sub_<random>
  form_type     TEXT NOT NULL,           -- Client Intake | Brand Assets
  business      TEXT,
  contact       TEXT,
  email         TEXT,
  phone         TEXT,
  fields        TEXT NOT NULL,           -- the whole structured record, as JSON
  body          TEXT NOT NULL,           -- the readable version, verbatim
  due_build     TEXT,                    -- quoted totals, as submitted
  due_monthly   TEXT,
  addons        TEXT,
  agreed_at     TEXT,                    -- the e-signature timestamp the client saw
  user_agent    TEXT,
  country       TEXT,                    -- from the edge, not the form
  ip_hash       TEXT,                    -- salted; never the address itself
  notified      INTEGER NOT NULL DEFAULT 0,
  notify_error  TEXT,                    -- why the email did not go, if it did not
  created_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS submissions_created ON submissions(created_at DESC);
CREATE INDEX IF NOT EXISTS submissions_notified ON submissions(notified, created_at);
CREATE INDEX IF NOT EXISTS submissions_email ON submissions(email);

-- The bytes live in R2, never here. A 4 MB logo base64s to 5.3 MB and D1
-- caps a row at 1 MB, so storing them in this table would fail the write
-- and take the intake down with it. r2_key is where the object actually
-- is; NULL means it was recorded by name only, which is what happens
-- before the bucket exists or when a file is over the ceiling.
CREATE TABLE IF NOT EXISTS submission_files (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  submission_id TEXT NOT NULL REFERENCES submissions(id),
  name          TEXT NOT NULL,
  mime          TEXT,
  bytes         INTEGER,
  r2_key        TEXT
);

CREATE INDEX IF NOT EXISTS submission_files_sub ON submission_files(submission_id);
