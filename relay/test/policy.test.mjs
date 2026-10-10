/*
============================================================
relay - the retry policy, which is the whole judgement
F-Keys | www.f-keys.com
------------------------------------------------------------
Delivery is a fetch. The part worth testing is knowing when to
STOP, because a relay that retries everything turns one broken
destination into permanent load on itself and on them.

The line people get wrong is "other 4xx". A 400 means the
destination read the request and refused it; the same bytes
cannot produce a different answer later, so a retry is a loop
that ends only when the cap does. 429 is a 4xx that means the
opposite - come back later - which is why the retryable ones
are carved out by number rather than by class.
============================================================
*/
import test from 'node:test';
import assert from 'node:assert/strict';
import { classify, backoff, ATTEMPT_CHUNK, RETRY_4XX }
  from '../src/deliver.js';

test('2xx is delivered and nothing else is', () => {
  for (const s of [200, 201, 202, 204, 299]) {
    assert.equal(classify(s), 'delivered', `${s} should be delivered`);
  }
  assert.notEqual(classify(300), 'delivered');
  assert.notEqual(classify(199), 'delivered');
});

test('5xx retries: the destination is broken, the event is not', () => {
  for (const s of [500, 502, 503, 504, 599]) {
    assert.equal(classify(s), 'retry', `${s} should retry`);
  }
});

test('a plain 4xx is refused and never retried', () => {
  // The one that matters. Retrying a 400 is an infinite loop with a bill.
  for (const s of [400, 401, 403, 404, 409, 410, 422]) {
    assert.equal(classify(s), 'refused', `${s} must not retry`);
  }
});

test('408, 425 and 429 are the 4xx that mean "later"', () => {
  for (const s of RETRY_4XX) {
    assert.equal(classify(s), 'retry', `${s} should retry`);
  }
  // and they are carved out by number, so no neighbour leaks through
  assert.equal(classify(407), 'refused');
  assert.equal(classify(409), 'refused');
  assert.equal(classify(428), 'refused');
  assert.equal(classify(430), 'refused');
});

test('backoff doubles and then stops doubling', () => {
  assert.equal(backoff(1), 30);
  assert.equal(backoff(2), 60);
  assert.equal(backoff(3), 120);
  assert.equal(backoff(4), 240);
  assert.equal(backoff(5), 480);
  // Capped. Unbounded doubling schedules attempt twelve for next week,
  // long after anyone is still waiting for it.
  assert.equal(backoff(6), 900);
  assert.equal(backoff(12), 900);
  assert.equal(backoff(40), 900);
});

test('backoff never returns something a queue would reject', () => {
  for (let i = 1; i <= 40; i++) {
    const d = backoff(i);
    assert.ok(Number.isFinite(d) && d > 0 && d <= 900,
      `backoff(${i}) = ${d}`);
  }
});

test('the attempt chunk stays under the D1 bound-parameter ceiling', () => {
  // attempts binds eight columns; 100 / 8 = 12 is the ceiling.
  assert.equal(ATTEMPT_CHUNK, 11);
  assert.ok(ATTEMPT_CHUNK * 8 <= 100,
    'a chunk that binds more than 100 parameters fails on every run');
  // and the headroom is real, not accidental
  assert.ok(ATTEMPT_CHUNK < Math.floor(100 / 8));
});
