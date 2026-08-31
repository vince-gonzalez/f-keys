# openapi-drift

> Does the service still do what the spec says?

Canonical: https://f-keys.com/openapi-drift/

An OpenAPI document is a promise about a service, and nothing keeps the two together. This checks whether the service still does what the document says &mdash; and whether a machine can still read the document at all.

pip install openapi-drift · MIT · safe calls only, never writes

## What it does

An OpenAPI document is a promise about a service, and nothing keeps the two
together. It quietly becomes a description of what the service used to do, and
every consumer finds out one failed call at a time.

**pip install openapi-drift**
openapi-drift openapi.json
openapi-drift https://example.com/openapi.json --live
The check that is easy to skip
A response schema behind a $ref is correct, valid, and useless
to the tools that turn an operation into a function signature, because they do
not dereference. A validator sees a schema; a converter sees an argument with
no type. The document passes everything and cannot be used.

That is not hypothetical. It cost a week on a specification that passed
every other check.

## What it is not

Not a fuzzer — it calls what you documented rather than generating
traffic hunting for crashes. Not a syntax validator — a perfectly
well-formed document can be unreadable by a machine.

## Only safe calls

--live calls parameterless GETs only. A path with a placeholder
or a required parameter is skipped rather than guessed at, because a guessed
value reports drift that is the checker's fault. Nothing is ever written.

## How it works

## What it checks

## Specifications

| Field | Value |
| --- | --- |
| Install | pip install openapi-drift |
| Licence | MIT |
| Action | vince-gonzalez/openapi-drift |
| Source | vince-gonzalez/openapi-drift |

## Questions

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
