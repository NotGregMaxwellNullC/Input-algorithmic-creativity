# How Basketball-GM Actually Works: A Code Deep-Dive for Non-Coders

> **What this is:** A guided tour through the actual source code of Basketball-GM (open source at github.com/zengm-games/zengm). We're going to read real code together and I'll explain what each piece does in plain English. No coding background required — just curiosity.

---

## Part 1: The Big Picture

Basketball-GM is built in **TypeScript** (a version of JavaScript). Every time you simulate a game, the computer runs through thousands of tiny decisions — who shoots, does it go in, who rebounds — all driven by player ratings and random numbers.

The key insight: **the game doesn't simulate basketball with physics.** It simulates basketball with *probability*. Every event has a calculated chance of happening, rolled like a dice.

The main files we'll explore:

| File | What it does |
|------|-------------|
| `src/common/constants.basketball.ts` | Defines all player ratings and how they combine |
| `src/worker/core/GameSim.basketball/index.ts` | The 2,890-line engine that simulates every possession |
| `src/worker/core/player/compositeRating.ts` | How raw ratings become game-action probabilities |

---

## Part 2: Player Ratings — The 15 Stats Under the Hood

Every player has **15 raw ratings**, each scored 0–100:

```
hgt   = Height
stre  = Strength
spd   = Speed
jmp   = Jumping
endu  = Endurance
ins   = Inside scoring
dnk   = Dunking
ft    = Free throw shooting
fg    = Mid-range shooting
tp    = Three-point shooting
oiq   = Offensive IQ
diq   = Defensive IQ
drb   = Dribbling
pss   = Passing
reb   = Rebounding
```

You never directly see most of these in the game — what you *do* see are the **composite ratings**, which are combinations of the raw ones.

---

## Part 3: Composite Ratings — Where It Gets Interesting

This is from `src/common/constants.basketball.ts`. This file is the *recipe book* for the game.

### Example: Blocking

```typescript
blocking: {
    ratings: ["hgt", "jmp", "diq"],
    weights: [2.5, 1.5, 0.5],
},
```

**Plain English:** A player's blocking ability = mostly height (2.5x), a lot of jumping (1.5x), and a little defensive IQ (0.5x). A short player with amazing hops can still block shots — just not as often as a tall one.

### Example: Three-Point Shooting

```typescript
shootingThreePointer: {
    ratings: ["oiq", "tp"],
    weights: [0.1, 1],
},
```

**Plain English:** Three-point shooting is almost entirely the `tp` rating, with just a tiny bit of Offensive IQ. Makes sense — a pure shooter.

### Example: Turnovers (note the negative weight!)

```typescript
turnovers: {
    ratings: [50, "ins", "pss", "oiq"],
    weights: [0.5, 1, 1, -1],
},
```

