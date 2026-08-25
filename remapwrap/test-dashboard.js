/* ============================================================
   test-dashboard — no button may point at nothing
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   Three separate times today a function was defined and never
   called, or called and never defined, and nothing said so
   until something quietly did not work. A button whose handler
   does not exist is the same defect wearing a different hat.

   Run:  node test-dashboard.js
   ============================================================ */
var fs = require('fs');
var path = require('path');

var fail = [];
function ok(name, cond, detail) {
  if (!cond) { fail.push(name); }
  console.log('  ' + (cond ? 'ok  ' : 'FAIL') + '  ' + name +
              (detail ? '  ' + detail : ''));
}

['dashboard.html', 'controller.html'].forEach(function (file) {
  var html = fs.readFileSync(path.join(__dirname, file), 'utf8');

  // Every inline handler names a function. It must exist.
  var called = [];
  var re = /on(?:click|change|input|submit)="([A-Za-z_$][\w$]*)\s*\(/g;
  var m;
  while ((m = re.exec(html)) !== null) {
    if (called.indexOf(m[1]) === -1) { called.push(m[1]); }
  }
  var undefinedHandlers = called.filter(function (n) {
    return html.indexOf('function ' + n + '(') === -1 &&
           html.indexOf(n + ' = function') === -1;
  });
  ok(file + ': every inline handler is defined',
     undefinedHandlers.length === 0,
     undefinedHandlers.length ? '-> ' + undefinedHandlers.join(', ')
                              : '(' + called.length + ' checked)');

  // Every element id the script reaches for must be in the markup.
  var wanted = [];
  var idRe = /getElementById\('([^']+)'\)/g;
  while ((m = idRe.exec(html)) !== null) {
    if (wanted.indexOf(m[1]) === -1) { wanted.push(m[1]); }
  }
  // An element can be in the markup or be built at runtime. The drag ghost
  // is made in code and given its id there, which is not a missing element
  // and must not be reported as one.
  var absent = wanted.filter(function (id) {
    return html.indexOf('id="' + id + '"') === -1 &&
           html.indexOf(".id = '" + id + "'") === -1;
  });
  ok(file + ': every id it reads for exists',
     absent.length === 0,
     absent.length ? '-> ' + absent.join(', ') : '(' + wanted.length + ' checked)');

  // Nothing below the floor he has asked for more than once.
  var sizes = (html.match(/font-size:\s*([0-9.]+)px/g) || []);
  var small = sizes.filter(function (x) {
    return parseFloat(x.match(/[0-9.]+/)[0]) < 13;
  });
  ok(file + ': no type under 13px', small.length === 0,
     small.length ? '-> ' + small.join(', ') : '(' + sizes.length + ' declared)');
});

console.log('  ---');
console.log('  ' + (fail.length ? fail.length + ' FAILED' : 'all pass'));
process.exit(fail.length ? 1 : 0);
