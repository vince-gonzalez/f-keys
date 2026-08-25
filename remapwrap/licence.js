/* ============================================================
   licence — which half of the product this copy is
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   WHAT IS FREE

   Everything that makes RemapWrap a control surface. Unlimited
   keys, unlimited profiles, unlimited pages, free placement, any
   shape, every command, and two phones at once. The competitor
   people compare us to charges to go past six buttons and to
   arrange them freely; that is exactly what is given away here,
   and it stays given away.

   WHAT IS PAID

   Things that either cost money to run or only a working
   professional wants:

     autoSwitch    the surface follows the foreground window
     imageKeys     artwork on a key instead of a label
     meters        live audio levels rather than the setting
     manyDevices   more than two phones at once
     commercial    use inside a business or institution

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
  devices: 2,
  autoSwitch: false, imageKeys: false, meters: false, commercial: false
};

var PRO = {
  keys: Infinity, profiles: Infinity, pages: Infinity,
  devices: Infinity,
  autoSwitch: true, imageKeys: true, meters: true, commercial: true
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
