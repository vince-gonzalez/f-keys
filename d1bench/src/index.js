/*
============================================================
d1bench - how fast can you write N rows to D1, and which
limit stops you first
F-Keys | www.f-keys.com
------------------------------------------------------------
This measures the thing every Workers developer guesses at.
Cloudflare documents its D1 limits individually; it does not
document how they interact, and they interact in a way that
changes which strategy is correct.

THREE STRATEGIES, each stopped by a DIFFERENT limit:

  params    one multi-row INSERT, values bound. Capped at
            floor(100 / C) rows per statement, where C is
            columns bound per row. Degrades on COLUMN COUNT.
  literal   one multi-row INSERT, values inlined. Capped by
            the 100,000-byte statement length instead.
            Degrades on ROW SIZE.
  onebyone  one single-row statement per row, all handed to
            batch(). Capped by queries per invocation and by
            the 30s ceiling on the whole batch() call.

WHY THIS RUNS INSIDE A WORKER. Two of those limits only
exist inside a Worker invocation - queries per invocation,
and the 30 second cap on one batch() call. Measured from a
laptop they do not exist at all, and the number you get is
mostly your own home internet.

------------------------------------------------------------
THE CLOCK, AND THE BIAS IT WOULD HAVE HIDDEN

In Workers, Date.now() advances only on I/O. It is frozen
across pure computation - a deliberate timing-attack
mitigation, not a bug.

For timing a D1 round trip that is fine: the await IS the
I/O, so the clock moves. But it means the CPU cost of
BUILDING a statement is invisible to this clock, and the
literal strategy is precisely the one that does more CPU
work - string concatenation and quote escaping per value.

Timed only from in here, literal SQL would look better than
it is, and the headline finding would be an artifact of the
measuring instrument.

So every run reports BOTH:

  d1_ms     the awaited D1 time, measured in here
  (and the driver records total request wall clock from
   outside, which includes the CPU the clock in here cannot
   see, plus network)

d1_ms isolates the database. The driver's outside number
catches what d1_ms structurally cannot. Reporting one
without the other is how this gets the answer wrong.
------------------------------------------------------------
Deploy:  cd d1bench && npx wrangler deploy
============================================================
*/

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8' },
});

/* Documented ceilings, 2026-10-10. Named rather than inlined so the
   report can state what it was measured against, and so a change on
   Cloudflare's side is a one-line edit rather than a hunt. */
const LIMITS = {
  bound_params_per_query: 100,
  statement_bytes: 100000,
  columns_per_table: 100,
  query_duration_s: 30,
  max_row_bytes: 2 * 1024 * 1024,
};

const table = (c) => `bench_c${c}`;
const cols = (c) => Array.from({ length: c }, (_, i) => `c${i}`);

/* A payload of an exact byte length, with no character that needs
   escaping. Escaping is measured separately and on purpose - mixing it
   into the size sweep would confound row size with quote density. */
function payload(bytes) {
  return 'x'.repeat(Math.max(0, bytes));
}

/* SQLite escapes a single quote by doubling it. There is no backslash
   escape in standard SQLite, and reaching for one is how an injection
   gets in. This is the whole reason the literal strategy needs
   justifying by measurement rather than taken on vibes. */
