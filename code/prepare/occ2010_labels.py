#!/usr/bin/env python3
"""The IPUMS OCC2010 value labels (code, title), taken from the authors' CPS extract (IPUMS-CPS, not distributed).
Run by the authors only; writes data/pipeline/occ2010_labels.csv, read by code/tables/tabB-crosswalk.py."""
import os, pandas as pd
F = os.path.expanduser("~/AI@Work/Research/AAICELO/data/cps_w_occ2010exp_june26.dta"); HERE = os.path.dirname(os.path.abspath(__file__))
labs = pd.io.stata.StataReader(F).value_labels()["OCC2010"]
pd.DataFrame(sorted(labs.items()), columns=["occ2010", "title"]).to_csv(os.path.join(HERE, "..", "..", "data", "pipeline", "occ2010_labels.csv"), index=False)
print(len(labs), "labels")
