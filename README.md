# Store Cohort Audit

**A regional rate can fall even when comparable stores improve.**

I made store composition part of the decision instead of treating the aggregate as self-explanatory. The usual before/after dashboard mixes a change in store performance with a change in which stores received orders. My framework is **declare the store universe → require support in both periods → report raw and fixed-mix rates → retain coverage and exclusions**.

The original audit uses explicit equal-store reference weights and a paired store-cluster bootstrap. It reports the common-store raw comparison alongside standardization so a population change cannot quietly masquerade as a performance gain. [The report](results/report.md) explains the sign reversal in the generated fixture and why it is not causal evidence.


## Recorded result

Across **19 supported common stores**, the raw completion change is **-26.713 percentage points**. Holding the declared store mix fixed gives **+4.272 points**, with a descriptive paired-store interval **[+2.754, +5.831]**. One sparse store is excluded from both periods; retained reference weight is **95%**. This is composition analysis, not a treatment effect.

## Reproduce and inspect

Python 3.11, CPU only. No API keys, paid services, provider calls, customer records or external data download.

```bash
python -m venv .venv
# Activate the environment for your shell.
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run.py --output runs/local
```

`core.py` contains the generator and actual comparison. `data/dataset.json` is the committed original input. `results/decisions.json` preserves the evaluated rows/traces. `results/metrics.json` and `results/report.md` state the measured outcomes. `results/manifest.json` binds core source, input, and output bytes with SHA-256. A fresh run writes to the requested directory and leaves committed results available for comparison.

This is a new independent portfolio experiment. Its results do not establish historical employer/client outcomes, production adoption, or service scale. Read the [data card](docs/data-card.md) and [provenance](docs/provenance.md) before interpreting the numbers.
