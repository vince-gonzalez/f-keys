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

const enc = new TextEncoder();

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

  await env.DB.prepare(
    'INSERT INTO events (id, source, sender_id, received_at, signature_ok,'
    + ' reject_reason, body_bytes, body) VALUES (?,?,?,?,?,?,?,?)')
    .bind(id, slug, senderId, now, v.ok ? 1 : 0, v.ok ? null : v.why,
          raw.length, raw)
    .run();

  if (!v.ok) return json({ error: 'signature rejected', reason: v.why }, 401);
  return json({ ok: true, id, received_at: now }, 202);
}

export default {
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

export { sameSig, verify, hmacHex };
