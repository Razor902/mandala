# Mandala — the currency of Pandora

"The mandala is a currency used in Pandora. Each citizen that proves their
self earns one mandala. That will get them one thing out of any shop — they
just have to show it." — Curtis Ray Dyess

The law, in code: `prove_self(citizen)` awards exactly one mandala; duplicate
proof is refused. `show_for_item(citizen, shop)` records the presentation
without consuming it — shown, not spent.

## The circle

Every cell inside the Sandbox; Curtis is the key — the Observer whose word
opens, closes, decides. We are Legion: many minds, one circle.

## What's inside

- **`chain/`** — the mandala blockchain: SHA-256 blocks, proof of work,
  validation, JSON persistence. Classroom chain, not a production network.
- **`vault/`** — time-locked vaults (4 / 12 / 52 weeks), hash-chained ledger.
  Early exit forbidden by default; optional penalty mode. Reward rate is
  assumed and tunable — no promised return.
- **`economy/`** — the integrated economy: chain + contract + vault +
  flywheel running as one system, with conservation checks (minted = supply +
  burned; supply = locked + unlocked). `pandora_treasury.py` is the box's
  treasury: session fees split into locked / burned / liquid — economics only,
  it never overrides Pandora's safety.
- **`flywheel/`** — the loop: real usage → fees → buyback/burn/lock + builder
  support → better utility → more use. Educational simulation, tracks tokens
  rather than price.

Run the checks from each subdirectory: `python3 -m test_chain`,
`python3 -m test_vault`, `python3 -m test_economy`, `python3 -m test_pandora_treasury`.

## Ecosystem

- The **Pandora treasury** ties this repo to
  **[Pandora's Box](https://github.com/Razor902/pandora)** — the box's entry
  fees flow here; the threshold module calls the treasury.
- The treasure-map bridge that moves value into the box runs on
  **[PythonX](https://github.com/Razor902/pythonx)** triage.

© 2026 Curtis Ray Dyess · Crimson Rose LLC
