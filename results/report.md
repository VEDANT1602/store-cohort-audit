# Store composition and the decision

Topic: retail operations. Decision: distinguish a change inside comparable stores from a change in the order mix.

The generator shifts volume from high-completion stores toward lower-completion stores while modestly improving each store's latent probability. My audit requires support in both periods, keeps the same common stores in both comparisons, and applies predeclared equal-store reference weights. Unsupported stores are reported instead of extrapolated.

Among 19 common supported stores, the raw completion difference is -26.71 percentage points. Fixed-mix standardization gives 4.27 points; the paired-store descriptive95%interval is [2.75,5.83] points. Reference-weight retention is 0.950. The excluded store and period coverage are preserved in decisions.json and metrics.json.

The sign reversal is a composition effect in an original simulation. These are observed before/after quantities, not an experiment or treatment effect. Equal-store weighting answers a different policy question from order-weighted averages. Stores are the resampling unit, and only nineteen supported stores limit uncertainty estimates. Next, I would agree the reference mix and population with operations owners before interpreting a region-wide dashboard.
