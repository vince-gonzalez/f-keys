-- ============================================================
-- relay 0003 - what delivery needs to know
-- F-Keys | www.f-keys.com
-- ------------------------------------------------------------
-- Two things the receive path did not need and the delivery
-- path cannot work without.
--
-- outbound_secret_name: we verify what senders give us, so we
-- sign what we give destinations. A relay that demands proof
-- and then provides none is asking its downstream to trust an
-- unauthenticated POST from an address on the open internet,
-- which is the exact problem the relay exists to solve.
--
-- max_attempts: a cap, per endpoint, because "retry until it
-- works" against a destination that is never coming back is an
-- infinite loop with a bill attached.
--
-- Apply:  npx wrangler d1 execute f-keys-relay --remote \
--           --file migrations/0003-delivery.sql
-- ============================================================

ALTER TABLE endpoints ADD COLUMN outbound_secret_name TEXT;
ALTER TABLE endpoints ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 8;

-- Terminal state per event, so "what is still trying" is one indexed
-- read rather than a scan of attempts. pending, delivered, refused
-- (the destination said 4xx and meant it), or exhausted.
ALTER TABLE events ADD COLUMN delivery_state TEXT NOT NULL DEFAULT 'pending';

CREATE INDEX IF NOT EXISTS idx_events_state
  ON events (delivery_state, received_at DESC);

-- The outcome of each attempt, not just its status code. A timeout has
-- no status at all, and "retry" versus "refused" is the distinction the
-- whole delivery policy turns on, so it is stored rather than recomputed
-- by every reader from a status that may be NULL.
ALTER TABLE attempts ADD COLUMN state TEXT;
