#!/usr/bin/env python3
"""Build the slide deck from slides.json as PowerPoint, HTML and PDF.

Figures are the PNGs exported by the plot scripts in this folder. This script
only places text, images and page rules; one layout drives all three outputs.
"""

from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import html
import json
import math
from pathlib import Path

from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent
AUTHOR = "COMP9501 research project"
W, H = 1600, 900
NAVY = "#203647"
TEAL = "#26786F"
MUTED = "#59646D"
LIGHT = "#D8DEE1"
WHITE = "#FFFFFF"
FONT = "Arial"
FONT_ROOT = Path("/usr/share/fonts/truetype/liberation")


def font(size, bold=False, serif=False):
    family = "LiberationSerif" if serif else "LiberationSans"
    weight = "Bold" if bold or serif else "Regular"
    return ImageFont.truetype(str(FONT_ROOT / f"{family}-{weight}.ttf"), round(size))


def wrap(text, width, size, bold=False, serif=False):
    f = font(size, bold, serif)
    lines = []
    for paragraph in str(text).split("\n"):
        current = ""
        for word in paragraph.split():
            proposed = f"{current} {word}".strip()
            if current and f.getlength(proposed) > width:
                lines.append(current)
                current = word
            else:
                current = proposed
        lines.append(current)
    return lines


class Canvas:
    def __init__(self):
        self.items = []
        self.warnings = []

    def rect(self, x, y, w, h, fill=WHITE, stroke=None, radius=0, sw=1):
        self.items.append(
            dict(kind="rect", x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, radius=radius, sw=sw)
        )

    def line(self, x1, y1, x2, y2, color=LIGHT, sw=1):
        self.items.append(
            dict(kind="line", x1=x1, y1=y1, x2=x2, y2=y2, color=color, sw=sw, arrow=False)
        )

    def image(self, path, x, y, w, h, alt=""):
        path = Path(path)
        with Image.open(path) as source:
            factor = min(w / source.width, h / source.height)
            fw, fh = source.width * factor, source.height * factor
        self.items.append(
            dict(
                kind="image", path=path, x=x + (w - fw) / 2, y=y + (h - fh) / 2, w=fw, h=fh, alt=alt
            )
        )

    def text(
        self,
        text,
        x,
        y,
        w,
        size=34,
        color=NAVY,
        bold=False,
        align="left",
        line_height=1.22,
        serif=False,
    ):
        lines = wrap(text, w, size, bold, serif)
        for i, line in enumerate(lines):
            self.items.append(
                dict(
                    kind="text",
                    text=line,
                    x=x,
                    y=y + i * size * line_height,
                    w=w,
                    size=size,
                    color=color,
                    bold=bold,
                    align=align,
                    serif=serif,
                )
            )
        bottom = y + len(lines) * size * line_height
        if bottom > 885 or x < 0 or x + w > W:
            self.warnings.append(f"Text outside slide: {text[:70]}")
        return bottom

    def bullets(self, values, x, y, w, size=32, gap=24):
        for value in values:
            self.text("•", x, y, 22, size, TEAL)
            y = self.text(value, x + 30, y, w - 30, size) + gap
        return y - gap

    def header(self, s, index, total):
        self.rect(0, 0, W, H)
        bottom = self.text(s["title"], 94, 69, 1410, 52, NAVY, True, serif=True)
        if bottom > 185:
            self.warnings.append("Title exceeds its reserved area")
        self.line(96, 822, 1504, 822)
        end = self.text(s.get("footer", ""), 96, 842, 1295, 20, MUTED, line_height=1.12)
        if end > 885:
            self.warnings.append("Footer is too long")
        self.text(f"{index} / {total}", 1400, 842, 104, 20, MUTED, align="right")

    def svg(self):
        result = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img">']
        for o in self.items:
            k = o["kind"]
            if k == "rect":
                result.append(
                    f'<rect x="{o["x"]}" y="{o["y"]}" width="{o["w"]}" height="{o["h"]}" fill="{o["fill"]}"/>'
                )
            elif k == "line":
                result.append(
                    f'<line x1="{o["x1"]}" y1="{o["y1"]}" x2="{o["x2"]}" y2="{o["y2"]}" stroke="{o["color"]}" stroke-width="{o["sw"]}"/>'
                )
            elif k == "text":
                anchor = {"left": "start", "center": "middle", "right": "end"}[o["align"]]
                tx = o["x"] + {"left": 0, "center": o["w"] / 2, "right": o["w"]}[o["align"]]
                family = (
                    "Liberation Serif, Georgia, serif"
                    if o["serif"]
                    else "Liberation Sans, Arial, sans-serif"
                )
                result.append(
                    f'<text x="{tx}" y="{o["y"] + o["size"] * 0.88}" font-family="{family}" font-size="{o["size"]}" font-weight="{700 if o["bold"] else 400}" fill="{o["color"]}" text-anchor="{anchor}">{html.escape(o["text"])}</text>'
                )
            elif k == "image":
                encoded = base64.b64encode(o["path"].read_bytes()).decode("ascii")
                result.append(
                    f'<image x="{o["x"]}" y="{o["y"]}" width="{o["w"]}" height="{o["h"]}" href="data:image/png;base64,{encoded}"><title>{html.escape(o["alt"])}</title></image>'
                )
        return "\n".join(result + ["</svg>"])


