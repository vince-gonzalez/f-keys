/*
============================================================
relay - tests for the part that must not be wrong
F-Keys | www.f-keys.com
------------------------------------------------------------
Verification is the only thing standing between this service
and anyone on the internet writing rows into it. A test that
only proves a good signature passes is worthless: every broken
implementation in history passed that test. These mostly prove
that bad signatures FAIL, including the near misses.

Run:  node --test test/
============================================================
*/
import test from 'node:test';
import assert from 'node:assert/strict';
import { sameSig, verify, hmacHex } from '../src/index.js';

const SECRET = 'shhh-test-only';
const BODY = JSON.stringify({ id: 'evt_1', hello: 'world' });
const now = () => Math.floor(Date.now() / 1000);

async function header(body, secret = SECRET, ts = now()) {
  return `t=${ts},v1=${await hmacHex(secret, `${ts}.${body}`)}`;
}

test('a correct signature passes', async () => {
  const r = await verify(BODY, await header(BODY), SECRET, 300);
  assert.equal(r.ok, true);
});

test('a body changed by one character fails', async () => {
  const h = await header(BODY);
  const tampered = BODY.replace('world', 'worlc');
  const r = await verify(tampered, h, SECRET, 300);
  assert.equal(r.ok, false);
  assert.equal(r.why, 'signature mismatch');
});

test('the wrong secret fails', async () => {
  const h = await header(BODY, 'not-the-secret');
  const r = await verify(BODY, h, SECRET, 300);
  assert.equal(r.ok, false);
});

test('a replayed request outside tolerance fails', async () => {
  // Signed correctly, just old. This is the attack that signing the
  // body alone would leave wide open for as long as the secret lived.
  const h = await header(BODY, SECRET, now() - 4000);
  const r = await verify(BODY, h, SECRET, 300);
  assert.equal(r.ok, false);
  assert.match(r.why, /^stale by/);
});

test('a replayed request inside tolerance still passes', async () => {
  const h = await header(BODY, SECRET, now() - 10);
  assert.equal((await verify(BODY, h, SECRET, 300)).ok, true);
});

test('moving the timestamp invalidates the signature', async () => {
  // The timestamp is inside the signed string, so an attacker cannot
  // freshen a captured request by editing t.
  const old = now() - 4000;
  const h = await header(BODY, SECRET, old);
  const freshened = h.replace(`t=${old}`, `t=${now()}`);
  const r = await verify(BODY, freshened, SECRET, 300);
  assert.equal(r.ok, false);
  assert.equal(r.why, 'signature mismatch');
});

test('a missing header fails rather than throwing', async () => {
  const r = await verify(BODY, null, SECRET, 300);
  assert.equal(r.ok, false);
  assert.equal(r.why, 'no signature header');
});

test('a malformed header fails rather than throwing', async () => {
  for (const h of ['', 'garbage', 't=', 'v1=abc', 't=abc,v1=']) {
    const r = await verify(BODY, h, SECRET, 300);
    assert.equal(r.ok, false, `expected ${JSON.stringify(h)} to fail`);
  }
});

test('an empty body is still signed over, not waved through', async () => {
  assert.equal((await verify('', await header(''), SECRET, 300)).ok, true);
  assert.equal((await verify('', await header('x'), SECRET, 300)).ok, false);
});

test('sameSig rejects on length before comparing', () => {
  assert.equal(sameSig('abc', 'abcd'), false);
  assert.equal(sameSig('abc', 'abc'), true);
  assert.equal(sameSig('abc', 'abd'), false);
});

test('sameSig does not throw on non-strings', () => {
  assert.equal(sameSig(null, 'a'), false);
  assert.equal(sameSig(undefined, undefined), false);
  assert.equal(sameSig(123, 123), false);
});

test('sameSig compares the whole string, not a prefix', () => {
  // The property that makes it constant time: every character is
  // visited whatever happens, so the answer carries no timing signal
  // about where the first difference was.
  const a = 'a'.repeat(64);
  assert.equal(sameSig(a, 'b' + a.slice(1)), false);
  assert.equal(sameSig(a, a.slice(0, 63) + 'b'), false);
});
