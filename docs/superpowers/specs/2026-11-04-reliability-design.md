# Reliability analysis design

I want to estimate equipment life without treating still-running units as failures or discarding their operating hours. This extends the existing Streamlit app and Python command-line workflows.

## Scope and approach

Use one independent lifetime per row, with positive observed age and `failed` equal to 1 (failure) or 0 (right-censored suspension). All rows use one age unit and one comparable population. Fit zero-location Weibull, lognormal and exponential models by censored maximum likelihood. Retain an empirical Kaplan-Meier curve even when no model can be estimated. Show fitted survival, hazard and censored probability diagnostics. Report mean life and B10, the age by which 10% fail, with configurable confidence intervals.

My implementation choice is a small standalone statistics module, a separate Streamlit page, and a command-line exporter. Reusing ordinary uncensored fitting would discard exposure information; a separate application would duplicate the existing app. No new dependencies are needed. The user has explicitly authorized implementation through merge without approval pauses.

## Statistical contract

- Censored observations contribute log survival, failures contribute log density. Location is fixed at zero.
- Use normalized log ages for numerical stability. Reject unidentifiable or boundary fits instead of emitting plausible defaults.
- Compute approximate confidence intervals with the observed-information matrix and the delta method on log life metrics. Explain their large-sample limitations. Kaplan-Meier bounds use Greenwood variance on the log-log scale.
- Process failures before suspensions at the same age. Include risk counts and suspension markers. Probability plots use empirical Kaplan-Meier failure probabilities, excluding undefined endpoints.
- MTBF is mean life only for independent replacement cycles restored to as-new condition; for first-life units the same quantity is MTTF. This is not a repairable-system trend model or an automatic replacement recommendation.
- Do not infer life with zero observed failures. Preserve Kaplan-Meier results and explicit exclusions. Require two distinct observed failures for two-parameter fits.

## Deliverables and constraints

`reliability.py` owns validated inputs, fitting, intervals and curves. `reliability_report.py` owns deterministic synthetic data and CSV/JSON/PNG export. `pages/2_Reliability.py` exposes editing/upload, fitting and downloads. A generated equipment log and a worked maintenance guide explain interpretation and assumptions. Existing features and dependencies remain intact. Tests check published NIST estimates, hand calculations, independent SciPy censored fits, scaling, invalid and sparse inputs, CLI and real Streamlit behavior. CI runs the full suite and exports the example. README stays first-person, plain at the top, with no keyword or skills section.