def figure_caption(c, s, x, y, w):
    return c.text(
        f"Figure {s['figure_number']}. {s['caption']}", x, y, w, 24, MUTED, line_height=1.18
    )


def render_slide(s, index, total):
    c = Canvas()
    c.header(s, index, total)
    if s["visual"] == "title":
        c.items = []
        c.rect(0, 0, W, H)
        c.text("COMP9501  /  AML RESEARCH", 100, 76, 1390, 22, TEAL, True)
        c.text(s["title"], 96, 230, 1400, 72, NAVY, True, serif=True)
        c.text(s["subtitle"], 100, 350, 1290, 39, NAVY)
        c.line(100, 492, 560, 492, TEAL, 2)
        c.text(s["lead"], 100, 548, 1250, 36, NAVY)
        c.text(
            "IBM AML HI-Small · Graph Isomorphism Network · Five-seed experiment",
            100,
            745,
            1390,
            25,
            MUTED,
        )
        c.text(s["footer"], 100, 838, 1390, 20, MUTED)
        return c
    layout = s.get("layout", "text")
    if layout == "wide_figure":
        # Wide evidence gets the full page width; interpretation follows below.
        image_height = s.get("figure_height", 440)
        image_top = s.get("figure_top", 186)
        c.image(ROOT / s["figure"], 96, image_top, 1408, image_height, s["figure_alt"])
        caption_top = image_top + image_height + 18
        end = figure_caption(c, s, 108, caption_top, 1384)
        end = c.bullets(s["bullets"], 108, max(end + 22, 706), 1384, 32, 12)
        if end > 804:
            c.warnings.append(f"Wide-figure interpretation is too long ({end:.0f})")
    elif layout in ("figure_left", "figure_right"):
        # Balanced explanatory pages use a wider prose column and fewer claims.
        image_x, text_x = (96, 995) if layout == "figure_left" else (684, 96)
        image_w, text_w = (820, 509) if layout == "figure_left" else (820, 510)
        image_top = s.get("figure_top", 215)
        c.image(ROOT / s["figure"], image_x, image_top, image_w, 480, s["figure_alt"])
        caption_end = figure_caption(c, s, image_x, image_top + 497, image_w)
        if caption_end > 804:
            c.warnings.append("Balanced-figure caption is too long")
        y = s.get("text_top", 248)
        end = c.bullets(s["bullets"], text_x, y, text_w, 34, 34)
        if s.get("scope"):
            end = c.text(s["scope"], text_x, end + 42, text_w, 28, MUTED)
        if end > 790:
            c.warnings.append(f"Balanced prose is too long ({end:.0f})")
    elif s.get("entries"):
        y = 215
        size = 29 if s["visual"] == "references" else 33
        for entry in s["entries"]:
            c.text(entry["label"], 96, y, 385, 27, TEAL, True)
            end = c.text(entry["text"], 510, y - 2, 985, size)
            y = max(y + 95, end + 46)
        if y - 46 > 800:
            c.warnings.append("Reference/literature entries are too long")
    elif layout == "statement":
        y = 220
        if s.get("lead"):
            y = c.text(s["lead"], 96, y, 1360, 42, TEAL, True, serif=True) + 58
        end = c.bullets(s["bullets"], 110, y, 1315, 36, 34)
        if s.get("scope"):
            end = c.text(s["scope"], 110, max(end + 48, 722), 1315, 28, MUTED)
        if end > 802:
            c.warnings.append("Statement slide is too long")
    else:
        y = 224
        if s.get("lead"):
            y = c.text(s["lead"], 96, y, 1350, 36, TEAL, True, serif=True) + 43
        end = c.bullets(s.get("bullets", []), 110, y, 1315, 36, 38)
        if s.get("scope"):
            y = max(end + 48, 708)
            end = c.text(s["scope"], 110, y, 1315, 28, MUTED)
        if end > 795:
            c.warnings.append(f"Main text is too long ({end:.0f})")
    return c


