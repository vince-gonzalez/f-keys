/* ============================================================
   licence — which half of the product this copy is
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   WHAT IS FREE

   Everything a person needs to use their own computer.

   That is the whole line, and it moved on purpose. This is
   assistive software that also happens to suit streamers, which
   means the features somebody depends on cannot sit behind a
   payment - and images are the clearest case. For a streamer,
   artwork on a key is a flourish. For somebody who does not read,
   the symbol IS the word, and charging for it would be charging
   for vocabulary.

   So free now includes what used to be paid:

     imageKeys     symbols and artwork on a key
     speech        the computer says what a key is for
     scanning      switch access, dwell, repeat guard
     devices       as many as somebody needs, not two

   along with unlimited keys, profiles, pages, free placement,
   any shape, and every command.

   WHAT IS PAID

   What an organisation wants, rather than what a person needs:

     autoSwitch    the surface follows the foreground window
     meters        live audio levels rather than the setting
     commercial    use inside a business or institution

   Free for a person, paid for an organisation. It is the model
   assistive software has used for a long time, for the reason
   that a school district has a budget and a family often does
   not.

   HOW IT IS CHECKED, HONESTLY

   A licence is a signed statement, verified against a public key
   compiled into this file. There is no server, no activation
   call, and nothing leaves the machine - a paid copy works on a
   plane and in a building with no internet.

   This stops a key being forged. It does not stop somebody
   editing this file, and it is not meant to: that is true of
   every client side check ever written, and pretending otherwise
   would be a lie told to a customer. It is a lock on an honest
   door.

   No dependencies. Node's own crypto.
   ============================================================ */

var crypto = require('crypto');

// The matching private key is not in this repository and never will be.
var PUBLIC_KEY_B64 = 'MCowBQYDK2VwAyEA+bu6W/pxo1+yKr5FUiJP7frxPHG/WcTHKgBAVwb/c8M=';

var FREE = {
  keys: Infinity, profiles: Infinity, pages: Infinity,
  devices: Infinity,
  imageKeys: true, speech: true, scanning: true,
  autoSwitch: false, meters: false, commercial: false
};

var PRO = {
  keys: Infinity, profiles: Infinity, pages: Infinity,
  devices: Infinity,
  imageKeys: true, speech: true, scanning: true,
  autoSwitch: true, meters: true, commercial: true
};

function publicKey() {
  return crypto.createPublicKey({
    key: Buffer.from(PUBLIC_KEY_B64, 'base64'),
    format: 'der', type: 'spki'
  });
}

function b64urlToBuf(s) {
  var t = String(s || '').replace(/-/g, '+').replace(/_/g, '/');
  while (t.length % 4) { t += '='; }
  return Buffer.from(t, 'base64');
}

function bufToB64url(buf) {
  return buf.toString('base64')
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/**
 * Read a licence key.
 * Returns { ok, tier, name, issued, expires, reason }. Anything that does
 * not verify comes back as the free tier with a reason, never as an error:
 * a bad key must not stop the application starting.
 */
function read(key) {
  var free = { ok: false, tier: 'free', name: null, issued: null,
               expires: null, reason: 'No licence key.' };
  if (!key || typeof key !== 'string') { return free; }

  var parts = key.trim().split('.');
  if (parts.length !== 2) {
    return Object.assign({}, free, { reason: 'That is not a licence key.' });
  }

  var payloadBuf, sigBuf, claim;
  try {
    payloadBuf = b64urlToBuf(parts[0]);
    sigBuf = b64urlToBuf(parts[1]);
    claim = JSON.parse(payloadBuf.toString('utf8'));
  } catch (e) {
    return Object.assign({}, free, { reason: 'That key is damaged.' });
  }

  var good = false;
  try {
    good = crypto.verify(null, payloadBuf, publicKey(), sigBuf);
  } catch (e) { good = false; }

  if (!good) {
    return Object.assign({}, free, { reason: 'That key was not issued by us.' });
  }

  // An expiry is optional. A key without one does not expire, which is what
  // somebody who bought a version rather than a subscription is owed.
  if (claim.expires && Date.parse(claim.expires) < Date.now()) {
    return Object.assign({}, free, {
      name: claim.name || null,
      expires: claim.expires,
      reason: 'That licence ran out on ' + String(claim.expires).slice(0, 10) + '.'
    });
  }

  return {
    ok: true,
    tier: claim.tier === 'pro' ? 'pro' : 'free',
    name: claim.name || null,
    issued: claim.issued || null,
    expires: claim.expires || null,
    reason: null
  };
}

/** What this copy may do. */
function features(key) {
  var seen = read(key);
  var set = seen.tier === 'pro' ? PRO : FREE;
  return Object.assign({}, set, { tier: seen.tier, name: seen.name,
                                  licensed: seen.ok, reason: seen.reason });
}

/**
 * Sign a licence. Only useful with the private key, which lives outside
 * this repository, so this is here for the issuing tool rather than for
 * the application.
 */
function sign(claim, privateKeyB64) {
  var payload = Buffer.from(JSON.stringify(claim), 'utf8');
  var pk = crypto.createPrivateKey({
    key: Buffer.from(privateKeyB64, 'base64'), format: 'der', type: 'pkcs8'
  });
  return bufToB64url(payload) + '.' + bufToB64url(crypto.sign(null, payload, pk));
}

module.exports = { read: read, features: features, sign: sign,
                   FREE: FREE, PRO: PRO, PUBLIC_KEY_B64: PUBLIC_KEY_B64 };
