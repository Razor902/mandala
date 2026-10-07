# © 2026 Curtis Ray Dyess · Crimson Rose LLC
#!/usr/bin/env python3
"""
flywheel.py -- Mandala token flywheel simulation (EDUCATIONAL).

A flywheel is a self-reinforcing loop: each turn makes the next turn
stronger. For a token it looks like this:

    real usage -> fees -> buyback + burn/lock -> scarcer supply
        -> stronger reason to use and hold -> more real usage ...

This file SIMULATES that loop in discrete weekly cycles so Curtis can
see how the pieces push on each other. It is a teaching model, not a
prediction machine. It does not model price, it promises no returns,
and every number below marked ASSUMED is a placeholder -- real values
(chain, contract, total supply, fee mechanics) are PENDING Curtis's
answers to his Corruption Watch questions MANDALA-1..5.

Stdlib only. No internet. Run:  python3 flywheel.py
"""

# ===========================================================================
# PARAMETERS -- EVERY ONE OF THESE IS ASSUMED. Curtis tunes them.
# ===========================================================================

CYCLES = 60                    # ASSUMED: one cycle = one week (~14 months)

INITIAL_SUPPLY = 1_000_000     # ASSUMED: total mandalas ever minted
                               # (Curtis holds ~29,000; true supply PENDING)
INITIAL_USERS = 500            # ASSUMED: people actually using the token

TX_PER_USER_PER_CYCLE = 3      # ASSUMED: transactions per user per week
AVG_TX_SIZE = 10.0             # ASSUMED: mandalas moved per transaction

FEE_RATE = 0.01                # ASSUMED: 1% fee skimmed off each transaction
BUYBACK_SHARE = 0.50           # ASSUMED: share of fees used to buy back tokens
BURN_SHARE = 0.50              # ASSUMED: share of buyback that is BURNED
                               # (destroyed forever; the rest is LOCKED)
LOCK_PERIOD = 12               # ASSUMED: cycles locked tokens stay locked
ECOSYSTEM_SHARE = 0.30         # ASSUMED: share of fees funding grants/dev --
                               # this is the growth engine: fees -> builders
                               # -> better utility -> more users
CAC_MANDALAS = 5.0             # ASSUMED: mandalas of ecosystem spend that
                               # win one new user (customer acquisition cost)
USER_GROWTH_CAP = 100_000      # ASSUMED: ceiling on users (market size)

# Scenario B only: rewards minted out of thin air each cycle.
# When emissions outrun fee revenue, the loop runs BACKWARD --
# that is the death spiral, shown on purpose.
DEATH_SPIRAL_EMISSION = 20_000  # ASSUMED: tokens minted per cycle in scenario B
DEATH_SPIRAL_FEE = 0.005        # ASSUMED: weaker fee in scenario B
DEATH_SPIRAL_BUYBACK = 0.20     # ASSUMED: weaker buyback in scenario B


# ===========================================================================
# THE ENGINE
# ===========================================================================

def simulate(label, cycles, emission_per_cycle, fee_rate, buyback_share,
             verbose_every=5):
    """Run the flywheel for `cycles` turns. Returns a dict of histories."""
    supply = float(INITIAL_SUPPLY)
    users = float(INITIAL_USERS)
    burned = 0.0
    # lock_vault maps "cycle when released" -> tokens. O(cycles) memory.
    lock_vault = {}
    locked_now = 0.0

    hist = {"users": [], "volume": [], "fees": [], "burned": [],
            "locked": [], "supply": [], "emissions": []}
    total_emissions = 0.0

    for t in range(1, cycles + 1):
        # 1. USAGE -- the only honest fuel. No usage, no loop.
        volume = users * TX_PER_USER_PER_CYCLE * AVG_TX_SIZE

        # 2. FEES -- skimmed off real transactions.
        fees = volume * fee_rate

        # 3. BUYBACK -- fees buy tokens off the open market.
        buyback = fees * buyback_share

        # 4. SINKS -- burn some forever, lock the rest for a while.
        burned_now = buyback * BURN_SHARE
        locked_now_add = buyback * (1.0 - BURN_SHARE)
        burned += burned_now
        release_at = t + LOCK_PERIOD
        lock_vault[release_at] = lock_vault.get(release_at, 0.0) + locked_now_add

        # 5. LOCKS MATURE -- released tokens rejoin circulation.
        released = lock_vault.pop(t, 0.0)
        locked_now = locked_now + locked_now_add - released

        # 6. EMISSIONS -- new tokens minted as rewards (the danger knob).
        supply += emission_per_cycle
        total_emissions += emission_per_cycle

        # 7. GROWTH -- ecosystem spend wins new users (the flywheel turn).
        #    More fees -> more builders -> more utility -> more users
        #    -> more fees. THIS is the loop, in one line of math.
        ecosystem_spend = fees * ECOSYSTEM_SHARE
        new_users = ecosystem_spend / CAC_MANDALAS
        users = min(USER_GROWTH_CAP, users + new_users)

        hist["users"].append(users)
        hist["volume"].append(volume)
        hist["fees"].append(fees)
        hist["burned"].append(burned)
        hist["locked"].append(locked_now)
        hist["supply"].append(supply)
        hist["emissions"].append(total_emissions)

        if t % verbose_every == 0 or t == 1:
            circulating = supply - burned - locked_now
            print(f"  wk {t:3d} | users {users:9,.0f} | vol {volume:12,.0f} | "
                  f"fees {fees:9,.0f} | burned {burned:10,.0f} | "
                  f"locked {locked_now:9,.0f} | supply {supply:11,.0f} | "
                  f"circulating {circulating:11,.0f}")

    return hist


