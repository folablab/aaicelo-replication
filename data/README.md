# Data files

Everything the scripts read is in this folder. No file contains individual-level survey records: the CPS-based files are
occupation-level (or occupation-by-group) aggregates built from the IPUMS-CPS extract described in the paper, and the scoring
files are model ratings of O*NET task statements. Sizes are approximate.

## cell_fd/ — the inputs of the first-difference regressions (Stata scripts 01 to 04)

One row per occupation, later quarter, and horizon (one, two, or three years), with the first difference of each outcome
between the later quarter and the base quarter (the same quarter one, two, or three years earlier), the base-quarter employment
(the regression weight), the twelve base-quarter composition shares (the controls), and the standardized exposure changes
`z_d_s4_s1`, `z_d_s3_s1`, `z_d_s3_s2` (stage 1 to 4, 1 to 3, 2 to 3). The paper uses the three-year horizon.

| File | What it is |
|---|---|
| `fd_baseline_3m_occ2010.dta` | All workers, harmonized OCC2010 occupations, occupation-quarter cells (`later_period` is a Stata quarterly date). 41,137 rows, 451 occupations. |
| `fd_baseline_3m_occ2010_<group>.dta` | The same for one group of workers: `age_u30`, `age_30_49`, `age_50_64`; `edu_no_ba`, `edu_ba_plus`; and the six `ageedu_<age>_<edu>` groups. Outcomes and weights are the group's; the composition controls are the whole occupation's. |
| `fd_baseline_6m_occ2010.dta` | All workers, six-month averages in place of quarter cells (Appendix Table C.2, panels B and D). |
| `fd_baseline_3m_cps_code*.dta`, `fd_baseline_6m_cps_code.dta` | The same files on the 2018 census occupation codes (`cps_code`, 513 occupations), without the 2017 to 2019 history (Appendix Tables F.9 and F.10). |
| `fd_table56_status_outcomes_3m_occ2010.dta` | Outcomes measured separately among the part-time and the full-time workers of each occupation (`status` = `pt`, `ft`): hours, log real hourly wage, the under-30 share, the share with a bachelor's degree or more, the share working part time for economic reasons (Appendix Table C.4). |
| `fd_robustness_inputs_occ2010.dta` | One row per occupation and base quarter (2023Q1, 2023Q2): base-quarter respondent counts, eleven base-quarter industry shares, and the standardized Eloundou et al. (2024) and Felten et al. (2023) exposure measures (Appendix Tables F.1, F.2, Figure 8). |

The telework variables (`base_telework_share`, `d_telework_share`, `base_telework_hours_share`, `d_telework_hours_share`,
`wfh_dingle_occ2010`) are the CPS telework share and share of hours worked from home, and Dingel and Neiman (2020)
teleworkability (Appendix Tables F.6 and F.7).

## cell_fe/ — the inputs of the occupation fixed-effects regressions (Stata scripts 05 to 07)

| File | What it is |
|---|---|
| `cell_fe_baseline_occ2010.dta` | Occupation-by-quarter panel, 2017Q1 to 2026Q2, all workers: the outcomes, the quarterly exposure score of the prevailing stage (`exposure_step_raw`) and the interpolated score (`exposure_interp_raw`), the fixed 2019 employment weight (`fe_weight`), respondent counts, and the telework measures. 17,542 rows, 450 occupations in the 2023Q1 to 2026Q2 window. |
| `cell_fe_age3_occ2010.dta`, `cell_fe_edu2_occ2010.dta` | The same panel by age group (`age3`: 1 under 30, 2 aged 30 to 49, 3 aged 50 to 64) and by education (`edu2`: 1 less than a bachelor's degree, 2 bachelor's degree or more), with the group's outcomes and 2019 weights. |
| `cell_fe_specification_inputs_occ2010.dta` | One row per occupation: major group, the number of 2018 census codes it collects (`one2one` = exactly one), 2019 industry and region shares, the Eloundou et al. (2024) and Felten et al. (2023) measures (Appendix Table F.3). |

## individual_fe/ — the individual-level fixed-effects estimates (Stata script 08)

The individual-level regressions (Appendix Table C.3, Panel B) are estimated on the linked monthly CPS records of each worker,
about 1.7 million person-months, which IPUMS terms do not allow us to redistribute. `estimates/` holds the saved Stata estimates
of the 24 regressions the table reports (`fe_<window>_<spec>_<outcome>.ster`, written by `code/stata/individual_fe_source/fe_run_occ2010.do`),
which script 08 reads. To re-estimate them, rebuild the IPUMS extract (see "What is not here") and run the two do-files in
`code/stata/individual_fe_source/`.

