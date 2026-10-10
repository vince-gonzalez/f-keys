/*
============================================================
relay - verify at the door, then write it down
F-Keys | www.f-keys.com
------------------------------------------------------------
Receives webhooks from other people's systems, proves they are
genuine, and records what happened.

THE ORDER IS THE DESIGN, as it is in intake-worker, but the
reason is different. There the row comes first so a mail
failure cannot cost an enquiry. Here:

  1. read the raw body ONCE
  2. verify the signature over those exact bytes
  3. only then parse
  4. write the row either way

Three after two is not fussiness. JSON.parse on an unverified
body is running a parser against input an attacker chose, and
the whole point of a signature is that nothing untrusted gets
touched before it passes. Four happens even on a rejection,
because "who is firing bad signatures at us" is the question
the log exists to answer.

A note on what is NOT here yet: a rejected request still costs
a D1 write, so an attacker can grow this table. That is what
the per-destination Durable Object is for and it is step 4.
Until then this is deployed behind a route that is not
advertised.

Deploy:  cd relay && npx wrangler deploy
============================================================
*/

import queue from './deliver.js';
import { take, EndpointLimiter } from './limiter.js';

const enc = new TextEncoder();

/* Four days. Stripe retries a failing webhook for three, and a dedupe
   window shorter than the sender's retry window is a window through
   which a duplicate walks on the last attempt. The KV entry expiring is
   not a correctness problem either way: the unique index outlives it. */
const DEDUPE_TTL_S = 4 * 24 * 60 * 60;

/* Compared with an XOR walk rather than ===, so a wrong signature
   cannot be guessed one character at a time from how long the
   comparison took. Same reasoning as intake-worker; same code,
   deliberately, because two different implementations of this is
   two chances to get it wrong. */
function sameSig(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function hex(buf) {
  return Array.from(new Uint8Array(buf), (x) =>
    x.toString(16).padStart(2, '0')).join('');
}

async function hmacHex(secret, message) {
  const key = await crypto.subtle.importKey(
    'raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' },
    false, ['sign']);
  return hex(await crypto.subtle.sign('HMAC', key, enc.encode(message)));
}

/* The signed string is timestamp + '.' + body, not the body alone.
   Signing the body alone means a captured request is replayable
   forever, because the signature stays valid as long as the secret
   does. The timestamp is inside the signature so it cannot be
   edited, and it is then checked against the clock. */
async function verify(raw, header, secret, toleranceS) {
  if (!header) return { ok: false, why: 'no signature header' };

  const parts = Object.fromEntries(
    header.split(',').map((p) => {
      const i = p.indexOf('=');
      return i < 0 ? ['', ''] : [p.slice(0, i).trim(), p.slice(i + 1).trim()];
    }));

  const ts = parts.t;
  const given = parts.v1;
  if (!ts || !given) return { ok: false, why: 'malformed signature header' };

  const age = Math.abs(Math.floor(Date.now() / 1000) - Number(ts));
  if (!Number.isFinite(age)) return { ok: false, why: 'bad timestamp' };
  if (age > toleranceS) return { ok: false, why: `stale by ${age}s` };

  const expected = await hmacHex(secret, `${ts}.${raw}`);
  if (!sameSig(expected, given)) return { ok: false, why: 'signature mismatch' };
  return { ok: true };
}

const json = (body, status) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8' },
});

/* An id the sender does not control. Using theirs as our primary key
   lets one sender collide with another, and lets any sender choose
   where their row lands. */
function newId() {
  return 'ev_' + hex(crypto.getRandomValues(new Uint8Array(12)));
}

