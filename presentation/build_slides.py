#!/usr/bin/env python3
"""Build an academic AML deck with Python-rendered figures and editable text.

All explanatory diagrams and statistical charts enter as image files exported
by Matplotlib. The presentation layer only places text, images and page rules.
The same layout drives PowerPoint, HTML, PDF and preview images.
"""
from __future__ import annotations
import argparse
import base64
import html
import json
import math
from pathlib import Path

from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

ROOT=Path(__file__).resolve().parent
W,H=1600,900
NAVY='#203647'
TEAL='#26786F'
MUTED='#59646D'
LIGHT='#D8DEE1'
WHITE='#FFFFFF'
FONT='Arial'
FONT_ROOT=Path('/usr/share/fonts/truetype/liberation')


def font(size,bold=False,serif=False):
    family='LiberationSerif' if serif else 'LiberationSans'
    weight='Bold' if bold or serif else 'Regular'
    return ImageFont.truetype(str(FONT_ROOT/f'{family}-{weight}.ttf'),round(size))


def wrap(text,width,size,bold=False,serif=False):
    f=font(size,bold,serif)
    lines=[]
    for paragraph in str(text).split('\n'):
        current=''
        for word in paragraph.split():
            proposed=f'{current} {word}'.strip()
            if current and f.getlength(proposed)>width:
                lines.append(current)
                current=word
            else:
                current=proposed
        lines.append(current)
    return lines


class Canvas:
    def __init__(self):
        self.items=[]
        self.warnings=[]

    def rect(self,x,y,w,h,fill=WHITE,stroke=None,radius=0,sw=1):
        self.items.append(dict(kind='rect',x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,radius=radius,sw=sw))

    def line(self,x1,y1,x2,y2,color=LIGHT,sw=1):
        self.items.append(dict(kind='line',x1=x1,y1=y1,x2=x2,y2=y2,color=color,sw=sw,arrow=False))

    def image(self,path,x,y,w,h,alt=''):
        path=Path(path)
        with Image.open(path) as source:
            factor=min(w/source.width,h/source.height)
            fw,fh=source.width*factor,source.height*factor
        self.items.append(dict(kind='image',path=path,x=x+(w-fw)/2,y=y+(h-fh)/2,w=fw,h=fh,alt=alt))

    def text(self,text,x,y,w,size=34,color=NAVY,bold=False,align='left',line_height=1.22,serif=False):
        lines=wrap(text,w,size,bold,serif)
        for i,line in enumerate(lines):
            self.items.append(dict(kind='text',text=line,x=x,y=y+i*size*line_height,w=w,size=size,color=color,bold=bold,align=align,serif=serif))
        bottom=y+len(lines)*size*line_height
        if bottom>885 or x<0 or x+w>W:
            self.warnings.append(f'Text outside slide: {text[:70]}')
        return bottom

    def bullets(self,values,x,y,w,size=32,gap=24):
        for value in values:
            self.text('•',x,y,22,size,TEAL)
            y=self.text(value,x+30,y,w-30,size)+gap
        return y-gap

    def header(self,s,index,total):
        self.rect(0,0,W,H)
        self.text(s.get('section','AML RESEARCH').upper(),85,39,1420,20,TEAL,True)
        bottom=self.text(s['title'],82,89,1430,49,NAVY,True,serif=True)
        if bottom>205:
            self.warnings.append('Title exceeds its reserved area')
        self.line(85,822,1515,822)
        end=self.text(s.get('footer',''),85,842,1300,18,MUTED,line_height=1.12)
        if end>885:self.warnings.append('Footer is too long')
        self.text(f'{index} / {total}',1405,842,110,20,MUTED,align='right')

    def svg(self):
        result=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img">']
        for o in self.items:
            k=o['kind']
            if k=='rect':
                result.append(f'<rect x="{o["x"]}" y="{o["y"]}" width="{o["w"]}" height="{o["h"]}" fill="{o["fill"]}"/>')
            elif k=='line':
                result.append(f'<line x1="{o["x1"]}" y1="{o["y1"]}" x2="{o["x2"]}" y2="{o["y2"]}" stroke="{o["color"]}" stroke-width="{o["sw"]}"/>')
            elif k=='text':
                anchor={'left':'start','center':'middle','right':'end'}[o['align']]
                tx=o['x']+{'left':0,'center':o['w']/2,'right':o['w']}[o['align']]
                family='Liberation Serif, Georgia, serif' if o['serif'] else 'Liberation Sans, Arial, sans-serif'
                result.append(f'<text x="{tx}" y="{o["y"]+o["size"]*.88}" font-family="{family}" font-size="{o["size"]}" font-weight="{700 if o["bold"] else 400}" fill="{o["color"]}" text-anchor="{anchor}">{html.escape(o["text"])}</text>')
            elif k=='image':
                encoded=base64.b64encode(o['path'].read_bytes()).decode('ascii')
                result.append(f'<image x="{o["x"]}" y="{o["y"]}" width="{o["w"]}" height="{o["h"]}" href="data:image/png;base64,{encoded}"><title>{html.escape(o["alt"])}</title></image>')
        return '\n'.join(result+['</svg>'])


