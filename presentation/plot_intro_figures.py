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
PALE = "#F0F5F5"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 17,
    "text.color": INK,
    "axes.labelcolor": INK,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "savefig.facecolor": "white",
})


def canvas(width=9, height=4.3):
    fig, ax = plt.subplots(figsize=(width, height))
    fig.subplots_adjust(left=.015, right=.985, bottom=.025, top=.975)
    ax.set(xlim=(0, 9), ylim=(0, height))
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
    """The figures show scoring and human assessment, not a guilt decision."""
    fig, ax = canvas(height=3.8)
    centers = [1.35, 4.5, 7.65]
    for x, heading in zip(centers, ["Transactions", "Risk scores", "Analyst review"]):
        label(ax, x, 3.35, heading, 19, weight="bold")

    # Incoming transfers form a directed transaction network.
    for y, n in [(2.7, "B"), (1.9, "C"), (1.1, "D")]:
        arrow(ax, (.65, 1.9), (2.05, y), NAVY, shrink=17)
        node(ax, 2.05, y, n, TEAL)
    node(ax, .65, 1.9, "A")
    label(ax, 1.35, .55, "Account relationships", 16, GRAY)

    # A score is a ranking signal. No invented numerical performance is shown.
    for y, score, col in [(2.65, .85, TEAL), (1.95, .46, GRAY), (1.25, .18, GRAY)]:
        ax.plot([3.7, 5.3], [y, y], color=LIGHT, lw=1.2)
        ax.plot(3.7+1.6*score, y, "o", ms=8, color=col)
    label(ax, 3.7, .85, "Low", 15, GRAY)
    label(ax, 5.3, .85, "High", 15, GRAY)
    label(ax, 4.5, .35, "Prioritized flags", 16, GRAY)

    # The document represents an assessment, not a conclusive laundering label.
    ax.add_patch(Rectangle((7.05, 1.05), 1.2, 1.8, facecolor="white", edgecolor=NAVY, lw=1.7))
    for y, length in [(2.45, .77), (2.15, .77), (1.85, .5)]:
        ax.plot([7.25, 7.25+length], [y, y], color=GRAY, lw=1.3)
    ax.add_patch(Circle((8.1, 1.18), .30, facecolor="white", edgecolor=TEAL, lw=1.7))
    ax.plot([8.31, 8.58], [.97, .70], color=TEAL, lw=2)
    label(ax, 7.65, .35, "Human assessment", 16, GRAY)
    arrow(ax, (2.67, 1.95), (3.25, 1.95), GRAY)
    arrow(ax, (5.72, 1.95), (6.30, 1.95), GRAY)
    save(fig, "workflow")


def counterparty_breadth():
    """Equal transfer frequency with different distinct-counterparty counts."""
    fig, ax = canvas()
    label(ax, 2.18, 3.95, "One relationship", 19, weight="bold")
    label(ax, 6.75, 3.95, "Four relationships", 19, weight="bold")
    ax.plot([4.5, 4.5], [.75, 3.45], color=LIGHT, lw=1)

    for radius in [-.42, -.14, .14, .42]:
        arrow(ax, (1.1, 2.2), (3.25, 2.2), NAVY, radius=radius, shrink=20)
    node(ax, 1.1, 2.2, "A", radius=.27)
    node(ax, 3.25, 2.2, "B", TEAL, radius=.27)

    for y, name in [(3.32, "B"), (2.58, "C"), (1.84, "D"), (1.10, "E")]:
        arrow(ax, (5.65, 2.2), (7.9, y), NAVY, shrink=20)
        node(ax, 7.9, y, name, TEAL, radius=.25)
    node(ax, 5.65, 2.2, "A", radius=.27)
    label(ax, 2.18, .55, "4 transfers; 1 distinct counterparty", 16)
    label(ax, 6.75, .55, "4 transfers; 4 distinct counterparties", 16)
    save(fig, "counterparty_breadth")


