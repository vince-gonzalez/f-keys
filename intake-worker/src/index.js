/*
============================================================
f-keys-intake - where a website enquiry actually lands
F-Keys | www.f-keys.com
------------------------------------------------------------
The order of operations is the whole design.

  1. validate
  2. write the row
  3. try to notify
  4. answer the browser

Three is allowed to fail. One and two are not, and four reports
what really happened rather than a timer. The form this serves
used to show "Submission Sent" on a 600ms setTimeout whether or
not anything left the browser; that is the defect this exists
to make impossible.
============================================================
*/

/* A Workers request body caps at 100 MB and base64 inflates by a third,
   so a per-file ceiling keeps one oversized photo from failing the whole
   enquiry. Anything larger is still recorded by name and asked for later. */
const MAX_FILE_BYTES = 12 * 1024 * 1024;

/* How long a download link in the notification stays good. Long enough
   to act on a lead over a weekend, short enough that a forwarded email
   is not a permanent key to someone's brand assets. */
const LINK_TTL_SECONDS = 14 * 24 * 60 * 60;

const now = () => new Date().toISOString();

const id = (prefix) => {
  const b = crypto.getRandomValues(new Uint8Array(12));
  return prefix + Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
};

/* An address is evidence in a dispute about what was agreed, so it is
   kept - but kept as a salted hash, so the table is not a list of
   visitor IP addresses if it ever leaks. */
async function hashIp(ip, salt) {
  if (!ip) return null;
  const data = new TextEncoder().encode(String(salt || '') + '|' + ip);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(digest).slice(0, 12),
    (x) => x.toString(16).padStart(2, '0')).join('');
}

/* A link in an email cannot carry the admin key, and the bucket must
   not be public - a client's logo is their property, not the internet's.
   So the link carries its own expiry and a signature over it. */
async function signFile(env, fileId, exp) {
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(String(env.FILE_SIGNING_KEY || env.IP_SALT || '')),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const mac = await crypto.subtle.sign('HMAC', key,
    new TextEncoder().encode(fileId + '.' + exp));
  return Array.from(new Uint8Array(mac).slice(0, 16),
    (x) => x.toString(16).padStart(2, '0')).join('');
}

/* Compared with a constant-time walk rather than ===, so a wrong
   signature cannot be guessed one character at a time from timing. */
function sameSig(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function allowed(origin, env) {
  const list = (env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim()).filter(Boolean);
  return list.includes(origin) ? origin : list[0] || '';
}

const json = (body, status, origin) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': origin,
      'Cache-Control': 'no-store'
    }
  });

/* Every address in NOTIFY_EMAIL, comma separated. Two inboxes is not
   redundancy for its own sake: if one of them silently stops
   delivering, the other one is how that gets noticed. */
const recipients = (env) => String(env.NOTIFY_EMAIL || '')
  .split(',').map((s) => s.trim()).filter(Boolean);

/* Resend if a key is set. Returns why it refused rather than a bare
   false: "the customer never got the email" has to be answerable, and
   an unverified domain and a rate limit are not the same problem.

   MAIL_FROM is a var, not a literal, because the sending domain is a
   SUBDOMAIN - f-keys.com itself is Apple's, and writing sender records
   at the apex would fight the MX that already works. */
async function notify(env, subject, text) {
  if (!env.RESEND_API_KEY) return { ok: false, why: 'no RESEND_API_KEY set' };
  const to = recipients(env);
  if (!to.length) return { ok: false, why: 'no NOTIFY_EMAIL set' };
  try {
    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: 'Bearer ' + env.RESEND_API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: env.MAIL_FROM || 'F-Keys Intake <intake@send.f-keys.com>',
        to: to,
        subject: subject,
        text: text
      })
    });
    if (!r.ok) {
      let why = '';
      try { why = (await r.text()).slice(0, 300); } catch (e) { why = 'unreadable body'; }
      return { ok: false, why: 'HTTP ' + r.status + ' ' + why };
    }
    return { ok: true, why: '' };
  } catch (e) {
    return { ok: false, why: String(e).slice(0, 300) };
  }
}

