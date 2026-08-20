"""
============================================================
keyj.render — a sequence, as a WAV file
F-Keys | www.f-keys.com
------------------------------------------------------------
WHY THIS EXISTS
The browser app's first export recorded your typing: every note
you had played since the page loaded, at the moment you played
it. Notes struck before you pressed Record all landed at time
zero, stacked into one instant that peaked sixty times louder
than a single note, and normalising that scaled the rest of the
file into silence. One audible second out of thirty-five.

What people actually want is the sequence: the notes they built
from a tab, evenly at a tempo. That is what this writes.

No dependencies. The standard library has a WAV writer, and
everything above it is arithmetic.
============================================================
"""

import array
import math
import wave

SAMPLE_RATE = 44100

WAVEFORMS = ("sine", "saw", "square", "triangle")

#: The browser app's tone presets, so `--tone shred` means the same thing
#: in both places. Release is in seconds here; the browser stores it in
#: milliseconds because its slider does.
TONES = {
    "clean":     dict(wave="triangle", attack=0.006, release=0.60, drive=0.15, reverb=0.18),
    "overdrive": dict(wave="saw",      attack=0.004, release=0.75, drive=0.55, reverb=0.22),
    "shred":     dict(wave="saw",      attack=0.002, release=0.45, drive=0.80, reverb=0.15),
    "bell":      dict(wave="sine",     attack=0.002, release=1.60, drive=0.00, reverb=0.45),
    "chip":      dict(wave="square",   attack=0.001, release=0.18, drive=0.00, reverb=0.05),
    "pluck":     dict(wave="triangle", attack=0.001, release=0.30, drive=0.10, reverb=0.12),
    "pad":       dict(wave="sine",     attack=0.220, release=1.80, drive=0.00, reverb=0.55),
}


def _sample(shape, phase):
    """One cycle of `shape` at `phase` in [0, 1)."""
    if shape == "sine":
        return math.sin(2.0 * math.pi * phase)
    if shape == "saw":
        return 2.0 * phase - 1.0
    if shape == "square":
        return 1.0 if phase < 0.5 else -1.0
    # triangle
    return 4.0 * abs(phase - 0.5) - 1.0


def _drive_curve(amount):
    """The same soft clipper the browser uses, as a function rather than a table."""
    k = amount * 100.0

    def shape(x):
        return ((1.0 + k) * x) / (1.0 + k * abs(x))
    return shape


def _reverb(buf, amount, rate):
    """
    Three feedback combs and one allpass. Not a convolution - a convolution
    at this length in pure Python would take longer than the song.
    """
    if amount <= 0.01:
        return buf
    out = array.array("d", buf)
    for delay_ms, feedback in ((29.7, 0.78), (37.1, 0.74), (41.1, 0.70)):
        d = int(rate * delay_ms / 1000.0)
        if d < 1 or d >= len(out):
            continue
        for i in range(d, len(out)):
            out[i] += out[i - d] * feedback * amount
    d = int(rate * 5.0 / 1000.0)
    if 1 <= d < len(out):
        for i in range(d, len(out)):
            out[i] += -0.7 * out[i - d]
    return out


def render(notes, bpm=140, tone="clean", volume=0.75, gap=0.9,
           rate=SAMPLE_RATE, reverb=None):
    """
    One note per beat, in order, through the chosen tone.

    Returns a mono array of floats, unnormalised. The caller decides what
    to do with the peak, because that decision is what broke the old export.
    """
    if not notes:
        raise ValueError("nothing to render")
    if tone not in TONES:
        raise ValueError("unknown tone {!r}; known: {}".format(
            tone, ", ".join(sorted(TONES))))

    t = dict(TONES[tone])
    if reverb is not None:
        t["reverb"] = reverb

    bpm = max(30, min(300, int(bpm)))
    step = 60.0 / bpm
    hold = step * gap
    tail = t["release"] + 0.5
    total = int((len(notes) * step + tail) * rate) + 1
    buf = array.array("d", [0.0]) * total

    attack = max(1, int(min(t["attack"], hold * 0.5) * rate))
    release = max(1, int(t["release"] * rate))
    body = max(1, int(hold * rate))
    span = body + release
    shape = t["wave"]

    for index, note in enumerate(notes):
        start = int(index * step * rate)
        inc = note.freq / rate
        phase = 0.0
        for n in range(span):
            pos = start + n
            if pos >= total:
                break
            if n < attack:
                env = n / float(attack)
            elif n < body:
                env = 1.0
            else:
                # exponential decay to silence, the shape a string has
                env = math.exp(-5.0 * (n - body) / float(release))
            buf[pos] += _sample(shape, phase) * env * 0.8
            phase += inc
            if phase >= 1.0:
                phase -= 1.0

    if t["drive"] > 0.01:
        curve = _drive_curve(t["drive"])
        for i in range(total):
            buf[i] = curve(buf[i])

    buf = _reverb(buf, t["reverb"], rate)

    vol = max(0.0, min(1.0, volume))
    for i in range(total):
        buf[i] *= vol
    return buf


def normalise(buf, ceiling=0.98):
    """Scale so the loudest sample sits at `ceiling`. Lossless, and reversible."""
    peak = 0.0
    for v in buf:
        a = abs(v)
        if a > peak:
            peak = a
    if peak <= 0.0:
        return buf, 0.0
    scale = ceiling / peak
    for i in range(len(buf)):
        buf[i] *= scale
    return buf, peak


def write_wav(path, buf, rate=SAMPLE_RATE, stereo=True):
    """16-bit PCM. Samples outside [-1, 1] are clamped, not wrapped."""
    frames = array.array("h")
    limit = 32767
    if stereo:
        for v in buf:
            s = int(max(-1.0, min(1.0, v)) * limit)
            frames.append(s)
            frames.append(s)
    else:
        for v in buf:
            frames.append(int(max(-1.0, min(1.0, v)) * limit))

    with wave.open(path, "wb") as fh:
        fh.setnchannels(2 if stereo else 1)
        fh.setsampwidth(2)
        fh.setframerate(rate)
        fh.writeframes(frames.tobytes())
    return len(buf) / float(rate)
