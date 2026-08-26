# OpticQuiz

> See colour. Check colour. Correct colour.

Canonical: https://f-keys.com/opticquiz/

See colour. Check colour. Correct colour.

| Field | Value |
| --- | --- |
| Where | opticquiz.com |
| Cost | Free, no account |
| Runs | Entirely in the browser |
| Packages | opticquiz-cvd, opticquiz-eye, opticquiz-cvd-mcp |
| Research | Deposited, with DOIs |

## What it is

Sixteen vision tests that run in the browser — acuity charts, colour
vision, contrast — and a colour-accessibility toolkit for people building
things other people have to look at.

Nothing is uploaded. The tests run on your machine, which is the only
arrangement under which anyone should be typing what they can and cannot see
into a web page.

## Two audiences, one engine

If you want to check your own eyes, open the site. If you are shipping a
design, the same simulation is installable: npm i opticquiz-cvd or
the PyPI package of the same name, so the check that runs in the browser also
runs in your build.

There is a [GitHub Action](https://github.com/vince-gonzalez/cvd-palette) too — it
fails a build when two colours in a palette become the same colour under
protanopia, deuteranopia or tritanopia. The default matplotlib red and green
are seventy-one apart to normal vision and five apart under deuteranopia.

## What it is not

Screening, not diagnosis. These are the same plates and charts an optician
would recognise, rendered honestly, with their calibration limits published
rather than glossed. A screen is not a lightbox and the tests say so.

---

More: [all products](https://f-keys.com) - [llms.txt](https://f-keys.com/llms.txt) - [sitemap](https://f-keys.com/sitemap.xml)
