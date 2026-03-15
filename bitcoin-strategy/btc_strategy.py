#!/usr/bin/env python3
"""
Bitcoin Price Model & Exit Strategy
=====================================

⚠️  NOT FINANCIAL ADVICE. Educational scenario modeling tool only. ⚠️

Modeling philosophy (why this tool is different):
  • BTC behaves as a high-beta RISK asset (~0.7 correlation with NASDAQ),
    NOT a proven inflation hedge or safe-haven (low correlation with gold)
  • Stock-to-Flow has clear out-of-sample failures; excluded as primary model
  • Power Law is a wide corridor, not a prediction; shown only as reference
  • Global M2 money supply and Fed policy regime are the dominant drivers
  • Most real-world buyers enter near cycle tops (behavioral reality)
  • Stagnation (Gold 1980–2000 analog) is a genuine base-case possibility
  • All scenarios include realistic -50% to -80% drawdown periods

Five scenarios modeled with probability weights:
  1. Catastrophic   (10%) — regulatory ban, tech failure, CBDC displacement
  2. Stagnation     (20%) — Gold 1980–2000: 15+ years near or below ATH
  3. Tight Money    (20%) — Hawkish Fed era, strong dollar, deep drawdown first
  4. Base Case      (30%) — BTC follows global M2, muted but positive cycles
  5. Bull Case      (20%) — Safe-haven narrative finally proven in a real crisis

Usage:
  pip install numpy matplotlib
  python btc_strategy.py

  Edit CONFIG below to match your situation.
  Output saved to btc_strategy_output.png
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURATION — edit to match your situation
# ═══════════════════════════════════════════════════════════════

CONFIG = {
    # --- Your current position ---
    "current_price":        84_000,   # USD/BTC right now
    "your_btc":               0.50,   # BTC you currently hold
    "avg_cost_basis":       84_000,   # Your average purchase price (USD)

    # --- Your financial profile ---
    "net_worth":           100_000,   # Investable net worth, USD (exclude home equity)
    "monthly_surplus":       1_500,   # Monthly $ you could invest

    # --- DCA accumulation plan ---
    "monthly_dca":             500,   # USD to buy each month (set 0 to disable)
    "dca_months":               24,   # Buy over this many months

    # --- Exit strategy ---
    # "Sell X% of remaining BTC each time price doubles from entry"
    # 2%  = very conservative → still hold 82% of BTC after 10 doublings
    # 5%  = moderate          → still hold 60% after 10 doublings
    # 10% = aggressive        → still hold 35% after 10 doublings
    "sell_pct_per_double":    0.02,   # fraction (0.02 = 2%)
    "entry_price_for_exit": 84_000,   # price from which to count doublings

    # --- Horizon ---
    "hold_years":               30,
}

# ═══════════════════════════════════════════════════════════════
#  HISTORICAL PRICE DATA (approximate year-end)
# ═══════════════════════════════════════════════════════════════

HIST = {
    2010: 0.30,   2011: 4.70,   2012: 13.5,   2013: 732,
    2014: 320,    2015: 430,    2016: 963,    2017: 13_800,
    2018: 3_709,  2019: 7_196,  2020: 28_990, 2021: 46_300,
    2022: 16_547, 2023: 42_265, 2024: 93_000, 2025: 84_000,
}

ATH_LABELS = {2013: 1_200, 2017: 20_000, 2021: 69_000, 2024: 108_000}
HALVINGS    = [2012, 2016, 2020, 2024, 2028, 2032, 2036]

# ═══════════════════════════════════════════════════════════════
#  SCENARIO DEFINITIONS
#
#  Each scenario is anchored by (year, price) pairs and
#  log-linearly interpolated between them.
#
#  Price paths deliberately include cycle peaks AND troughs —
#  because holding through -70% drawdowns is the actual experience.
# ═══════════════════════════════════════════════════════════════

SCENARIOS = {
    "catastrophic": {
        "label":   "Catastrophic",
        "sub":     "Regulatory ban / tech failure / CBDC displacement",
        "color":   "#C0392B",
        "lw":      2.5,
        "ls":      "-",
        "weight":  0.10,
        "anchors": [
            (2026, 55_000), (2027, 28_000), (2028, 11_000),
            (2030,  3_000), (2033,    400), (2040,     50),
            (2050,      5), (2055,      1),
        ],
        "note": (
            "Near-total loss. Bitcoin made illegal in major jurisdictions, "
            "or superseded by better technology / CBDCs. Size your position "
            "so this outcome doesn't destroy you."
        ),
    },

    "stagnation": {
        "label":   "Stagnation",
        "sub":     "Gold 1980–2000: 15+ years near or below ATH",
        "color":   "#E67E22",
        "lw":      2.5,
        "ls":      "-",
        "weight":  0.20,
        "anchors": [
            (2026, 70_000), (2027, 46_000), (2028, 55_000),
            (2029, 40_000), (2030, 57_000), (2032, 66_000),
            (2035, 82_000), (2038, 100_000),(2040, 122_000),
            (2045, 215_000),(2050, 390_000),(2055, 640_000),
        ],
        "note": (
            "Gold peaked at $850 in Jan 1980. Didn't recover that level "
            "until 2008 — 28 years. BTC has had its 2021 and 2024 ATH moments. "
            "If adoption plateaus and no new narrative emerges, expect a long sideways grind. "
            "Returns beat inflation only after ~2038."
        ),
    },

    "tight_money": {
        "label":   "Tight Money",
        "sub":     "Hawkish Fed era (Warsh), strong dollar, risk-off 2026–2029",
        "color":   "#D4AC0D",
        "lw":      2.5,
        "ls":      "-",
        "weight":  0.20,
        "anchors": [
            (2026, 51_000), (2027, 31_000), (2028, 25_000),
            (2029, 75_000), (2030, 150_000),(2031, 88_000),
            (2033, 240_000),(2035, 190_000),(2037, 500_000),
            (2040, 950_000),(2045, 2_700_000),(2050, 6_200_000),(2055, 13_000_000),
        ],
        "note": (
            "BTC acts like a leveraged tech stock in a tightening cycle: "
            "down 60–70% as dollar surges and liquidity drains. "
            "The 2027–2028 trough is the buy-more zone. "
            "When the Fed eventually pivots (as they always do), "
            "the recovery is sharp. Long-term intact but delayed 5–7 years."
        ),
    },

    "base": {
        "label":   "Base Case",
        "sub":     "BTC tracks global M2 liquidity — muted, positive cycles",
        "color":   "#2ECC71",
        "lw":      3.0,
        "ls":      "-",
        "weight":  0.30,
        "anchors": [
            (2026, 138_000),(2027, 90_000), (2028, 64_000),
            (2029, 255_000),(2030, 330_000),(2031, 195_000),
            (2033, 530_000),(2035, 430_000),(2037, 950_000),
            (2040, 1_800_000),(2045, 4_800_000),(2050, 11_000_000),(2055, 22_000_000),
        ],
        "note": (
            "BTC as a global liquidity barometer. "
            "Cycles continue but with decreasing amplitude as the market matures. "
            "Expect 3–4 more -50% to -70% corrections. Each halving triggers a cycle. "
            "30-year hold turns $84k/BTC into ~$22M in this scenario. "
            "Patience and not selling in corrections is the entire job."
        ),
    },

    "bull": {
        "label":   "Bull Case",
        "sub":     "Safe-haven narrative proven — crisis validates BTC",
        "color":   "#3498DB",
        "lw":      2.5,
        "ls":      "-",
        "weight":  0.20,
        "anchors": [
            (2026, 270_000),(2027, 165_000),(2028, 118_000),
            (2029, 710_000),(2030, 930_000),(2031, 540_000),
            (2033, 2_200_000),(2035, 1_800_000),(2037, 4_500_000),
            (2040, 9_000_000),(2045, 24_000_000),(2050, 55_000_000),(2055, 100_000_000),
        ],
        "note": (
            "A sovereign debt crisis, dollar crisis, or major bank failure "
            "finally makes BTC act as the safe haven it's claimed to be. "
            "Institutional ETF inflows accelerate. Nation-state adoption begins. "
            "Requires an actual crisis where BTC *doesn't* sell off with equities. "
            "This has NOT happened yet — it remains the key falsifiable test."
        ),
    },
}

# ═══════════════════════════════════════════════════════════════
#  CORE MATH
# ═══════════════════════════════════════════════════════════════

def interpolate_log_linear(anchors: list, years: list) -> dict:
    """Log-linear interpolation between (year, price) anchor points."""
    ax = np.array([a[0] for a in anchors], dtype=float)
    ay = np.log10(np.array([a[1] for a in anchors], dtype=float))
    result = {}
    for y in years:
        if y <= ax[0]:
            result[y] = 10 ** ay[0]
        elif y >= ax[-1]:
            result[y] = 10 ** ay[-1]
        else:
            i = int(np.searchsorted(ax, y)) - 1
            t = (y - ax[i]) / (ax[i + 1] - ax[i])
            result[y] = 10 ** (ay[i] + t * (ay[i + 1] - ay[i]))
    return result


def generate_paths(start: int = 2026, end: int = 2055) -> tuple:
    years = list(range(start, end + 1))
    paths = {k: interpolate_log_linear(v["anchors"], years) for k, v in SCENARIOS.items()}
    return years, paths


def probability_weighted(years: list, paths: dict) -> dict:
    return {y: sum(paths[k][y] * SCENARIOS[k]["weight"] for k in paths) for y in years}


def doubling_schedule(entry_price: float, btc: float, sell_pct: float, n: int = 12) -> list:
    """
    Simulate 'sell X% of remaining stack each time price doubles'.
    Returns list of dicts with one row per doubling event.
    """
    rows = []
    remaining = btc
    cumulative_usd = 0.0
    for i in range(1, n + 1):
        price       = entry_price * (2 ** i)
        btc_sold    = remaining * sell_pct
        usd_recv    = btc_sold * price
        remaining  -= btc_sold
        cumulative_usd += usd_recv
        rows.append({
            "n":             i,
            "price":         price,
            "mult":          2 ** i,
            "btc_sold":      btc_sold,
            "usd_recv":      usd_recv,
            "btc_remaining": remaining,
            "pct_remaining": remaining / btc * 100,
            "cumul_usd":     cumulative_usd,
        })
    return rows


def stress_test(net_worth: float, current_price: float, drawdown: float = 0.80) -> list:
    allocs = np.linspace(0, 0.60, 121)
    return [
        {
            "alloc_pct":    a * 100,
            "btc_value":    net_worth * a,
            "loss":         net_worth * a * drawdown,
            "worth_after":  net_worth * (1 - a * drawdown),
        }
        for a in allocs
    ]

# ═══════════════════════════════════════════════════════════════
#  FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════════

def fmt_price(x, _=None):
    if x >= 1_000_000_000: return f"${x/1e9:.0f}B"
    if x >= 1_000_000:     return f"${x/1e6:.1f}M"
    if x >= 1_000:         return f"${x/1e3:.0f}k"
    if x >= 1:             return f"${x:.0f}"
    return f"${x:.2f}"

def fmt_dollar(x, _=None):
    if x >= 1_000_000_000: return f"${x/1e9:.1f}B"
    if x >= 1_000_000:     return f"${x/1e6:.2f}M"
    if x >= 1_000:         return f"${x/1e3:.0f}k"
    return f"${x:.0f}"

# ═══════════════════════════════════════════════════════════════
#  CHART STYLING
# ═══════════════════════════════════════════════════════════════

BG   = "#0D1117"
GRID = "#21262D"
TEXT = "#E6EDF3"
MUTED= "#8B949E"

def style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(BG)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.grid(True, color=GRID, linewidth=0.5, alpha=0.8)
    if title:  ax.set_title(title,  color=TEXT,  fontsize=10, fontweight="bold", pad=7)
    if xlabel: ax.set_xlabel(xlabel, color=MUTED, fontsize=9)
    if ylabel: ax.set_ylabel(ylabel, color=MUTED, fontsize=9)

# ═══════════════════════════════════════════════════════════════
#  CHART 1 — Scenario Fan  (top-left)
# ═══════════════════════════════════════════════════════════════

def plot_scenario_fan(ax, years, paths):
    # Historical line
    hy = sorted(HIST.keys())
    hp = [HIST[y] for y in hy]
    ax.plot(hy, hp, color="white", lw=2.5, zorder=10, label="Historical price")

    # Halving vertical markers
    for h in HALVINGS:
        ax.axvline(h, color="#F39C12", alpha=0.25, lw=1, ls=":")
    ax.annotate("▲ halvings", xy=(2012.1, 0.12), color="#F39C12",
                fontsize=7, alpha=0.7)

    # ATH dots
    for yr, p in ATH_LABELS.items():
        ax.plot(yr, p, "^", color="#F1C40F", markersize=7, zorder=11, alpha=0.8)

    # Scenario paths
    for key, sc in SCENARIOS.items():
        prices = [paths[key][y] for y in years]
        ax.plot(years, prices,
                color=sc["color"], lw=sc["lw"], ls=sc["ls"], alpha=0.88, zorder=5,
                label=f"{sc['label']}  ({sc['weight']*100:.0f}%)")

    # Probability-weighted path
    pw = probability_weighted(years, paths)
    ax.plot(years, [pw[y] for y in years],
            color="white", lw=2.5, ls="--", alpha=0.85, zorder=8,
            label="Prob-weighted expected value")

    # Current price reference
    cp = CONFIG["current_price"]
    ax.axhline(cp, color="white", lw=1, ls=":", alpha=0.4)
    ax.annotate(f" {fmt_price(cp)} today", xy=(2026.1, cp),
                color=MUTED, fontsize=8, va="center")

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_price))
    ax.set_xlim(2010, 2056)
    ax.set_ylim(0.08, 3e8)
    style_ax(ax,
             "Bitcoin — Five Scenario Fan (2010–2055, log scale)",
             "Year", "BTC Price (USD)")

    leg = ax.legend(loc="upper left", fontsize=8, framealpha=0.15,
                    labelcolor=TEXT, facecolor=BG, edgecolor=GRID, ncol=2)

    # Scenario weight total check
    total_w = sum(s["weight"] for s in SCENARIOS.values())
    ax.annotate(f"Σ weights = {total_w:.0%}", xy=(0.98, 0.03),
                xycoords="axes fraction", color=MUTED, fontsize=7, ha="right")

# ═══════════════════════════════════════════════════════════════
#  CHART 2 — Your Portfolio Value Per Scenario  (top-right)
# ═══════════════════════════════════════════════════════════════

def plot_portfolio_value(ax, years, paths):
    btc = CONFIG["your_btc"]
    cb  = CONFIG["avg_cost_basis"]
    entry_val = btc * cb

    # Entry cost basis line
    ax.axhline(entry_val, color=MUTED, lw=1, ls=":", alpha=0.7)
    ax.annotate(f"  Entry: {fmt_dollar(entry_val)}", xy=(years[0], entry_val),
                color=MUTED, fontsize=8, va="bottom")

    # DCA accumulation — show how BTC grows via monthly buys
    monthly_dca = CONFIG["monthly_dca"]
    dca_months  = CONFIG["dca_months"]
    if monthly_dca > 0:
        dca_btc_added = 0.0
        avg_dca_price = cb  # rough approximation
        dca_btc_added = (monthly_dca * dca_months) / avg_dca_price
        total_btc = btc + dca_btc_added
        ax.annotate(
            f"  +{dca_btc_added:.3f} BTC via DCA\n  → {total_btc:.3f} BTC total",
            xy=(years[0], entry_val * 1.5), color="#2ECC71", fontsize=8
        )
    else:
        total_btc = btc

    # Scenario value lines
    for key, sc in SCENARIOS.items():
        vals = [paths[key][y] * total_btc for y in years]
        ax.plot(years, vals,
                color=sc["color"], lw=sc["lw"], ls=sc["ls"], alpha=0.88,
                label=sc["label"])

    # Probability-weighted
    pw = probability_weighted(years, paths)
    ax.plot(years, [pw[y] * total_btc for y in years],
            color="white", lw=2.5, ls="--", alpha=0.85, label="Prob-weighted avg")

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_dollar))
    ax.set_xlim(years[0], years[-1])
    style_ax(ax,
             f"Your {total_btc:.3f} BTC — Portfolio Value by Scenario",
             "Year", f"Value of {total_btc:.3f} BTC (USD)")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.15,
              labelcolor=TEXT, facecolor=BG, edgecolor=GRID)

# ═══════════════════════════════════════════════════════════════
#  CHART 3 — Exit Strategy Comparison  (bottom-left)
# ═══════════════════════════════════════════════════════════════

def plot_exit_strategy(ax):
    entry = CONFIG["entry_price_for_exit"]
    btc   = CONFIG["your_btc"]

    RULES = [
        (0.02,  "#3498DB", "2% / double — very conservative"),
        (0.05,  "#2ECC71", "5% / double — moderate"),
        (0.10,  "#F39C12", "10% / double — aggressive"),
        (0.20,  "#E74C3C", "20% / double — very aggressive"),
    ]

    for sell_pct, color, label in RULES:
        sched = doubling_schedule(entry, btc, sell_pct, n=12)
        prices  = [r["price"]    for r in sched]
        cumul   = [r["cumul_usd"] for r in sched]
        ax.plot(prices, cumul, color=color, lw=2.5, marker="o",
                markersize=4, label=label)

    # Annotate % BTC remaining for the 2% rule
    sched2 = doubling_schedule(entry, btc, 0.02, n=12)
    for row in sched2[1::3]:   # every 3rd point
        ax.annotate(
            f"{row['pct_remaining']:.0f}% BTC\nremaining",
            xy=(row["price"], row["cumul_usd"]),
            color="#3498DB", fontsize=6.5,
            xytext=(6, 4), textcoords="offset points"
        )

    # Vertical price milestone lines
    for p, lbl in [(200_000, "$200k"), (500_000, "$500k"),
                   (1_000_000, "$1M"), (5_000_000, "$5M"), (10_000_000, "$10M")]:
        if p > entry:
            ax.axvline(p, color=GRID, lw=1, ls=":", alpha=0.7)
            ax.annotate(lbl, xy=(p, ax.get_ylim()[0] if ax.get_ylim()[0] > 0 else 1),
                        color=MUTED, fontsize=7, ha="center", rotation=90,
                        xytext=(0, 4), textcoords="offset points")

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_price))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_dollar))
    style_ax(ax,
             f"Exit Strategy: Cumulative USD Received\n"
             f"(starting {btc} BTC @ {fmt_price(entry)} entry, per doubling rule)",
             "BTC Price Level (USD, log scale)", "Cumulative USD Pocketed")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.15,
              labelcolor=TEXT, facecolor=BG, edgecolor=GRID)

# ═══════════════════════════════════════════════════════════════
#  CHART 4 — Position Sizing / Stress Test  (bottom-right)
# ═══════════════════════════════════════════════════════════════

def plot_stress_test(ax):
    nw = CONFIG["net_worth"]
    cp = CONFIG["current_price"]
    results = stress_test(nw, cp, drawdown=0.80)

    allocs  = [r["alloc_pct"]  for r in results]
    losses  = [r["loss"]       for r in results]
    worths  = [r["worth_after"] for r in results]

    ax.fill_between(allocs, losses, alpha=0.20, color="#E74C3C")
    ax.plot(allocs, losses,  color="#E74C3C", lw=2.5, label="Dollar loss in −80% crash")
    ax.plot(allocs, worths,  color="#2ECC71", lw=2.0, ls="--",
            label="Net worth remaining after −80%")

    # "Danger zone" threshold: loss > 20% of net worth
    danger = nw * 0.20
    ax.axhline(danger, color="#F39C12", lw=1.5, ls=":",
               label=f"Danger threshold: 20% of net worth (${danger:,.0f})")

    # Current allocation marker
    current_val  = CONFIG["your_btc"] * cp
    current_alloc = current_val / nw * 100
    current_loss  = current_val * 0.80
    ax.axvline(current_alloc, color="white", lw=1.5, ls=":",
               label=f"Your allocation ({current_alloc:.1f}%)")
    ax.plot(current_alloc, current_loss, "wo", markersize=9, zorder=10)
    ax.annotate(f" Your loss: {fmt_dollar(current_loss)}\n in −80% crash",
                xy=(current_alloc, current_loss), color="white", fontsize=8.5, va="bottom")

    # Allocation reference labels
    for pct, label in [(2, "BlackRock\n1–2%"), (10, "VanEck\noptimal"), (25, "Aggressive")]:
        loss_at = nw * pct / 100 * 0.80
        ax.annotate(label, xy=(pct, loss_at), color=MUTED, fontsize=7.5,
                    ha="center", va="top", xytext=(0, -12), textcoords="offset points")

    ax.set_xlim(0, 60)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_dollar))
    style_ax(ax,
             f"Position Sizing: −80% Drawdown Impact  (net worth = {fmt_dollar(nw)})\n"
             "How much can you lose and still hold? That sets your max size.",
             "BTC as % of Net Worth", "USD Amount")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.15,
              labelcolor=TEXT, facecolor=BG, edgecolor=GRID)

# ═══════════════════════════════════════════════════════════════
#  CONSOLE REPORT
# ═══════════════════════════════════════════════════════════════

def print_report(years, paths):
    cp   = CONFIG["current_price"]
    btc  = CONFIG["your_btc"]
    cb   = CONFIG["avg_cost_basis"]
    nw   = CONFIG["net_worth"]
    spd  = CONFIG["sell_pct_per_double"]
    ep   = CONFIG["entry_price_for_exit"]

    div = "═" * 68
    print(f"\n{div}")
    print("  BITCOIN STRATEGY REPORT")
    print("  ⚠️  NOT FINANCIAL ADVICE — Educational modeling tool only")
    print(div)

    print(f"\n📊  YOUR POSITION")
    print(f"    {btc} BTC  |  avg cost basis: {fmt_price(cb)}  |  current: {fmt_price(cp)}")
    pnl = (cp / cb - 1) * 100
    print(f"    Current value: {fmt_dollar(btc * cp)}  |  P&L: {pnl:+.1f}%")
    print(f"    As % of net worth: {btc * cp / nw * 100:.1f}%")

    print(f"\n📉  STRESS TEST: −80% DRAWDOWN")
    loss = btc * cp * 0.80
    print(f"    Dollar loss:       {fmt_dollar(loss)}")
    print(f"    Remaining BTC val: {fmt_dollar(btc * cp * 0.20)}")
    print(f"    % of net worth:    {loss / nw * 100:.1f}%")
    if loss / nw > 0.20:
        print(f"    ⚠️  This exceeds 20% of your net worth. Consider sizing down.")
    else:
        print(f"    ✓  Manageable loss. You could realistically hold through this.")

    print(f"\n🎯  EXIT SCHEDULE: sell {spd*100:.0f}% of remaining BTC per doubling from {fmt_price(ep)}")
    hdr = f"  {'Price':>12}  {'Mult':>5}  {'BTC sold':>10}  {'USD (cumul)':>12}  {'BTC left':>10}  {'% left':>7}"
    print(hdr)
    print("  " + "-" * 66)
    sched = doubling_schedule(ep, btc, spd, n=10)
    for r in sched:
        print(f"  {fmt_price(r['price']):>12}  {r['mult']:>4}x"
              f"  {r['btc_sold']:>10.4f}  {fmt_dollar(r['cumul_usd']):>12}"
              f"  {r['btc_remaining']:>10.4f}  {r['pct_remaining']:>6.1f}%")

    print(f"\n📈  SCENARIO OUTCOMES for {btc} BTC (what your stack is worth)")
    print(f"  {'Scenario':>16}  {'Weight':>6}  {'2030':>12}  {'2040':>12}  {'2055':>14}")
    print("  " + "-" * 66)
    for key, sc in SCENARIOS.items():
        v30 = paths[key].get(2030, 0) * btc
        v40 = paths[key].get(2040, 0) * btc
        v55 = paths[key].get(2055, 0) * btc
        print(f"  {sc['label']:>16}  {sc['weight']*100:>5.0f}%"
              f"  {fmt_dollar(v30):>12}  {fmt_dollar(v40):>12}  {fmt_dollar(v55):>14}")
    pw = probability_weighted(years, paths)
    v30 = pw.get(2030, 0) * btc
    v40 = pw.get(2040, 0) * btc
    v55 = pw.get(2055, 0) * btc
    print(f"  {'Prob-wtd avg':>16}  {'':>6}"
          f"  {fmt_dollar(v30):>12}  {fmt_dollar(v40):>12}  {fmt_dollar(v55):>14}")

    print(f"\n🔑  KEY REMINDERS")
    reminders = [
        "BTC correlates ~0.7 with NASDAQ. It is a RISK asset, not a safe haven (yet).",
        "Global M2 money supply is the best macro predictor of BTC price.",
        "S2F missed its own 2021–2022 targets by 70%. Excluded as primary model here.",
        "Power Law is a wide corridor ($48k–$490k currently) — it's a location map, not a target.",
        "Expect −50% to −80% drawdowns. That is normal. Selling in them is the real risk.",
        "The stagnation scenario (20%) is historically realistic — Gold did this for 28 years.",
        "The catastrophic scenario (10%) is real. Don't allocate money you can't afford to lose.",
        "Hawkish Fed / strong dollar = BTC headwinds. Watch DXY and Fed policy first.",
    ]
    for r in reminders:
        print(f"    • {r}")
    print(f"\n{div}\n")

# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    years, paths = generate_paths(2026, 2055)

    fig = plt.figure(figsize=(20, 20), facecolor=BG)
    fig.suptitle(
        "Bitcoin Price Model & Exit Strategy    ⚠️  NOT FINANCIAL ADVICE",
        color=TEXT, fontsize=13, fontweight="bold", y=0.985
    )

    gs = gridspec.GridSpec(
        2, 2, figure=fig,
        hspace=0.35, wspace=0.26,
        left=0.06, right=0.97,
        top=0.96, bottom=0.04
    )

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])

    plot_scenario_fan(ax1, years, paths)
    plot_portfolio_value(ax2, years, paths)
    plot_exit_strategy(ax3)
    plot_stress_test(ax4)

    fig.text(
        0.5, 0.005,
        "Scenarios are illustrative models, not predictions. "
        "Probability weights are author estimates, not empirical probabilities. "
        "Past performance does not indicate future results.",
        ha="center", color=MUTED, fontsize=7.5, style="italic"
    )

    outfile = "btc_strategy_output.png"
    plt.savefig(outfile, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\n✓  Chart saved → {outfile}")
    plt.show()

    print_report(years, paths)


if __name__ == "__main__":
    main()