## pipeline/ — the authors' occupation scores and occupation-by-quarter panels

| File | What it is |
|---|---|
| `occ2010_measures.dta` | One row per harmonized (IPUMS OCC2010) occupation: the three-model exposure score at each capability stage (`ens_s1` to `ens_s4`), the changes between stages (`d_ens_s4_s1` etc.), the Eloundou et al. (2024) and Felten et al. (2023) measures, and Real-Time Population Survey adoption (`rps_adoption`, `rps_n`). The paper's exposure measure is `d_ens_s4_s1`. |
| `occ_measures.csv` | The same measures on 2018 census occupation codes (`cps_code`), before harmonization, with additional occupation characteristics; used for the adoption table and figures (Table 2, Figure A.2, Table A.11) and the crosswalk table. |
| `occ2010_quarter_panel_v2.dta` | Occupation-by-quarter panel, 2017Q1 to 2026Q2, all workers: employment (`emp`, the quarterly sum of monthly CPS weights, so a monthly average is `emp/3`), unemployment rate, hours, part-time share, mean log real hourly earnings, composition shares (`prop_*`), and the measures merged in. |
| `occ2010_quarter_panel.dta` | The earlier version of the panel, read only for the list of codes and quarters in the unscored-codes table (Table B.2). |
| `occ2010_q_age3.dta`, `occ2010_q_edu2.dta` | The panel by age group and by education. The age file's value labels carry the OCC2010 titles used in figure annotations. |
| `fig31_series_s41.csv` | Quarterly series by quartile of the exposure change for Appendix Figure B.2. |
| `flow_counts.csv` | Entrant and exit counts by group from the month-linked CPS, three-year differences (Appendix Table D.5); built from the microdata and shipped as counts. |
| `occ2010_labels.csv` | The IPUMS OCC2010 value labels (code, title). |

## crosswalks/

| File | What it is |
|---|---|
| `onet_to_cps_crosswalk_cleaned.dta` | O*NET-SOC 2019 occupation to SOC 2018 to 2018 census occupation code. |
| `occ_to_occ2010_2020_2026.dta` | 2018 census codes to harmonized OCC2010 codes with CPS person-month frequencies, January 2020 to June 2026. |
| `occ2010_major_groups.csv` | The 22 major groups of the 2010 census occupation classification with their OCC2010 code ranges (used for the leave-one-group-out checks and the decomposition by major group). |

## scoring/ — the task-level scores and the records of the scoring runs

| File | What it is |
|---|---|
| `master_task_scores.csv` (26 MB) | One row per O*NET task (19,281): each model's ratings A, B, C at each stage, in the capability-only and constraint-adjusted versions, the per-model composites, and the three-model composite (`ensemble3_composite_s1` to `_s4`). |
| `prompts/` | The scoring prompts, verbatim (Prompt 0 and ratings A, B, C), the whole-task prompt, and the stage definitions. |
| `p0_subtasks.csv` | Every subtask of the Prompt 0 decomposition: task, subtask, activity type, share of task time (99,169 rows). |
| `anthropic_usage.csv` | Token counts of the Claude Haiku 4.5 batch runs by prompt; the cost table prices them at list prices. |
| `runlogs/<model>/p{a,b,c}_full_runlog.json`, `p{a,b,c}_pilot1000_runlog.json` | The OpenRouter runner's logs (tokens, cost) for the production runs of the other three models and for the seven pilot models. |
| `parquet/production/prompt_{0,a,b,c}_summary.parquet` | Task-level summaries of the original Claude Haiku 4.5 runs (April 2026). |
| `parquet/claude-rerun/prompt_{a,b,c}_summary.parquet` | The August 2026 rerun of the Claude pipeline on the 1,000-task pilot sample (Table A.9, Panel B). |
| `occupation_scores_all_weights_<model>.csv` | Each model's task scores aggregated to O*NET occupations under four task-weighting schemes (Tables A.9 and A.10). |
| `whole_task_*.csv` | The whole-task versus subtask comparison (Table A.6). |
| `task_7359/` | The decomposition and the three models' subtask ratings for one task, the worked example of Table A.5. |

`p0_subtasks.csv`, `anthropic_usage.csv`, and the parquet summaries were summarized from the raw model output (about 1.1 GB of
JSON, kept by the authors and available on request) by the two scripts in `code/prepare/`, which are included for the record
and cannot run without that output.

## What is not here

The IPUMS-CPS microdata extract (basic monthly samples, January 2017 to June 2026, with the variables listed in the paper's data
section), which IPUMS terms do not allow us to redistribute. It is the source of every CPS-based file above and of the
individual-level regressions, whose cleaning and estimation do-files are in `code/stata/individual_fe_source/`.
