# Replication package: Advancing AI Capabilities and Evolving Labor Outcomes

Jacob Dominski, Tyler Boes, and Yong Suk Lee (University of Notre Dame). Working paper: https://arxiv.org/abs/2507.08244.

The paper scores the AI exposure of every occupation at four capability stages (pre-generative machine learning, chatbots,
reasoning models, AI agents) from language-model ratings of O*NET task statements, and relates the change in exposure across
occupations to labor market outcomes in the Current Population Survey (CPS) through June 2026.

This repository contains the data and code that produce every table and figure of the paper and its Online Appendix.
Nothing is read from outside the repository.

## Requirements

- Stata 17 or later with `reghdfe` and `ftools` (`ssc install reghdfe ftools`).
- Python 3.9 or later with pandas, numpy, statsmodels, matplotlib, and pyarrow (`requirements.txt` has the versions used).

## How to run

Two steps, from the repository root (the folder that holds `data/`, `code/`, and `output/`). The regressions are estimated
in Stata and the tables and figures are drawn in Python, so there is one runner for each.

```
stata-se -b do run_all.do       # step 1, about a minute: estimates every regression
                                #   -> output/estimates/*.csv, one row per coefficient
python3 run_all.py              # step 2, about a minute: builds every table and figure
                                #   -> output/tables/*.tex and output/figures/*.png
python3 run_all.py --check      # step 2 again, then lists any output that differs from the committed one
```

Step 2 reads the CSV files that step 1 writes. The repository ships those files and all tables and figures, so step 2 can be
run on its own, and `--check` confirms that a rebuild matches what is committed. To run a single script: Stata scripts are
run from the repository root (`do code/stata/01_fd_main.do`); Python scripts can be run from anywhere
(`python3 code/figures/fig3-who-holds-jobs.py`).

## What you get

### Step 1: the regressions (`code/stata/`, results in `output/estimates/`)

| Script | What it estimates | Result file |
|---|---|---|
| `01_fd_main.do` | Three-year first differences on occupation cells: headline window (2026Q1 vs 2023Q1 and 2026Q2 vs 2023Q2), pre-AI placebo window (2021Q4 vs 2018Q4 through 2022Q3 vs 2019Q3), base period in 2022, single end quarters; all workers, by age, by education, by age and education; quarter cells and six-month averages; harmonized and 2018 census occupation codes | `fd_main.csv` |
| `02_fd_specification.do` | The headline regression under 37 alternative specifications and samples, including alternative exposure measures and leaving each major occupation group out | `fd_specification.csv` |
| `03_fd_composition.do` | Three-year differences of outcomes within the part-time and within the full-time workforce of each occupation | `fd_composition.csv` |
| `04_fd_telework.do` | The headline regression with remote-work controls, all workers and by group | `fd_telework.csv` |
| `05_fe_main.do` | Occupation-by-quarter fixed-effects regressions: pooled, era split at 2025Q1, interpolated exposure; two windows; all workers, by age, by education | `fe_main.csv` |
| `06_fe_specification.do` | The era-split regression under 33 alternative specifications and samples | `fe_specification.csv` |
| `07_fe_telework.do` | The fixed-effects regressions with remote-work controls | `fe_telework.csv` |
| `08_individual_fe.do` | The individual-level fixed-effects estimates, read from the saved estimates in `data/individual_fe/estimates/` (see Data) | `individual_fe.csv` |

Each result file has one row per coefficient: estimate, standard error, p-value, N, number of occupation clusters,
R-squared, and the outcome mean in the estimation sample. The header of each script lists its specification, inputs, and
output.

### Step 2: the tables and figures (`code/tables/`, `code/figures/`, results in `output/`)

Paper:

| Exhibit | Output file | Script |
|---|---|---|
| Table 1, largest and smallest exposure changes | `tables/tab2-3-top-bottom.tex` | `tables/tab2-3-top-bottom.py` |
| Table 2, exposure and adoption | `tables/tab2-4-adoption-correlations.tex` | `tables/tab2-4-adoption-correlations.py` |
| Table 3, headline and placebo windows | `tables/tab3-headline.tex` | `tables/regression_tables.py` |
| Table 4, by age and by education | `tables/tab4-by-group.tex` | `tables/regression_tables.py` |
| Table 5, occupation fixed effects | `tables/tab5-fe.tex` | `tables/regression_tables.py` |
| Figure 1, raw relation by age | `figures/fig1-raw-intro.png` | `figures/fig-scatter-groups.py` |
| Figure 2, exposure by stage and rating | `figures/fig2-2-raters-dimensions.png` | `figures/fig2-2-raters-dimensions.py` |
| Figure 3, groups and cells, headline and placebo | `figures/fig3-who-holds-jobs.png` | `figures/fig3-who-holds-jobs.py` |
| Figure 4, decomposition scatters | `figures/fig4-decomposition-two-panels.png` | `figures/fig6-decomposition.py` |
| Figure 5, contributions by major group | `figures/fig-decomposition-groups-vertical.png` | `figures/fig6-decomposition.py` |
| Figure 6, windows and designs | `figures/fig-timing-designs.png` | `figures/fig-timing-designs.py` |
| Figure 7, three-year difference by end quarter | `figures/fig-timing-byquarter.png` | `figures/fig-timing-byquarter.py` |
| Figure 8, alternative explanations | `figures/fig6-alternatives.png` | `figures/fig6-alternatives.py` |

