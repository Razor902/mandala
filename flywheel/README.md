# The Mandala Flywheel — Design & Simulation

**For Curtis · October 7, 2026 · Status: GATHERED (design, not deployed)**
**Rule: nothing here is financial advice. No returns are promised. The sim tracks tokens, never price.**

---

## 1. What a flywheel is (plain words)

A flywheel is a loop where each turn makes the next turn stronger. Push once,
and the wheel keeps some of your push; push again, and it spins a little
faster on its own. For Curtis's mandala economy, the loop is:

1. **People USE mandalas for something real** — paying for content, tipping
   creators, unlocking features. This is the only honest fuel. No usage, no loop.
2. **Every use pays a small fee** into the vault.
3. **The vault buys back mandalas** off the open market with those fees.
4. **Bought-back tokens are burned (destroyed) or locked** away for a while.
   Supply shrinks; circulating tokens get scarcer.
5. **Some fees fund builders** — grants, better tools, better content.
   Better utility wins more users.
6. **More users → more usage → more fees → back to step 1**, a little faster.

One line: **real usage pays fees, fees shrink supply and fund growth, growth
brings usage.** The wheel turns on work, not wishes.

---

## 2. The honest rules

- **Utility first.** The token must DO something people want. A flywheel with
  no utility is a hamster wheel — lots of spinning, going nowhere.
- **No promised returns.** The design never guarantees price, yield, or profit.
  Anyone promising those is selling, not building.
- **Sinks AND sources.** Tokens must have ways to get used up or locked away
  (fees, burns, locks), not just ways to be handed out (rewards, emissions).
  A bathtub with the tap running and no drain overflows.
- **Revenue before rewards.** Rewards paid from real fee revenue are sharing;
  rewards minted from nothing are dilution. The sim's Scenario B shows what
  dilution looks like — read it before touching emissions.
- **Transparent knobs.** Every parameter is written down, labeled, and tunable.
  No hidden levers.

---

## 3. Failure modes — how flywheels break (read this twice)

- **The death spiral.** Rewards are minted faster than fees come in. Each new
  token dilutes the last, usage can't keep up, and the loop runs backward.
  Scenario B in the sim IS this shape, on purpose — learn to recognize it.
- **Mercenary capital.** People show up for rewards, not utility, and leave the
  day rewards shrink. Defense: reward *usage*, not *holding*; make the utility
  itself the reason to stay.
- **The ponzi shape.** Early participants are paid from later participants'
  money, with no real revenue underneath. The test is simple: remove all new
  buyers — does anything still pay anyone? If no, it's not a flywheel.
- **Fee starvation.** Fees set so low (or dodged so easily) that the vault
  never fills. The buyback/burn engine sputters and the loop coasts to a stop.
- **Lock cliffs.** Too many locked tokens releasing on the same day floods
  supply at once. Defense: stagger lock periods so releases trickle, never wave.

---

## 4. Parameters — every value ASSUMED until Curtis tunes it

| Parameter | Assumed value | What it means |
|---|---|---|
| Total supply | 1,000,000 | All mandalas that exist (Curtis holds ~29,000) |
| Starting users | 500 | People actually using the token |
| Tx per user / week | 3 | How often each user transacts |
| Avg tx size | 10 mandalas | Typical transaction size |
| Fee rate | 1% | Skimmed off each transaction into the vault |
| Buyback share | 50% of fees | Used to buy tokens off the market |
| Burn share | 50% of buyback | Destroyed forever (rest is locked) |
| Lock period | 12 weeks | How long locked tokens sit out |
| Ecosystem share | 30% of fees | Funds builders/grants — the growth engine |
| User acq. cost | 5 mandalas | Ecosystem spend that wins one new user |
| User cap | 100,000 | Ceiling on adoption |
| Emission (Scenario B) | 20,000 / week | Rewards minted from nothing — the danger knob |

**PENDING from Curtis** (Corruption Watch MANDALA-1..5, still open):
chain/network, contract or mint address, what "growing on its own" means,
true total supply, and how fees/rewards actually work on his chain.

---

## 5. How to run the simulation

```
cd ~/workspace/flywheel
python3 flywheel.py
```

Stdlib only — no installs, no internet. Every run prints the assumptions
banner first, then two scenarios:

- **Scenario A — sustainable:** zero emissions. Watch users climb, supply hold,
  burns accumulate. The loop runs forward on real fees.
- **Scenario B — death spiral:** heavy emissions, weak fees. Watch supply
  inflate while the warning fires. Shown on purpose — this is the shape to
  never build.

**Tuning:** change the ASSUMED values at the top of `flywheel.py` and re-run.
Try: raising the fee rate (does volume survive?), cutting the burn share
(does locking alone hold the loop?), adding small emissions to Scenario A
(how much can the loop absorb before it tips backward?).

**Reading the output:** watch the *users* column — users are the engine. If
users stall, the loop stalls no matter what the supply column says. The
"honest reading" at the end of each scenario says in plain words which way
the loop ran and why.

---

## 6. What's still needed from Curtis

1. The chain and contract — so the design can meet reality.
2. What "growing on its own" means — staking? reflections? something else?
3. What the mandala is FOR — the utility the whole loop hangs on.
4. His tuned parameters — every ASSUMED value above is his to change.

Until then, this is a teaching model of a sound loop — not a launch plan.

---
© 2026 Curtis Ray Dyess · Crimson Rose LLC
