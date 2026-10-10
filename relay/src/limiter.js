/*
============================================================
relay - the rate limiter, one object per endpoint
F-Keys | www.f-keys.com
------------------------------------------------------------
Until this existed, anyone who knew an endpoint name could
make this service write a D1 row by POSTing garbage at it. The
signature check rejected the content; it did not stop the
write, because recording a rejection is the point of recording
rejections. That is why there was no custom domain.

TWO BUCKETS, NOT ONE, AND THAT IS THE WHOLE DESIGN.

The first version had a single bucket and charged a rejected
request five tokens instead of one. It drained correctly under
a flood of bad signatures - and then a live test fired one
GOOD request immediately afterwards and got 429. A stranger
could silence a real sender just by shouting at the same
endpoint, which makes a rate limiter into the denial of
service it is supposed to prevent. The first version of this
test even had the excuse pre-written into it: "the bucket is
shared, which is expected". It is not expected. It is the bug.

So:

  verified requests spend OK tokens
  rejected requests spend BAD tokens

and the two never touch. A flood of garbage empties the bad
bucket and cannot reach the good one, so a genuine sender on
the same endpoint is unaffected by any amount of noise.

WHAT A FLOOD STILL COSTS, stated plainly: one object call, one
indexed D1 read and one HMAC per request. That is bounded and
cheap. What it no longer costs is an unbounded D1 WRITE, which
was the thing keeping this off a real domain. When the bad
bucket is empty the answer is still 401 - the sender learns
nothing new - but the row is not recorded.

Refill is continuous rather than a window that resets. A fixed
window lets a sender spend the whole budget in the last second
of one window and the whole budget again in the first second
of the next, which is twice the rate the number claims.
============================================================
*/

/* Verified traffic: generous. A busy sender in a retry storm is still
   a legitimate sender and should not be throttled for being busy. */
const OK_CAPACITY = 600;
const OK_REFILL_PER_S = 10;

/* Rejected traffic: tight. A correctly configured sender produces
   approximately none of this, so a small bucket costs real users
   nothing and a flood hits the floor in seconds. */
const BAD_CAPACITY = 20;
const BAD_REFILL_PER_S = 0.2;   // one every five seconds

const BUCKETS = {
  ok:  { cap: OK_CAPACITY,  rate: OK_REFILL_PER_S,  key: 'ok' },
  bad: { cap: BAD_CAPACITY, rate: BAD_REFILL_PER_S, key: 'bad' },
};

export class EndpointLimiter {
  constructor(state) {
    this.state = state;
    this.mem = null;
  }

  async load() {
    if (this.mem) return;
    const saved = await this.state.storage.get(['ok', 'bad']);
    const now = Date.now();
    this.mem = {
      ok:  saved.get('ok')  ?? { tokens: OK_CAPACITY,  updated: now },
      bad: saved.get('bad') ?? { tokens: BAD_CAPACITY, updated: now },
    };
  }

  async fetch(request) {
    await this.load();
    const kind = new URL(request.url).searchParams.get('bucket') === 'bad'
      ? 'bad' : 'ok';
    const spec = BUCKETS[kind];
    const b = this.mem[kind];

    const now = Date.now();
    const elapsed = Math.max(0, now - b.updated) / 1000;
    b.tokens = Math.min(spec.cap, b.tokens + elapsed * spec.rate);
    b.updated = now;

    const allowed = b.tokens >= 1;
    if (allowed) b.tokens -= 1;

    await this.state.storage.put({ [spec.key]: b });

    /* Tell a throttled caller when to come back. A sender told nothing
       retries immediately and makes the problem worse. */
    const retryAfter = allowed
      ? 0 : Math.max(1, Math.ceil((1 - b.tokens) / spec.rate));

    return new Response(JSON.stringify({
      allowed, bucket: kind,
      remaining: Math.floor(b.tokens),
      retry_after_s: retryAfter,
    }), { headers: { 'content-type': 'application/json' } });
  }
}

/* A limiter that fails closed takes the service down the first time the
   object is slow, and a limiter is not the component that should be able
   to do that. If it cannot answer, the request proceeds: the signature
   check is still in front of everything that matters. */
export async function take(env, slug, bucket) {
  try {
    const id = env.LIMITER.idFromName(slug);
    const res = await env.LIMITER.get(id).fetch(
      `https://limiter/take?bucket=${bucket}`);
    return await res.json();
  } catch (err) {
    console.error('limiter unavailable', String(err && err.message || err));
    return { allowed: true, remaining: null, retry_after_s: 0, degraded: true };
  }
}

export { OK_CAPACITY, OK_REFILL_PER_S, BAD_CAPACITY, BAD_REFILL_PER_S };
