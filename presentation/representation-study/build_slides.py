#!/usr/bin/env python3
"""Build the research-question edition, then render the actual PPTX with LibreOffice."""
from __future__ import annotations
import argparse
import base64
import html
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent
W, H = 1600, 900
BG, INK, BLUE, TEAL, MUTED, LIGHT = '#FAF9F5', '#15232F', '#1F4F8A', '#38786F', '#56646F', '#CFCABC'


def font(size, serif=False, bold=False):
    family = 'EBGaramond' if serif else 'Inter'
    return ImageFont.truetype(str(ROOT/'fonts'/f'{family}-{"Semibold" if bold else "Regular"}.ttf'), round(size))


def wrap(value, width, size, serif=False, bold=False):
    f = font(size, serif, bold)
    result = []
    for paragraph in value.split('\n'):
        line = ''
        for word in paragraph.split():
            proposed = f'{line} {word}'.strip()
            if line and f.getlength(proposed) > width:
                result.append(line)
                line = word
            else:
                line = proposed
        result.append(line)
    return result


class Page:
    def __init__(self, background=BG):
        self.background = background
        self.items = []

    def text(self, value, x, y, width, size=30, color=INK, serif=False, bold=False, spacing=1.18):
        lines = wrap(value, width, size, serif, bold)
        for i, line in enumerate(lines):
            yy = y+i*size*spacing
            if x < 0 or x+width > W or yy+size*1.35 > H:
                raise ValueError(f'Text exceeds page: {value}')
            self.items.append(dict(kind='text', text=line, x=x, y=yy, width=width, size=size,
                                   color=color, serif=serif, bold=bold))
        return y+len(lines)*size*spacing

    def line(self, x1, y1, x2, y2, color=LIGHT):
        self.items.append(dict(kind='line', x1=x1, y1=y1, x2=x2, y2=y2, color=color))

    def image(self, path, x, y, width, height, alt=''):
        with Image.open(path) as im:
            scale = min(width/im.width, height/im.height)
            ww, hh = im.width*scale, im.height*scale
        self.items.append(dict(kind='image', path=path, x=x+(width-ww)/2, y=y+(height-hh)/2,
                               width=ww, height=hh, alt=alt))

    def bullets(self, values, x, y, width, size=29, gap=14, color=INK):
        for value in values:
            self.text('•', x, y, 24, size, color)
            y = self.text(value, x+30, y, width-30, size, color)+gap
        return y-gap


def layout(s, count):
    kind = s['layout']
    dark = kind in ('cover', 'question', 'conclusion')
    p = Page(BLUE if kind == 'question' else (INK if dark else BG))
    fg, muted = (BG, '#CCD5DC') if dark else (INK, MUTED)
    p.text(s['section'].upper(), 106, 66, 1388, 18, muted, bold=True)
    if kind == 'cover':
        p.text('What Do Port\nNumbers Add?', 106, 230, 1350, 92, fg, serif=True, spacing=1.02)
        p.text(s['subtitle'], 110, 448, 1350, 38, fg, serif=True)
        p.line(110, 535, 690, 535, TEAL)
        p.text(s['lead'], 110, 590, 1320, 32, fg)
    elif kind == 'question':
        p.text(s['title'], 106, 220, 1380, 64, fg, serif=True, spacing=1.08)
        p.text(s['lead'], 110, 422, 1320, 35, fg, serif=True)
        p.line(110, 550, 1490, 550, '#6683A5')
        p.bullets(s['bullets'], 110, 602, 1350, 30, 22, fg)
    else:
        title_bottom = p.text(s['title'], 106, 102, 1388, 52, fg, serif=True, spacing=1.06)
        if title_bottom > 178:
            raise ValueError(f'Title needs shortening: {s["number"]}: {s["title"]}')
        if kind == 'wide_figure':
            p.image(ROOT/s['figure'], 106, 190, 1388, 440, s['caption'])
            end = p.text(f'Figure {s["figure_number"]}. {s["caption"]}', 110, 650, 1380, 20, MUTED)
            end = p.bullets(s['bullets'], 110, max(704, end+18), 1380, 28, 12)
            if end > 824:
                raise ValueError(f'Supporting text too long on slide {s["number"]}: {end}')
        elif kind == 'methods':
            for x, group in zip([110, 830], s['groups']):
                p.text(group['label'], x, 250, 660, 36, BLUE, serif=True)
                p.text(group['text'], x, 320, 660, 30, spacing=1.3)
            p.line(110, 620, 1490, 620)
            p.text(s['scope'], 110, 664, 1370, 29)
            p.text('F1 balances precision and recall for the laundering class.', 110, 752, 1370, 25, MUTED)
        elif kind == 'references':
            y = 220
            for e in s['entries']:
                label = e.get('label', '')
                body = e.get('text', '')
                p.text(label, 110, y, 330, 26, BLUE, bold=True)
                end = p.text(body, 470, y, 1010, 25)
                y = max(y+96, end+25)
            if y > 824:
                raise ValueError('References exceed reserved space')
        else:
            y = 250
            if s.get('lead'):
                y = p.text(s['lead'], 110, y, 1340, 40, fg if dark else BLUE, serif=True)+58
            end = p.bullets(s['bullets'], 110, y, 1340, 34 if dark else 32, 38, fg)
            if end > 814:
                raise ValueError(f'Body too long on slide {s["number"]}: {end}')
    p.text(s.get('footer', ''), 106, 848, 1320, 17, muted)
    p.text(f'{s["number"]} / {count}', 1435, 848, 110, 17, muted)
    return p


