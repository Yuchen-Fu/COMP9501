"""Revise the supplied research deck using saved results, without fitting models.

Preserve the user's introductory diagrams and visual style. Plot saved effects
and descriptive confusion counts in Python, add the first-contact evidence page,
and make the central finding and speaker notes direct. No new inference is run.
"""
from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/aml-final-mpl")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/aml-final-cache")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = HERE / "source/user_refined_2026-11-17.pptx"
CONCLUSION_SOURCE = HERE / "source/user_conclusion_layout_2026-11-17.pptx"
FIGURES = HERE / "figures"
BG, INK, BLUE, TEAL, MUTED, GRID = "FAF9F5", "15232F", "1F4F8A", "38786F", "56646F", "CFCABC"
CP, CN = "counts+ports", "counts+novelty"


def color(value):
    return RGBColor.from_string(value)


def text(slide, value, x, y, width, height, size=20, serif=False, ink=INK, bold=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(width), Inches(height))
    tf = box.text_frame
    tf.clear()
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    for i, line in enumerate(value.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.name = "EB Garamond" if serif else "Inter"
        p.font.size = Pt(size)
        p.font.color.rgb = color(ink)
        p.font.bold = bold
        p.space_before = p.space_after = Pt(0)
        p.line_spacing = 1.15
    return box


def replace_text(slide, before, after):
    matches = [s for s in slide.shapes if s.has_text_frame and s.text == before]
    if len(matches) != 1:
        raise ValueError(f"Expected one text box: {before!r}")
    shape = matches[0]
    paragraphs = shape.text_frame.paragraphs
    lines = after.split("\n")
    if len(lines) == len(paragraphs) and all(p.runs for p in paragraphs):
        for p, line in zip(paragraphs, lines):
            p.runs[0].text = line
            for run in p.runs[1:]:
                run.text = ""
    else:
        first = paragraphs[0].runs[0]
        first.text = after
        for p in paragraphs:
            for run in p.runs:
                if run is not first:
                    # python-pptx wrappers are not identity-stable across iteration.
                    if run._r is not first._r:
                        run.text = ""
    return shape


def clear(slide, background=BG):
    for shape in list(slide.shapes):
        shape._element.getparent().remove(shape._element)
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color(background)


def header(slide, label, title, subtitle=None, dark=False):
    ink = BG if dark else INK
    muted = "CCD5DC" if dark else MUTED
    text(slide, label.upper(), .89, .75, 11.6, .28, 12, ink=muted, bold=True)
    text(slide, title, .89, 1.13, 11.6, .62, 32, serif=True, ink=ink)
    if subtitle:
        text(slide, subtitle, .89, 1.84, 11.6, .48, 18, serif=True, ink=ink)


def picture(slide, name, x, y, width, height, description):
    path = FIGURES / f"{name}.png"
    with Image.open(path) as im:
        ratio = min(width / im.width, height / im.height)
        w, h = ratio * im.width, ratio * im.height
    pic = slide.shapes.add_picture(str(path), Inches(x + (width-w)/2), Inches(y + (height-h)/2),
                                   width=Inches(w), height=Inches(h))
    pic._element.nvPicPr.cNvPr.set("descr", description)


def notes(slide, value):
    slide.notes_slide.notes_text_frame.text = value


def conclusion_layout(slide):
    """Use the user's one-slide, three-column template with updated findings."""
    template = Presentation(CONCLUSION_SOURCE).slides[0]
    clear(slide, INK)
    slide._element.cSld.replace(slide._element.cSld.bg, deepcopy(template._element.cSld.bg))
    for shape in template.shapes:
        if shape.has_text_frame and shape.text.strip().isdigit() and shape.top > Inches(6.7):
            continue
        slide.shapes._spTree.insert_element_before(deepcopy(shape._element), "p:extLst")
    replace_text(slide,
                 "Account-level counts do not substitute for ports, and explicit pair novelty provides a useful feature for AML detection",
                 "A first-contact flag helps find laundering on new pairs")
    for before, after in [
            ("TESTED AN EXPLANATION", "PORTS STILL HELP AFTER COUNTS"),
            ("IDENTIFIED A PAIR FEATURE", "THE FLAG IMPROVES DETECTION"),
            ("INFORMS FEATURE DESIGN", "EXTRA DETECTIONS: FIRST CONTACTS")]:
        replace_text(slide, before, after)
    bodies = [
        ("Ports retain a 14.91-point F1 benefit after the four historical counts are supplied.",
         "Ports still improve F1 by 14.91 points after all four historical counts are supplied."),
        ("Adding pair novelty to those counts improves F1 by 24.33 points.",
         "Adding the flag to Counts improves F1 by 24.33 points. Replacing ports with the flag adds 9.42 points."),
        ("These results support evaluating pair-specific history alongside account-level activity summaries in AML feature design.",
         "First-contact laundering recall rises from 47.1% to 64.0%, with more detections in all five seeds.")]
    for before, after in bodies:
        body = replace_text(slide, before, after)
        body.height = Inches(1.60)
    footnotes = [
        ("95% interval 10.11 to 19.71", "95% CI [10.11, 19.71]"),
        ("95% interval 21.47 to 27.19", "Addition: 95% CI [21.47, 27.19]\nReplacement: 95% CI [5.73, 13.11]"),
        ("“Has this sender paid this receiver before?”", "First-contact F1: +11.40 points\n95% CI [7.54, 15.26]")]
    for before, after in footnotes:
        footnote = replace_text(slide, before, after)
        footnote.top = Inches(5.12)
        footnote.height = Inches(.60)
    text(slide, "Contribution: distinguish account activity from pair history and quantify where detection improves.",
         .889, 6.03, 11.902, .38, 14, serif=True, ink="CCD5DC")
    text(slide, "Original five-epoch HI-Small protocol · Five paired seeds · Supplementary flag comparison; descriptive error analysis.",
         .889, 6.55, 11.902, .27, 11, ink="CCD5DC")


def configuration_slide(slide):
    """Keep the four-card layout and report settings from completed run records."""
    pilot = json.loads((REPO / "results/runs/base_s0.json").read_text())
    followup = json.loads((REPO / "results/representation_8h/runs/cp_s15.json").read_text())
    hp = pilot["hp"]
    if hp != followup["hp"]:
        raise ValueError("Shared hyperparameter statement no longer matches saved runs")
    replace_text(slide, "The study at a glance", "Model, training and evaluation configuration")
    replace_text(slide, "The network is held fixed. What changes is the history each transfer carries.",
                 "Fixed GIN settings; CPU for the original study, RTX 3090 for the follow-up.")
    shapes = {shape.shape_id: shape for shape in slide.shapes}
    # Shape IDs refer to the unchanged four-card methodology template.
    card_labels = {6: "DATA", 12: "SHARED SETTINGS", 18: "SHARED SETTINGS", 24: "TRAINING BUDGET"}
    for shape_id, value in card_labels.items():
        shape = shapes[shape_id]
        shape.text_frame.paragraphs[0].runs[0].text = value
    contents = {
        7: "HI-Small", 8: "5,078,345 transfers\n515,088 accounts", 9: "5,177 laundering labels\n(0.102% of transfers)",
        13: "GIN model", 14: f'{hp["n_gnn_layers"]} GINE layers · hidden {hp["n_hidden"]}\nClassifier: 50 → 25 → 2',
        15: f'Dropout: {hp["final_dropout"]:.4f}\nNeighbors: {hp["num_neighbors"]}',
        19: "Optimization", 20: f'Adam · lr {hp["lr"]:.6f}\nBatch: {hp["batch_size"]:,} target transfers',
        21: f'Weighted cross-entropy\nClass weights ≈ 1 : {hp["w_ce"][1]:.3f}',
        25: "Completed runs", 26: "Original: 25 runs × 5 epochs\nSeeds 0–4",
        27: "Follow-up: 15 runs\n20–30 epochs · seeds 15–19"}
    for shape_id, value in contents.items():
        shape = shapes[shape_id]
        replace_text(slide, shape.text, value)
    for shape_id in (8, 14, 20, 26):
        shapes[shape_id].height = Inches(.62)
    for shape_id in (9, 15, 21, 27):
        shapes[shape_id].top = Inches(3.88)
        shapes[shape_id].height = Inches(.54)
    replace_text(slide, shapes[28].text,
                 "Checkpoint: best validation F1 (original); best validation AP (follow-up). Both choose the decision threshold by validation F1.")
    text(slide, "Original: split-specific scaling; dropout and batch statistics remain active at scoring.\nFollow-up: train-only shared scaling; evaluation mode; 11 matched input slots.",
         .889, 6.47, 11.902, .42, 11.5, ink=MUTED)
    notes(slide, f"This page states the configuration used in the completed experiments, checked against all 25 original and all 15 follow-up run records. Both share a two-layer edge-feature GIN implemented with GINEConv, hidden width {hp['n_hidden']}, and a classifier with widths 198, 50, 25 and 2. The classifier dropout probability is {hp['final_dropout']}; the slide rounds it to four decimals. Adam uses learning rate {hp['lr']} and default zero weight decay. The batch size is {hp['batch_size']} target transactions, not graph nodes. Two-hop neighbor sampling uses up to 100 neighbors at each hop. Weighted cross-entropy uses class weights {hp['w_ce'][0]} for legitimate transfers and {hp['w_ce'][1]} for laundering. These values are fixed within and across the two studies, while the supplied input slots and evaluation protocol differ. The original experiment has five feature cells and seeds zero through four, giving 25 CPU runs of five epochs each. Its reported checkpoint maximizes validation F1 over zero-based epochs one to four; the first epoch, indexed zero, is excluded from this selection. Its input width varies by cell, scaling is computed separately within each cumulative split graph, and dropout and batch statistics stay active during scoring. The follow-up has three cells and seeds fifteen through nineteen, giving 15 CUDA runs on NVIDIA GeForce RTX 3090 GPUs, one GPU per training process. The submitted eight-hour batch uses four GPUs in parallel. It uses eleven matched input slots, train-only shared port/count scaling, evaluation-mode scoring and fixed seed-specific evaluation sampling. Training runs for at least twenty and at most thirty epochs, with patience ten and a validation-AP progress threshold of 0.001. The selected checkpoint is the exact maximum validation AP, independently of the patience progress threshold; ties select the earliest checkpoint. Stopping does not demonstrate convergence. Both studies select the decision cutoff by maximum validation F1 at the chosen checkpoint. The follow-up runtime manifest records Python 3.12.16, PyTorch 2.8.0+cu126 and PyG 2.6.1. HI-Small contains 5,078,345 transfers, 515,088 accounts and 5,177 laundering labels. The whole-day cut points are six and eight. Historical features follow timestamp order with a label-independent fixed order for ties. Both studies use cumulative transductive graphs, so this is not an online-causal deployment evaluation. The next page shows which feature combinations are compared.")


def savefig(fig, name):
    for ext in ("png", "pdf", "svg"):
        fig.savefig(FIGURES / f"{name}.{ext}", dpi=260, bbox_inches="tight", facecolor="#"+BG)
    plt.close(fig)


def definition_figures():
    """Illustrate feature definitions with a fixed, fully worked example."""
    fig, ax = plt.subplots(figsize=(11.8, 2.05), layout="constrained")
    ax.axis("off")
    rows = [["1. S → A", "0", "0", "0", "Yes"],
            ["2. S → B", "1", "1", "1", "Yes"],
            ["3. S → A", "2", "2", "0", "No: repeat"],
            ["4. S → C", "3", "2", "2", "Yes"]]
    labels = ["Current transfer", "Earlier outgoing\ntransfers", "Earlier distinct\nreceivers", "S's outgoing port\nfor this receiver", "Pair new?"]
    table = ax.table(cellText=rows, colLabels=labels, cellLoc="center", loc="center",
                     colWidths=[.19, .20, .20, .25, .16], bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(13)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#"+GRID)
        cell.set_linewidth(.6)
        cell.set_facecolor("#"+BG if row % 2 else "#F1F0EB")
        cell.get_text().set_color("#"+INK)
        if row == 0:
            cell.set_height(.28)
            cell.set_facecolor("#E7EBEE")
            cell.get_text().set_fontweight("semibold")
            cell.get_text().set_fontsize(12)
        elif col in (1, 2):
            cell.get_text().set_color("#"+BLUE)
        elif col == 3:
            cell.get_text().set_color("#"+TEAL)
            cell.get_text().set_fontweight("semibold")
    savefig(fig, "example1_counts_vs_ports")

    fig, ax = plt.subplots(figsize=(11.8, 3.1), layout="constrained")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    ax.text(.5, .94, "Earlier transfers, in order:  S → A,  S → B,  D → B,  S → A",
            ha="center", va="center", fontsize=13)
    ax.text(.01, .72, "Sender S", fontsize=17, fontweight="semibold")
    ax.text(.64, .72, "Receiver B", fontsize=17, fontweight="semibold")
    ax.annotate("", xy=(.60, .74), xytext=(.36, .74),
                arrowprops={"arrowstyle": "->", "color": "#"+INK, "lw": 1.7})
    ax.text(.48, .60, "Current transfer: S → B", ha="center", fontsize=12)
    for x, lines in [(.01, ["Earlier outgoing transfers: 3", "Earlier distinct receivers: 2"]),
                     (.64, ["Earlier incoming transfers: 2", "Earlier distinct senders: 2"])]:
        ax.text(x, .43, lines[0], fontsize=14, color="#"+BLUE)
        ax.text(x, .28, lines[1], fontsize=14, color="#"+BLUE)
    ax.text(.01, .07, "Outgoing port for B: 1", fontsize=14, color="#"+TEAL)
    ax.text(.64, .07, "Incoming port for S: 0", fontsize=14, color="#"+TEAL)
    savefig(fig, "example2_four_counts_two_ports")


def figures(original, followup):
    for path in (REPO / "presentation/representation-study/fonts").glob("*.ttf"):
        font_manager.fontManager.addfont(path)
    plt.rcParams.update({"font.family": "Inter", "font.size": 12, "axes.titlesize": 13,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.facecolor": "#"+BG, "figure.facecolor": "#"+BG,
                         "text.color": "#"+INK, "axes.labelcolor": "#"+INK,
                         "xtick.color": "#"+MUTED, "ytick.color": "#"+MUTED,
                         "axes.edgecolor": "#"+GRID, "pdf.fonttype": 42, "svg.fonttype": "none"})
    definition_figures()
    full = original["subsets"]["all"]
    # Figure 1: original factorial, same-seed pairs; no new intervals.
    fig, ax = plt.subplots(figsize=(7.4, 3.45), layout="constrained")
    groups = [(0, "base", "Base", MUTED), (1, "ports", "Ports", BLUE),
              (3, "counts", "Counts", MUTED), (4, CP, "Counts +\nPorts", BLUE)]
    for left, right in (("base", "ports"), ("counts", CP)):
        x = [0, 1] if left == "base" else [3, 4]
        for a, b in zip(full["cells"][left]["per_seed"], full["cells"][right]["per_seed"]):
            ax.plot(x, [a, b], color="#"+GRID, lw=1, zorder=1)
    for x, arm, label, ink in groups:
        vals = full["cells"][arm]["per_seed"]
        ax.scatter([x]*5, vals, color="#"+ink, s=30, zorder=3)
        mean = full["cells"][arm]["mean"]
        ax.plot([x-.15, x+.15], [mean, mean], color="#"+ink, lw=3)
        ax.text(x, max(vals)+4, f"{mean:.2f}", ha="center", color="#"+ink, fontsize=12)
    ax.set(xticks=[0, 1, 3, 4], xticklabels=[x[2] for x in groups], ylim=(0, 55),
           ylabel="Test F1 (%)", xlim=(-.5, 4.5))
    ax.grid(axis="y", alpha=.2)
    savefig(fig, "figure1_counts_and_ports")

    # Figure 2: supplementary representation comparison.
    fig, ax = plt.subplots(figsize=(7.4, 3.45), layout="constrained")
    arms = ["counts", CP, CN]
    for seed in range(5):
        ax.plot(range(3), [full["cells"][a]["per_seed"][seed] for a in arms], color="#"+GRID, lw=1)
    for x, arm, ink in zip(range(3), arms, (MUTED, BLUE, TEAL)):
        vals = full["cells"][arm]["per_seed"]
        mean = full["cells"][arm]["mean"]
        ax.scatter([x]*5, vals, color="#"+ink, s=30, zorder=3)
        ax.plot([x-.11, x+.11], [mean, mean], color="#"+ink, lw=3)
        ax.text(x, max(vals)+4, f"{mean:.2f}", ha="center", color="#"+ink, fontsize=12)
    ax.set(xticks=range(3), xticklabels=["Counts", "Counts + Ports", "Counts + flag"],
           ylim=(0, 65), ylabel="Test F1 (%)", xlim=(-.4, 2.4))
    ax.grid(axis="y", alpha=.2)
    savefig(fig, "figure2_first_contact_flag")

    # Figure 3: a descriptive decomposition of saved counts, not new inference.
    first = original["subsets"]["first_contact"]
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 3.35), layout="constrained", gridspec_kw={"width_ratios": [1, 1.15]})
    recall = {a: np.array([r["tp"] for r in first["cells"][a]["confusion_per_seed"]]) / first["n_laundering"] * 100 for a in (CP, CN)}
    for a, b in zip(recall[CP], recall[CN]):
        axes[0].plot([0, 1], [a, b], color="#"+GRID, lw=1)
    for x, a, ink in ((0, CP, BLUE), (1, CN, TEAL)):
        axes[0].scatter([x]*5, recall[a], color="#"+ink, s=28)
        mean = recall[a].mean()
        axes[0].plot([x-.13, x+.13], [mean, mean], color="#"+ink, lw=3)
        axes[0].text(x, 94, f"Mean {mean:.1f}%", ha="center", color="#"+ink)
    axes[0].set(xticks=[0, 1], xticklabels=["Counts + Ports", "Counts + flag"],
                xlim=(-.4, 1.4), ylim=(0, 105), ylabel="Recall (%)", title="(a) First-contact laundering")
    changes = {}
    for x, subset in enumerate(("first_contact", "repeat")):
        cells = original["subsets"][subset]["cells"]
        a, b = [cells[arm]["confusion_per_seed"] for arm in (CP, CN)]
        values = np.array([bb["tp"]-aa["tp"] for aa, bb in zip(a, b)])
        mean = values.mean()
        axes[1].scatter(x+np.linspace(-.10, .10, 5), values, color="#"+MUTED, alpha=.65, s=25)
        axes[1].scatter(x, mean, color="#"+TEAL, marker="D", s=48, zorder=3)
        axes[1].annotate(f"Mean {mean:+.1f}", (x, mean), xytext=(12, 8), textcoords="offset points", fontsize=12)
        changes[subset] = {"tp_difference_per_seed": values.tolist(), "mean_tp_difference": float(mean),
                           "fp_difference_per_seed": [bb["fp"]-aa["fp"] for aa, bb in zip(a,b)]}
    axes[1].axhline(0, ls="--", color="#"+GRID)
    axes[1].set(xticks=[0, 1], xticklabels=["First contact", "Repeat"], xlim=(-.35, 1.6),
                ylim=(-85, 530), ylabel="Change in true-positive count", title="(b) Counts + flag minus Counts + Ports")
    for ax in axes:
        ax.grid(axis="y", alpha=.2)
    savefig(fig, "figure3_where_detection_improves")

    # Figure 4: retain the predeclared follow-up, including AP.
    effect = followup["selections"]["best_validation"]["subsets"]["all"]["effects"]["explicit_addition"]
    fig, ax = plt.subplots(figsize=(7.0, 2.8), layout="constrained")
    for y, metric in enumerate(("f1", "ap")):
        e = effect[metric]
        mean = e["mean"]; lo, hi = e["ci95"]
        ax.scatter(e["per_seed"], y+np.linspace(-.08, .08, 5), s=25, color="#"+MUTED, alpha=.6)
        ax.errorbar(mean, y, xerr=[[mean-lo], [hi-mean]], fmt="D", color="#"+BLUE, lw=2, capsize=4, ms=6)
        ax.text(-26, y+.26, f"{mean:+.2f} [{lo:+.2f}, {hi:+.2f}]", fontsize=12)
    ax.axvline(0, ls="--", color="#"+GRID)
    ax.set(yticks=[0, 1], yticklabels=["F1", "AP"], ylim=(1.55, -.4), xlim=(-27, 15),
           xlabel="CP + flag minus CP (percentage points)")
    ax.grid(axis="x", alpha=.2)
    savefig(fig, "figure4_addition_followup")
    (HERE / "figure_data.json").write_text(json.dumps({"status": "saved-result plotting and descriptive counts only",
        "original_summary_sha256": hashlib.sha256((REPO/"results/summary.json").read_bytes()).hexdigest(),
        "followup_summary_sha256": hashlib.sha256((REPO/"results/representation_8h/summary.json").read_bytes()).hexdigest(),
        "first_contact_recall_percent": {a:v.tolist() for a,v in recall.items()}, "changes": changes}, indent=2)+"\n")


