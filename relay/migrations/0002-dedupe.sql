-- ============================================================
-- relay 0002 - make duplicate delivery impossible, not unlikely
-- F-Keys | www.f-keys.com
-- ------------------------------------------------------------
-- Senders retry. Stripe retries a webhook for up to three days,
-- and it retries when OUR 202 fails to reach IT, which means a
-- duplicate arrives precisely when everything looked fine from
-- our side. A relay that delivers the same event twice is
-- broken in the way that costs its user money.
--
-- The obvious fix is a KV lookup, and KV alone is not enough.
-- KV IS EVENTUALLY CONSISTENT. Two copies of the same event
-- arriving within the replication window can both read "not
-- seen" and both proceed, which is exactly the case that
-- matters because that is what a retry storm looks like.
--
-- So KV is the FAST PATH and this index is the GUARANTEE. KV
-- saves a D1 round trip in the ordinary case; the database is
-- what makes the answer true. A unique violation here is not an
-- error, it is the second copy being told what the first one's
-- id was.
--
-- The index is partial. sender_id is NULL on every rejected
-- event, and rejections must never be deduplicated: "who keeps
-- firing bad signatures at us" is answered by counting them.
-- SQLite treats NULLs as distinct in a unique index anyway, but
-- writing the predicate says so on purpose rather than relying
-- on a reader knowing that.
--
-- Apply:  npx wrangler d1 execute f-keys-relay --remote \
--           --file migrations/0002-dedupe.sql
-- ============================================================

DROP INDEX IF EXISTS idx_events_sender;

CREATE UNIQUE INDEX IF NOT EXISTS idx_events_sender_unique
  ON events (source, sender_id)
  WHERE sender_id IS NOT NULL;