def render_slide(s,index,total):
    c=Canvas()
    c.header(s,index,total)
    if s['visual']=='title':
        c.items=[]
        c.rect(0,0,W,H)
        c.text('COMP9501  /  AML RESEARCH',100,76,1390,22,TEAL,True)
        c.text(s['title'],96,230,1400,72,NAVY,True,serif=True)
        c.text(s['subtitle'],100,350,1290,39,NAVY)
        c.line(100,492,560,492,TEAL,2)
        c.text(s['lead'],100,548,1250,36,NAVY)
        c.text('IBM AML HI-Small · Graph Isomorphism Network · Five-seed experiment',100,745,1390,25,MUTED)
        c.text(s['footer'],100,838,1390,20,MUTED)
        return c
    if s.get('figure'):
        c.image(ROOT/s['figure'],65,233,985,482,s['figure_alt'])
        caption=f'Figure {s["figure_number"]}. {s["caption"]}'
        end=c.text(caption,85,739,970,24,MUTED,line_height=1.18)
        if end>809:c.warnings.append('Figure caption exceeds its reserved area')
        c.text(s.get('evidence_label','Evidence'),1095,235,420,22,TEAL,True)
        end=c.bullets(s['bullets'],1095,286,420,31,26)
        if end>790:c.warnings.append(f'Evidence column is too long ({end:.0f})')
    elif s.get('entries'):
        y=230
        size=29 if s['visual']=='references' else 33
        for entry in s['entries']:
            c.text(entry['label'],85,y,410,26,TEAL,True)
            end=c.text(entry['text'],515,y-2,990,size)
            y=max(y+95,end+46)
        if y-46>800:c.warnings.append('Reference/literature entries are too long')
    else:
        y=239
        if s.get('lead'):
            y=c.text(s['lead'],85,y,1390,39,TEAL,True,serif=True)+43
        end=c.bullets(s.get('bullets',[]),100,y,1340,36,32)
        if s.get('scope'):
            y=max(end+48,708)
            end=c.text(s['scope'],100,y,1340,28,MUTED)
        if end>795:c.warnings.append(f'Main text is too long ({end:.0f})')
    return c