def write_pptx(slides, pages, path):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(40/3), Inches(7.5)
    prs.core_properties.title = 'What Do Port Numbers Add? Making pair history explicit'
    prs.core_properties.subject = 'Fixed-budget representation study in AML graph neural networks'
    prs.core_properties.author = 'COMP9501 research project'
    def pos(value): return Inches(value/120)
    def rgb(value): return RGBColor.from_string(value.lstrip('#'))
    for source, page in zip(slides, pages):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = rgb(page.background)
        for item in page.items:
            k = item['kind']
            if k == 'text':
                box = slide.shapes.add_textbox(pos(item['x']), pos(item['y']), pos(item['width']), pos(item['size']*1.45))
                tf = box.text_frame
                tf.clear()
                tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
                tf.word_wrap = False
                para = tf.paragraphs[0]
                para.text = item['text']
                para.font.name = 'EB Garamond' if item['serif'] else 'Inter'
                para.font.size = Pt(item['size']*.6)
                para.font.bold = item['bold']
                para.font.color.rgb = rgb(item['color'])
                para.space_before = para.space_after = Pt(0)
                para.line_spacing = 1.0
            elif k == 'line':
                shape = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, pos(item['x1']), pos(item['y1']), pos(item['x2']), pos(item['y2']))
                shape.line.color.rgb = rgb(item['color'])
                shape.line.width = Pt(.8)
            else:
                picture = slide.shapes.add_picture(str(item['path']), pos(item['x']), pos(item['y']), width=pos(item['width']), height=pos(item['height']))
                picture._element.nvPicPr.cNvPr.set('descr', item['alt'])
        notes = source.get('notes', '')
        slide.notes_slide.notes_text_frame.text = '\n\n'.join(notes) if isinstance(notes, list) else notes
    prs.save(path)


