# Independent review of analysis implementation

Reviewed the current `src/analyze.py` without editing it. The review identified
a Fieller-set topology error for strongly asymmetric numerator/denominator
scales: a relative coefficient tolerance discarded a small but nonzero quadratic
term. The implementation agent corrected this by preserving nonzero polynomial
degree, and added regression tests. The report now prints actual Fieller interval
sets, including disjoint unions and infinite endpoints when the share is not
identified. Unsupported wording about a published 100-epoch budget was corrected.

Checked paired seed ordering, sample covariance divided by five, t(4) intervals,
ratio-to-share interval reversal, original validation-selected epochs 1–4 with
earliest ties, final/day sensitivities, strict completeness of the 20 core runs,
and explicit omission of an incomplete supplementary cell. No remaining blocking
issue was found in those paths.

An independent randomized test compared the returned Fieller confidence sets to
direct inversion of the paired-residual t test, rather than reusing the quadratic
solver. It generated 2,000 numerator/denominator sample pairs with independent
scales between 1e-8 and 1e8. There were **0 mismatches in 119,621 membership checks**.
Another 379 candidate points fell within eight floating-point ULPs of a transformed
share-set endpoint and were excluded from exact membership comparisons because
rounding a ratio to `1-ratio` can move a representable endpoint. This numerical
boundary caveat does not justify discarding polynomial degree.

The standalone loader checks that hyperparameters match across all runs. Exact
fixed hyperparameters are checked by the separate resume preflight, so the full
research workflow has that protection. The analysis must still be run on the
completed real design; fixture and numerical tests do not establish a scientific
conclusion. Secondary intervals remain exploratory and same-sign agreement is
not significance or equivalence.

Reviewed source SHA-256: `198ff02b8f0a4de85a3d929627c878e04432bf53d449b96f228164b229f0b022`.