async function receive(request, env, slug) {
  const ep = await env.DB
    .prepare('SELECT slug, destination, secret_name, scheme, tolerance_s, active'
             + ' FROM endpoints WHERE slug = ?')
    .bind(slug).first();

  /* Unknown and inactive answer identically. Telling a stranger which
     endpoint names exist is telling them what to aim at. */
  if (!ep || !ep.active) return json({ error: 'unknown endpoint' }, 404);
  if (ep.scheme !== 'hmac-sha256-hex') {
    return json({ error: 'unsupported scheme' }, 500);
  }

  /* Read once. A request body is a stream and cannot be read twice,
     and the signature covers the exact bytes that arrived, not a
     re-serialised object that may differ by a space. */
  const raw = await request.text();
  const secret = env[ep.secret_name];
  if (!secret) return json({ error: 'endpoint not configured' }, 500);

  const v = await verify(raw, request.headers.get('x-relay-signature'),
                         secret, ep.tolerance_s);

  const id = newId();
  const now = new Date().toISOString();

  /* Only parse once it is proven genuine. */
  let senderId = null;
  if (v.ok) {
    try {
      const parsed = JSON.parse(raw);
      senderId = typeof parsed?.id === 'string' ? parsed.id : null;
    } catch {
      return json({ error: 'verified but not JSON' }, 400);
    }
  }

  /* A rejection is decided here, before anything is written. The BAD
     bucket is spent only by rejections and verified traffic never
     touches it, so no amount of garbage aimed at this endpoint can
     throttle a real sender. When it is empty the answer is still 401 -
     the sender learns nothing new - but the row is not recorded, and
     the unbounded D1 write is the cost this exists to stop. */
  if (!v.ok) {
    const bad = await take(env, slug, 'bad');
    if (!bad.allowed) {
      return new Response(
        JSON.stringify({ error: 'signature rejected', reason: v.why }), {
          status: 401,
          headers: { 'content-type': 'application/json',
                     'retry-after': String(bad.retry_after_s) },
        });
    }
    await env.DB.prepare(
      'INSERT INTO events (id, source, sender_id, received_at, signature_ok,'
      + ' reject_reason, body_bytes, body) VALUES (?,?,?,?,?,?,?,?)')
      .bind(id, slug, null, now, 0, v.why, raw.length, raw).run();
    return json({ error: 'signature rejected', reason: v.why }, 401);
  }

  /* Verified traffic spends its own bucket, which a flood cannot reach. */
  const okGate = await take(env, slug, 'ok');
  if (!okGate.allowed) {
    return new Response(JSON.stringify({ error: 'rate limited' }), {
      status: 429,
      headers: { 'content-type': 'application/json',
                 'retry-after': String(okGate.retry_after_s) },
    });
  }

  /* FAST PATH. KV answers in a millisecond and saves a D1 round trip on
     the ordinary retry, which is most of them. It is not the guarantee:
     KV is eventually consistent, so two copies arriving inside the
     replication window can both read "not seen" and both continue. That
     is not a corner case, it is exactly what a retry storm looks like.
     The unique index in migration 0002 is what makes the answer true. */
  const seenKey = senderId ? `${slug}:${senderId}` : null;
  if (seenKey) {
    const already = await env.SEEN.get(seenKey);
    if (already) return json({ ok: true, id: already, duplicate: true }, 200);
  }

  try {
    await env.DB.prepare(
      'INSERT INTO events (id, source, sender_id, received_at, signature_ok,'
      + ' reject_reason, body_bytes, body) VALUES (?,?,?,?,?,?,?,?)')
      .bind(id, slug, senderId, now, 1, null, raw.length, raw).run();
  } catch (err) {
    /* THE GUARANTEE. A unique violation here is not a failure, it is the
       second copy of an event learning what the first copy's id was. Any
       other database error is a real one and must not be swallowed. */
    if (!/UNIQUE constraint failed/i.test(String(err && err.message))) throw err;
    const first = await env.DB
      .prepare('SELECT id FROM events WHERE source = ? AND sender_id = ?')
      .bind(slug, senderId).first();
    if (seenKey && first) {
      await env.SEEN.put(seenKey, first.id, { expirationTtl: DEDUPE_TTL_S });
    }
    return json({ ok: true, id: first ? first.id : null, duplicate: true }, 200);
  }

  if (seenKey) {
    await env.SEEN.put(seenKey, id, { expirationTtl: DEDUPE_TTL_S });
  }

  /* Queued AFTER the row exists, for the same reason the row comes
     before the mail in intake-worker. If the enqueue fails the event is
     still on disk and can be replayed; if it were the other way round a
     queue hiccup would lose an event we had already told the sender we
     had. */
  await env.DELIVERIES.send({ eventId: id, slug });
  return json({ ok: true, id, received_at: now }, 202);
}

export default {
  queue,

  async fetch(request, env) {
    const url = new URL(request.url);
    const m = url.pathname.match(/^\/in\/([a-z0-9][a-z0-9-]{0,62})$/);

    if (m && request.method === 'POST') {
      try {
        return await receive(request, env, m[1]);
      } catch (err) {
        /* The sender is told it failed and nothing else. The detail
           goes to the log, where it is ours. */
        console.error('receive failed', err && err.stack || String(err));
        return json({ error: 'internal error' }, 500);
      }
    }

    if (url.pathname === '/health') return json({ ok: true }, 200);
    if (m) return json({ error: 'POST only' }, 405);
    return json({ error: 'not found' }, 404);
  },
};

export { EndpointLimiter };
export { sameSig, verify, hmacHex };