def feature_history():
    """Sender-side zero-based local ranks with a repeated third counterparty."""
    fig, ax = canvas()
    cols = [4.3, 6.1, 7.90]
    for x, name in zip(cols, ["Transfer 1", "Transfer 2", "Transfer 3"]):
        label(ax, x, 3.98, name, 16, GRAY)
    for i, (x, partner) in enumerate(zip(cols, ["B", "C", "B"])):
        node(ax, x-.46, 3.35, "A", radius=.20)
        node(ax, x+.46, 3.35, partner, TEAL, radius=.20)
        arrow(ax, (x-.22, 3.35), (x+.22, 3.35), NAVY)
        label(ax, x, 2.84, "New pair" if i < 2 else "Repeated pair", 16,
              TEAL if i < 2 else NAVY)
    ax.plot([.28, 8.75], [2.50, 2.50], color=LIGHT, lw=1.2)
    rows = [
        (2.12, "Previous transfers", ["0", "1", "2"], INK),
        (1.51, "Distinct recipients", ["0", "1", "2"], INK),
        (.90, "Outgoing port", ["0", "1", "0"], NAVY),
    ]
    for y, heading, values, color in rows:
        label(ax, .30, y, heading, 16, color, ha="left")
        for x, value in zip(cols, values):
            label(ax, x, y, value, 19, color)
    ax.plot([.28, 8.75], [.56, .56], color=LIGHT, lw=1.2)
    label(ax, 4.5, .20, "Counts use earlier transfers; a repeated counterparty keeps its port.", 15, GRAY)
    save(fig, "feature_history")


def factorial_design():
    """Four primary cells plus a clearly separate supplementary comparison."""
    fig, ax = canvas()
    # Fine grid and ordinary type avoid dashboard-card emphasis.
    x0, x1, x2 = 2.4, 5.35, 8.3
    for x, heading in [(3.875, "Ports absent"), (6.825, "Ports present")]:
        label(ax, x, 3.97, heading, 18, GRAY)
    for y, heading in [(3.05, "Counts\nabsent"), (1.85, "Counts\npresent")]:
        label(ax, 1.12, y, heading, 18, GRAY)
    for y in [3.65, 2.45, 1.25]:
        ax.plot([x0, x2], [y, y], color=LIGHT, lw=1.2)
    ax.plot([x1, x1], [1.25, 3.65], color=LIGHT, lw=1.2)
    for x, y, name, tag in [(3.875, 3.05, "Base", "B"), (6.825, 3.05, "Ports", "P"),
                            (3.875, 1.85, "Counts", "C"), (6.825, 1.85, "Counts + Ports", "CP")]:
        label(ax, x, y+.13, name, 19, NAVY, "bold")
        label(ax, x, y-.27, tag, 15, GRAY)
    label(ax, 4.5, .68, "Supplement: Counts + novelty (CN)", 18, TEAL)
    label(ax, 4.5, .20, "Each cell uses the same GIN settings and five random seeds.", 15, GRAY)
    save(fig, "factorial_design")


def estimand():
    """The share is a ratio of mean seed contrasts, not a mean of ratios."""
    fig, ax = canvas()
    rows = [
        (3.55, "Original port gain", r"$D_s = P_s - B_s$", NAVY),
        (2.55, "Port gain after counts", r"$N_s = CP_s - C_s$", TEAL),
    ]
    for y, text, formula, color in rows:
        label(ax, .55, y, text, 19, color, ha="left")
        label(ax, 6.4, y, formula, 23, color)
    ax.plot([.55, 8.45], [1.95, 1.95], color=LIGHT, lw=1.2)
    label(ax, .55, 1.23, "Share explained", 19, ha="left")
    label(ax, 6.4, 1.23, r"$S = 1 - \frac{\overline{N}}{\overline{D}}$", 25)
    label(ax, 4.5, .35, "Bars denote means across the five paired seeds.", 17, GRAY)
    save(fig, "estimand")


def counterexample():
    """Three alternative next transfers share counts but differ in pair history."""
    fig, ax = canvas()
    label(ax, 4.5, 3.98, "Earlier transfers:  u → a,  u → b,  d → c", 18, NAVY)
    xs = [1.08, 3.62, 6.15, 8.08]
    for x, heading in zip(xs, ["Next transfer", "Prior counts", "Ports\n(in, out)", "Novelty"]):
        label(ax, x, 3.24, heading, 17, weight="bold")
    ax.plot([.28, 8.78], [2.93, 2.93], color=LIGHT, lw=1.3)
    rows = [
        ["u → a", "(2, 2; 1, 1)", "(0, 0)", "0"],
        ["u → b", "(2, 2; 1, 1)", "(0, 1)", "0"],
        ["u → c", "(2, 2; 1, 1)", "(1, 2)", "1"],
    ]
    for y, row in zip([2.56, 1.90, 1.24], rows):
        for x, value in zip(xs, row):
            label(ax, x, y, value, 19, TEAL if value == "1" else INK)
    ax.plot([.28, 8.78], [.89, .89], color=LIGHT, lw=1.3)
    label(ax, 4.5, .48, "Counts: sender total, distinct; receiver total, distinct.", 16, GRAY)
    label(ax, 4.5, .10, "The rows are alternative next transfers, not a sequence.", 16, GRAY)
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