def to_pptx(slides, canvases, path, title):
    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)
    props = prs.core_properties
    props.title = title
    props.subject = "Counterparty counts and relationship history in AML models"
    props.author = props.last_modified_by = AUTHOR
    props.comments = ""
    props.created = props.modified = datetime.now(timezone.utc).replace(tzinfo=None)
    scale = 16 / W

    def pos(v):
        return Inches(v * scale)

    def rgb(v):
        return RGBColor.from_string(v.lstrip("#"))

    for source, c in zip(slides, canvases):
        sl = prs.slides.add_slide(prs.slide_layouts[6])
        for o in c.items:
            k = o["kind"]
            if k == "rect":
                shape = sl.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE if o["radius"] else MSO_SHAPE.RECTANGLE,
                    pos(o["x"]),
                    pos(o["y"]),
                    pos(o["w"]),
                    pos(o["h"]),
                )
                if o["radius"]:
                    try:
                        shape.adjustments[0] = min(0.15, o["radius"] / max(1, min(o["w"], o["h"])))
                    except (ValueError, IndexError):
                        pass
                shape.fill.solid()
                shape.fill.fore_color.rgb = rgb(o["fill"])
                if o["stroke"]:
                    shape.line.color.rgb = rgb(o["stroke"])
                    shape.line.width = Pt(o["sw"] * 0.6)
                else:
                    shape.line.fill.background()
            elif k == "circle":
                shape = sl.shapes.add_shape(
                    MSO_SHAPE.OVAL,
                    pos(o["x"] - o["r"]),
                    pos(o["y"] - o["r"]),
                    pos(o["r"] * 2),
                    pos(o["r"] * 2),
                )
                shape.fill.solid()
                shape.fill.fore_color.rgb = rgb(o["fill"])
                if o["stroke"]:
                    shape.line.color.rgb = rgb(o["stroke"])
                else:
                    shape.line.fill.background()
            elif k == "line":
                shape = sl.shapes.add_connector(
                    MSO_CONNECTOR.STRAIGHT, pos(o["x1"]), pos(o["y1"]), pos(o["x2"]), pos(o["y2"])
                )
                shape.line.color.rgb = rgb(o["color"])
                shape.line.width = Pt(o["sw"] * 0.6)
                if o["arrow"]:
                    tail = OxmlElement("a:tailEnd")
                    tail.set("type", "triangle")
                    shape.line._get_or_add_ln().append(tail)
            elif k == "text":
                box = sl.shapes.add_textbox(
                    pos(o["x"]), pos(o["y"]), pos(o["w"]), pos(o["size"] * 1.4)
                )
                tf = box.text_frame
                tf.clear()
                tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
                tf.word_wrap = False
                p = tf.paragraphs[0]
                p.text = o["text"]
                p.font.name = "Times New Roman" if o.get("serif") else FONT
                p.font.size = Pt(o["size"] * 0.72)
                p.font.bold = o["bold"]
                p.font.color.rgb = rgb(o["color"])
                p.alignment = {
                    "left": PP_ALIGN.LEFT,
                    "center": PP_ALIGN.CENTER,
                    "right": PP_ALIGN.RIGHT,
                }[o["align"]]
                p.space_before = p.space_after = Pt(0)
            elif k == "image":
                picture = sl.shapes.add_picture(
                    str(o["path"]), pos(o["x"]), pos(o["y"]), width=pos(o["w"]), height=pos(o["h"])
                )
                picture._element.nvPicPr.cNvPr.set("descr", o["alt"])
        notes = source.get("notes", "")
        if isinstance(notes, list):
            notes = "\n\n".join(notes)
        sl.notes_slide.notes_text_frame.text = notes
    prs.save(path)


