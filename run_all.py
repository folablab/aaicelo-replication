#!/usr/bin/env python3
"""Build every table and figure of the paper and the Online Appendix from the data in data/ and the regression results in
output/estimates/ (written by run_all.do).

    python3 run_all.py            builds everything into output/tables/ and output/figures/ (about five minutes)
    python3 run_all.py --check    the same, then lists every output file that differs from the one committed in the repository

Each step is a script in code/tables/ or code/figures/; any of them can be run alone, from any working directory, with
python3 code/<folder>/<script>.py. Run run_all.do first (or use the committed results in output/estimates/)."""
import hashlib, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent
STEPS = [
    ("1. regression tables from output/estimates/", "code/tables/regression_tables.py"),
    ("2. tables built from the data", "code/tables/tab2-3-top-bottom.py", "code/tables/tab2-4-adoption-correlations.py", "code/tables/tab3-1-characteristics.py",
     "code/tables/tab8-decomposition.py", "code/tables/tabA-measurement.py", "code/tables/tabA-worked-example.py", "code/tables/tabB-crosswalk.py",
     "code/tables/tabB-whole-task.py", "code/tables/tabD-flows.py"),
    ("3. figures", "code/figures/fig-scatter-groups.py", "code/figures/fig6-decomposition.py", "code/figures/fig-timing-designs.py", "code/figures/fig-timing-byquarter.py",
     "code/figures/fig3-who-holds-jobs.py", "code/figures/fig6-alternatives.py", "code/figures/figG1-byquarter-groups.py", "code/figures/sec3_figures.py",
     "code/figures/fig2-2-raters-dimensions.py", "code/figures/fig2-3-adoption.py", "code/figures/fig3-1-frontier.py"),
]
check = "--check" in sys.argv
missing = [f for f in ["fd_main", "fd_specification", "fd_composition", "fd_telework", "fe_main", "fe_specification", "fe_telework", "individual_fe"]
           if not (ROOT / "output/estimates" / f"{f}.csv").exists()]
if missing: sys.exit("missing regression results in output/estimates/: " + ", ".join(missing) + ". Run run_all.do first.")
def outputs(): return [p for p in (ROOT / "output").rglob("*") if p.is_file() and p.suffix in (".tex", ".png", ".csv")]
def body(p): return re.sub(r"(?m)^%.*\n", "", p.read_text()).encode() if p.suffix == ".tex" else p.read_bytes()   # .tex compared without comment lines
before = {p: (hashlib.sha256(p.read_bytes()).hexdigest(), hashlib.sha256(body(p)).hexdigest()) for p in outputs()} if check else {}
for title, *scripts in STEPS:
    print(f"\n==== {title}", flush=True)
    for s in scripts:
        print("--", pathlib.Path(s).name, flush=True)
        r = subprocess.run([sys.executable, str(ROOT / s)], cwd=ROOT, capture_output=True, text=True)
        if r.returncode: print(r.stdout[-2000:], r.stderr[-4000:]); sys.exit(f"failed: {s}")
if check:
    print("\n==== check against the files that were in output/ before this run")
    changed = 0
    for p in sorted(outputs()):
        if p not in before: print("new:", p.relative_to(ROOT)); changed += 1; continue
        full, content = before[p]
        if hashlib.sha256(body(p)).hexdigest() != content: print("changed:", p.relative_to(ROOT)); changed += 1
        elif hashlib.sha256(p.read_bytes()).hexdigest() != full: print("comment lines only:", p.relative_to(ROOT))
    print("every output reproduces the committed version" if not changed else f"{changed} files differ from the committed version")
print("\ndone")
