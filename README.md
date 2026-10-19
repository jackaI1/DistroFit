# DistroFit

A local Streamlit app for exploring numeric data and comparing fitted probability distributions. Use generated sample data, paste numbers, or upload a CSV and choose a numeric column. The interface includes outlier filtering, histogram controls, and fit rankings.

https://github.com/user-attachments/assets/00c28d05-d43e-4624-865b-ed5906c0648e

## Run locally

Use Python 3.12 and run these commands from the repository root:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run DistroFit.py --server.headless=true
```

Open the local URL printed by Streamlit. To choose a different port, add `--server.port=8502` to the last command. Stop the app with Ctrl-C.

For an initial check, use generated sample data. Keep private CSVs and other personal data outside this repository.

## Analysis workflow

- Select candidate families to fit them together in a bounded parallel batch. Parameters are learned from a seeded training split; the winner has the lowest mean held-out negative log likelihood. The table also compares training loss, AIC, BIC, histogram error and held-out KS distance. Failed fits and support violations are shown explicitly.
- Inspect the tail survival curve and model versus held-out exceedance rates above the training 95th percentile. Q-Q, CDF residual and density residual views show where the selected curve misses.
- Paste another scenario to score the existing models without refitting. Adjust shape, location and scale in the Manual tab, with PDF or CDF views. Relative controls offset the location in training standard deviations and multiply the scale; **Reset shape** restores the training parameters.
- Click **Download reproducible report** for a PDF containing the method, settings, library versions, candidate parameters and scores, failures, tail checks, plots, current manual parameters, scenario results, every input observation, and training/held-out membership. The first-page PDF annotation also stores the complete analysis as JSON.

## Checks and limitations

Run the synthetic regression and Streamlit interaction tests with:

```sh
python -m unittest discover -s tests -v
python -m compileall -q DistroFit.py analysis.py tests
```

Direct dependencies are pinned to the tested Python 3.12 environment. No separate lint, typecheck or packaging build is configured. At least eight finite, varying observations are required. Nonfinite observations are removed with a count; Z-score/IQR outlier filtering is optional and occurs before splitting, so filtering can change the target population and hide tails. AIC/BIC/SSE describe training fit and do not select the winner. Infinite held-out or scenario loss means a model rejects at least one observation outside its support. Tail flags use an exploratory 95% binomial prediction interval, without multiple-test correction. Repeatedly tuning against the same held-out sample makes it less independent. Manual adjustments and scenario rankings do not change the held-out winner. Distribution fits are exploratory and need independent validation before use in decisions.
## License

MIT, see LICENSE. Third-party components are listed in THIRD_PARTY_NOTICES.md.