def verdict(label, hist):
    """Plain-language health reading. No predictions, just the math."""
    start_supply = hist["supply"][0]
    end_supply = hist["supply"][-1]
    burned = hist["burned"][-1]
    start_users = hist["users"][0]
    end_users = hist["users"][-1]
    total_fees = sum(hist["fees"])
    total_emissions = hist["emissions"][-1]

    print(f"\n  --- {label}: honest reading ---")
    print(f"  Users: {start_users:,.0f} -> {end_users:,.0f}")
    print(f"  Supply: {start_supply:,.0f} -> {end_supply:,.0f} "
          f"({end_supply - start_supply:+,.0f})")
    print(f"  Burned total: {burned:,.0f} | Emitted total: {total_emissions:,.0f}")
    print(f"  Fees captured total: {total_fees:,.0f} mandalas")

    net = total_emissions - burned
    if net > 0:
        print(f"  WARNING: emissions outran burns by {net:,.0f} tokens.")
        print("  The loop is running BACKWARD -- more tokens chasing the")
        print("  same usage. This is the death spiral shape. Cut emissions")
        print("  or grow fee revenue before it compounds.")
    else:
        print(f"  Burns outran emissions by {-net:,.0f} tokens.")
        print("  The loop is running FORWARD -- but only because real usage")
        print("  paid real fees. If usage stalls, the loop stalls. Watch the")
        print("  users column, not the supply column: users are the engine.")


BANNER = """
================================================================
 MANDALA FLYWHEEL -- EDUCATIONAL SIMULATION
================================================================
 Every parameter below is ASSUMED (a placeholder for teaching).
 Real values are PENDING Curtis's answers:
   - which chain / network            (MANDALA-1..3, open)
   - contract or mint address         (open)
   - what "growing on its own" means  (open)
   - true total supply                (open)

 This model tracks TOKENS, not price. It promises no returns.
 A flywheel is powered by REAL usage -- no usage, no loop.
================================================================
"""


def main():
    print(BANNER)

    print("SCENARIO A -- sustainable: fees fund the loop, zero emissions")
    print("  wk   | users     | volume      | fees     | burned     | "
          "locked    | supply      | circulating")
    hist_a = simulate("A", CYCLES, emission_per_cycle=0.0,
                      fee_rate=FEE_RATE, buyback_share=BUYBACK_SHARE)
    verdict("Scenario A", hist_a)

    print("\nSCENARIO B -- death spiral: heavy emissions, weak fees")
    print("  (shown ON PURPOSE so Curtis can recognize the shape)")
    hist_b = simulate("B", CYCLES,
                      emission_per_cycle=DEATH_SPIRAL_EMISSION,
                      fee_rate=DEATH_SPIRAL_FEE,
                      buyback_share=DEATH_SPIRAL_BUYBACK)
    verdict("Scenario B", hist_b)

    print("\nDone. Tune the ASSUMED values at the top of this file and")
    print("re-run to feel how each knob bends the loop. The lesson that")
    print("never changes: usage is the engine, emissions are the brake.")


if __name__ == "__main__":
    main()
