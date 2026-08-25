/* ============================================================
   test-licence — a forged key must not open the paid half
   F-Keys | www.f-keys.com
   ============================================================ */
var fs = require('fs');
var crypto = require('crypto');
var lic = require('./licence');
var fail = [];
function ok(n, c) { if (!c) { fail.push(n); }
  console.log('  ' + (c ? 'ok  ' : 'FAIL') + '  ' + n); }

// The signing key lives outside this repository and is not on every
// machine. Without it these cases cannot run, and a test that cannot run
// must say so rather than fail as though the code were broken.
var KEY_PATH = process.env.REMAPWRAP_SIGNING_KEY ||
               'C:/Users/Admin/.remapwrap-signing/PRIVATE-KEY.txt';
if (!fs.existsSync(KEY_PATH)) {
  console.log('  skipped: no signing key at ' + KEY_PATH);
  console.log('  set REMAPWRAP_SIGNING_KEY to run these.');
  process.exit(0);
}

var privLines = fs.readFileSync(KEY_PATH, 'utf8')
                  .trim().split('\n');
var PRIV = privLines[privLines.length - 1].trim();

// ── a real key ──
var real = lic.sign({ name: 'A Buyer', tier: 'pro', issued: '2026-08-25' }, PRIV);
var f = lic.features(real);
ok('a signed pro key reads as pro', f.tier === 'pro' && f.licensed);
ok('pro unlocks auto switching', f.autoSwitch === true);
ok('pro unlocks meters', f.meters === true);
ok('pro is licensed for an organisation', f.commercial === true);
ok('the buyer name survives', f.name === 'A Buyer');

// ── no key at all ──
var none = lic.features(null);
ok('no key is the free tier', none.tier === 'free' && !none.licensed);
ok('free has unlimited keys', none.keys === Infinity);
ok('free has unlimited profiles', none.profiles === Infinity);
ok('free has unlimited pages', none.pages === Infinity);
ok('free has no device limit', none.devices === Infinity);

// The reason this product exists in the shape it does. Somebody who does
// not read needs the symbol; somebody who cannot speak needs the voice;
// somebody with one reliable movement needs scanning. None of the three
// may ever sit behind a payment, and a test is a stronger promise than a
// paragraph.
ok('free has symbols on keys', none.imageKeys === true);
ok('free has speech', none.speech === true);
ok('free has switch access', none.scanning === true);

ok('free does not auto switch', none.autoSwitch === false);
ok('free does not carry a commercial licence', none.commercial === false);

// Paying must never take something away.
ok('nothing free is missing from paid',
   Object.keys(lic.FREE).every(function (k) {
     return lic.FREE[k] === false || lic.PRO[k] === lic.FREE[k] ||
            lic.PRO[k] === true;
   }));

// ── forgery: same claim, no signature ──
function b64url(o) { return Buffer.from(JSON.stringify(o)).toString('base64')
  .replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''); }
var unsigned = b64url({ name: 'Thief', tier: 'pro' }) + '.' + b64url({});
ok('an unsigned claim is refused', lic.features(unsigned).tier === 'free');

// ── forgery: signed with a different key ──
var other = crypto.generateKeyPairSync('ed25519');
var otherPriv = other.privateKey.export({ type: 'pkcs8', format: 'der' }).toString('base64');
var wrongSigner = lic.sign({ name: 'Thief', tier: 'pro' }, otherPriv);
ok('a key from another signer is refused', lic.features(wrongSigner).tier === 'free');
ok('and it says why',
   /not issued by us/.test(lic.features(wrongSigner).reason || ''));

// ── tamper: flip the tier inside a genuine key ──
var freeKey = lic.sign({ name: 'A Buyer', tier: 'free', issued: '2026-08-25' }, PRIV);
var tampered = b64url({ name: 'A Buyer', tier: 'pro', issued: '2026-08-25' }) +
               '.' + freeKey.split('.')[1];
ok('upgrading a genuine key by editing it fails', lic.features(tampered).tier === 'free');

// ── expiry ──
var expired = lic.sign({ name: 'Lapsed', tier: 'pro', expires: '2020-01-01' }, PRIV);
ok('an expired key falls back to free', lic.features(expired).tier === 'free');
ok('an expired key says when', /ran out on 2020-01-01/.test(lic.features(expired).reason || ''));
var future = lic.sign({ name: 'Current', tier: 'pro', expires: '2099-01-01' }, PRIV);
ok('a key in date still works', lic.features(future).tier === 'pro');
var perpetual = lic.sign({ name: 'Owner', tier: 'pro' }, PRIV);
ok('a key with no expiry never expires', lic.features(perpetual).tier === 'pro');

// ── junk must never throw ──
var junk = ['', null, undefined, 'x', 'a.b', '....', '\u0000', 'a'.repeat(5000),
            b64url({ tier: 'pro' })];
var threw = false;
junk.forEach(function (j) { try { lic.features(j); } catch (e) { threw = true; } });
ok('no input crashes the check', !threw);

console.log('  ---');
console.log('  ' + (fail.length ? fail.length + ' FAILED' : 'all pass'));
process.exit(fail.length ? 1 : 0);
