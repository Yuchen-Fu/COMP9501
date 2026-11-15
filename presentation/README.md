# AML research presentation

The academic edition has 16 main slides and three appendices. It introduces the
AML review problem before the data, literature, research question, methodology,
findings, and conclusion. Slides 2–4 explain review capacity, relationship
breadth, and port indices through simple examples.

Every graph, conceptual diagram, and displayed feature table is rendered in
Python with Matplotlib. PowerPoint embeds the resulting images; it does not
construct the figures from native shapes. The deck uses a white background,
serif headings, restrained colors, complete sentences, and numbered captions
from Figure 1 to Figure 12. Results lead with a conclusion and supporting bullets.
There are no oversized number panels.

- [PowerPoint](AML_BUSINESS_SLIDES.pptx) retains editable slide text and speaker notes.
- [PDF](AML_BUSINESS_SLIDES.pdf) contains all 19 slides.
- [HTML](AML_BUSINESS_SLIDES.html) is a standalone browser presentation; arrow keys
  navigate, and the notes button reveals the speaking script.
- [Slide overview](preview/contact-sheet.png) previews the full deck.
- [Speaker script](../AML_BUSINESS_PRESENTATION.md) follows the same source content.
- [slides.json](slides.json) is the source for displayed text, captions, and notes.
- [figures/](figures/) contains 300-dpi PNGs and standalone SVG/PDF versions.

Rebuild with a plotting/presentation interpreter, without changing the training
interpreter:

```bash
python3 presentation/plot_intro_figures.py
python3 presentation/plot_results_slides.py
python3 presentation/plot_data_slide.py
python3 presentation/build_slides.py
```

The three plotting scripts produce the figures. The builder inserts them and
generates PowerPoint, HTML, PDF, previews, and the Markdown speaker script from
one layout. Required packages are NumPy, Matplotlib, python-pptx, Pillow,
ReportLab, and PyMuPDF. The PDF renderer uses Liberation fonts under
`/usr/share/fonts/truetype/liberation/`; PowerPoint uses the compatible Arial and
Times New Roman families. These dependencies are present in the cloud plotting
interpreter.

Numerical values come from `../results/summary.json` and the audited dataset
records. Primary results use validation-selected checkpoints and thresholds;
final-epoch and time-slice results remain disclosed sensitivities. The novelty
cell is supplementary. The redesign does not change training, predictions,
results, or research conclusions.

Transaction flags are not unique investigations or measured investigator costs.
The statistical intervals describe seed variation on this fixed synthetic
dataset and five-epoch protocol. See [DESIGN_REVIEW.md](DESIGN_REVIEW.md) for
export verification and design checks.
