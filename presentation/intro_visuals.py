"""Native editable introductory diagrams for the AML presentation.

Each function draws into the shared 1600×900 Canvas; the caller owns headers,
takeaway bands, and footers. The relationship networks are illustrations, not
sampled or labelled dataset examples.
"""
from pathlib import Path

NAVY = '#14273F'
TEAL = '#007E87'
BLUE = '#247BB4'
ORANGE = '#C76225'
PURPLE = '#8061A8'
MUTED = '#5E6D7D'
LIGHT = '#E8EFF3'
WHITE = '#FFFFFF'


def _account(c, x, y, name, color=NAVY, radius=31):
    c.circle(x, y, radius, color)
    c.text(name, x-radius, y-19, 2*radius, 31, WHITE, True, align='center')


def draw_feature_history(c, s):
    """Show how sender-side counts, outgoing ports, and novelty evolve."""
    c.text('Earlier\nhistory', 80, 258, 195, 29, MUTED, True)
    c.text('Prior transfers /\ndistinct partners', 80, 435, 205, 25, NAVY, True)
    c.text('Outgoing port\n(local rank)', 80, 521, 205, 26, NAVY, True)
    c.text('Pair novelty', 80, 609, 205, 27, NAVY, True)
    events = [('a', 0, 0, 0, 1), ('b', 1, 1, 1, 1),
              ('a', 2, 2, 0, 0), ('c', 3, 2, 2, 1)]
    partner_colors = {'a': BLUE, 'b': TEAL, 'c': PURPLE}
    for i, (partner, total, distinct, port, novelty) in enumerate(events):
        x = 305 + 300*i
        color = TEAL if novelty else ORANGE
        c.rect(x, 245, 270, 405, WHITE, stroke=LIGHT, radius=14)
        c.rect(x, 245, 270, 7, color, radius=3)
        c.text(f'{i+1}.  u → {partner}', x+15, 269, 240, 33, NAVY, True, align='center')
        _account(c, x+65, 345, 'u')
        _account(c, x+205, 345, partner, partner_colors[partner])
        c.line(x+100, 345, x+168, 345, partner_colors[partner], 4, True)
        c.text('First contact' if novelty else 'Repeated pair',
               x+15, 393, 240, 26, color, True, align='center')
        c.text(f'{total} / {distinct}', x+15, 445, 240, 37, NAVY, True, align='center')
        c.text(str(port), x+15, 532, 240, 39, partner_colors[partner], True, align='center')
        c.text(str(novelty), x+15, 606, 240, 35, color, True, align='center')
        if i<3:
            c.line(x+276, 287, x+294, 287, MUTED, 3, True)
    c.text('Sender-side illustration. Counts are measured before the current transfer; the model also receives receiver-side counts.',
           80, 672, 1440, 25, MUTED)


def draw_dataset(c, s):
    """Pair an illustrative multigraph with the verified dataset scale."""
    c.rect(80, 245, 780, 435, WHITE, stroke=LIGHT, radius=14)
    c.text('Accounts connected by individual transfers', 105, 265, 730, 30, NAVY, True)
    # Repeated A→B transfers are separate directed edges; remaining arrows
    # illustrate additional counterparties rather than actual labelled records.
    pos = {'A': (470, 465), 'B': (235, 365), 'C': (700, 365),
           'D': (700, 570), 'E': (235, 570)}
    for offset in (-13, 0, 13):
        c.line(435, 450+offset, 270, 378+offset, BLUE, 3, True)
    for x1,y1,x2,y2 in [(505,450,665,378),(498,485,669,555),
                         (270,557,435,482),(235,402,235,532),
                         (665,570,270,570)]:
        c.line(x1,y1,x2,y2,TEAL,3,True)
    for name,(x,y) in pos.items():
        _account(c,x,y,name,NAVY if name=='A' else TEAL,40 if name=='A' else 34)
    c.text('Account nodes  •  Transfer arrows', 105, 626, 730, 27, MUTED, align='center')
    for i,m in enumerate(s['metrics']):
        y=245+145*i
        c.rect(915,y,605,128,WHITE,stroke=LIGHT,radius=14)
        c.text(m['value'],940,y+15,555,48,TEAL,True,align='center')
        c.text(m['label'],940,y+78,555,29,NAVY,align='center')
    c.text('Illustrative graph; no node or edge is labelled suspicious.', 80, 681, 1440, 24, MUTED)


def draw_timeline(c, s):
    """Embed the audited daily-data plot."""
    image_path = Path(__file__).resolve().parent/'figures/temporal_shift.png'
    c.image(image_path, 80, 235, 1440, 455, 'Daily transaction volume and laundering prevalence, with temporal split periods.')


def draw_literature(c, s):
    """Move from architectural foundations and data to the explanatory gap."""
    items = [
        ('2019', 'Graph model',
         'GIN studies how neighborhood aggregation distinguishes graph structure.',
         'Xu et al. · ICLR', BLUE),
        ('2023', 'Labelled AML data',
         'Financial simulation supplies transactions and laundering labels.',
         'Altman et al. · NeurIPS', TEAL),
        ('2024', 'Ports improve GIN',
         'Local ranks tag counterparties. HI-Small F1: 28.70 → 54.85.',
         'Egressy et al. · AAAI', PURPLE),
        ('This study', 'Explanation test',
         'Do counts remove the port benefit? What does explicit pair novelty add?',
         'Completed factorial experiment', ORANGE),
    ]
    c.line(245,277,1355,277,LIGHT,7)
    for i,(year,title,body,citation,color) in enumerate(items):
        x=80+370*i
        c.circle(x+165,277,13,color)
        c.text(year,x,234,330,31,color,True,align='center')
        c.rect(x,315,330,355,WHITE,stroke=LIGHT,radius=14)
        c.rect(x,315,330,8,color,radius=4)
        c.text(title,x+25,344,280,33,color,True)
        c.text(body,x+25,423,280,30,NAVY)
        c.text(citation,x+25,612,280,24,MUTED)
        if i<3:
            c.line(x+343,492,x+362,492,color,3,True)
