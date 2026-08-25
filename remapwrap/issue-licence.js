#!/usr/bin/env node
/* ============================================================
   issue-licence — write a key for somebody who paid
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   Needs the private signing key, which is not in this repository.

     node issue-licence.js --name "Jane Doe" --key PRIVATE-KEY.txt
     node issue-licence.js --name "Acme Ltd" --expires 2027-08-25 \
                           --key PRIVATE-KEY.txt

   No expiry means the key never expires, which is what somebody
   who bought a version rather than a subscription is owed.
   ============================================================ */
var fs = require('fs');
var lic = require('./licence');

var args = {};
for (var i = 2; i < process.argv.length; i += 2) {
  args[String(process.argv[i]).replace(/^--/, '')] = process.argv[i + 1];
}

if (!args.name || !args.key) {
  console.log('  usage: node issue-licence.js --name "Buyer" --key PRIVATE-KEY.txt');
  console.log('         [--expires YYYY-MM-DD] [--tier pro|free]');
  process.exit(2);
}

var text = fs.readFileSync(args.key, 'utf8').trim().split('\n');
var priv = text[text.length - 1].trim();

var claim = { name: args.name, tier: args.tier || 'pro',
              issued: (args.issued || new Date().toISOString().slice(0, 10)) };
if (args.expires) { claim.expires = args.expires; }

var key = lic.sign(claim, priv);

// Never hand over a key without checking it opens the door it promises.
var back = lic.features(key);
if (back.tier !== claim.tier) {
  console.log('  REFUSED: the key just signed does not read back as ' +
              claim.tier + ' (' + (back.reason || 'unknown') + ')');
  process.exit(1);
}

console.log('  ' + claim.name + '  ·  ' + claim.tier +
            (claim.expires ? '  ·  until ' + claim.expires : '  ·  no expiry'));
console.log('');
console.log(key);