def main():
    FIGURES.mkdir(exist_ok=True)
    original = json.loads((REPO/"results/summary.json").read_text())["selections"]["best_validation"]
    followup = json.loads((REPO/"results/representation_8h/summary.json").read_text())
    figures(original, followup)
    prs = Presentation(SOURCE)
    s = list(prs.slides)
    # Keep the supplied diagrams and the user's visual identity.
    replace_text(s[0], "What Do Port\nNumbers Add?", "Beyond\nCounterparty Counts")
    replace_text(s[0], "Multigraph GNNs for anti-money laundering", "Ports and Pair Novelty in AML Graph Learning")
    notes(s[0], "This project starts from Egressy and colleagues' finding that port numbering improves AML graph learning. I ask whether ports still help when account-level counts are provided, whether a simple first-contact flag helps, and where the improvement appears. The main finding is straightforward: under our original protocol, replacing ports with the flag identifies more laundering on first-contact transfers. I will show the controlled comparisons and then a separate follow-up. All results refer to HI-Small.")
    notes(s[1], s[1].notes_slide.notes_text_frame.text.replace("What gives laundering away is the shape of the flows.", "The shape of the flows can provide evidence; legitimate activity can also form these patterns, so a shape is not itself proof of laundering."))
    notes(s[3], s[3].notes_slide.notes_text_frame.text.replace("Together they can, in theory, detect any pattern in a directed multigraph.", "Under the paper's theoretical assumptions, sufficiently expressive GNNs with all three adaptations can detect any directed subgraph pattern. This is not a guarantee about our particular two-layer trained model."))
    clear(s[4])
    header(s[4], "Feature definitions", "Counts measure activity; ports label counterparties", "Example: S sends to A, then B, then A again, then C.")
    text(s[4], "Counts: historical totals", .89, 2.48, 5.55, .35, 19, ink=BLUE, bold=True)
    text(s[4], "How many transfers has S sent?\nHow many different receivers has S paid?", .89, 2.93, 5.55, .78, 18)
    text(s[4], "Port: a local counterparty label", 6.9, 2.48, 5.55, .35, 19, ink=TEAL, bold=True)
    text(s[4], "S labels receivers 0, 1, 2, … at first contact.\nThe same receiver keeps the same label.", 6.9, 2.93, 5.55, .78, 18)
    picture(s[4], "example1_counts_vs_ports", .89, 3.92, 11.6, 1.98,
            "Four transfers S to A, B, A and C. Earlier transfer counts are 0,1,2,3; distinct receiver counts 0,1,2,2; outgoing ports 0,1,0,2.")
    text(s[4], "On the fourth transfer: 3 earlier payments, 2 earlier receivers, and port 2 for the new receiver C.", .89, 6.05, 11.6, .37, 17, serif=True)
    text(s[4], "Counts exclude the current transfer. Ports start at 0 and are local to each account; they are not global account IDs.", .89, 6.55, 11.6, .33, 12, ink=MUTED)
    notes(s[4], "Count means a historical total. We use two types on each side of a transfer: the number of earlier transfers and the number of earlier distinct counterparties. Port means a local label for a counterparty, assigned in first-contact order starting at zero. It is not a network-service port or a global account ID. In the table, S pays A, B, A, then C. Before the third transfer, S has sent two transfers to two receivers; A keeps port zero because S has paid A before. Before the fourth transfer, S has sent three transfers but has seen only two receivers, A and B. C is new, so it receives port two. This fourth row makes the difference between transfer count and distinct-counterparty count explicit. Counts summarize how much activity there has been; a port labels the particular counterparty involved now. We calculate counts before the current transaction in the fixed timestamp and tie order. Next, I show both sides of one transaction and all six feature values used by the models.")
    replace_text(s[5], s[5].shapes[1].text, "What do ports add beyond account counts?\nCan a first-contact flag capture useful pair history?")
    replace_text(s[5], "QUESTION 1 · EXPERIMENT 1", "QUESTION 1 · FACTORIAL")
    question_one = replace_text(s[5], "Do counts remove the port gain?", "Do ports still help when counts are provided?")
    question_one.height = Inches(.85)
    replace_text(s[5], "QUESTION 2", "QUESTION 2 · SUPPLEMENTARY")
    question_two = replace_text(s[5], "Does a one-bit new-pair flag help beyond counts?", "Does a first-contact flag improve detection beyond counts?")
    question_two.height = Inches(1.08)
    replace_text(s[5], "QUESTION 3", "QUESTION 3 · ERROR ANALYSIS")
    question_three = replace_text(s[5], "Does the flag still help a model that keeps its ports?", "Where are the extra detections when the flag replaces ports?")
    question_three.height = Inches(1.08)
    notes(s[5], "There are three steps in the argument. First: do ports still help when counts are provided? The relevant contrast is Counts plus Ports minus Counts. We also compare that residual gain with Ports minus Base, as in the original factorial design. Second: does a first-contact flag improve detection beyond counts? This compares Counts plus flag with Counts; neither arm has ports. The supplementary flag model is also compared with Counts plus Ports, establishing the replacement comparison that leads into the third question. Third: where are the extra detections when the flag replaces ports? Both models keep counts, and we describe the change in true-positive counts on first-contact and repeat transfers separately. This third question locates the observed detections; it does not identify a causal internal mechanism. These are not three newly declared primary tests: the flag model is supplementary and the error decomposition is descriptive. The completed follow-up that adds the flag while retaining ports is a separate comparison under a different protocol.")
    configuration_slide(s[6])
    replace_text(s[7], s[7].shapes[30].text, "Five seeds × five epochs per input set. Nominal paired-seed 95% t-intervals describe variation on this fixed dataset.")
    text(s[7], "Original protocol: split-specific normalization; dropout and batch statistics remain active during scoring.\nBoth studies use cumulative transductive graphs. The follow-up changes scaling and scoring.", .89, 6.02, 11.6, .60, 12, ink=MUTED)
    notes(s[7], "The original experiment has a two-by-two design: Base, Counts, Ports and Counts plus Ports. The four counts are earlier outgoing transfer and distinct-receiver counts for the sender, and earlier incoming transfer and distinct-sender counts for the receiver. We compare the port gain without and with these counts. The original named estimand is one minus residual port gain divided by the port gain without counts; the additive contrasts make it easier to interpret. Counts plus flag is supplementary. Each model has five seeds and a five-epoch budget. The original protocol normalizes separately in each cumulative split graph and leaves dropout and batch statistics active at scoring. Its checkpoints maximize validation F1 over the declared eligible epochs. This is a fixed-budget, transductive comparison; the intervals quantify training and scoring seed variation, not uncertainty across banks. The supplementary intervals are unadjusted. The later protocol changes these evaluation choices and is reported separately.")

    clear(s[8]); header(s[8], "Results · Question 1", "Do ports still help when counts are provided?", "Yes. Ports add 14.91 F1 points beyond counts (95% CI [10.11, 19.71]).")
    picture(s[8], "figure1_counts_and_ports", .89, 2.35, 7.35, 3.25, "Paired seed F1 scores for Base, Ports, Counts and Counts plus Ports.")
    text(s[8], "Without counts, ports add 7.48 F1 points.\n95% CI [2.96, 12.00]", 8.6, 2.75, 3.83, 1.05, 20, serif=True, ink=BLUE)
    text(s[8], "With counts, ports still add 14.91 points.\n95% CI [10.11, 19.71]", 8.6, 4.05, 3.83, 1.05, 20, serif=True, ink=BLUE)
    text(s[8], "Figure 1. Points are individual seeds; short bars are means; lines connect paired seeds.", .89, 5.8, 11.6, .35, 12, ink=MUTED)
    text(s[8], "The planned share-explained interval is −512.7% to +8.4% (Fieller 95%).\nIt does not support these counts explaining most of the port gain under this protocol.", .89, 6.25, 11.6, .48, 12, ink=MUTED)
    notes(s[8], "Do ports still help when counts are provided? Yes, in this original protocol. The right-hand pair compares Counts plus Ports, at mean F1 39.57, with Counts, at 24.66. Adding ports therefore improves F1 by 14.91 points, with interval 10.11 to 19.71; every paired seed has a positive difference. The left-hand pair is the reference port gain without counts: 7.48 points. The 14.91 is the effect of adding ports to a model with counts, not the effect of adding counts. A direct replacement question would instead compare Counts with Ports, which is a different contrast. Our conclusion is that ports retain predictive value after the four counts are supplied. This does not establish that counts are useless or that the two feature sets have a statistically significant interaction; the interaction interval crosses zero. The original planned share-explained Fieller interval remains minus 512.7 to plus 8.4 percent, conditional on this protocol and statistical model. Next, what information do the count scalars leave out?")
    replace_text(s[9], "METHODOLOGY", "INTERPRETATION")
    replace_text(s[9], "This suggests a direct test: give the Counts model that one fact, as a single bit.", "Test a simple flag: 1 for a first observed pair, 0 for a repeated pair.")
    notes(s[9], "The account counts can be identical even when the current pair is new in one case and repeated in another. Here u has paid a and b, while d has paid c. The three possible next transfers from u have identical count vectors but different ports. Comparing a port with its corresponding earlier distinct count determines whether the pair is new. With d for the distinct count and p for the zero-based port, d minus p is zero for a first contact and positive for a repeat. On repeats, d minus p minus one counts counterparties first encountered after this relationship. That explains the temporal meaning of the encoding; it does not prove which computation the trained classifier uses. We test the simple first-contact bit as a supplementary input. Does adding this flag improve detection beyond counts alone?")

    clear(s[10]); header(s[10], "Results · Question 2", "Does a first-contact flag improve detection beyond counts?", "Yes. The flag adds 24.33 F1 points beyond counts (95% CI [21.47, 27.19]).")
    picture(s[10], "figure2_first_contact_flag", .89, 2.3, 7.35, 3.25, "Paired F1 for Counts, Counts plus Ports and Counts plus first-contact flag.")
    text(s[10], "Adding the flag to Counts improves F1 by 24.33 points.\n95% CI [21.47, 27.19]", 8.6, 2.6, 3.83, 1.35, 20, serif=True, ink=TEAL)
    text(s[10], "Replacing ports with the flag improves F1 by 9.42 points.\n95% CI [5.73, 13.11]", 8.6, 4.15, 3.83, 1.35, 20, serif=True, ink=TEAL)
    text(s[10], "Figure 2. Supplementary flag comparison; original five-epoch protocol. Points show five paired seeds.", .89, 5.8, 11.6, .4, 12, ink=MUTED)
    text(s[10], "Flag versus Counts: days 8–9 F1 +18.19 [17.31, 19.06]; full-test AP +28.89 [21.05, 36.74].\nThese sensitivity views reuse the same models and data; intervals are nominal and unadjusted.", .89, 6.24, 11.6, .5, 12, ink=MUTED)
    notes(s[10], "Does a first-contact flag improve detection beyond counts? In the original experiment, yes. To answer this, compare Counts plus flag with Counts. Neither model has ports. Their mean F1 scores are 48.99 and 24.66, so adding the flag improves F1 by 24.33 points, with a nominal paired interval of 21.47 to 27.19. The benefit remains positive on days eight and nine and on average precision. This flag model is supplementary. The same figure provides a second, distinct comparison: Counts plus flag versus Counts plus Ports, whose mean F1 is 39.57. Keeping counts and replacing ports with the flag improves F1 by 9.42 points, with interval 5.73 to 13.11. That replacement comparison leads to Question 3: where are the extra detections when the flag replaces ports? The later follow-up instead keeps ports and adds the flag; it is a separate question.")

    # Insert one evidence slide immediately after the original flag result.
    extra = prs.slides.add_slide(s[10].slide_layout)
    clear(extra)
    note_body = deepcopy(s[10].notes_slide.notes_placeholder._element)
    note_body.xpath(".//p:cNvPr")[0].set("id", "100")
    extra.notes_slide._element.spTree.insert_element_before(note_body, "p:extLst")
    slide_id = prs.slides._sldIdLst[-1]
    prs.slides._sldIdLst.remove(slide_id)
    prs.slides._sldIdLst.insert(11, slide_id)
    header(extra, "Error analysis · Question 3", "Where are the extra detections when the flag replaces ports?", "On first contacts: laundering recall rises from 47.1% to 64.0%.")
    picture(extra, "figure3_where_detection_improves", .89, 2.35, 11.6, 3.1, "First-contact recall and descriptive paired changes in true-positive counts by first-contact or repeat status.")
    text(extra, "Figure 3. Counts + flag versus Counts + Ports; original five-epoch protocol.\nPoints show paired seeds and means. Count changes are descriptive, not a decomposition of F1.", .89, 5.57, 11.6, .44, 12, ink=MUTED)
    text(extra, "First-contact F1 improves by 11.40 points [7.54, 15.26].", .89, 6.08, 11.6, .38, 21, serif=True, ink=TEAL)
    text(extra, "Mean first-contact false alerts: 903.2 → 903.4; seed changes vary. Each model uses its own validation-selected threshold.", .89, 6.56, 11.6, .3, 11.5, ink=MUTED)
    notes(extra, "Where are the extra detections when the flag replaces ports? They are on first-contact transfers. Both models retain the four counts; the comparison is Counts plus flag minus Counts plus Ports, rather than Counts plus flag minus Counts. On first-contact transfers, Counts plus Ports finds 623.8 laundering transactions on average; Counts plus flag finds 848.4. Recall rises from 47.08 to 64.03 percent, an increase of 16.95 percentage points. Every seed detects more first-contact positives. First-contact F1 rises by 11.40 points, with a nominal interval of 7.54 to 15.26. The right panel locates the net increase: first-contact true positives increase by 224.6, while repeat true positives decrease by 7.4, giving a total net increase of 217.2. These are mean count differences, not the number of newly discovered cases or a decomposition of F1. First-contact false alerts average 903.2 versus 903.4, but the individual changes range from minus 435 to plus 506, and thresholds differ. We do not claim equal workload or proven unchanged false positives. The repeat-pair F1 difference is minus 4.05 with interval minus 12.03 to plus 3.93, so no separate repeat benefit is established. This is descriptive localization of the observed detections, not proof of an internal causal mechanism. One completed follow-up checks whether the flag also helps when ports are retained.")

    clear(s[11]); header(s[11], "Controlled follow-up", "Keeping ports: no additional flag benefit was established", "A separate protocol with five new paired seeds and 20–30 training epochs.")
    picture(s[11], "figure4_addition_followup", .89, 2.65, 7.1, 2.85, "Prespecified CPN minus CP F1 and AP effects with paired-seed intervals.")
    text(s[11], "A has Counts + Ports.\nB has Counts + Ports + flag.", 8.35, 2.6, 4.08, .9, 20, serif=True)
    text(s[11], "Both use 11 input slots, train-only scaling and evaluation-mode scoring.", 8.35, 3.77, 4.08, 1.0, 18)
    text(s[11], "Both intervals cross zero. A positive addition benefit is not established.", 8.35, 4.95, 4.08, 1.0, 18, ink=BLUE)
    text(s[11], "Figure 4. Mean and nominal paired-seed 95% intervals; small dots show individual differences.", .89, 5.95, 11.6, .35, 12, ink=MUTED)
    text(s[11], "No Counts-only arm: this does not re-test the +24.33 result. The two protocols are not pooled.\nThe third arm, Counts + flag, is retained in the full report; its secondary contrasts are inconclusive.", .89, 6.35, 11.6, .47, 12, ink=MUTED)
    notes(s[11], "This completed follow-up asks a different question: does an explicit flag help when counts and ports are both retained? Raw counts and ports already determine the flag, so this tests an explicit representation of available information, not added information. All arms have eleven slots, matched initialization and parameter count, training-only shared count-port scaling, and evaluation-mode scoring. Runs use new seeds fifteen to nineteen and twenty to thirty epochs with validation stopping. The exact highest validation-AP checkpoint is selected, followed by a validation-F1 threshold. The paired F1 change is minus 7.21 points with interval minus 15.46 to plus 1.03; AP is minus 4.49 with interval minus 19.11 to plus 10.13. A positive addition benefit is not established, nor are harm or equivalence proved. Nine of fifteen runs reached the cap, so stopping is not convergence. This protocol has no Counts-only arm and cannot directly re-test the plus 24.33 contrast. Its third arm, Counts plus flag, is included in the full report, and its secondary contrasts are unresolved. The protocol changed several things, so differences between studies cannot be attributed only to training duration. I now return to the positive findings established in the original experiment.")

    conclusion_layout(s[12])
    notes(s[12], "I close with three concrete findings. First, account-history counts do not remove the port benefit. After all four counts are supplied, ports still improve F1 by 14.91 points. Second, under the original experimental protocol, a first-contact flag has clear predictive value. Adding it to Counts improves F1 by 24.33 points, and replacing ports with the flag, while retaining counts, improves F1 by 9.42 points. Third, we locate the additional detections: laundering recall on first-contact transfers rises from 47.1 to 64.0 percent, and every one of the five seeds detects more of these laundering transfers. Our research contribution is to distinguish account-level activity from the history of the specific account pair through controlled feature comparisons, and to quantify both the predictive value of a simple relationship flag and the transaction group where detection improves. For AML feature design, the implication is to consider whether the current sender has previously paid this receiver alongside cumulative transaction and counterparty counts. This study provides evidence for that relationship feature on the current benchmark and protocol; the observed patterns are not proof of laundering by themselves. The flag comparison is supplementary, the detection breakdown is descriptive, and the completed follow-up did not establish an additional benefit when ports were retained. These boundaries do not change the three reported findings. Thank you; I welcome questions.")

    replace_text(s[13], "What do port numbers add?", "Beyond Counterparty Counts")
    text(s[13], "4", .89, 4.15, .33, .35, 20, serif=True, ink=BLUE)
    text(s[13], "Reference implementation: IBM/Multi-GNN — github.com/IBM/Multi-GNN", 1.33, 4.2, 11.1, .5, 14)
    text(s[13], "Project code, frozen protocols, results and full analysis:\ngithub.com/Yuchen-Fu/COMP9501", 1.33, 5.15, 11.1, .8, 16)
    notes(s[13], "The first paper motivates directed multigraph port numbering and its theoretical role. The second supplies the synthetic AML benchmark; the third establishes the GIN framework. The repository links contain the model conventions, project code, both completed experiments and full statistical scope. The research-result figures were generated in Python directly from saved JSON, with no new training or hypothesis tests. There are 25 original runs and 15 follow-up runs. The first-contact error decomposition is descriptive; it is not a new causal attribution or multiplicity-controlled finding.")

    # Insert an explicit four-count / two-port example before the questions.
    feature_slide = prs.slides.add_slide(s[4].slide_layout)
    clear(feature_slide)
    note_body = deepcopy(s[4].notes_slide.notes_placeholder._element)
    note_body.xpath(".//p:cNvPr")[0].set("id", "100")
    feature_slide.notes_slide._element.spTree.insert_element_before(note_body, "p:extLst")
    slide_id = prs.slides._sldIdLst[-1]
    prs.slides._sldIdLst.remove(slide_id)
    prs.slides._sldIdLst.insert(5, slide_id)
    header(feature_slide, "Feature definitions", "Each transfer has four counts and two ports", "The sender records outgoing history; the receiver records incoming history.")
    picture(feature_slide, "example2_four_counts_two_ports", .89, 2.45, 11.6, 2.9,
            "Earlier transfers S to A, S to B, D to B, S to A. The next S to B has sender counts 3 and 2, receiver counts 2 and 2, incoming port 0 and outgoing port 1.")
    text(feature_slide, "Counts = [3, 2, 2, 2]", .89, 5.56, 5.55, .4, 21, serif=True, ink=BLUE)
    text(feature_slide, "Ports = [0, 1]  (incoming, outgoing)", 6.9, 5.56, 5.55, .4, 21, serif=True, ink=TEAL)
    text(feature_slide, "Novelty asks: has S paid B before? Yes → first-contact flag = 0 (repeat).", .89, 6.12, 11.6, .42, 19, serif=True)
    text(feature_slide, "Raw values before scaling. History starts at the beginning of the observed dataset; first contact means first observed directed pair.", .89, 6.65, 11.6, .28, 11.5, ink=MUTED)
    notes(feature_slide, "For each current sender-to-receiver transfer, Counts supplies four numbers in this order: the sender's earlier outgoing transfer count, its earlier distinct-receiver count, the receiver's earlier incoming transfer count, and its earlier distinct-sender count. Ports supplies two local labels: the receiver's incoming label for this sender and the sender's outgoing label for this receiver. These are different numbering lists. In the worked history S to A, S to B, D to B, S to A, S has sent three times to two receivers. B has received twice from two senders. The next transfer S to B therefore has Counts [3,2,2,2]. S met A first and B second, so its outgoing port for B is one. B received from S first and D second, so its incoming port for S is zero. Ports are stored in incoming-then-outgoing order, [0,1], matching the code. Counts plus Ports supplies all six values, alongside the transaction's own fields. Novelty is a separate one-bit flag: one for the first observed directed pair and zero for a repeated pair; it is zero here. The raw port equals the corresponding earlier distinct count on first contacts and is smaller on repeats. These are raw values before normalization. With the feature definitions clear, I can now state the research questions.")

    # Renumber every actual page and export the complete English speaking notes.
    notes_md = ["# Beyond Counterparty Counts — speaker notes", "", f"{len(prs.slides)} slides, including cover and references. No backup section.", ""]
    for i, slide in enumerate(prs.slides, 1):
        if i > 1:
            footer = [sh for sh in slide.shapes if sh.has_text_frame and sh.text.strip().isdigit() and sh.top > Inches(6.7)]
            for sh in footer:
                sh._element.getparent().remove(sh._element)
            dark = i in (7, 15)
            text(slide, str(i), 12.25, 6.94, .35, .23, 11, ink="CCD5DC" if dark else MUTED)
        notes_md += [f"## Slide {i}", "", slide.notes_slide.notes_text_frame.text, ""]
    prs.core_properties.title = "Beyond Counterparty Counts: Ports and Pair Novelty in AML Graph Learning"
    prs.core_properties.subject = "Two completed studies; the first-contact detection finding and its scope"
    target = HERE / "Beyond_Counterparty_Counts_FINAL.pptx"
    prs.save(target)
    (HERE / "SPEAKER_NOTES.md").write_text("\n".join(notes_md))
    # Also deliver the conclusion alone so it can replace a page in another deck.
    single = Presentation(target)
    conclusion_index = 14
    conclusion_slide = single.slides[conclusion_index]
    for sh in list(conclusion_slide.shapes):
        if sh.has_text_frame and sh.text.strip().isdigit() and sh.top > Inches(6.7):
            sh._element.getparent().remove(sh._element)
    for index in reversed(range(len(single.slides))):
        if index == conclusion_index:
            continue
        slide_id = single.slides._sldIdLst[index]
        single.part.drop_rel(slide_id.rId)
        single.slides._sldIdLst.remove(slide_id)
    single.core_properties.title = "Conclusion: three findings about counts and pair history"
    single.save(HERE / "Conclusion_Three_Findings.pptx")
    print(f"Saved {target} ({len(prs.slides)} slides), a one-slide conclusion, four result figures, two definition figures and English notes.")


if __name__ == "__main__":
    main()
