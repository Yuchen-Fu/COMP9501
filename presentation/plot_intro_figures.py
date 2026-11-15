#!/usr/bin/env python3
"""Render conceptual AML diagrams as publication-style Matplotlib figures.

These are explanatory examples, not observed or labelled transactions. Counts
refer to strictly preceding events in the transaction order. PowerPoint only
embeds the resulting PNGs; editable vector versions are retained as SVG/PDF.
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/comp9501-academic-mpl")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/comp9501-academic-system-cache")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures"
INK = "#243342"
NAVY = "#244C73"
TEAL = "#247C79"
GRAY = "#687581"
LIGHT = "#D7DEE3"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 17,
    "text.color": INK,
    "axes.labelcolor": INK,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "savefig.facecolor": "white",
})


def canvas(width, height):
    fig, ax = plt.subplots(figsize=(width, height))
    fig.subplots_adjust(left=.015, right=.985, bottom=.025, top=.975)
    ax.set(xlim=(0, width), ylim=(0, height))
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"academic_{name}.{extension}", dpi=300)
    plt.close(fig)


def label(ax, x, y, text, size=17, color=INK, weight="normal", **kwargs):
    return ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
                   ha=kwargs.pop("ha", "center"), va=kwargs.pop("va", "center"),
                   **kwargs)


def arrow(ax, start, end, color=GRAY, radius=0, lw=1.8, shrink=0):
    ax.add_patch(FancyArrowPatch(start, end, connectionstyle=f"arc3,rad={radius}",
                                arrowstyle="-|>", mutation_scale=13,
                                color=color, lw=lw, shrinkA=shrink, shrinkB=shrink))


def node(ax, x, y, name, color=NAVY, radius=.22):
    ax.add_patch(Circle((x, y), radius, facecolor="white", edgecolor=color, lw=1.8,
                        zorder=4))
    label(ax, x, y, name, 17, color, zorder=5)


def workflow():
    """Three stages are drawn across the page, with no explanatory sidebar."""
    fig, ax = canvas(13.5, 3.8)
    for x, heading in [(2.2, "Transactions"), (6.75, "Risk scores"), (11.3, "Analyst review")]:
        label(ax, x, 3.4, heading, 21, weight="bold")
    for y, name in [(2.65, "B"), (1.85, "C"), (1.05, "D")]:
        arrow(ax, (1.0, 1.85), (3.05, y), NAVY, shrink=19)
        node(ax, 3.05, y, name, TEAL, radius=.25)
    node(ax, 1.0, 1.85, "A", radius=.25)
    label(ax, 2.2, .35, "Account relationships", 18, GRAY)

    for y, score, col in [(2.6, .85, TEAL), (1.85, .46, GRAY), (1.1, .18, GRAY)]:
        ax.plot([5.45, 8.05], [y, y], color=LIGHT, lw=1.2)
        ax.plot(5.45+2.6*score, y, "o", ms=8, color=col)
    label(ax, 5.45, .6, "Low", 17, GRAY)
    label(ax, 8.05, .6, "High", 17, GRAY)

    ax.add_patch(Rectangle((10.55, .85), 1.5, 2.0, facecolor="white", edgecolor=NAVY, lw=1.7))
    for y, length in [(2.4, 1.0), (2.05, 1.0), (1.7, .7)]:
        ax.plot([10.8, 10.8+length], [y, y], color=GRAY, lw=1.3)
    ax.add_patch(Circle((11.95, 1.0), .32, facecolor="white", edgecolor=TEAL, lw=1.7))
    ax.plot([12.18, 12.52], [.77, .43], color=TEAL, lw=2)
    label(ax, 11.3, .25, "Human assessment", 18, GRAY)
    arrow(ax, (3.85, 1.85), (4.7, 1.85), GRAY)
    arrow(ax, (8.75, 1.85), (9.6, 1.85), GRAY)
    save(fig, "workflow")


def counterparty_breadth():
    """Two large ego networks compare four transfers with one or four partners."""
    fig, ax = canvas(13.5, 4.3)
    label(ax, 3.3, 3.95, "One relationship", 21, weight="bold")
    label(ax, 10.1, 3.95, "Four relationships", 21, weight="bold")
    ax.plot([6.7, 6.7], [.7, 3.5], color=LIGHT, lw=1)
    for radius in [-.32, -.11, .11, .32]:
        arrow(ax, (1.5, 2.15), (5.05, 2.15), NAVY, radius=radius, shrink=22)
    node(ax, 1.5, 2.15, "A", radius=.30)
    node(ax, 5.05, 2.15, "B", TEAL, radius=.30)
    for y, name in [(3.3, "B"), (2.55, "C"), (1.80, "D"), (1.05, "E")]:
        arrow(ax, (8.25, 2.15), (11.95, y), NAVY, shrink=22)
        node(ax, 11.95, y, name, TEAL, radius=.28)
    node(ax, 8.25, 2.15, "A", radius=.30)
    label(ax, 3.3, .45, "4 transfers · 1 distinct recipient", 19)
    label(ax, 10.1, .45, "4 transfers · 4 distinct recipients", 19)
    save(fig, "counterparty_breadth")


def feature_history():
    """Sender-side counts precede each transfer; local ranks persist on repeats."""
    fig, ax = canvas(13.5, 4.3)
    cols = [5.7, 8.9, 12.1]
    for x, name in zip(cols, ["Transfer 1", "Transfer 2", "Transfer 3"]):
        label(ax, x, 3.96, name, 18, GRAY)
    for i, (x, partner) in enumerate(zip(cols, ["B", "C", "B"])):
        node(ax, x-.60, 3.34, "A", radius=.24)
        node(ax, x+.60, 3.34, partner, TEAL, radius=.24)
        arrow(ax, (x-.30, 3.34), (x+.30, 3.34), NAVY)
        label(ax, x, 2.78, "New pair" if i < 2 else "Repeated pair", 18,
              TEAL if i < 2 else NAVY)
    ax.plot([.35, 13.1], [2.42, 2.42], color=LIGHT, lw=1.2)
    rows = [
        (1.98, "Previous transfers", ["0", "1", "2"], INK),
        (1.25, "Distinct recipients", ["0", "1", "2"], INK),
        (.52, "Outgoing port", ["0", "1", "0"], NAVY),
    ]
    for y, heading, values, color in rows:
        label(ax, .40, y, heading, 20, color, ha="left")
        for x, value in zip(cols, values):
            label(ax, x, y, value, 21, color)
    save(fig, "feature_history")


def factorial_design():
    """A compact, balanced-page matrix separates the supplementary cell."""
    fig, ax = canvas(7.8, 4.8)
    x0, x1, x2 = 1.95, 4.65, 7.35
    for x, heading in [(3.30, "Ports absent"), (6.00, "Ports present")]:
        label(ax, x, 4.35, heading, 19, GRAY)
    for y, heading in [(3.35, "Counts\nabsent"), (1.95, "Counts\npresent")]:
        label(ax, .85, y, heading, 18, GRAY)
    for y in [4.0, 2.65, 1.25]:
        ax.plot([x0, x2], [y, y], color=LIGHT, lw=1.2)
    ax.plot([x1, x1], [1.25, 4.0], color=LIGHT, lw=1.2)
    for x, y, name, tag in [(3.30, 3.35, "Base", "B"), (6.00, 3.35, "Ports", "P"),
                            (3.30, 1.95, "Counts", "C"), (6.00, 1.95, "Counts + Ports", "CP")]:
        label(ax, x, y+.13, name, 20, NAVY, "bold")
        label(ax, x, y-.32, tag, 17, GRAY)
    label(ax, 3.9, .55, "Supplement: Counts + novelty (CN)", 18, TEAL)
    save(fig, "factorial_design")


def estimand():
    """Balanced-page equation panel; the ratio uses mean seed contrasts."""
    fig, ax = canvas(8.2, 4.5)
    rows = [
        (3.6, "Original port gain", r"$D_s = P_s - B_s$", NAVY),
        (2.5, "Port gain after counts", r"$N_s = CP_s - C_s$", TEAL),
    ]
    for y, text, formula, color in rows:
        label(ax, .20, y, text, 18, color, ha="left")
        label(ax, 6.0, y, formula, 23, color)
    ax.plot([.20, 7.9], [1.82, 1.82], color=LIGHT, lw=1.2)
    label(ax, .20, 1.0, "Share explained", 18, ha="left")
    label(ax, 6.0, 1.0, r"$S = 1 - \frac{\overline{N}}{\overline{D}}$", 24)
    save(fig, "estimand")


def counterexample():
    """Alternative next transfers share raw counts but differ in pair history."""
    fig, ax = canvas(13.5, 4.3)
    label(ax, 6.75, 3.98, "Earlier transfers:  u → a,  u → b,  d → c", 20, NAVY)
    xs = [1.5, 5.0, 8.65, 11.9]
    for x, heading in zip(xs, ["Next transfer", "Prior counts", "Ports (in, out)", "Novelty"]):
        label(ax, x, 3.20, heading, 19, weight="bold")
    ax.plot([.35, 13.1], [2.84, 2.84], color=LIGHT, lw=1.3)
    rows = [
        ["u → a", "(2, 2; 1, 1)", "(0, 0)", "0"],
        ["u → b", "(2, 2; 1, 1)", "(0, 1)", "0"],
        ["u → c", "(2, 2; 1, 1)", "(1, 2)", "1"],
    ]
    for y, row in zip([2.38, 1.58, .78], rows):
        for x, value in zip(xs, row):
            label(ax, x, y, value, 21, TEAL if value == "1" else INK)
    ax.plot([.35, 13.1], [.35, .35], color=LIGHT, lw=1.3)
    save(fig, "counterexample")


def main():
    workflow()
    counterparty_breadth()
    feature_history()
    factorial_design()
    estimand()
    counterexample()
    print("Rendered six academic conceptual figures as PNG, SVG, and PDF.")


if __name__ == "__main__":
    main()