def to_pptx(slides, canvases, path, title):
    prs=Presentation();prs.slide_width=Inches(16);prs.slide_height=Inches(9)
    prs.core_properties.title=title;prs.core_properties.subject='AML business interpretation of the completed counts × ports experiment'
    prs.core_properties.author='COMP9501 research project'
    scale=16/W
    def pos(v):return Inches(v*scale)
    def rgb(v):return RGBColor.from_string(v.lstrip('#'))
    for source,c in zip(slides,canvases):
        sl=prs.slides.add_slide(prs.slide_layouts[6])
        for o in c.items:
            k=o['kind']
            if k=='rect':
                shape=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if o['radius'] else MSO_SHAPE.RECTANGLE,pos(o['x']),pos(o['y']),pos(o['w']),pos(o['h']))
                if o['radius']:
                    try:shape.adjustments[0]=min(.15,o['radius']/max(1,min(o['w'],o['h'])))
                    except (ValueError,IndexError):pass
                shape.fill.solid();shape.fill.fore_color.rgb=rgb(o['fill'])
                if o['stroke']:shape.line.color.rgb=rgb(o['stroke']);shape.line.width=Pt(o['sw']*.6)
                else:shape.line.fill.background()
            elif k=='circle':
                shape=sl.shapes.add_shape(MSO_SHAPE.OVAL,pos(o['x']-o['r']),pos(o['y']-o['r']),pos(o['r']*2),pos(o['r']*2));shape.fill.solid();shape.fill.fore_color.rgb=rgb(o['fill'])
                if o['stroke']:shape.line.color.rgb=rgb(o['stroke'])
                else:shape.line.fill.background()
            elif k=='line':
                shape=sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,pos(o['x1']),pos(o['y1']),pos(o['x2']),pos(o['y2']));shape.line.color.rgb=rgb(o['color']);shape.line.width=Pt(o['sw']*.6)
                if o['arrow']:
                    tail=OxmlElement('a:tailEnd');tail.set('type','triangle');shape.line._get_or_add_ln().append(tail)
            elif k=='text':
                box=sl.shapes.add_textbox(pos(o['x']),pos(o['y']),pos(o['w']),pos(o['size']*1.4))
                tf=box.text_frame;tf.clear();tf.margin_top=tf.margin_bottom=tf.margin_left=tf.margin_right=0;tf.word_wrap=False
                p=tf.paragraphs[0];p.text=o['text'];p.font.name='Times New Roman' if o.get('serif') else FONT;p.font.size=Pt(o['size']*.72);p.font.bold=o['bold'];p.font.color.rgb=rgb(o['color'])
                from pptx.enum.text import PP_ALIGN
                p.alignment={'left':PP_ALIGN.LEFT,'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT}[o['align']]
                p.space_before=p.space_after=Pt(0)
            elif k=='image':
                picture=sl.shapes.add_picture(str(o['path']),pos(o['x']),pos(o['y']),width=pos(o['w']),height=pos(o['h']))
                picture._element.nvPicPr.cNvPr.set('descr',o['alt'])
        notes=source.get('notes','')
        if isinstance(notes,list):notes='\n\n'.join(notes)
        sl.notes_slide.notes_text_frame.text=notes
    prs.save(path)


def write_html(slides,canvases,path,title):
    pages=[]
    for i,(s,c) in enumerate(zip(slides,canvases)):
        note=s.get('notes','');note='\n\n'.join(note) if isinstance(note,list) else note
        pages.append(f'<section class="slide" id="slide-{i+1}" aria-label="{html.escape(s["title"])}">{c.svg()}<aside class="notes">{html.escape(note)}</aside></section>')
    content='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'''+html.escape(title)+'''</title><style>
*{box-sizing:border-box}body{margin:0;background:#122034;font-family:Arial,sans-serif}.slide{display:none;width:min(100vw,177.777vh);margin:auto;position:relative}.slide.active{display:block}svg{display:block;width:100%;height:auto}.notes{display:none;background:#fff;color:#14273f;white-space:pre-wrap;padding:28px;font-size:20px;line-height:1.5}.show-notes .notes{display:block}nav{display:flex;justify-content:center;gap:16px;padding:12px;color:#fff;align-items:center}button{font:16px Arial;padding:9px 16px;border:0;border-radius:5px;background:#e8eff3;color:#14273f;cursor:pointer}#count{min-width:80px;text-align:center}@page{size:16in 9in;margin:0}@media print{body{background:#fff}.slide{display:block;width:16in;height:9in;page-break-after:always;break-after:page;margin:0}.slide:last-of-type{page-break-after:auto;break-after:auto}.slide svg{width:16in;height:9in}.notes,nav{display:none!important}}
</style></head><body>'''+''.join(pages)+'''<nav><button id="prev">← Previous</button><span id="count" aria-live="polite"></span><button id="next">Next →</button><button id="notes">Speaker notes</button><button onclick="window.print()">Print / PDF</button></nav><script>
const slides=[...document.querySelectorAll('.slide')];let i=Math.max(0,Math.min(slides.length-1,parseInt(location.hash.replace('#slide-',''))-1||0));function show(n){i=Math.max(0,Math.min(slides.length-1,n));slides.forEach((s,k)=>s.classList.toggle('active',k===i));document.querySelector('#count').textContent=`${i+1} / ${slides.length}`;history.replaceState(null,'',`#slide-${i+1}`)}document.querySelector('#prev').onclick=()=>show(i-1);document.querySelector('#next').onclick=()=>show(i+1);document.querySelector('#notes').onclick=()=>document.body.classList.toggle('show-notes');document.addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();show(i+1)}if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();show(i-1)}if(e.key==='Home')show(0);if(e.key==='End')show(slides.length-1);if(e.key.toLowerCase()==='n')document.body.classList.toggle('show-notes')});show(i);
</script></body></html>'''
    path.write_text(content)


def write_pdf(canvases, path, title):
    from reportlab.pdfgen.canvas import Canvas as PDFCanvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.colors import HexColor
    pdfmetrics.registerFont(TTFont('AML',str(FONT_ROOT/'LiberationSans-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('AML-Bold',str(FONT_ROOT/'LiberationSans-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('AML-Serif',str(FONT_ROOT/'LiberationSerif-Bold.ttf')))
    pdf=PDFCanvas(str(path),pagesize=(1152,648),pageCompression=1)
    pdf.setTitle(title);pdf.setAuthor('COMP9501 research project')
    for c in canvases:
        pdf.saveState();pdf.scale(.72,.72)
        for o in c.items:
            k=o['kind']
            if k in ('rect','circle'):
                pdf.setFillColor(HexColor(o['fill']))
                if o['stroke']:pdf.setStrokeColor(HexColor(o['stroke']));pdf.setLineWidth(o['sw'])
                if k=='rect':
                    pdf.roundRect(o['x'],H-o['y']-o['h'],o['w'],o['h'],o['radius'],stroke=int(bool(o['stroke'])),fill=1)
                else:pdf.circle(o['x'],H-o['y'],o['r'],stroke=int(bool(o['stroke'])),fill=1)
            elif k=='line':
                pdf.setStrokeColor(HexColor(o['color']));pdf.setLineWidth(o['sw'])
                pdf.line(o['x1'],H-o['y1'],o['x2'],H-o['y2'])
                if o['arrow']:
                    dx=o['x2']-o['x1'];dy=o['y2']-o['y1'];length=math.hypot(dx,dy);ux,uy=dx/length,dy/length
                    tip=(o['x2'],H-o['y2']);base=(o['x2']-ux*14,H-o['y2']+uy*14)
                    p=pdf.beginPath();p.moveTo(*tip);p.lineTo(base[0]-uy*7,base[1]-ux*7);p.lineTo(base[0]+uy*7,base[1]+ux*7);p.close()
                    pdf.setFillColor(HexColor(o['color']));pdf.drawPath(p,stroke=0,fill=1)
            elif k=='text':
                pdf.setFillColor(HexColor(o['color']));pdf.setFont('AML-Serif' if o.get('serif') else ('AML-Bold' if o['bold'] else 'AML'),o['size'])
                xx=o['x'];yy=H-o['y']-o['size']*.88
                if o['align']=='center':pdf.drawCentredString(xx+o['w']/2,yy,o['text'])
                elif o['align']=='right':pdf.drawRightString(xx+o['w'],yy,o['text'])
                else:pdf.drawString(xx,yy,o['text'])
            elif k=='image':
                pdf.drawImage(str(o['path']),o['x'],H-o['y']-o['h'],o['w'],o['h'],mask='auto')
        pdf.restoreState();pdf.showPage()
    pdf.save()


def write_speaker_script(data, path):
    """Keep the accompanying Markdown aligned with the displayed slides."""
    lines=[
        '# What do port numbers add?',
        '',
        '## AML motivation',
        '',
        'Anti-money-laundering monitoring must identify transfers worth investigating '
        'among a much larger volume of legitimate activity. This study asks whether '
        'account activity counts preserve the useful signal in counterparty history. '
        'Its business relevance is to feature design and model validation; it does '
        'not measure investigator productivity or establish deployment effectiveness.',
        '',
        '## Presentation structure',
        '',
        'The academic edition has 16 main slides and three appendices. Slides 2–4 '
        'introduce the review process, relationship breadth, and local port indices. '
        'Data, literature, methodology, results, and AML implications follow. '
        'Twelve numbered figures are rendered directly in Python and inserted as '
        'images. Detailed explanations remain in the notes below and in PowerPoint.',
        '',
        '**Evidence scope.** The completed study uses five seeds, five epochs, one '
        'synthetic dataset, and transductive graph evaluation. The primary endpoint '
        'uses validation-selected checkpoints and thresholds. The supplementary '
        'novelty model does not isolate port-rank value after explicit novelty.',
        '',
        '## Slide text and speaker notes',
        '',
    ]
    for s in data['slides']:
        lines.extend([f'### {s["number"]}. {s["title"]}', '', f'**{s["section"]}**', ''])
        for key in ('subtitle','lead'):
            if s.get(key): lines.extend([s[key], ''])
        if s.get('figure'):
            lines.extend([f'![{s["figure_alt"]}](presentation/{s["figure"]})', '',
                          f'**Figure {s["figure_number"]}.** {s["caption"]}', ''])
        for b in s.get('bullets',[]): lines.append(f'- {b}')
        for entry in s.get('entries',[]): lines.append(f'- **{entry["label"]}.** {entry["text"]}')
        lines.append('')
        if s.get('scope'): lines.extend([f'**Scope.** {s["scope"]}', ''])
        lines.extend([f'**Speaker notes.** {s["notes"]}', '', f'*Source / scope:* {s["footer"]}', ''])
    path.write_text('\n'.join(lines))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,default=ROOT/'slides.json');parser.add_argument('--out',type=Path,default=ROOT);parser.add_argument('--no-pdf',action='store_true');args=parser.parse_args()
    data=json.loads(args.source.read_text());slides=data['slides'];args.out.mkdir(parents=True,exist_ok=True)
    canvases=[render_slide(s,i+1,len(slides)) for i,s in enumerate(slides)]
    warnings=[f'Slide {i+1}: {message}' for i,c in enumerate(canvases) for message in c.warnings]
    if warnings:raise ValueError('\n'.join(warnings))
    title=data.get('title','What transaction history matters for AML?')
    pptx_path=args.out/'AML_BUSINESS_SLIDES.pptx';html_path=args.out/'AML_BUSINESS_SLIDES.html';pdf_path=args.out/'AML_BUSINESS_SLIDES.pdf'
    to_pptx(slides,canvases,pptx_path,title);write_html(slides,canvases,html_path,title)
    if not args.no_pdf:
        write_pdf(canvases,pdf_path,title)
        import fitz
        pdf=fitz.open(pdf_path);assert len(pdf)==len(slides),(len(pdf),len(slides));preview=args.out/'preview';preview.mkdir(exist_ok=True)
        for i,page in enumerate(pdf):page.get_pixmap(matrix=fitz.Matrix(1.1,1.1)).save(preview/f'slide-{i+1:02d}.png')
        sheet=Image.new('RGB',(1680,315*math.ceil(len(slides)/3)),WHITE)
        for i in range(len(slides)):
            with Image.open(preview/f'slide-{i+1:02d}.png') as page:
                page=page.resize((560,315),Image.Resampling.LANCZOS)
                sheet.paste(page,((i%3)*560,(i//3)*315))
        sheet.save(preview/'contact-sheet.png')
    write_speaker_script(data,args.out.parent/'AML_BUSINESS_PRESENTATION.md')
    print(json.dumps({'slides':len(slides),'pptx':str(pptx_path),'html':str(html_path),'pdf':str(pdf_path),'layout_warnings':warnings},indent=2))

if __name__=='__main__':main()
