# AML business presentation

The deck introduces the AML monitoring problem before the data, literature,
research question, methods, and results. It has 16 main slides for approximately
16–18 minutes, followed by three appendices for questions.

The revised visual edition replaces the main data and results tables with
plots and uses graph diagrams for relationship history, the experimental design,
the literature, and validation priorities. Exact tabular values and the full
spoken explanation remain in the accompanying Markdown and speaker notes.

- `AML_BUSINESS_SLIDES.pptx`: editable PowerPoint, including speaker notes.
- `AML_BUSINESS_SLIDES.pdf`: 19 slides for reading or sharing.
- `AML_BUSINESS_SLIDES.html`: standalone browser presentation; use the navigation
  buttons or arrow keys, and the notes button to reveal the speaking script.
- `slides.json`: slide content, numerical values, sources, and speaker notes.
- `build_slides.py`: produces PowerPoint, HTML, PDF, and slide previews.
- `figures/`: standalone PNG and SVG statistical plots.
- `plot_results_slides.py`, `plot_data_slide.py`: regenerate figures from the
  audited results; `intro_visuals.py` draws the introductory diagrams.
- `../AML_BUSINESS_PRESENTATION.md`: introductory business narrative, presentation
  plan, complete slide text, and speaker notes.

Rebuild in a separate plotting/presentation interpreter, without changing the
training environment:

```bash
python3 presentation/plot_results_slides.py
python3 presentation/plot_data_slide.py
python3 presentation/build_slides.py
```

The builder requires Python 3.10 or later, `python-pptx`, `Pillow`, `reportlab`,
and `PyMuPDF`, plus Liberation Sans fonts at
`/usr/share/fonts/truetype/liberation/`. All are present in the cloud environment
used to create these files. Plot generation additionally uses NumPy and
Matplotlib in the presentation interpreter. Native PowerPoint text,
diagrams, and shapes are editable. Statistical plots are embedded as high-resolution
images; their SVG exports and Matplotlib source are included for further editing.

All numerical findings derive from `../results/summary.json` and the completed
research report. The operational counts are means across five seeds at each
model's own validation-selected threshold. They are transaction flags, not
unique investigations or measured investigator costs. No additional models,
thresholds, training epochs, or research outcomes were selected for this deck.
