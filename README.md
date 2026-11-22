# Replication package: Advancing AI Capabilities and Evolving Labor Outcomes

Jacob Dominski, Tyler Boes, and Yong Suk Lee (University of Notre Dame). This repository holds the cleaned data and the
code that estimate every regression of the paper and its Online Appendix and build every table and figure. It is
self-contained: nothing is read from outside the repository. The working paper is at https://arxiv.org/abs/2507.08244;
the journal version will be linked when it appears.

The paper constructs an occupational AI exposure score at four capability stages (pre-generative machine learning, chatbots,
reasoning models, AI agents) by having three language models rate the subtasks of every O*NET task, and relates the change in
exposure across occupations to labor market outcomes in the Current Population Survey (CPS) through June 2026.

## What is in the repository

| Folder | Contents |
|---|---|
| `data/` | Every input: the cleaned occupation-cell regression files (`cell_fd/`, `cell_fe/`), the saved individual-level estimates (`individual_fe/`), the occupation scores and occupation-by-quarter panels (`pipeline/`), the task-level scores and the records of the scoring runs (`scoring/`), and the crosswalks. `data/README.md` describes each file. No individual-level survey records. |
| `code/stata/` | Eight Stata scripts, `01_fd_main.do` to `08_individual_fe.do`, that estimate every regression and write the results to `output/estimates/` as CSV files (one row per coefficient: estimate, standard error, p-value, N, clusters, R-squared, outcome mean). `00_setup.do` holds the paths and shared programs. `individual_fe_source/` holds the cleaning and estimation do-files of the individual-level design, which need the CPS microdata (see below). |
| `code/tables/` | Python scripts that write the LaTeX tables: `regression_tables.py` builds the 23 regression tables from `output/estimates/`; the other scripts build the measurement, descriptive, and decomposition tables from `data/`. |
| `code/figures/` | Python scripts that draw the figures, from `data/` and `output/estimates/`. |
| `code/prepare/` | The two scripts that summarized the raw model output into the files in `data/scoring/`; kept for the record, they cannot run without that output (1.1 GB, available from the authors). |
| `output/` | What the scripts write: `estimates/` (the regression results), `tables/` (LaTeX), `figures/` (PNG at 200 dpi). The committed files are the ones behind the submitted paper, so a rebuild can be checked against them. |
| `run_all.do`, `run_all.py` | Rebuild everything: the Stata script runs the eight estimation scripts in order; the Python script then builds the tables and figures. |

## How to rebuild

Stata 17 or later with `reghdfe` and `ftools` (`ssc install reghdfe ftools`), and Python 3.9 or later with pandas, numpy,
statsmodels, matplotlib, and pyarrow (`requirements.txt` lists the versions that built the committed exhibits). From the
repository root:

```
stata-se -b do run_all.do       # the regressions: about a minute; results in output/estimates/
python3 run_all.py              # the tables and figures: a few minutes
python3 run_all.py --check      # the same, then a list of every output file that differs from the committed one
```

Every Stata script starts with `do code/stata/00_setup.do` and expects the working directory to be the repository root, so to
run one alone, `cd` there first. Every Python script finds its inputs through `code/paths.py` and can be run from anywhere
(`python3 code/tables/regression_tables.py`). The Python step needs the eight CSV files in `output/estimates/`; the committed
ones can be used without rerunning Stata.

Rebuilt figures are pixel-identical to the committed ones with the listed library versions; LaTeX tables are identical.
The regression results reproduce the point estimates, standard errors, sample sizes, and outcome means of every regression
table of the submitted manuscript (checked cell by cell on November 22, 2026).

## The regressions

All regressions use the harmonized IPUMS OCC2010 occupation codes (451 occupations in the first differences, 450 in the
fixed-effects panel) unless the exhibit says otherwise, standard errors clustered by occupation, and the change in exposure
from stage 1 to stage 4 standardized across occupations as the regressor.