async function handleSubmit(request, env, origin) {
  let payload;
  try {
    payload = await request.json();
  } catch (e) {
    return json({ error: 'body was not JSON' }, 400, origin);
  }

  const f = payload.fields || {};
  const body = typeof payload.body === 'string' ? payload.body : '';
  const email = String(f['Email'] || '').trim();

  /* A submission with no readable body and no email is not an intake,
     it is a probe. Everything else is stored even if it is partial -
     a half-filled enquiry from a real business is still a lead. */
  if (!body && !email) {
    return json({ error: 'nothing to record' }, 400, origin);
  }

  const subId = id('sub_');
  const ts = now();

  await env.DB.prepare(
    'INSERT INTO submissions' +
    ' (id, form_type, business, contact, email, phone, fields, body,' +
    '  due_build, due_monthly, addons, agreed_at, user_agent, country,' +
    '  ip_hash, notified, created_at)' +
    ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?)'
  ).bind(
    subId,
    String(payload.formType || 'Client Intake').slice(0, 60),
    String(f['Business Name'] || '').slice(0, 200) || null,
    String(f['Contact'] || '').slice(0, 200) || null,
    email.slice(0, 200) || null,
    String(f['Phone'] || '').slice(0, 60) || null,
    JSON.stringify(f),
    body,
    String(f['Due To Build'] || '').slice(0, 40) || null,
    String(f['Monthly After Launch'] || '').slice(0, 40) || null,
    String(f['Add-Ons'] || '').slice(0, 2000) || null,
    String(f['Agreement Accepted'] || '').slice(0, 200) || null,
    (request.headers.get('User-Agent') || '').slice(0, 300) || null,
    request.headers.get('CF-IPCountry') || null,
    await hashIp(request.headers.get('CF-Connecting-IP'), env.IP_SALT),
    ts
  ).run();

  /* The bytes go to R2 and never into D1 - a 4 MB logo base64s past the
     1 MB row cap, and a failed write here would take the intake down
     with it. If FILES is not bound the name is still recorded, so the
     intake keeps working before the bucket exists rather than after. */
  const files = Array.isArray(payload.files) ? payload.files.slice(0, 20) : [];
  const stored = [];
  for (const file of files) {
    const name = String((file && file.name) || '').slice(0, 300);
    if (!name) continue;
    const bytes = typeof file.data === 'string'
      ? Math.round(file.data.length * 3 / 4) : null;

    let r2Key = null;
    if (env.FILES && typeof file.data === 'string' && bytes && bytes <= MAX_FILE_BYTES) {
      try {
        const raw = Uint8Array.from(atob(file.data), (c) => c.charCodeAt(0));
        r2Key = subId + '/' + name.replace(/[^\w.\- ]+/g, '_');
        await env.FILES.put(r2Key, raw, {
          httpMetadata: { contentType: String(file.type || 'application/octet-stream') }
        });
      } catch (e) {
        r2Key = null;   // the enquiry survives a failed upload
      }
    }

    const row = await env.DB.prepare(
      'INSERT INTO submission_files (submission_id, name, mime, bytes, r2_key)' +
      ' VALUES (?,?,?,?,?) RETURNING id'
    ).bind(subId, name, String(file.type || '').slice(0, 120) || null, bytes, r2Key).first();
    stored.push({ id: row && row.id, name: name, bytes: bytes, r2Key: r2Key });
  }

  const subject = String(payload.subject
    || ('Website Intake - ' + (f['Business Name'] || 'no name')));
  let lines = body;
  if (stored.length) {
    const exp = Math.floor(Date.now() / 1000) + LINK_TTL_SECONDS;
    const base = new URL(request.url).origin;
    const parts = [];
    for (const s of stored) {
      if (s.r2Key && s.id) {
        const sig = await signFile(env, String(s.id), exp);
        parts.push('  ' + s.name + '\n    ' + base + '/file/' + s.id
          + '?exp=' + exp + '&sig=' + sig);
      } else {
        parts.push('  ' + s.name + '  (not stored - ask for it in the reply)');
      }
    }
    lines += '\n\nFILES\n' + parts.join('\n')
      + '\n\n  Links expire in 14 days. Save anything you want to keep.';
  }

  const sent = await notify(env, subject, lines);
  await env.DB.prepare(
    'UPDATE submissions SET notified = ?, notify_error = ? WHERE id = ?'
  ).bind(sent.ok ? 1 : 0, sent.ok ? null : sent.why.slice(0, 300), subId).run();

  /* The browser is told the truth about the part that matters. The row
     is safe; whether the email went is a separate fact and is reported
     as one. */
  return json({
    ok: true,
    id: subId,
    recorded: true,
    notified: sent.ok,
    received_at: ts
  }, 200, origin);
}

