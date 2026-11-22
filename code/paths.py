"""Repository-relative paths shared by every Python script in the package. Nothing here needs editing: all inputs
ship in data/, the Stata scripts write their results to output/estimates/, and the Python scripts write tables and
figures under output/. Scripts can be run from any working directory."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PIPELINE = DATA / "pipeline"              # the authors' harmonized occupation scores and occupation-by-quarter panels
CROSSWALKS = DATA / "crosswalks"          # O*NET to census and 2018 census to OCC2010 crosswalks; the 22 major groups
SCORING = DATA / "scoring"                # task-level scores and the summaries of the scoring runs
CELL_FD = DATA / "cell_fd"                # the occupation-cell first-difference files (inputs of the Stata scripts)
CELL_FE = DATA / "cell_fe"                # the occupation-by-quarter panels of the fixed-effects design
OUT = ROOT / "output"
ESTIMATES = OUT / "estimates"             # regression results written by code/stata/*.do, and the figure data files
TABLES = OUT / "tables"                   # LaTeX tables written by code/tables/
FIGURES = OUT / "figures"                 # figures written by code/figures/
for p in (TABLES, FIGURES, ESTIMATES): p.mkdir(parents=True, exist_ok=True)
