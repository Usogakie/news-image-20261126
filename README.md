# The World Today — 26 November 2026

A one-image newspaper front page summing up Thursday 26 November 2026's
world news, generated entirely by code.

## What the image shows

A 1024×1024 front page, **"THE WORLD TODAY"**, dated Thursday 26 November
2026, with:

- **Lead story — Trade:** the US unveils new tariffs on China, Japan, the
  EU and others, rattling global markets on Thanksgiving Day — beside a
  hand-drawn chart of Brent crude climbing to $94 a barrel.
- **Houthis claim strike on Saudi refinery** as Brent tops $94 (Middle East).
- **Israel strikes in Gaza; ceasefire under strain** — Hamas security chief
  Mohammad Abuelouf killed with his wife and two children.
- **Pakistan's first astronaut heads for Tiangong** aboard China's
  Shenzhou-24, the first foreign astronaut on the station.
- **Russia's own figures: nearly 500,000 lost in the Ukraine war.**
- **In brief:** BepiColombo reaches Mercury orbit; a fuel-tanker fire on a
  Cairo highway kills at least 30; Duran Duran guitarist Andy Taylor dies
  aged 65; Bangladesh raises garment workers' minimum wage 36%; India marks
  18 years since the 26/11 Mumbai attacks.

Sources: BBC, Reuters, AP — all stories reported 26 November 2026.

## How to run

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024×1024). Python 3 standard library
only — no network, no downloads, no external fonts or images. The program
draws everything itself: a hand-made 5×7 pixel font, a framebuffer, rules,
boxes, a line chart, and a hand-rolled PNG encoder (zlib + struct).
Output is deterministic: running it twice produces identical bytes.
