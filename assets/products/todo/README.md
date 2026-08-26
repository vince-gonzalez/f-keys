# Marks that are not marks yet

Each file here is a real image for a real product that `productart.py`
cannot use, with the reason. They are parked rather than deleted, and
parked HERE rather than left one directory up, because a source sitting
next to the valid ones fails the build for everybody until it is fixed
— and a gate that blocks unrelated work is a gate somebody switches off.

A mark has to be **square** and **at least 256px**. Not because the tool
is fussy: the smallest derivative is a 32px favicon, and a 1900x828
banner squeezed into 32x32 is a smear. These are banner and screenshot
crops, which is a different picture with a different job.

| file | is | needs |
|---|---|---|
| `pixelstaff.png` | 1408x768 | a square crop |
| `prompt.png` | 1024x1536 | a square crop |
| `micdrop.png` | 1254x705 | a square crop |
| `wikipolish.png` | 1408x768 | a square crop |
| `modulign.png` | 468x410 | a square crop |
| `poticas.png` | 1900x828 | a square crop |
| `tipstreams.png` | 864x1229 | a square crop |
| `5best2buy.png` | 220x229 | square, and bigger — it is under the 256px floor |

Fix one and move it up to `assets/products/`, then run:

    python tools/productart.py