| Script | Design | Output file | Exhibits |
|---|---|---|---|
| `01_fd_main.do` | Stacked three-year first differences on occupation cells (Eq. 1): the headline window (2026Q1 vs 2023Q1 and 2026Q2 vs 2023Q2), the pre-AI placebo window (2021Q4 vs 2018Q4 through 2022Q3 vs 2019Q3), the window with the base period in 2022, and single end quarters; all workers and by age, by education, and by age and education jointly; quarter cells and six-month averages; harmonized and 2018 census codes; stage 1 to 4 and stage 1 to 3 exposure changes; eleven outcomes | `fd_main.csv` | Tables 3, 4; C.2, D.1 to D.3, F.9, F.10, G.1, G.2; Figures 1, 3, 6, 7, G.1 |
| `02_fd_specification.do` | The headline regression under 37 changes of specification or sample, including the Eloundou et al. (2024) and Felten et al. (2023) measures as added or alternative regressors and leaving each major occupation group out | `fd_specification.csv` | Tables F.1, F.2, F.4, F.5; Figure 8 |
| `03_fd_composition.do` | Three-year differences of outcomes within the part-time and within the full-time workforce of each occupation | `fd_composition.csv` | Table C.4 |
| `04_fd_telework.do` | The headline regression with remote-work controls, all workers and by group | `fd_telework.csv` | Tables F.6, F.7; Figure 8 |
| `05_fe_main.do` | Occupation-by-quarter fixed-effects regressions (Eqs. 2 and 3): pooled step, era split at 2025Q1, interpolated step; 2023Q1 to 2026Q2 and 2021Q3 to 2026Q2; all workers, by age group, by education | `fe_main.csv` | Table 5; C.3 (Panel A), D.4; Figure 6 |
| `06_fe_specification.do` | The era-split regression under 33 changes of specification or sample | `fe_specification.csv` | Table F.3 |
| `07_fe_telework.do` | The fixed-effects regressions with remote-work controls | `fe_telework.csv` | Table F.8 |
| `08_individual_fe.do` | The individual-level fixed-effects estimates, read from the saved estimates in `data/individual_fe/estimates/` | `individual_fe.csv` | Table C.3 (Panel B) |

The individual-level regressions (Appendix Table C.3, Panel B) are estimated on about 1.7 million linked person-months of the
CPS, which IPUMS terms do not allow us to redistribute. The package ships the saved Stata estimates of the 24 regressions the
table reports and the do-files that cleaned the microdata and estimated them (`code/stata/individual_fe_source/`); a reader
with an IPUMS-CPS extract can rerun them. Every other regression in the paper is re-estimated by the scripts above.

The Stata code was written for this package from the lab's estimation code (`folablab/aaicelo`, Tyler Boes, commit d3ac192
of November 2, 2026), which is where the submitted tables came from; the cleaned input files are that code's output. The
decomposition of Appendix E and the scatter figures (Figures 1, 4, 5, E.1) estimate the headline regression again in Python,
in `code/tables/tab8-decomposition.py`, `code/figures/fig6-decomposition.py`, and `code/figures/fig-scatter-groups.py`, with
the same point estimates.

## The exhibits

Paper (numbers as in the submitted manuscript):

| Exhibit | Output file | Script | Inputs |
|---|---|---|---|
| Table 1, ten largest and smallest exposure changes | `tables/tab2-3-top-bottom.tex` | `tables/tab2-3-top-bottom.py` | `pipeline/occ2010_measures.dta`, `occ2010_quarter_panel_v2.dta`, `occ2010_labels.csv` |
| Table 2, exposure and adoption | `tables/tab2-4-adoption-correlations.tex` | `tables/tab2-4-adoption-correlations.py` | `pipeline/occ_measures.csv` |
| Table 3, three-year headline and placebo | `tables/tab3-headline.tex` | `tables/regression_tables.py` | `estimates/fd_main.csv` |
| Table 4, by age and by education | `tables/tab4-by-group.tex` | `tables/regression_tables.py` | `estimates/fd_main.csv` |
| Table 5, occupation fixed effects | `tables/tab5-fe.tex` | `tables/regression_tables.py` | `estimates/fe_main.csv` |
| Figure 1, raw relation, under 30 and 30 to 64 | `figures/fig1-raw-intro.png` | `figures/fig-scatter-groups.py` | `cell_fd/`, `pipeline/occ2010_q_age3.dta` |
| Figure 2, exposure by stage and rating | `figures/fig2-2-raters-dimensions.png` | `figures/fig2-2-raters-dimensions.py` | `scoring/master_task_scores.csv` |
| Figure 3, groups and cells, headline and placebo | `figures/fig3-who-holds-jobs.png` | `figures/fig3-who-holds-jobs.py` | `estimates/fd_main.csv` |
| Figure 4, decomposition scatters | `figures/fig4-decomposition-two-panels.png` | `figures/fig6-decomposition.py` | `cell_fd/fd_baseline_3m_occ2010_age_u30.dta`, `_ageedu_u30_no_ba.dta`, `pipeline/occ2010_q_age3.dta`, `crosswalks/occ2010_major_groups.csv` |
| Figure 5, contributions by major group | `figures/fig-decomposition-groups-vertical.png` | `figures/fig6-decomposition.py` | as Figure 4 |
| Figure 6, windows and designs | `figures/fig-timing-designs.png` | `figures/fig-timing-designs.py` | `estimates/fd_main.csv`, `fe_main.csv` |
| Figure 7, three-year difference by end quarter | `figures/fig-timing-byquarter.png` | `figures/fig-timing-byquarter.py` | `estimates/fd_main.csv` |
| Figure 8, alternative explanations | `figures/fig6-alternatives.png` | `figures/fig6-alternatives.py` | `estimates/fd_specification.csv`, `fd_telework.csv`, `fd_main.csv` |

