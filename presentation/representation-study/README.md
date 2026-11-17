# Making pair history explicit

**Follow-up notice (17 November 2026):** the completed controlled addition experiment did not establish an explicit-novelty benefit. Its [actual server report](../../results/representation_8h/FOLLOWUP_REPORT.md) and [import provenance](../../results/representation_8h/IMPORT_NOTES.md) are now available. The decks below remain the historical five-epoch presentation; the [revised storyline](FOLLOWUP_STORYLINE.md) describes the required research update.

This edition centers the presentation on a specific representation question:

> Under the same five-epoch GIN protocol, does explicitly encoding pair novelty improve AML prediction when that fact is already recoverable from historical counts and port numbers?

The presentation contains 17 main slides and three appendices. Egressy et al.
receive one background slide; the original factorial, supplementary representation
comparison, learning trajectories, error analysis and sensitivity checks form
the main evidence sequence. The original counts × ports estimand retains its
primary status. The novelty comparison remains supplementary, and the newly
displayed learning curves are descriptive views of existing saved logs.

- [PowerPoint](AML_REPRESENTATION_STUDY.pptx)
- [PDF rendered from the PowerPoint](AML_REPRESENTATION_STUDY.pdf)
- [Standalone browser presentation](AML_REPRESENTATION_STUDY.html)
- [Slide overview](preview/contact-sheet.png)
- [Speaker notes](SPEAKER_NOTES.md)
- [Detailed update rationale in Chinese](UPDATE_NOTES.md)
- [Editable content source](slides.json)

The color palette and typography follow the user's refined deck: cream pages,
navy and blue statement pages, EB Garamond headings and Inter body text. All
eleven diagrams and graphs are rendered in Python and numbered consecutively.
PowerPoint embeds the PNG figures; standalone SVG/PDF versions remain available.
There are no native PowerPoint charts or diagram objects.

## Rebuild

From the repository root:

```bash
python presentation/representation-study/plot_conceptual_figures.py
python presentation/representation-study/plot_representation_figures.py
python presentation/representation-study/build_slides.py
```

The scripts require NumPy, Matplotlib, Pillow, python-pptx and PyMuPDF. PDF and
preview generation additionally require LibreOffice (`soffice`). Use
`--skip-render` only to generate PowerPoint, HTML and the Markdown notes without
rendering. Bundled static Inter and EB Garamond fonts retain their SIL Open Font
License notices. The builder uses an isolated LibreOffice profile and font cache.

## Evidence and validation

All result figures read the completed study's `results/summary.json` or saved
run logs. No model was trained, no checkpoint was reselected, and no new hypothesis
test was added for this edition. In particular, the learning curves show every
saved epoch. CP's final-epoch mean F1 is 39.94; its validation-selected mean F1 is
39.57. These correspond to different, disclosed selections.

The claim is improved prediction under the tested representation and protocol.
It does not identify a failure to infer novelty inside the model. Replacing ports
also removes rank information and changes numerical form and input dimension.
The study does not establish convergence, a new expressive-power theorem, a
globally novel feature, or deployment benefit.

The actual exported PowerPoint was rendered with LibreOffice and its twenty
pages visually reviewed. Numerical and narrative claims received a separate
review against the completed report. Source text, notes, figure embedding,
numbering and slide bounds were checked programmatically. Fifty-five protected
research files retain their pre-edit hashes. Rendering in Microsoft PowerPoint
itself was not performed; the bundled fonts can be installed if a local viewer
substitutes fonts.
