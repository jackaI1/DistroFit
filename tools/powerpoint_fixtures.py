"""Generate boundary-case presentations for independent Office schema validation."""
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from analysis import fit_candidates, report_payload, get_supported_distributions
from powerpoint_report import create_powerpoint

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
values = np.random.default_rng(27).gamma(2, 2, 240)
payload = report_payload(fit_candidates(values, list(get_supported_distributions())), values, {})
(out/'all-candidates.pptx').write_bytes(create_powerpoint(payload))
for name, rows in [('empty', []), ('infinite', deepcopy(payload['results'])), ('negative', deepcopy(payload['results']))]:
    fixture = deepcopy(payload)
    fixture['results'] = rows
    if name == 'infinite':
        for row in rows:
            row['Held-out NLL'] = 'inf'
    if name == 'negative':
        rows[0]['Held-out NLL'] = -2.5
    (out/f'{name}.pptx').write_bytes(create_powerpoint(fixture, title='A & B <review>'))