Online Appendix:

| Exhibit | Output file | Script | Inputs |
|---|---|---|---|
| Figure A.1, the pipeline; Table A.1, the stages | text only, in the paper | | `scoring/prompts/stages.txt` for Table A.1 |
| Prompts | `data/scoring/prompts/*.txt` | the scoring prompts, verbatim | |
| Table A.2, models and settings | text only, in the paper | | `scoring/runlogs/` |
| Tables A.3, A.4, A.8 to A.11 (cost, subtasks, pilot, agreement, weights, adoption regressions) and A.7 (two rating versions) | `tables/tabA-*.tex` | `tables/tabA-measurement.py` | `scoring/`, `pipeline/occ_measures.csv` |
| Table A.5, worked example | `tables/tabA-worked-example.tex` | `tables/tabA-worked-example.py` | `scoring/task_7359/`, `master_task_scores.csv` |
| Table A.6, whole-task comparison | `tables/tabB-whole-task.tex` | `tables/tabB-whole-task.py` | `scoring/whole_task_*.csv` |
| Figure A.2, adoption against each measure | `figures/figB-adoption-all.png` | `figures/fig2-3-adoption.py` | `pipeline/occ_measures.csv` |
| Tables B.1 and B.2, crosswalk and unscored codes | `tables/tabB-crosswalk.tex`, `tabB-unscored.tex` | `tables/tabB-crosswalk.py` | `crosswalks/`, `pipeline/`, `scoring/master_task_scores.csv` |
| Figure B.1, exposure across the workforce | `figures/fig3-1-frontier.png` | `figures/fig3-1-frontier.py` | `pipeline/occ2010_measures.dta`, `occ2010_quarter_panel_v2.dta` |
| Table B.3, characteristics by quartile | `tables/tab3-1-characteristics.tex` | `tables/tab3-1-characteristics.py` | `pipeline/occ2010_quarter_panel_v2.dta` |
| Figures B.2 to B.4, outcomes by quartile, gaps by age and education | `figures/fig3-3-outcomes-quartiles.png`, `fig3-4-gaps-age.png`, `fig3-5-gaps-edu.png` | `figures/sec3_figures.py` | `pipeline/fig31_series_s41.csv`, `occ2010_measures.dta`, `occ2010_q_age3.dta`, `occ2010_q_edu2.dta` |
| Table C.1, the stacked windows | text only, in the paper | | |
| Table C.2, three-year differences in full | `tables/tabC2-fd-full.tex` | `tables/regression_tables.py` | `estimates/fd_main.csv` |
| Table C.3, fixed effects, occupation (Panel A) and individual (Panel B) | `tables/tabC3-fe-windows-A.tex`, `-B.tex` | `tables/regression_tables.py` | `estimates/fe_main.csv`, `individual_fe.csv` |
| Table C.4, within part-time and full-time | `tables/tabC4-composition.tex` | `tables/regression_tables.py` | `estimates/fd_composition.csv`, `fd_main.csv` |
| Tables D.1 to D.3, age by education jointly | `tables/tabD1-ageedu-s4.tex`, `tabD2-ageedu-s3.tex`, `tabD3-ageedu-secondary.tex` | `tables/regression_tables.py` | `estimates/fd_main.csv` |
| Table D.4, fixed effects by group | `tables/tabD4-fe-groups.tex` | `tables/regression_tables.py` | `estimates/fe_main.csv` |
| Table D.5, entry and exit flows by group | `tables/tabD-flows.tex` | `tables/tabD-flows.py` | `pipeline/flow_counts.csv` |
| Tables E.1 and E.2, decomposition and top occupations | `tables/tab8-1-decomposition.tex`, `tab8-2-top-occupations.tex` | `tables/tab8-decomposition.py` | as Figure 4 |
| Figure E.1, decomposition by age group | `figures/fig6-resid-panels.png` | `figures/fig-scatter-groups.py` | as Figure 1 |
| Tables F.1 to F.5, specification checks | `tables/tabF1-fd-spec-primary.tex`, `tabF2-fd-spec-secondary.tex`, `tabF3-fe-spec.tex`, `tabF4-logo-1-11.tex`, `tabF5-logo-12-22.tex` | `tables/regression_tables.py` | `estimates/fd_specification.csv`, `fe_specification.csv`, `crosswalks/occ2010_major_groups.csv` |
| Tables F.6 to F.8, remote work | `tables/tabF6-fd-telework.tex`, `tabF7-fd-telework-u30.tex`, `tabF8-fe-telework.tex` | `tables/regression_tables.py` | `estimates/fd_telework.csv`, `fe_telework.csv` |
| Tables F.9 and F.10, 2018 census codes | `tables/tabF9-fd-cps-code.tex`, `tabF10-fd-cps-groups.tex` | `tables/regression_tables.py` | `estimates/fd_main.csv` |
| Tables G.1 and G.2, placebo windows by group | `tables/tabG1-placebo-groups.tex`, `tabG2-placebo-ageedu.tex` | `tables/regression_tables.py` | `estimates/fd_main.csv` |
| Figure G.1, by end quarter and age group | `figures/figG1-byquarter-groups.png` | `figures/figG1-byquarter-groups.py` | `estimates/fd_main.csv` |

