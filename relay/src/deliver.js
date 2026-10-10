/*
============================================================
relay - delivery, and knowing when to stop
F-Keys | www.f-keys.com
------------------------------------------------------------
The queue consumer. Takes a verified event, signs it as us,
POSTs it to the destination, and records what happened.

THE DECISION THAT MATTERS HERE IS WHEN NOT TO RETRY.

A relay that retries everything is worse than one that retries
nothing, because it turns one broken destination into a
permanent load on itself and on them. The rule:

  2xx            delivered. Done.
  408, 425, 429  retry. The destination said "not now".
  other 4xx      REFUSED. Do not retry, ever.
  5xx            retry. The destination is broken, not the event.
  no response    retry. We never got an answer.

The "other 4xx" line is the one people get wrong. A 400 means
the destination read the request and rejected it. Sending the
same bytes again cannot produce a different answer, so retrying
is a loop that ends when the cap does. 429 is a 4xx that means
the opposite - come back later - which is why it is carved out
by number rather than by class.

Backoff is exponential with a ceiling, and the ceiling matters:
unbounded doubling means attempt twelve is scheduled for next
week, long after anyone cares.
============================================================
*/

const enc = new TextEncoder();

/* Retried by number, not by class. */
const RETRY_4XX = new Set([408, 425, 429]);

/* 30s, 1m, 2m, 4m, 8m, 15m, 15m, ... Capped: doubling without a
   ceiling schedules the later attempts for a date nobody is waiting
   for any more. */
const BASE_DELAY_S = 30;
const MAX_DELAY_S = 15 * 60;

function backoff(attemptNo) {
  return Math.min(MAX_DELAY_S, BASE_DELAY_S * Math.pow(2, attemptNo - 1));
}

function hex(buf) {
  return Array.from(new Uint8Array(buf), (x) =>
    x.toString(16).padStart(2, '0')).join('');
}

async function sign(secret, ts, body) {
  const key = await crypto.subtle.importKey(
    'raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' },
    false, ['sign']);
  return hex(await crypto.subtle.sign('HMAC', key, enc.encode(`${ts}.${body}`)));
}

function classify(status) {
  if (status >= 200 && status < 300) return 'delivered';
  if (status >= 500) return 'retry';
  if (RETRY_4XX.has(status)) return 'retry';
  if (status >= 400) return 'refused';
  return 'retry';
}

/* attempts binds eight columns and D1 allows a hundred bound parameters
   per query, so the ceiling is twelve rows a statement and this takes
   eleven. DERIVED, not typed: add a column to attempts and this follows
   it down on its own. Typing a number next to a limit is the bug that
   failed f-keys-datapipe silently on every run for months. */
const D1_MAX_BOUND_PARAMS = 100;
const ATTEMPT_COLUMNS = 8;
const ATTEMPT_CHUNK =
  Math.floor(D1_MAX_BOUND_PARAMS / ATTEMPT_COLUMNS) - 1;

async function recordAttempts(env, rows) {
  for (let i = 0; i < rows.length; i += ATTEMPT_CHUNK) {
    const chunk = rows.slice(i, i + ATTEMPT_CHUNK);
    const places = chunk.map(() => '(?,?,?,?,?,?,?,?)').join(',');
    const params = [];
    for (const r of chunk) {
      params.push(r.event_id, r.destination, r.attempt_no, r.started_at,
                  r.duration_ms, r.status, r.error, r.state);
    }
    await env.DB.prepare(
      'INSERT INTO attempts (event_id, destination, attempt_no, started_at,'
      + ' duration_ms, status, error, state) VALUES ' + places)
      .bind(...params).run();
  }
}

async function deliverOne(env, msg) {
  const { eventId, slug } = msg.body;

  /* The queue counts this for us, and it is the only counter that
     survives a redelivery. retry() re-delivers the ORIGINAL message, so
     a counter written into msg.body during one run is simply gone on
     the next one - the first version of this incremented a field that
     nothing ever read back. msg.attempts starts at 1. */
  const attemptNo = msg.attempts;

  const ev = await env.DB.prepare(
    'SELECT e.id, e.body, p.destination, p.outbound_secret_name, p.max_attempts'
    + ' FROM events e JOIN endpoints p ON p.slug = e.source'
    + ' WHERE e.id = ? AND e.source = ?')
    .bind(eventId, slug).first();

  /* The event is gone, or the endpoint was removed under it. Nothing to
     deliver and nothing to retry toward. */
  if (!ev || !ev.body) return { ack: true, row: null };

  const started = Date.now();
  const ts = Math.floor(started / 1000);
  const headers = { 'content-type': 'application/json',
                    'user-agent': 'f-keys-relay/0.1',
                    'x-relay-event-id': ev.id,
                    'x-relay-attempt': String(attemptNo) };

  /* We verify what senders give us, so we sign what we hand on. */
  const outSecret = ev.outbound_secret_name ? env[ev.outbound_secret_name] : null;
  if (outSecret) {
    headers['x-relay-signature'] =
      `t=${ts},v1=${await sign(outSecret, ts, ev.body)}`;
  }

  let status = null;
  let error = null;
  try {
    const res = await fetch(ev.destination, {
      method: 'POST', headers, body: ev.body,
      signal: AbortSignal.timeout(15000),
    });
    status = res.status;
  } catch (err) {
    error = String(err && err.message || err).slice(0, 200);
  }

  const state = status === null ? 'retry' : classify(status);
  const row = {
    event_id: ev.id, destination: ev.destination, attempt_no: attemptNo,
    started_at: new Date(started).toISOString(),
    duration_ms: Date.now() - started, status, error, state,
  };

  if (state === 'delivered' || state === 'refused') {
    await env.DB.prepare('UPDATE events SET delivery_state = ? WHERE id = ?')
      .bind(state, ev.id).run();
    return { ack: true, row };
  }

  if (attemptNo >= ev.max_attempts) {
    await env.DB.prepare(
      'UPDATE events SET delivery_state = ? WHERE id = ?')
      .bind('exhausted', ev.id).run();
    return { ack: true, row };
  }

  return { ack: false, delaySeconds: backoff(attemptNo), row };
}

export default async function queue(batch, env) {
  const rows = [];

  /* Deliveries run concurrently: one slow destination must not hold up
     every other destination in the same batch. */
  const results = await Promise.all(batch.messages.map(async (msg) => {
    try {
      return { msg, ...(await deliverOne(env, msg)) };
    } catch (err) {
      console.error('deliver failed', err && err.stack || String(err));
      /* Back off on the real attempt count, not on 1. Using 1 here would
         have retried a persistently throwing message every 30 seconds
         forever, which is the opposite of backing off. */
      return { msg, ack: false, delaySeconds: backoff(msg.attempts), row: null };
    }
  }));

  for (const r of results) {
    if (r.row) rows.push(r.row);
    if (r.ack) r.msg.ack();
    else r.msg.retry({ delaySeconds: r.delaySeconds });
  }

  /* One batched write for the whole batch rather than one per message. */
  if (rows.length) await recordAttempts(env, rows);
}

export { classify, backoff, ATTEMPT_CHUNK, RETRY_4XX };