def write_html(slides, canvases, path, title):
    pages = []
    for i, (s, c) in enumerate(zip(slides, canvases)):
        note = s.get("notes", "")
        note = "\n\n".join(note) if isinstance(note, list) else note
        pages.append(
            f'<section class="slide" id="slide-{i + 1}" aria-label="{html.escape(s["title"])}">{c.svg()}<aside class="notes">{html.escape(note)}</aside></section>'
        )
    content = (
        """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>"""
        + html.escape(title)
        + """</title><style>
*{box-sizing:border-box}body{margin:0;background:#122034;font-family:Arial,sans-serif}.slide{display:none;width:min(100vw,177.777vh);margin:auto;position:relative}.slide.active{display:block}svg{display:block;width:100%;height:auto}.notes{display:none;background:#fff;color:#14273f;white-space:pre-wrap;padding:28px;font-size:20px;line-height:1.5}.show-notes .notes{display:block}nav{display:flex;justify-content:center;gap:16px;padding:12px;color:#fff;align-items:center}button{font:16px Arial;padding:9px 16px;border:0;border-radius:5px;background:#e8eff3;color:#14273f;cursor:pointer}#count{min-width:80px;text-align:center}@page{size:16in 9in;margin:0}@media print{body{background:#fff}.slide{display:block;width:16in;height:9in;page-break-after:always;break-after:page;margin:0}.slide:last-of-type{page-break-after:auto;break-after:auto}.slide svg{width:16in;height:9in}.notes,nav{display:none!important}}
</style></head><body>"""
        + "".join(pages)
        + """<nav><button id="prev">← Previous</button><span id="count" aria-live="polite"></span><button id="next">Next →</button><button id="notes">Speaker notes</button><button onclick="window.print()">Print / PDF</button></nav><script>
const slides=[...document.querySelectorAll('.slide')];let i=Math.max(0,Math.min(slides.length-1,parseInt(location.hash.replace('#slide-',''))-1||0));function show(n){i=Math.max(0,Math.min(slides.length-1,n));slides.forEach((s,k)=>s.classList.toggle('active',k===i));document.querySelector('#count').textContent=`${i+1} / ${slides.length}`;history.replaceState(null,'',`#slide-${i+1}`)}document.querySelector('#prev').onclick=()=>show(i-1);document.querySelector('#next').onclick=()=>show(i+1);document.querySelector('#notes').onclick=()=>document.body.classList.toggle('show-notes');document.addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();show(i+1)}if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();show(i-1)}if(e.key==='Home')show(0);if(e.key==='End')show(slides.length-1);if(e.key.toLowerCase()==='n')document.body.classList.toggle('show-notes')});show(i);
</script></body></html>"""
    )
    path.write_text(content)


