#!/usr/bin/env python3
"""Build the AML presentation as editable PowerPoint and standalone HTML/PDF.

The source is slides.json. Diagrams use native vector elements; statistical
plots have standalone PNG/SVG sources. Speaker notes retain the presentation script. Run with system Python
with python-pptx, Pillow, ReportLab, and PyMuPDF installed.
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

from intro_visuals import draw_feature_history, draw_dataset, draw_timeline, draw_literature

ROOT = Path(__file__).resolve().parent
W, H = 1600, 900
NAVY = '#14273F'
TEAL = '#007E87'
BLUE = '#247BB4'
ORANGE = '#C76225'
PURPLE = '#8061A8'
MUTED = '#5E6D7D'
LIGHT = '#E8EFF3'
BG = '#F7F9FB'
WHITE = '#FFFFFF'
FONT = 'Arial'
FONT_ROOT = Path('/usr/share/fonts/truetype/liberation')


def font(size, bold=False):
    return ImageFont.truetype(str(FONT_ROOT / ('LiberationSans-Bold.ttf' if bold else 'LiberationSans-Regular.ttf')), round(size))


def wrap(text, width, size, bold=False):
    f = font(size, bold)
    lines = []
    for para in str(text).split('\n'):
        current = ''
        for word in para.split():
            proposed = f'{current} {word}'.strip()
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
        self.items.append(dict(kind='rect', x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, radius=radius, sw=sw))

    def circle(self, x, y, r, fill=TEAL, stroke=None, sw=1):
        self.items.append(dict(kind='circle', x=x, y=y, r=r, fill=fill, stroke=stroke, sw=sw))

    def line(self, x1, y1, x2, y2, color=MUTED, sw=2, arrow=False):
        self.items.append(dict(kind='line', x1=x1, y1=y1, x2=x2, y2=y2, color=color, sw=sw, arrow=arrow))

    def image(self, path, x, y, w, h, alt=''):
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(path)
        with Image.open(path) as source:
            factor=min(w/source.width,h/source.height)
            fitted_w,fitted_h=source.width*factor,source.height*factor
        x,y=x+(w-fitted_w)/2,y+(h-fitted_h)/2
        w,h=fitted_w,fitted_h
        self.items.append(dict(kind='image', path=path, x=x, y=y, w=w, h=h, alt=alt))

    def text(self, text, x, y, w, size=32, color=NAVY, bold=False, align='left', line_height=1.18):
        lines = wrap(text, w, size, bold)
        for i, line in enumerate(lines):
            self.items.append(dict(kind='text', text=line, x=x, y=y+i*size*line_height, w=w, size=size, color=color, bold=bold, align=align))
        bottom = y + len(lines)*size*line_height
        if bottom > 875 or x < 0 or x+w > W+1:
            self.warnings.append(f'Text out of bounds: {text[:80]} ({bottom:.1f})')
        return bottom

    def bullet_list(self, bullets, x, y, w, size=32, gap=24, color=NAVY):
        for value in bullets:
            self.circle(x+5, y+size*.52, 4.5, TEAL)
            y = self.text(value, x+27, y, w-27, size, color) + gap
        return y

    def header(self, slide, number, total):
        self.rect(0,0,W,H,BG)
        self.rect(0,0,14,H,TEAL)
        self.text(slide.get('section','AML RESEARCH').upper(),80,38,1350,21,TEAL,True)
        title = slide['title']
        title_size = 51 if len(title)<63 else 45
        bottom = self.text(title,80,86,1440,title_size,NAVY,True)
        if slide.get('subtitle'):
            self.text(slide['subtitle'],80,max(163,bottom+12),1440,27,MUTED)
        self.line(80,825,1520,825,LIGHT,2)
        footer = slide.get('footer','IBM AML HI-Small | Completed five-seed, five-epoch study')
        self.text(footer,80,845,1325,17,MUTED)
        self.text(f'{number:02d} / {total:02d}',1410,842,110,21,MUTED,align='right')

    def takeaway(self, value, y=716):
        if not value: return
        self.rect(80,y,1440,92,'#E4F1F1',radius=12)
        self.rect(80,y,7,92,TEAL)
        self.text(value,106,y+18,1385,29,TEAL,True)

    def svg(self):
        result = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img">',
                  '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L9,4.5 L0,9 Z" fill="context-stroke"/></marker></defs>']
        esc=html.escape
        for o in self.items:
            k=o['kind']
            if k=='rect':
                result.append(f'<rect x="{o["x"]}" y="{o["y"]}" width="{o["w"]}" height="{o["h"]}" rx="{o["radius"]}" fill="{o["fill"]}" stroke="{o["stroke"] or "none"}" stroke-width="{o["sw"]}"/>')
            elif k=='circle':
                result.append(f'<circle cx="{o["x"]}" cy="{o["y"]}" r="{o["r"]}" fill="{o["fill"]}" stroke="{o["stroke"] or "none"}" stroke-width="{o["sw"]}"/>')
            elif k=='line':
                marker=' marker-end="url(#arrow)"' if o['arrow'] else ''
                result.append(f'<line x1="{o["x1"]}" y1="{o["y1"]}" x2="{o["x2"]}" y2="{o["y2"]}" stroke="{o["color"]}" stroke-width="{o["sw"]}"{marker}/>')
            elif k=='text':
                anchor={'left':'start','center':'middle','right':'end'}[o['align']]
                tx=o['x']+({'left':0,'center':o['w']/2,'right':o['w']}[o['align']])
                result.append(f'<text x="{tx}" y="{o["y"]+o["size"]*.88}" font-family="Arial, Liberation Sans, sans-serif" font-size="{o["size"]}" font-weight="{700 if o["bold"] else 400}" fill="{o["color"]}" text-anchor="{anchor}">{esc(o["text"])}</text>')
            elif k=='image':
                encoded=base64.b64encode(o['path'].read_bytes()).decode('ascii')
                result.append(f'<image x="{o["x"]}" y="{o["y"]}" width="{o["w"]}" height="{o["h"]}" href="data:image/png;base64,{encoded}" preserveAspectRatio="xMidYMid meet"><title>{esc(o["alt"])}</title></image>')
        return '\n'.join(result+['</svg>'])


def card(c, x,y,w,h,title,body,color=TEAL):
    c.rect(x,y,w,h,WHITE,stroke=LIGHT,radius=14)
    c.rect(x,y,w,8,color,radius=4)
    end=c.text(title,x+25,y+27,w-50,32,color,True)
    size=28
    while size>23 and len(wrap(body,w-50,size))*size*1.18 > y+h-25-(end+20):size-=1
    c.text(body,x+25,end+20,w-50,size,NAVY)


def table(c, headers, rows, x=80,y=250,w=1440,row_h=70,widths=None,size=27):
    n=len(headers)
    widths=widths or [w/n]*n
    widths=[v*w/sum(widths) for v in widths]
    def heights(fs):
        return [max(row_h,max(len(wrap(str(v),cw-36,fs,True))*fs*1.18+32 for v,cw in zip(headers,widths)))] + [max(row_h,max(len(wrap(str(v),cw-36,fs,j==0))*fs*1.18+32 for j,(v,cw) in enumerate(zip(row,widths)))) for row in rows]
    sizes=heights(size)
    while sum(sizes)>465 and size>28:
        size-=1;sizes=heights(size)
    c.rect(x,y,w,sizes[0],NAVY,radius=8)
    xx=x
    for h,cw in zip(headers,widths):
        c.text(h,xx+18,y+17,cw-36,size,WHITE,True)
        xx+=cw
    yy=y+sizes[0]
    for i,row in enumerate(rows):
        rh=sizes[i+1]
        c.rect(x,yy,w,rh,WHITE if i%2==0 else '#EDF2F6')
        xx=x
        for j,(v,cw) in enumerate(zip(row,widths)):
            c.text(str(v),xx+18,yy+17,cw-36,size,NAVY,j==0)
            xx+=cw
        yy+=rh
    return yy


def draw_chart(c, chart, x=110,y=265,w=1370,h=390):
    labels=chart.get('labels',chart.get('categories',[])); vals=chart['values']
    lower=chart.get('lower'); upper=chart.get('upper')
    colors=chart.get('colors',[TEAL]*len(vals))
    if len(colors)<len(vals): colors=[TEAL]*len(vals)
    lo=chart.get('min',min([0]+(lower or vals)))
    hi=chart.get('max',max((upper or vals))*1.15)
    left=x+chart.get('label_width',370); right=x+w-30
    axis_y=y+h
    def sx(v):return left+(v-lo)/(hi-lo)*(right-left)
    ticks=chart.get('ticks',[lo+(hi-lo)*i/4 for i in range(5)])
    for t in ticks:
        xx=sx(t);c.line(xx,y-10,xx,axis_y,LIGHT,2)
        c.text(f'{t:g}',xx-50,axis_y+14,100,23,MUTED,align='center')
    if lo <= 0 <= hi:c.line(sx(0),y-10,sx(0),axis_y,'#A7B4C1',2)
    spacing=h/len(vals)
    for i,(label,v) in enumerate(zip(labels,vals)):
        cy=y+(i+.5)*spacing
        c.text(label,x,cy-20,left-x-30,29,NAVY,True)
        if lower is not None:
            c.line(sx(lower[i]),cy,sx(upper[i]),cy,colors[i],5)
            c.line(sx(lower[i]),cy-12,sx(lower[i]),cy+12,colors[i],3)
            c.line(sx(upper[i]),cy-12,sx(upper[i]),cy+12,colors[i],3)
            c.circle(sx(v),cy,10,colors[i])
            value=f'{v:+.2f} [{lower[i]:+.2f}, {upper[i]:+.2f}]'
            c.text(value,left,cy+19,right-left,28,colors[i],align='right')
        else:
            c.rect(sx(0),cy-22,max(sx(v)-sx(0),1),44,colors[i],radius=4)
            c.text(f'{v:.2f}',sx(v)+16,cy-19,100,29,colors[i],True)
    c.text(chart.get('unit','F1 percentage points'),left,axis_y+52,right-left,24,MUTED,align='center')


def network_panel(c, x, title, repeated):
    c.rect(x,250,690,430,WHITE,stroke=LIGHT,radius=16)
    c.text(title,x+25,272,640,32,NAVY,True)
    sx=x+130;tx=x+530
    if repeated:
        for offset in (-40,-24,-8,8,24,40):c.line(sx+48,466+offset,tx-48,466+offset,BLUE,3,True)
        c.circle(tx,466,49,TEAL);c.text('B',tx-30,442,60,42,WHITE,True,align='center')
    else:
        for label,cy in zip('BCDEFG',(335,390,445,500,555,610)):
            c.line(sx+43,466,tx-42,cy,BLUE,3,True)
            c.circle(tx,cy,25,TEAL);c.text(label,tx-18,cy-17,36,29,WHITE,True,align='center')
    c.circle(sx,466,49,NAVY);c.text('A',sx-30,442,60,42,WHITE,True,align='center')
    c.text('6 transfers · '+('1 counterparty' if repeated else '6 counterparties'),x+25,642,640,27,MUTED,align='center')


def cover(c,s,index,total):
    c.items=[];c.rect(0,0,W,H,NAVY);c.rect(0,0,18,H,TEAL)
    c.text('AML  /  RESEARCH FOR BETTER TRANSACTION MONITORING',85,65,1410,23,'#68C5C6',True)
    c.text(s['title'],85,175,1340,77,WHITE,True)
    c.text(s.get('subtitle',''),90,410,1320,34,'#D9E5EE')
    bullets=s.get('bullets',[])
    if bullets:c.text('  •  '.join(bullets),90,560,1360,28,'#B9CAD8')
    if s.get('takeaway'):c.text(s['takeaway'],90,665,1360,36,'#68C5C6',True)
    c.line(85,810,1515,810,'#385069',2)
    c.text('COMP9501  |  IBM AML HI-Small  |  Completed five-seed experiment',90,841,1300,21,'#B9CAD8')
    c.text(f'{index:02d} / {total:02d}',1405,841,110,21,'#B9CAD8',align='right')
    return c


def draw_factorial(c, s):
    # Native shapes keep the experimental design editable in PowerPoint.
    for x, heading in ((340,'Ports absent'),(795,'Ports present')):
        c.text(heading,x,230,380,29,MUTED,True,align='center')
    for y, label in ((300,'Counts absent'),(470,'Counts present')):
        c.text(label,80,y+43,235,29,MUTED,True)
    panels=[(340,295,'B','Base',BLUE),(795,295,'P','Ports',BLUE),
            (340,465,'C','Counts',TEAL),(795,465,'CP','Counts + Ports',TEAL)]
    for x,y,tag,label,color in panels:
        c.rect(x,y,380,130,WHITE,stroke=LIGHT,radius=14)
        c.circle(x+55,y+65,31,color)
        c.text(tag,x+26,y+43,58,34,WHITE,True,align='center')
        c.text(label,x+103,y+43,260,33,NAVY,True)
    for y in (360,530):c.line(736,y,777,y,ORANGE,4,True)
    for x in (530,985):c.line(x,433,x,456,TEAL,4,True)
    c.rect(1230,295,290,300,'#E4F1F1',radius=14)
    c.text('Supplement',1252,319,246,28,TEAL,True,align='center')
    c.text('CN',1252,378,246,49,TEAL,True,align='center')
    c.text('Counts +\nexplicit novelty',1252,452,246,29,NAVY,align='center')
    c.text('20 factorial runs',340,626,835,28,MUTED,align='center')
    c.text('5 extra runs',1230,626,290,28,MUTED,align='center')
    c.text('Every cell: same model and split • 5 seeds • 5 epochs',80,674,1440,27,MUTED,align='center')


def draw_estimand(c,s):
    rows=[(255,'Without counts','Base','Ports','D = P − B',BLUE),
          (435,'With counts','Counts','Counts + Ports','N = CP − C',ORANGE)]
    for y,label,left,right,formula,color in rows:
        c.text(label,80,y+39,270,31,color,True)
        for x,txt in ((380,left),(850,right)):
            c.rect(x,y,330,115,WHITE,stroke=LIGHT,radius=14)
            c.text(txt,x+20,y+34,290,34,NAVY,True,align='center')
        c.line(735,y+57,825,y+57,color,5,True)
        c.text('add ports',720,y+83,120,23,MUTED,align='center')
        c.text(formula,1230,y+35,285,35,color,True)
    c.text('Share explained = 1 − mean(N) / mean(D)',100,617,1400,41,TEAL,True,align='center')
    c.text('Validation selects the epoch and threshold • paired-seed uncertainty',100,676,1400,26,MUTED,align='center')


def draw_question(c,s):
    card(c,80,250,430,245,'Supply account counts','Make transfer volume and counterparty breadth explicit.',BLUE)
    c.line(527,372,568,372,TEAL,4,True)
    card(c,585,250,430,245,'Add port numbers','Measure what they still contribute under the same model.',ORANGE)
    c.line(1032,372,1073,372,TEAL,4,True)
    card(c,1090,250,430,245,'Compare the gain','Does the port improvement shrink when counts are present?',TEAL)
    c.rect(160,552,1280,130,'#E4F1F1',radius=12)
    c.text('Mechanism check: make pair novelty explicit',195,574,1210,35,TEAL,True,align='center')
    c.text('Ask whether first-observed relationship status is a useful representation.',195,629,1210,29,NAVY,align='center')


def draw_roadmap(c,s):
    steps=[('01','Preserve pair context','Retain the current sender–receiver history alongside account counts.',BLUE),
           ('02','Test explicit novelty','Compare novelty and ranks with an adequate fixed training budget.',TEAL),
           ('03','Validate review capacity','Measure detection and case yield at a common alert budget.',ORANGE)]
    for i,(number,title,body,color) in enumerate(steps):
        x=80+500*i
        c.circle(x+45,285,34,color);c.text(number,x+15,264,60,34,WHITE,True,align='center')
        if i<2:c.line(x+100,285,x+460,285,LIGHT,4,True)
        card(c,x,345,440,250,title,body,color)
    c.text('Next validation: past-only information • later real-world periods • case-level outcomes',95,633,1410,28,MUTED,align='center')
    c.text('A simple model input still needs reliable identities and historical pair state.',95,675,1410,27,MUTED,align='center')


def draw_conclusion(c,s):
    values=[('+14.91 pts','Port benefit remains','F1 gain after the specified counts',BLUE),
            ('+9.42 pts','Explicit novelty helps','F1 gain: CN versus CP at this budget',TEAL),
            ('Unresolved','Extra rank value','after novelty is explicitly supplied',ORANGE)]
    for i,(value,title,body,color) in enumerate(values):
        x=80+500*i
        c.rect(x,255,440,285,WHITE,stroke=LIGHT,radius=14)
        c.rect(x,255,440,8,color,radius=4)
        c.text(value,x+20,296,400,51,color,True,align='center')
        c.text(title,x+22,390,396,32,NAVY,True,align='center')
        c.text(body,x+25,449,390,28,MUTED,align='center')
        c.line(x+220,554,x+220,593,color,4,True)
    c.rect(80,611,1440,79,'#E4F1F1',radius=12)
    c.text('AML decision: validate relationship features at realistic review capacity',110,632,1380,34,TEAL,True,align='center')


def render_slide(s, index, total):
    c=Canvas(); c.header(s,index,total)
    visual=s.get('visual','bullets')
    if isinstance(visual,dict):kind=visual.get('type','bullets')
    else:kind=visual
    bullets=s.get('bullets',[])
    if kind=='title':return cover(c,s,index,total)
    if kind=='plot':
        c.image(ROOT/s['figure'],80,235,1440,455,s.get('figure_alt',''))
    elif kind=='feature_history':draw_feature_history(c,s)
    elif kind=='dataset':draw_dataset(c,s)
    elif kind=='timeline_plot':draw_timeline(c,s)
    elif kind=='literature_flow':draw_literature(c,s)
    elif kind=='question':draw_question(c,s)
    elif kind=='estimand':draw_estimand(c,s)
    elif kind=='roadmap':draw_roadmap(c,s)
    elif kind=='conclusion':draw_conclusion(c,s)
    elif kind=='network_comparison':
        network_panel(c,80,'Repeated transfers to one partner',True)
        network_panel(c,830,'Transfers distributed across partners',False)
    elif kind=='workflow':
        for i,(title,body) in enumerate([('Transactions','Incoming transfers'),('Model scores','Rank transactions'),('Review queue','Human investigation')]):
            xx=80+i*500;card(c,xx,250,440,150,title,body)
            if i<2:c.line(xx+452,324,xx+484,324,TEAL,4,True)
        defs=[('Precision', 'Among flagged transactions, how many carry a laundering label?'),('Recall','Among labelled laundering transactions, how many are found?'),('F1','Balances precision and recall; does not measure financial return or staffing needs.')]
        for i,(title,body) in enumerate(defs):card(c,80+i*500,445,440,230,title,body,BLUE)
    elif kind=='factorial':
        draw_factorial(c,s)
    elif s.get('table'):
        t=s['table']
        widths=t.get('widths') or {'feature_cards':[320,600,520],'timeline':[600,420,420], 'literature':[280,580,580], 'operations':[520,290,315,315], 'robustness':[375,355,355,355], 'roadmap':[325,455,660], 'example':[260,560,390,230]}.get(kind)
        rh=58 if kind in ('operations','example') else 66
        end=table(c,t['headers'],t['rows'],y=240,widths=widths,row_h=t.get('row_height',rh),size=t.get('font_size',29))
        if bullets:
            bs=28 if kind in ('operations','example','roadmap') else 29
            end=c.bullet_list(bullets,95,end+20,1400,bs,gap=8 if kind=='roadmap' else 11)
            if end>715:c.warnings.append(f'Content meets takeaway band: {kind}, bottom={end:.1f}')
    elif s.get('chart'):
        chart=dict(s['chart']);chart['colors']=[BLUE,ORANGE];chart['min']=0;chart['max']=22;chart['ticks']=[0,5,10,15,20];chart['label_width']=450
        draw_chart(c,chart,x=90,y=255,w=1400,h=220)
        c.bullet_list(bullets,95,580,1400,29,gap=14)
    elif s.get('cards'):
        cards=s['cards']; n=len(cards);gap=28;cw=(1440-gap*(n-1))/n
        for i,item in enumerate(cards):card(c,80+i*(cw+gap),260,cw,370,item['title'],item['body'],item.get('color',TEAL))
    elif s.get('metrics'):
        metrics=s['metrics'];n=len(metrics);gap=28;cw=(1440-gap*(n-1))/n
        yy=245;hh=190 if kind=='share' else 220
        for i,m in enumerate(metrics):
            xx=80+i*(cw+gap);c.rect(xx,yy,cw,hh,WHITE,stroke=LIGHT,radius=14)
            fs=57
            while font(fs,True).getlength(m['value'])>cw-40:fs-=1
            c.text(m['value'],xx+20,yy+30,cw-40,fs,TEAL,True,align='center')
            c.text(m['label'],xx+25,yy+115,cw-50,28,NAVY,align='center')
        end=c.bullet_list(bullets,100,yy+hh+40,1380,30 if kind=='share' else 31,gap=16)
        if end>715:c.warnings.append(f'Content meets takeaway band: {kind}, bottom={end:.1f}')
    else:
        bs=29 if kind=='references' else 35
        gap=16 if kind=='references' else 31
        end=c.bullet_list(bullets,95,250,1390,bs,gap=gap)
        if end>715:c.warnings.append(f'Content meets takeaway band: {kind}, bottom={end:.1f}')
    c.takeaway(s.get('takeaway',''))
    return c


def to_pptx(slides, canvases, path, title):
    prs=Presentation();prs.slide_width=Inches(13.333333);prs.slide_height=Inches(7.5)
    prs.core_properties.title=title;prs.core_properties.subject='AML business interpretation of the completed counts × ports experiment'
    prs.core_properties.author='COMP9501 research project'
    scale=13.333333/W
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
                p=tf.paragraphs[0];p.text=o['text'];p.font.name=FONT;p.font.size=Pt(o['size']*.6);p.font.bold=o['bold'];p.font.color.rgb=rgb(o['color'])
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
                pdf.setFillColor(HexColor(o['color']));pdf.setFont('AML-Bold' if o['bold'] else 'AML',o['size'])
                xx=o['x'];yy=H-o['y']-o['size']*.88
                if o['align']=='center':pdf.drawCentredString(xx+o['w']/2,yy,o['text'])
                elif o['align']=='right':pdf.drawRightString(xx+o['w'],yy,o['text'])
                else:pdf.drawString(xx,yy,o['text'])
            elif k=='image':
                pdf.drawImage(str(o['path']),o['x'],H-o['y']-o['h'],o['w'],o['h'],mask='auto')
        pdf.restoreState();pdf.showPage()
    pdf.save()


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
        for i,page in enumerate(pdf):page.get_pixmap(matrix=fitz.Matrix(.7,.7)).save(preview/f'slide-{i+1:02d}.png')
    print(json.dumps({'slides':len(slides),'pptx':str(pptx_path),'html':str(html_path),'pdf':str(pdf_path),'layout_warnings':warnings},indent=2))

if __name__=='__main__':main()