function sqlLiteral(s) {
  return "'" + String(s).replace(/'/g, "''") + "'";
}

function rows(n, c, bytes) {
  const v = payload(bytes);
  const out = [];
  for (let i = 0; i < n; i++) {
    const r = new Array(c);
    /* Column 0 carries the row index so the written data is
       distinguishable; the rest carry the size payload. */
    r[0] = `r${i}`;
    for (let j = 1; j < c; j++) r[j] = v;
    out.push(r);
  }
  return out;
}

/* ---------- strategy: bound parameters, chunked ---------- */
function buildParams(c, data, rowsPerStmt) {
  const names = cols(c).join(',');
  const one = '(' + new Array(c).fill('?').join(',') + ')';
  const stmts = [];
  for (let i = 0; i < data.length; i += rowsPerStmt) {
    const slice = data.slice(i, i + rowsPerStmt);
    stmts.push({
      sql: `INSERT INTO ${table(c)} (${names}) VALUES `
         + new Array(slice.length).fill(one).join(','),
      binds: slice.flat(),
    });
  }
  return stmts;
}

/* ---------- strategy: literal SQL, chunked by byte budget ---------- */
function buildLiteral(c, data, byteBudget) {
  const names = cols(c).join(',');
  const head = `INSERT INTO ${table(c)} (${names}) VALUES `;
  const stmts = [];
  let parts = [];
  let len = head.length;
  for (const r of data) {
    const tup = '(' + r.map(sqlLiteral).join(',') + ')';
    /* +1 for the comma that will join it. Checked BEFORE appending,
       because a statement discovered to be over the limit after the
       fact is a failed query, not a measurement. */
    if (parts.length && len + 1 + tup.length > byteBudget) {
      stmts.push({ sql: head + parts.join(','), binds: [] });
      parts = [];
      len = head.length;
    }
    len += (parts.length ? 1 : 0) + tup.length;
    parts.push(tup);
  }
  if (parts.length) stmts.push({ sql: head + parts.join(','), binds: [] });
  return stmts;
}

/* ---------- strategy: one statement per row ---------- */
function buildOneByOne(c, data) {
  const names = cols(c).join(',');
  const one = '(' + new Array(c).fill('?').join(',') + ')';
  const sql = `INSERT INTO ${table(c)} (${names}) VALUES ${one}`;
  return data.map((r) => ({ sql, binds: r }));
}

const BUILDERS = {
  params: (c, data, opt) =>
    buildParams(c, data, opt.rowsPerStmt
      || Math.max(1, Math.floor(LIMITS.bound_params_per_query / c))),
  literal: (c, data, opt) =>
    buildLiteral(c, data, opt.byteBudget || LIMITS.statement_bytes - 2000),
  onebyone: (c, data) => buildOneByOne(c, data),
};

async function setup(env, cSweep) {
  const made = [];
  for (const c of cSweep) {
    if (c > LIMITS.columns_per_table) continue;
    const defs = cols(c).map((n) => `${n} TEXT`).join(', ');
    await env.DB.prepare(`DROP TABLE IF EXISTS ${table(c)}`).run();
    await env.DB.prepare(`CREATE TABLE ${table(c)} (${defs})`).run();
    made.push({ columns: c, table: table(c) });
  }
  return made;
}

async function runOne(env, strategy, c, n, bytes, opt) {
  const data = rows(n, c, bytes);
  const built = BUILDERS[strategy](c, data, opt);

  const stmts = built.map((s) => {
    const p = env.DB.prepare(s.sql);
    return s.binds.length ? p.bind(...s.binds) : p;
  });

  const maxSqlBytes = built.reduce((m, s) => Math.max(m, s.sql.length), 0);
  const maxBinds = built.reduce((m, s) => Math.max(m, s.binds.length), 0);

  /* The measured quantity. Everything either side of these two lines is
     setup, and setup is what the driver's outside clock catches. */
  const t0 = Date.now();
  await env.DB.batch(stmts);
  const d1_ms = Date.now() - t0;

  return {
    strategy, columns: c, rows: n, row_bytes: bytes,
    d1_ms,
    statements: built.length,
    rows_per_stmt_max: Math.ceil(n / built.length),
    max_bound_params: maxBinds,
    max_stmt_bytes: maxSqlBytes,
    /* Stated, not implied: which ceiling this run came nearest to. */
    nearest_limit: {
      bound_params: +(maxBinds / LIMITS.bound_params_per_query).toFixed(3),
      stmt_bytes: +(maxSqlBytes / LIMITS.statement_bytes).toFixed(3),
      queries: built.length,
    },
  };
}

/* ---------- probes: find the REAL ceiling, do not trust the doc ----------
   Each probe climbs until D1 refuses, and reports the last value that
   worked plus the error text at the first that did not. A documented
   limit that has never been hit on purpose is a number someone typed. */
async function probeParams(env, c) {
  const names = cols(c).join(',');
  const one = '(' + new Array(c).fill('?').join(',') + ')';
  let lastOk = 0, failedAt = null, err = null;
  for (let r = 1; r <= 120; r++) {
    const data = rows(r, c, 4);
    const sql = `INSERT INTO ${table(c)} (${names}) VALUES `
      + new Array(r).fill(one).join(',');
    try {
      await env.DB.prepare(sql).bind(...data.flat()).run();
      lastOk = r;
    } catch (e) {
      failedAt = r;
      err = String((e && e.message) || e).slice(0, 220);
      break;
    }
  }
  return {
    columns: c,
    max_rows_per_statement: lastOk,
    params_at_max: lastOk * c,
    failed_at_rows: failedAt,
    params_at_failure: failedAt ? failedAt * c : null,
    predicted: Math.floor(LIMITS.bound_params_per_query / c),
    error: err,
  };
}

async function probeBatch(env, c, ladder) {
  /* How many statements may one batch() call carry. This is the limit
     that tells us which D1 plan is in force: 50 on free, 1000 on paid.
     Climbs by doubling, then walks back to find the edge. */
  const names = cols(c).join(',');
  const one = '(' + new Array(c).fill('?').join(',') + ')';
  const sql = `INSERT INTO ${table(c)} (${names}) VALUES ${one}`;
  const mk = (k) => Array.from({ length: k }, (_, i) =>
    env.DB.prepare(sql).bind(...rows(1, c, 4)[0].map((v, j) => j === 0 ? `b${i}` : v)));

  let lastOk = 0, failedAt = null, err = null;
  const rungs = ladder && ladder.length ? ladder
    : [1, 10, 25, 50, 51, 100, 250, 500, 999, 1000, 1001, 1500];
  const timings = [];
  for (const k of rungs) {
    try {
      const t0 = Date.now();
      await env.DB.batch(mk(k));
      timings.push({ statements: k, d1_ms: Date.now() - t0 });
      lastOk = k;
    } catch (e) {
      failedAt = k;
      err = String((e && e.message) || e).slice(0, 220);
      break;
    }
  }
  return {
    max_statements_per_batch_observed: lastOk,
    failed_at: failedAt,
    error: err,
    timings,
    /* 50 would mean the free plan's cap is in force, 1000 the paid
       plan's. Inferring the plan from which features are bound is a
       guess; climbing until D1 refuses is a measurement. Anything
       ABOVE 1000 means the documented "queries per Worker invocation"
       cap is not being charged per statement inside batch(), which is
       the opposite of how it is usually read. */
    implies: failedAt === null
      ? `no refusal through ${lastOk} statements - above both documented caps`
      : (lastOk <= 50 ? 'free-plan cap (50) in force'
        : lastOk <= 1000 ? 'paid-plan cap (1000) in force'
          : 'refused above the documented 1000'),
  };
}

async function probeStmtBytes(env, c) {
  /* Walk the statement length up with literal SQL until it is refused. */
  const names = cols(c).join(',');
  const head = `INSERT INTO ${table(c)} (${names}) VALUES `;
  let lastOk = 0, failedAt = null, err = null;
  for (const target of [1000, 10000, 50000, 90000, 99000, 100000, 100500, 120000, 200000]) {
    /* One row, padded so the whole statement lands near `target`. */
    const overhead = head.length + 2 + (c * 4);
    const per = Math.max(1, Math.floor((target - overhead) / c));
    const r = new Array(c).fill(payload(per));
    r[0] = 'r0';
    const sql = head + '(' + r.map(sqlLiteral).join(',') + ')';
    try {
      await env.DB.prepare(sql).run();
      lastOk = sql.length;
    } catch (e) {
      failedAt = sql.length;
      err = String((e && e.message) || e).slice(0, 220);
      break;
    }
  }
  return {
    columns: c,
    max_statement_bytes_observed: lastOk,
    failed_at_bytes: failedAt,
    documented: LIMITS.statement_bytes,
    error: err,
  };
}

/* Constant-time compare, same reasoning and same code as the relay. */
function sameToken(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname;

    /* EVERY WRITING ROUTE IS GATED, and the reason is money rather than
       secrecy. This endpoint inserts D1 rows on demand, in bulk, as fast
       as it can. Left open on the internet it is a billing hole with a
       documented API: anyone who found it could run the row counter up
       on someone else's account. /limits is static text and open. */
    if (p !== '/limits') {
      if (!env.BENCH_TOKEN
          || !sameToken(request.headers.get('x-bench-token') || '',
                        env.BENCH_TOKEN)) {
        return json({ error: 'not found' }, 404);
      }
    }

    try {
      if (p === '/limits') return json({ documented: LIMITS });

      if (p === '/setup' && request.method === 'POST') {
        const body = await request.json();
        return json({ ok: true, tables: await setup(env, body.columns || [2, 4, 8, 16, 32, 64]) });
      }

      if (p === '/truncate' && request.method === 'POST') {
        const body = await request.json();
        const done = [];
        for (const c of body.columns || []) {
          await env.DB.prepare(`DELETE FROM ${table(c)}`).run();
          done.push(c);
        }
        return json({ ok: true, truncated: done });
      }

      if (p === '/run' && request.method === 'POST') {
        const b = await request.json();
        if (!BUILDERS[b.strategy]) return json({ error: 'unknown strategy' }, 400);
        return json(await runOne(env, b.strategy, b.columns, b.rows,
          b.row_bytes ?? 16, b.options || {}));
      }

      if (p === '/probe/params' && request.method === 'POST') {
        const b = await request.json();
        return json(await probeParams(env, b.columns));
      }
      if (p === '/probe/batch' && request.method === 'POST') {
        const b = await request.json();
        return json(await probeBatch(env, b.columns ?? 4, b.ladder));
      }
      if (p === '/probe/stmtbytes' && request.method === 'POST') {
        const b = await request.json();
        return json(await probeStmtBytes(env, b.columns ?? 4));
      }

      if (p === '/count') {
        const b = Object.fromEntries(url.searchParams);
        const c = Number(b.columns || 4);
        const r = await env.DB.prepare(
          `SELECT COUNT(*) AS n FROM ${table(c)}`).first();
        return json({ columns: c, rows: r ? r.n : null });
      }

      return json({ error: 'not found', routes: ['/limits', '/setup', '/run', '/truncate', '/probe/params', '/probe/batch', '/probe/stmtbytes', '/count'] }, 404);
    } catch (err) {
      /* A benchmark that swallows its errors reports speed it did not
         achieve. The error text IS data here - it names the limit. */
      return json({
        error: 'run failed',
        message: String((err && err.message) || err).slice(0, 400),
      }, 500);
    }
  },
};