def write_html(slides, pages, path):
    fonts = ''
    for family, file in [('Inter','Inter-Regular.ttf'), ('EB Garamond','EBGaramond-Regular.ttf')]:
        encoded = base64.b64encode((ROOT/'fonts'/file).read_bytes()).decode()
        fonts += f'@font-face{{font-family:"{family}";src:url(data:font/ttf;base64,{encoded})}}'
    sections = []
    for s, page in zip(slides, pages):
        svg = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"><rect width="1600" height="900" fill="{page.background}"/>']
        for item in page.items:
            if item['kind'] == 'text':
                family = 'EB Garamond' if item['serif'] else 'Inter'
                weight = 600 if item['bold'] else 400
                svg.append(f'<text x="{item["x"]}" y="{item["y"]+item["size"]*.95}" font-family="{family}" font-size="{item["size"]}" font-weight="{weight}" fill="{item["color"]}">{html.escape(item["text"])}</text>')
            elif item['kind'] == 'line':
                svg.append(f'<line x1="{item["x1"]}" y1="{item["y1"]}" x2="{item["x2"]}" y2="{item["y2"]}" stroke="{item["color"]}"/>')
            else:
                data = base64.b64encode(item['path'].read_bytes()).decode()
                svg.append(f'<image x="{item["x"]}" y="{item["y"]}" width="{item["width"]}" height="{item["height"]}" href="data:image/png;base64,{data}"><title>{html.escape(item["alt"])}</title></image>')
        svg.append('</svg>')
        notes = s.get('notes', '')
        notes = '\n\n'.join(notes) if isinstance(notes, list) else notes
        sections.append(f'<section>{"".join(svg)}<aside>{html.escape(notes)}</aside></section>')
    path.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Making pair history explicit</title><style>'+fonts+'body{margin:0;background:#15232f}section{display:none;max-width:1400px;margin:auto}section.active{display:block}svg{display:block;width:100%}aside{display:none;white-space:pre-wrap;padding:30px;background:#faf9f5;font:18px Inter;line-height:1.6}.notes aside{display:block}nav{text-align:center;padding:12px;color:white;font:16px Inter}button{margin:0 8px;padding:8px;font:inherit}</style>'+''.join(sections)+'<nav><button id="prev">Previous</button><span id="count"></span><button id="next">Next</button><button id="notes">Speaker notes</button></nav><script>const pages=[...document.querySelectorAll("section")];let i=0;function show(n){i=Math.min(pages.length-1,Math.max(0,n));pages.forEach((p,k)=>p.classList.toggle("active",k===i));document.querySelector("#count").textContent=`${i+1} / ${pages.length}`}document.querySelector("#prev").onclick=()=>show(i-1);document.querySelector("#next").onclick=()=>show(i+1);document.querySelector("#notes").onclick=()=>document.body.classList.toggle("notes");document.onkeydown=e=>{if(e.key==="ArrowRight")show(i+1);if(e.key==="ArrowLeft")show(i-1)};show(0)</script></html>')


def write_script(data):
    lines = ['# Making pair history explicit in AML graph learning', '', data['central_research_question'], '',
             'The original primary counts × ports factorial and supplementary novelty comparison retain their original status. This presentation emphasizes the representation finding without changing the study protocol.', '']
    for s in data['slides']:
        lines += [f'## {s["number"]}. {s["title"]}', '', f'**{s["section"]}**', '']
        if s.get('subtitle'): lines += [s['subtitle'], '']
        if s.get('lead'): lines += [s['lead'], '']
        if s.get('figure'): lines += [f'![Figure {s["figure_number"]}]({s["figure"]})', '', f'Figure {s["figure_number"]}. {s["caption"]}', '']
        for b in s.get('bullets', []): lines += [f'- {b}']
        for g in s.get('groups', []): lines += [f'- **{g["label"]}:** {g["text"]}']
        for e in s.get('entries', []): lines += [f'- **{e["label"]}:** {e["text"]}']
        if s.get('scope'): lines += ['', s['scope']]
        notes = s.get('notes', '')
        if isinstance(notes, list): notes = '\n\n'.join(notes)
        lines += ['', '**Speaker notes.** '+notes, '', '*Source and scope:* '+s.get('footer', ''), '']
    script = '\n'.join(lines)
    (ROOT/'SPEAKER_NOTES.md').write_text(script)
    (ROOT.parents[1]/'AML_BUSINESS_PRESENTATION.md').write_text(
        script.replace('](figures/', '](presentation/representation-study/figures/'))


def render_and_preview(pptx):
    import fitz
    with tempfile.TemporaryDirectory(prefix='aml-rq-render-') as tmp:
        tmp = Path(tmp)
        config = tmp/'fonts.conf'
        config.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><include>/etc/fonts/fonts.conf</include><dir>'+html.escape(str(ROOT/'fonts'))+'</dir><cachedir>'+str(tmp/'font-cache')+'</cachedir></fontconfig>')
        env = dict(os.environ, FONTCONFIG_FILE=str(config), XDG_CACHE_HOME=str(tmp/'cache'))
        subprocess.run(['soffice', f'-env:UserInstallation={(tmp/"profile").as_uri()}', '--headless', '--convert-to', 'pdf', '--outdir', str(ROOT), str(pptx)], check=True, env=env)
    pdf = fitz.open(pptx.with_suffix('.pdf'))
    preview = ROOT/'preview'
    preview.mkdir(exist_ok=True)
    sheet = Image.new('RGB', (1600, 300*math.ceil(len(pdf)/3)), BG)
    for i, page in enumerate(pdf):
        file = preview/f'slide-{i+1:02d}.png'
        page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(file)
        with Image.open(file) as image:
            image = image.resize((533, 300), Image.Resampling.LANCZOS)
            sheet.paste(image, ((i%3)*533, (i//3)*300))
    sheet.save(preview/'contact-sheet.png')
    return len(pdf)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-render', action='store_true')
    args = parser.parse_args()
    data = json.loads((ROOT/'slides.json').read_text())
    slides = data['slides']
    pages = [layout(s, len(slides)) for s in slides]
    path = ROOT/'AML_REPRESENTATION_STUDY.pptx'
    write_pptx(slides, pages, path)
    write_html(slides, pages, path.with_suffix('.html'))
    write_script(data)
    if not args.skip_render: assert render_and_preview(path) == len(slides)
    print(json.dumps({'slides':len(slides), 'pptx':str(path), 'rendered':not args.skip_render}))


if __name__ == '__main__':
    main()