/* Reading the table back without the dashboard. Guarded by a secret
   because it returns other businesses contact details. */
async function handleList(request, env, origin) {
  const key = request.headers.get('X-Admin-Key') || '';
  if (!env.ADMIN_KEY || key !== env.ADMIN_KEY) {
    return json({ error: 'not authorised' }, 401, origin);
  }
  const url = new URL(request.url);
  const limit = Math.min(parseInt(url.searchParams.get('limit') || '25', 10) || 25, 100);
  const full = url.searchParams.get('full') === '1';
  const cols = full
    ? 'id, created_at, form_type, business, contact, email, phone, due_build, due_monthly, addons, agreed_at, country, notified, notify_error, body'
    : 'id, created_at, form_type, business, contact, email, phone, due_build, due_monthly, notified, notify_error';
  const rows = await env.DB.prepare(
    'SELECT ' + cols + ' FROM submissions ORDER BY created_at DESC LIMIT ?'
  ).bind(limit).all();
  return json({ count: rows.results.length, submissions: rows.results }, 200, origin);
}

/* Serves one uploaded file to whoever holds an unexpired signature.
   No public bucket and no admin key in an email link. */
async function handleFile(request, env, origin, fileId) {
  if (!env.FILES) return json({ error: 'no file storage' }, 404, origin);
  const url = new URL(request.url);
  const exp = parseInt(url.searchParams.get('exp') || '0', 10);
  const sig = url.searchParams.get('sig') || '';
  if (!exp || Math.floor(Date.now() / 1000) > exp) {
    return json({ error: 'link expired' }, 410, origin);
  }
  if (!sameSig(sig, await signFile(env, fileId, exp))) {
    return json({ error: 'not authorised' }, 401, origin);
  }
  const row = await env.DB.prepare(
    'SELECT name, mime, r2_key FROM submission_files WHERE id = ?'
  ).bind(fileId).first();
  if (!row || !row.r2_key) return json({ error: 'no such file' }, 404, origin);

  const obj = await env.FILES.get(row.r2_key);
  if (!obj) return json({ error: 'file missing from storage' }, 404, origin);

  return new Response(obj.body, {
    headers: {
      'Content-Type': row.mime || 'application/octet-stream',
      'Content-Disposition': 'inline; filename="' + String(row.name).replace(/"/g, '') + '"',
      'Cache-Control': 'private, no-store'
    }
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = allowed(request.headers.get('Origin') || '', env);

    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': origin,
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, X-Admin-Key',
          'Access-Control-Max-Age': '86400'
        }
      });
    }

    if (url.pathname === '/health') {
      return json({ ok: true, at: now() }, 200, origin);
    }

    if (url.pathname === '/submit' && request.method === 'POST') {
      try {
        return await handleSubmit(request, env, origin);
      } catch (e) {
        /* The browser must not be told "sent" because a write threw.
           It falls back to the copy box, which is why that box exists. */
        return json({ error: 'not recorded', detail: String(e).slice(0, 200) }, 500, origin);
      }
    }

    const fileMatch = url.pathname.match(/^\/file\/(\d+)$/);
    if (fileMatch && request.method === 'GET') {
      try {
        return await handleFile(request, env, origin, fileMatch[1]);
      } catch (e) {
        return json({ error: String(e).slice(0, 200) }, 500, origin);
      }
    }

    if (url.pathname === '/submissions' && request.method === 'GET') {
      try {
        return await handleList(request, env, origin);
      } catch (e) {
        return json({ error: String(e).slice(0, 200) }, 500, origin);
      }
    }

    return json({ error: 'no such route' }, 404, origin);
  }
};