Online Appendix:

| Exhibit | Output file | Script |
|---|---|---|
| Tables A.3 to A.11, measurement (cost, subtasks, pilot, agreement, weights, adoption regressions, worked example, whole-task comparison) | `tables/tabA-*.tex`, `tabB-whole-task.tex` | `tables/tabA-measurement.py`, `tabA-worked-example.py`, `tabB-whole-task.py` |
| Figure A.2, adoption against each measure | `figures/figB-adoption-all.png` | `figures/fig2-3-adoption.py` |
| Tables B.1 and B.2, crosswalk and unscored codes | `tables/tabB-crosswalk.tex`, `tabB-unscored.tex` | `tables/tabB-crosswalk.py` |
| Figure B.1, exposure across the workforce | `figures/fig3-1-frontier.png` | `figures/fig3-1-frontier.py` |
| Table B.3, characteristics by quartile | `tables/tab3-1-characteristics.tex` | `tables/tab3-1-characteristics.py` |
| Figures B.2 to B.4, outcomes by quartile, gaps by age and education | `figures/fig3-3-outcomes-quartiles.png`, `fig3-4-gaps-age.png`, `fig3-5-gaps-edu.png` | `figures/sec3_figures.py` |
| Table C.2, headline and placebo windows in full | `tables/tabC2-fd-full.tex` | `tables/regression_tables.py` |
| Table C.3, fixed effects, occupation (A) and individual (B) level | `tables/tabC3-fe-windows-A.tex`, `-B.tex` | `tables/regression_tables.py` |
| Table C.4, within part-time and full-time | `tables/tabC4-composition.tex` | `tables/regression_tables.py` |
| Tables D.1 to D.3, age by education jointly | `tables/tabD1-ageedu-s4.tex`, `tabD2-ageedu-s3.tex`, `tabD3-ageedu-secondary.tex` | `tables/regression_tables.py` |
| Table D.4, fixed effects by group | `tables/tabD4-fe-groups.tex` | `tables/regression_tables.py` |
| Table D.5, entry and exit flows | `tables/tabD-flows.tex` | `tables/tabD-flows.py` |
| Tables E.1 and E.2, decomposition by major group and top occupations | `tables/tab8-1-decomposition.tex`, `tab8-2-top-occupations.tex` | `tables/tab8-decomposition.py` |
| Figure E.1, decomposition by age group | `figures/fig6-resid-panels.png` | `figures/fig-scatter-groups.py` |
| Tables F.1 to F.5, specification checks | `tables/tabF1-fd-spec-primary.tex`, `tabF2-fd-spec-secondary.tex`, `tabF3-fe-spec.tex`, `tabF4-logo-1-11.tex`, `tabF5-logo-12-22.tex` | `tables/regression_tables.py` |
| Tables F.6 to F.8, remote work | `tables/tabF6-fd-telework.tex`, `tabF7-fd-telework-u30.tex`, `tabF8-fe-telework.tex` | `tables/regression_tables.py` |
| Tables F.9 and F.10, 2018 census codes | `tables/tabF9-fd-cps-code.tex`, `tabF10-fd-cps-groups.tex` | `tables/regression_tables.py` |
| Tables G.1 and G.2, placebo window by group | `tables/tabG1-placebo-groups.tex`, `tabG2-placebo-ageedu.tex` | `tables/regression_tables.py` |
| Figure G.1, by end quarter and age group | `figures/figG1-byquarter-groups.png` | `figures/figG1-byquarter-groups.py` |

Paths are relative to `output/` and `code/`. Tables A.1, A.2, and C.1 and Figure A.1 are text typeset in the paper and have no
data. The scoring prompts of Appendix A are in `data/scoring/prompts/`. The figure scripts also write a few variants the paper
does not use, listed in their headers.

## Data

`data/README.md` describes every file. The CPS-based files are occupation-level aggregates built from an IPUMS-CPS extract
(basic monthly samples, January 2017 to June 2026); the extract itself cannot be redistributed under IPUMS terms and is not
included. The one exhibit estimated on individual records, Appendix Table C.3 Panel B, is therefore reproduced from the saved
Stata estimates in `data/individual_fe/estimates/`; the do-files that built the individual-level file from the extract and
estimated those regressions are in `code/stata/individual_fe_source/` for a reader with IPUMS access.

Other sources: O*NET task statements (U.S. Department of Labor, public domain); Real-Time Population Survey adoption shares by
occupation (Bick, Blandin, Deming, and Schumacher, 2026); the exposure measures of Eloundou et al. (2024) and Felten et al.
(2023); Dingel and Neiman (2020) teleworkability; and the authors' model ratings (Claude Haiku 4.5, GPT-5.6-luna, Gemini 3.1
Flash-Lite, DeepSeek V4 Flash), whose task-level scores are in `data/scoring/master_task_scores.csv`.

## License and contact

Code, the authors' scores, and the built exhibits: Creative Commons Attribution-NonCommercial 4.0 (`LICENSE`). Third-party
data remain subject to their sources' terms. Contact: Yong Suk Lee, University of Notre Dame (yong.s.lee@nd.edu).