def write_pdf(canvases, path, title):
    from reportlab.pdfgen.canvas import Canvas as PDFCanvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.colors import HexColor

    pdfmetrics.registerFont(TTFont("AML", str(FONT_ROOT / "LiberationSans-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("AML-Bold", str(FONT_ROOT / "LiberationSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("AML-Serif", str(FONT_ROOT / "LiberationSerif-Bold.ttf")))
    pdf = PDFCanvas(str(path), pagesize=(1152, 648), pageCompression=1)
    pdf.setTitle(title)
    pdf.setAuthor(AUTHOR)
    for c in canvases:
        pdf.saveState()
        pdf.scale(0.72, 0.72)
        for o in c.items:
            k = o["kind"]
            if k in ("rect", "circle"):
                pdf.setFillColor(HexColor(o["fill"]))
                if o["stroke"]:
                    pdf.setStrokeColor(HexColor(o["stroke"]))
                    pdf.setLineWidth(o["sw"])
                if k == "rect":
                    pdf.roundRect(
                        o["x"],
                        H - o["y"] - o["h"],
                        o["w"],
                        o["h"],
                        o["radius"],
                        stroke=int(bool(o["stroke"])),
                        fill=1,
                    )
                else:
                    pdf.circle(o["x"], H - o["y"], o["r"], stroke=int(bool(o["stroke"])), fill=1)
            elif k == "line":
                pdf.setStrokeColor(HexColor(o["color"]))
                pdf.setLineWidth(o["sw"])
                pdf.line(o["x1"], H - o["y1"], o["x2"], H - o["y2"])
                if o["arrow"]:
                    dx = o["x2"] - o["x1"]
                    dy = o["y2"] - o["y1"]
                    length = math.hypot(dx, dy)
                    ux, uy = dx / length, dy / length
                    tip = (o["x2"], H - o["y2"])
                    base = (o["x2"] - ux * 14, H - o["y2"] + uy * 14)
                    p = pdf.beginPath()
                    p.moveTo(*tip)
                    p.lineTo(base[0] - uy * 7, base[1] - ux * 7)
                    p.lineTo(base[0] + uy * 7, base[1] + ux * 7)
                    p.close()
                    pdf.setFillColor(HexColor(o["color"]))
                    pdf.drawPath(p, stroke=0, fill=1)
            elif k == "text":
                pdf.setFillColor(HexColor(o["color"]))
                pdf.setFont(
                    "AML-Serif" if o.get("serif") else ("AML-Bold" if o["bold"] else "AML"),
                    o["size"],
                )
                xx = o["x"]
                yy = H - o["y"] - o["size"] * 0.88
                if o["align"] == "center":
                    pdf.drawCentredString(xx + o["w"] / 2, yy, o["text"])
                elif o["align"] == "right":
                    pdf.drawRightString(xx + o["w"], yy, o["text"])
                else:
                    pdf.drawString(xx, yy, o["text"])
            elif k == "image":
                pdf.drawImage(
                    str(o["path"]), o["x"], H - o["y"] - o["h"], o["w"], o["h"], mask="auto"
                )
        pdf.restoreState()
        pdf.showPage()
    pdf.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "slides.json")
    parser.add_argument("--out", type=Path, default=ROOT)
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.source.read_text())
    slides = data["slides"]
    args.out.mkdir(parents=True, exist_ok=True)
    canvases = [render_slide(s, i + 1, len(slides)) for i, s in enumerate(slides)]
    warnings = [
        f"Slide {i + 1}: {message}" for i, c in enumerate(canvases) for message in c.warnings
    ]
    if warnings:
        raise ValueError("\n".join(warnings))
    title = data["title"]
    pptx_path = args.out / "AML_BUSINESS_SLIDES.pptx"
    html_path = args.out / "AML_BUSINESS_SLIDES.html"
    pdf_path = args.out / "AML_BUSINESS_SLIDES.pdf"
    to_pptx(slides, canvases, pptx_path, title)
    write_html(slides, canvases, html_path, title)
    if not args.no_pdf:
        write_pdf(canvases, pdf_path, title)
    print(f"{len(slides)} slides written to {args.out}")


if __name__ == "__main__":
    main()
