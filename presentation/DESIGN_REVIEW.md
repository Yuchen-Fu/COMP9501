# Academic presentation review

Reviewed 15 November 2026 (UTC+08:00).

The presentation has been redesigned in response to feedback about crowded
slides, incomplete sentences, oversized numbers, and PowerPoint-drawn diagrams.

## Design changes

- Slides 2–4 now introduce the AML review workflow, equal transfer activity with
  different counterparties, and a three-transfer port-history example.
- All twelve figures are rendered in Python/Matplotlib and have sequential
  captions, Figure 1 through Figure 12. PNG exports use 300 dpi; SVG and PDF
  exports preserve vectors for reuse.
- White backgrounds, serif headings, restrained colors, and ordinary-size
  numerical annotations replace dashboard cards and large-number panels.
- Each results slide begins with its conclusion and supplies three concise,
  complete-sentence evidence bullets. Detailed qualifications remain in notes,
  with the essential scope also visible on the slides.
- PowerPoint retains editable narrative text and notes. Graphs enter as images;
  native shapes are limited to the page background and a horizontal page rule.

## Verification

The presentation was rebuilt into PowerPoint, PDF, standalone HTML, a contact
sheet, and nineteen slide previews. All nineteen PDF previews were visually
inspected. The builder reported no layout-boundary warnings.

Programmatic checks confirmed:

- Nineteen PowerPoint slides and nineteen PDF pages exist.
- The source titles and evidence bullets appear in both outputs.
- All PowerPoint speaker notes match the source.
- Each figure's embedded PowerPoint bytes exactly match its exported PNG.
- Figure numbering is consecutive, and every figure has PNG/SVG/PDF versions.
- No native chart objects are present; every slide contains only a background,
  a page rule, editable text, and its figure image where applicable.
- All slide objects stay within slide bounds.
- Fifty-five protected research files, including all fifty run/prediction files,
  the numerical summary, research report, and three core research scripts, retain
  their original SHA-256 hashes.

PDF previews are produced from the shared layout. PowerPoint was reopened and
checked structurally with python-pptx; it was not rendered in Microsoft
PowerPoint on this machine. Arial and Times New Roman are specified for common
PowerPoint availability, with compatible Liberation fonts used in the PDF.

## Scientific review

An independent content review checked the shortened claims against the completed
report and summary. It confirmed that the primary analysis uses the
validation-selected checkpoint and threshold, with zero-based epochs 1–4
eligible. Final-epoch results remain a sensitivity. The deck introduces F1 before
the results and does not claim an established doubling, a causal identity
mechanism, or reduced investigator workload.

Counts plus novelty remains supplementary. The five-epoch, synthetic-data,
transductive scope and the post-hoc nature of sensitivity analyses remain
visible. No model was trained, restarted, or selected during the redesign.