Output paths are relative to `output/`, scripts to `code/`, inputs to `data/` or `output/`. The figure scripts also write a
few figures and data files that the paper does not use (the scatter for each age group, for instance); they are listed in
each script's header. Four exhibits of the paper contain no data (the pipeline diagram, the stage and model descriptions, and
the list of stacked windows); they are typeset text in the paper and are not reproduced here.

## Data sources and terms

- **Current Population Survey**, basic monthly samples January 2017 to June 2026, from IPUMS-CPS (University of Minnesota).
  IPUMS terms do not allow redistribution of the extract, so the package ships occupation-level aggregates only;
  `data/README.md` says what the extract is needed for and where the code that builds the aggregates from it lives.
- **O*NET** task statements and occupation data (O*NET database, O*NET-SOC 2019 taxonomy, U.S. Department of Labor), public
  domain. The task-level score file carries the 19,281 task statements with their identifiers and O*NET-SOC codes.
- **Real-Time Population Survey** adoption shares by occupation (Bick, Blandin, Deming, and Schumacher, 2026, "What Work Does
  Generative AI Do?", Federal Reserve Bank of St. Louis Working Paper 2026-017), as occupation-level aggregates.
- **Eloundou et al. (2024)** and **Felten et al. (2023)** exposure measures, as published by their authors; **Dingel and
  Neiman (2020)** teleworkability by occupation.
- **Model ratings** (Claude Haiku 4.5, GPT-5.6-luna, Gemini 3.1 Flash-Lite, DeepSeek V4 Flash): produced by the authors through
  the Anthropic and OpenRouter APIs with the prompts in `data/scoring/prompts/`; the task-level scores are in
  `data/scoring/master_task_scores.csv`, and the raw model output is available from the authors.

## License

The code, the authors' exposure and task scores, and the built exhibits are released under the Creative Commons
Attribution-NonCommercial 4.0 license (`LICENSE`): use, copy, redistribute, and adapt with attribution, not for commercial use.
Third-party data remain subject to the terms of their sources above.

## Contact

Yong Suk Lee, University of Notre Dame (yong.s.lee@nd.edu).
