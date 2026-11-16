"""Recompute the prospective paired-t sensitivity from the saved pilot differences."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.stats import nct, t

ROOT = Path(__file__).resolve().parents[2]


def minimum_detectable_effect(n, sd, alpha=.05, target=.8):
    critical = t.ppf(1 - alpha / 2, n - 1)
    def power(delta):
        noncentrality = delta * np.sqrt(n) / sd
        # Reflection gives the left tail without cancellation at negative t.
        return nct.sf(critical, n - 1, noncentrality) + nct.sf(critical, n - 1, -noncentrality)
    return brentq(lambda delta: power(delta) - target, 0, 3 * sd)


def main():
    saved = json.loads((ROOT / 'results/representation_followup/planning_power.json').read_text())
    sd = float(np.std(saved['pilot_differences'], ddof=1))
    assert np.isclose(sd, saved['pilot_difference_sd'], atol=1e-12)
    values = {str(n): minimum_detectable_effect(n, sd, saved['alpha'], saved['target_power']) for n in (5, 10)}
    for n, value in values.items():
        assert np.isclose(value, saved['mdes_using_pilot_sd'][n], atol=1e-8)
    print(json.dumps({'paired_sd_f1_points': sd, 'mdes_f1_points': values,
                      'interpretation': saved['limitations']}, indent=2))


if __name__ == '__main__':
    main()