**Plain English:** Higher inside scoring + passing = *more* turnovers (because you're handling the ball more). But higher Offensive IQ *reduces* turnovers (that `-1` weight flips it). The `50` is a baseline constant — everyone starts with some turnover chance.

### The Full Recipe Book

| Composite Rating | Raw Ratings Used | What It Means |
|-----------------|-----------------|---------------|
| `shootingAtRim` | hgt, stre, dnk, oiq | Dunks & layups |
| `shootingLowPost` | hgt, stre, spd, ins, oiq | Post game |
| `shootingMidRange` | oiq, fg, stre | Jumpers |
| `shootingThreePointer` | oiq, tp | 3-pointers |
| `shootingFT` | ft | Free throws |
| `rebounding` | hgt, stre, jmp, reb, oiq, diq | Boards |
| `stealing` | 50, spd, diq | Steals |
| `blocking` | hgt, jmp, diq | Blocks |
| `fouling` | 50, hgt, diq, spd | Foul tendency |
| `passing` | drb, pss, oiq | Assists |
| `dribbling` | drb, spd | Ball handling |
| `defense` | hgt, stre, spd, jmp, diq | General D |
| `defenseInterior` | hgt, stre, spd, jmp, diq | Paint defense |
| `defensePerimeter` | hgt, stre, spd, jmp, diq | Perimeter D |
| `endurance` | 50, endu | Fatigue resistance |
| `athleticism` | stre, spd, jmp, hgt | Overall athleticism |
| `jumpBall` | hgt, jmp | Tip-off |

---

## Part 4: How the Math Works (It's Simpler Than It Looks)

From `src/worker/core/player/compositeRating.ts`:

```typescript
for (const [i, component] of components.entries()) {
    numerator += factor * weights[i];
    denominator += 100 * weights[i];
}
return helpers.bound(numerator / denominator, 0, 1);
```

**Plain English:** Take each raw rating, multiply by its weight, add them up, then divide by the *maximum possible* sum. The result is always between 0 and 1.

**Example — Blocking for a 7-foot shot-blocker:**
- `hgt` = 90 → 90 × 2.5 = 225
- `jmp` = 60 → 60 × 1.5 = 90
- `diq` = 40 → 40 × 0.5 = 20
- Numerator = 335
- Denominator = 100×2.5 + 100×1.5 + 100×0.5 = 450
- Blocking composite = 335/450 = **0.74** (solid shot blocker)

---

## Part 5: The Game Clock — How a Possession Actually Works

From `src/worker/core/GameSim.basketball/index.ts`, the `run()` function:

```typescript
run() {
    this.simRegulation();  // Simulate all 4 quarters

    while (this.team[0].stat.pts === this.team[1].stat.pts) {
        this.simOvertime();  // Keep playing OT until someone wins
    }
}
```

Inside `simRegulation()`:

```typescript
while (this.t > 0) {
    this.simPossession();  // One possession at a time
}
```

**The game clock `this.t` is in seconds.** Each quarter starts at `quarterLength * 60` seconds (default: 12 minutes = 720 seconds).

### One Possession, Step by Step

The `simPossession()` function:

1. **Switch who has the ball** — offense (`this.o`) and defense (`this.d`) flip
2. **Figure out game situation** — is the team up? Down? Should they rush? Hold for one shot?
3. **Run `getPossessionOutcome()`** — the main decision tree

---

## Part 6: The Decision Tree — What Happens Each Possession

This is the heart of the simulation. `getPossessionOutcome()` works through these checks in order:

### Step 1: Is time running out?
```typescript
if (clockFactor === "runOutClock") {
    // Winning team just dribbles — game over
    return "endOfPeriod";
}
```

### Step 2: Turnover in backcourt?
```typescript
if (Math.random() < this.probTov()) {
    return this.doTov();
}
```

`probTov()` formula:
```
turnover chance = (0.14 × defense_rating) / (0.5 × (dribbling + passing))
```
**Plain English:** Better defense = more turnovers forced. Better ball-handling = fewer turnovers.

### Step 3: Non-shooting foul?
```typescript
if (Math.random() < 0.08 * g.get("foulRateFactor")) {
    // Send to free throws or give the ball back
}
```

Base rate: **8% chance** per possession of a non-shooting foul (adjustable by league settings).

### Step 4: Pick the shooter!
```typescript
const shooter = this.pickPlayer("usage", this.o, 1.25);
```

Players with higher `usage` composite ratings get the ball more often. Stars take more shots.

### Step 5: The shot

---

## Part 7: The Shot — Where Points Come From

This is `doShot()` and `getShotInfo()`. Every shot goes through this:

### Picking the shot type

The game calculates three random numbers:
```typescript
const r1 = 0.8 * Math.random() * p.compositeRating.shootingMidRange;
const r2 = Math.random() * p.compositeRating.shootingAtRim;
const r3 = Math.random() * p.compositeRating.shootingLowPost;
```

Whichever is highest determines the shot type (or three-pointer, which has its own check first). This means a player's strengths make those shots *more likely to be chosen*.

### Shot probability formulas

| Shot Type | Base Make % Formula | Range |
|-----------|-------------------|-------|
| Three-pointer | `tp_rating × 0.3 + 0.36` | 36%–45% |
| At rim (dunk/layup) | `atRim_rating × 0.41 + 0.54` | 54%–95% |
| Mid-range | `midRange_rating × 0.32 + 0.42` | 42%–74% |
| Low post | `lowPost_rating × 0.32 + 0.34` | 34%–66% |

Then **defense reduces it:**
```typescript
probMake = probMake - 0.25 × defense_rating
```

And **fatigue reduces it:**
```typescript
probMake = probMake * currentFatigue
```

And **assisted shots are easier:**
```typescript
if (passer !== undefined) probMake += 0.025;
```

### Block check
```typescript
if (this.probBlk() > Math.random()) {
    blocked = true;
}
```
Block formula: `(hgt × 2.5 + jmp × 1.5 + diq × 0.5)` — the blocker's rating vs. the shooter's.

### Final outcome
The game rolls a random number and checks:
1. **Blocked?** → Missed, possible rebound
2. **Miss + foul?** → Free throws
3. **Make + foul?** → And-one
4. **Make?** → 2 or 3 points
5. **Miss?** → Rebound battle

---

## Part 8: Fatigue — Why Minutes Management Matters

```typescript
this.fatigueFactor = 0.055;  // Regular season
// In playoffs: fatigueFactor /= 1.85  (less fatigue — players dig deeper)
```

Every possession, players on court lose energy:
```typescript
energy -= min * fatigueFactor * (1 - p.compositeRating.endurance)
```

Players on the bench recover:
```typescript
energy += min * 0.094
```

**Key insight:** High endurance rating = less energy lost. Low endurance + lots of minutes = worse performance late in games (lower `probMake` on shots, worse defense).

The fatigue function:
```typescript
fatigue(energy) {
    energy += 0.016;  // Small baseline boost
    return energy;    // Output: 0 to 1 (1 = no fatigue)
}
```

This number directly multiplies shot probability. A player at 70% energy shoots worse than one at 100%.

---

## Part 9: Substitutions — The Coach's Algorithm

The game auto-subs based on a score for each player:

```typescript
ovrs[player.id] = player.valueNoPot
    × fatigue(player.energy)
    × random.uniform(0.9, 1.1)  // Small randomness
    × player.ptModifier;         // Your playing time settings
```

Sub conditions:
- **Bench player better than court player** AND bench player rested enough (2+ bench minutes) AND court player played enough (2+ court minutes)
- **Player fouled out** → forced off
- **Blowout late** → stars sit more (`× (i+1)/10` — bench player index penalty)
- **Foul trouble** → player at limit gets 0.75× score (more likely to sit)
- **Position requirement** → must have 2 guards (or 1 PG) and 2 forwards (or 1 center) on the floor

---

## Part 10: Team Synergy — Why Roster Construction Matters

```typescript
this.synergyFactor = 0.1;  // Regular season
// In playoffs: synergyFactor *= 2.5  (MUCH more important!)
```

The game checks what skills your 5 players on court have collectively (3-point shooting, dribbling, passing, interior/perimeter defense, post, rebounding, athleticism).

Having multiple 3-point shooters gets an exponential bonus:
```typescript
synergy.off += 5 × sigmoid(skillsCount["3"], 3, 2)
```

This synergy score then boosts team composite ratings:
```typescript
team.compositeRating.dribbling += 0.1 × synergy.off
team.compositeRating.passing   += 0.1 × synergy.off
team.compositeRating.rebounding+= 0.1 × synergy.reb
team.compositeRating.defense   += 0.1 × synergy.def
```

**Real-world translation:** In the playoffs (2.5× synergy), roster construction is dramatically more important. A team of specialists who fit together will outperform a team of stars who don't.

---

## Part 11: Home Court Advantage

```typescript
homeCourtAdvantage(homeCourtFactor) {
    const modifier = homeCourtFactor × (1 + homeCourtAdvantage/100);

    // Home team: all ratings × modifier (typically ~1.01)
    // Away team: all ratings ÷ modifier
}
```

Note: Turnover and fouling ratings are *divided* by the modifier (since higher = worse for those).

This is subtle but consistent — home teams are slightly better at everything, away teams slightly worse.

---

## Part 12: End-Game Situations — The AI's Clutch Logic

The game tracks what it calls `clockFactor`:

```typescript
getClockFactor() {
    // Winning with <24 seconds left? Run out the clock
    if (t <= 24 && pointDifferential > 0) return "runOutClock";

    // Last shot of quarter? Hold for it
    if (t <= 26) return "holdForLastShot";

    // Down big late? Rush shots
    if (t <= 3min && down by 10+) return "catchUp";

    // Up big late? Slow it down
    if (t <= 3min && up by 10+) return "maintainLead";

    // 32-52 seconds left? Try "two-for-one" strategy
    if (t >= 32 && t <= 52) return "twoForOne";
}
```

**Intentional fouling logic:**
```typescript
shouldIntentionalFoul() {
    return offenseWinningBy1to6
        && final period
        && t < 27 seconds;
}
```

---

## Part 13: What This All Means for How You Play the Game

Understanding the code reveals some non-obvious strategic truths:

### Stars matter, but not infinitely
Shot probability is capped. Even the best shooter at rim: `0.41 × 1.0 + 0.54 = 95%`. Defense can subtract up to 25% from any shot. So even the best shooter against elite defense hits around 70%.

### Endurance is underrated
Low endurance = worse performance in the 4th quarter of every game. This compounds across an 82-game season.

### The playoffs change everything
- Fatigue matters **46% less** per possession (1/1.85)
- Synergy matters **2.5× more**
- Translation: depth matters less, lineup fit matters much more

### Three-point shooting is efficiency-capped by design
The code explicitly scales down three-point ratings at the high end to prevent everyone shooting only threes. This is a deliberate design choice to mirror real-world team construction tradeoffs.

### Assists actually help
`probMake += 0.025` for assisted shots. Build teams with passers and your shooters hit more.

### Foul trouble is dynamically managed
The AI uses a `foulTroubleLimit` that scales by quarter. A star in foul trouble in Q1 gets sat more conservatively than the same star in Q4.

---

## What to Explore Next

The codebase has a lot more to dig into:

- `src/worker/core/player/develop.ts` — How players improve and decline with age
- `src/worker/core/draft/` — How the draft lottery and picks work
- `src/worker/core/trade/` — How AI teams evaluate trades
- `src/worker/core/freeAgents/` — How player contracts and demands work
- `src/worker/core/player/genContract.ts` — How contract values are calculated

---

*Source code: github.com/zengm-games/zengm — MIT licensed, open source*
*Cloned locally at: `/home/user/zengm`*
