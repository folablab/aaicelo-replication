# The regression tables of the paper and the Online Appendix, built from the results that the Stata scripts write to
# output/estimates/ (fd_main, fd_specification, fd_composition, fd_telework, fe_main, fe_specification, fe_telework,
# individual_fe). Every number in these tables is read from those files; nothing is typed in. Run from anywhere:
#   python3 code/tables/regression_tables.py
# Writes to output/tables/ (exhibit numbers as in the paper):
#   tab3-headline.tex            Table 3    three-year differences, headline and pre-AI placebo windows, all workers
#   tab4-by-group.tex            Table 4    by age and by education, headline window
#   tab5-fe.tex                  Table 5    occupation fixed effects, 2023Q1 to 2026Q2, all workers and pooled coefficient by group
#   tabC2-fd-full.tex            C.2        headline and placebo windows, quarter cells and six-month averages, stage 1 to 4 and 1 to 3
#   tabC3-fe-windows-A.tex, -B.tex  C.3     occupation fixed effects (Panel A) and individual fixed effects (Panel B), two windows
#   tabC4-composition.tex        C.4        what changed within the part-time and within the full-time workforce
#   tabD1-ageedu-s4.tex          D.1        age by education jointly, stage 1 to 4
#   tabD2-ageedu-s3.tex          D.2        age by education jointly, stage 1 to 3
#   tabD3-ageedu-secondary.tex   D.3        age by education jointly, secondary outcomes
#   tabD4-fe-groups.tex          D.4        occupation fixed effects by age group and by education
#   tabF1-fd-spec-primary.tex    F.1        specification checks, first differences, main outcomes
#   tabF2-fd-spec-secondary.tex  F.2        specification checks, first differences, part-time, full-time, under-30 employment
#   tabF3-fe-spec.tex            F.3        specification checks, fixed-effects era split
#   tabF4-logo-1-11.tex          F.4        leave one major group out, groups 1 to 11
#   tabF5-logo-12-22.tex         F.5        leave one major group out, groups 12 to 22
#   tabF6-fd-telework.tex        F.6        remote-work controls, first differences, all workers
#   tabF7-fd-telework-u30.tex    F.7        remote-work controls, first differences, workers under 30
#   tabF8-fe-telework.tex        F.8        remote-work controls, occupation fixed effects
#   tabF9-fd-cps-code.tex        F.9        headline window on 2018 census occupation codes
#   tabF10-fd-cps-groups.tex     F.10       by age and by education on 2018 census occupation codes
#   tabG1-placebo-groups.tex     G.1        by age and by education, pre-AI placebo window
#   tabG2-placebo-ageedu.tex     G.2        age by education jointly, pre-AI placebo window
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import pandas as pd, numpy as np

E = {k: pd.read_csv(ESTIMATES / f"{k}.csv") for k in
     ["fd_main", "fd_specification", "fd_composition", "fd_telework", "fe_main", "fe_specification", "fe_telework", "individual_fe"]}

# ------------------------------------------------------------------ outcomes, scaling, column headers
SCALE = {"d_hours_main": 1, "d_hours_total": 1, "d_hours_second": 1, "hours_main": 1, "hours_total": 1, "hours_second": 1, "ahrswork1": 1}
def scale(y): return SCALE.get(y, 100)                      # log outcomes and shares are reported times 100
def mean_scale(y):                                          # outcome means: shares times 100, logs and hours in levels
    if y.startswith("d_"): return scale(y)                  # first differences: scaled like the coefficient
    return 100 if y in ("unemp_rate", "pt_share", "second_job", "Demp", "parttime_usual") else 1
FD_PRIMARY = ["d_log_emp", "d_unemp_rate", "d_hours_main", "d_log_hrearn_real", "d_pt_share"]
FD_SECONDARY = ["d_log_pt_emp", "d_log_ft_emp", "d_second_job", "d_hours_total", "d_hours_second", "d_log_wkearn_real"]
FE_PRIMARY = ["log_emp", "unemp_rate", "hours_main", "log_hrearn_real", "pt_share"]
HEAD = {"d_log_emp": "Log\\\\employment", "d_unemp_rate": "Unemployment\\\\(pp)", "d_hours_main": "Hours", "d_log_hrearn_real": "Log real hourly\\\\earnings",
        "d_pt_share": "Part-time share\\\\(pp)", "d_log_pt_emp": "Log part-time\\\\employment", "d_log_ft_emp": "Log full-time\\\\employment",
        "d_second_job": "Second job\\\\(pp)", "d_hours_total": "Total\\\\hours", "d_hours_second": "Second-job\\\\hours", "d_log_wkearn_real": "Log weekly\\\\earnings",
        "log_emp": "Log\\\\employment", "unemp_rate": "Unemployment\\\\(pp)", "hours_main": "Hours", "log_hrearn_real": "Log real hourly\\\\earnings", "pt_share": "Part-time share\\\\(pp)",
        "Demp": "Employed\\\\(pp)", "ahrswork1": "Hours", "ln_hrearn_tc_real": "Log real hourly\\\\earnings", "parttime_usual": "Part time\\\\(pp)"}
def head(y): return "\\shortstack{" + HEAD[y] + "}" if "\\\\" in HEAD[y] else HEAD[y]

# ------------------------------------------------------------------ formatting
def stars(p): return "\\textsuperscript{***}" if p < 0.01 else "\\textsuperscript{**}" if p < 0.05 else "\\textsuperscript{*}" if p < 0.10 else ""
def coef(r, s=None):
    s = scale(r.outcome) if s is None else s
    return f"{r.b * s:.2f}{stars(r.p)} ({r.se * s:.2f})"
def num(x, d=2): return f"{x:,.{d}f}" if d else f"{int(round(x)):,}"
def one(df, **kw):
    r = df
    for k, v in kw.items(): r = r[r[k] == v]
    assert len(r) == 1, (kw, len(r)); return r.iloc[0]

def table(fname, caption, label, cols, body, notes, colspec=None):
    """body: list of lines, each a list of cells (first the row label) or a string (a raw line such as a panel title)."""
    k = len(cols)
    L = [f"% Generated by code/tables/regression_tables.py from the files in output/estimates/. Do not edit by hand.",
         "% Requires the booktabs and adjustbox packages.",
         "\\begin{table}[htbp]", "\\centering", f"\\caption{{{caption}}}", f"\\label{{{label}}}", "\\small", "\\setlength{\\tabcolsep}{4pt}",
         "\\begin{adjustbox}{max width=\\linewidth}", "\\begin{tabular}{" + (colspec or "l" + "c" * k) + "}", "\\toprule",
         " & " + " & ".join(head(c) if c in HEAD else c for c in cols) + " \\\\", "\\midrule"]
    for row in body:
        if isinstance(row, str): L.append(row)
        else: L.append(" & ".join(row) + " \\\\")
    L += ["\\bottomrule", "\\end{tabular}", "\\end{adjustbox}", "\\par\\vspace{0.5em}", "\\begin{minipage}{\\linewidth}\\footnotesize", "\\textit{Notes:} " + notes,
          "\\end{minipage}", "\\end{table}", ""]
    (TABLES / fname).write_text("\n".join(L)); print("wrote tables/" + fname)
def panel(title, k): return f"\\multicolumn{{{k + 1}}}{{@{{}}l}}{{\\textbf{{\\textit{{{title}}}}}}} \\\\"
def rule(k): return f"\\cmidrule(lr){{1-{k + 1}}}"
STARS = "\\textsuperscript{*}$p<0.10$, \\textsuperscript{**}$p<0.05$, \\textsuperscript{***}$p<0.01$."
FD_NOTES = ("Each entry is the coefficient on the standardized change in exposure in the stacked three-year first difference, with standard errors "
            "clustered by occupation in parentheses. Regressions are weighted by base-period employment and include the twelve base-period "
            "composition controls and period effects. Log outcomes and shares are multiplied by 100; hours are in hours. The mean outcome change is the "
            "weighted mean of the first-differenced outcome in the estimation sample; $N$ is the number of occupation-window observations. ")

# ------------------------------------------------------------------ first-difference blocks
FD = E["fd_main"]
def fd(group, window, exp="s4_s1", unit="q", system="occ2010"):
    return lambda y: one(FD, system=system, group=group, unit=unit, window=window, exposure=exp, outcome=y)
def fd_block(get, ys, label, with_r2=True, exps=None):
    """coefficient row(s), R2, mean, N for one sample and window"""
    rows = []
    if exps is None: rows.append([label] + [coef(get(y)) for y in ys])
    else:
        for lab, g in exps: rows.append([lab] + [coef(g(y)) for y in ys])
    if with_r2: rows.append(["$R^{2}$"] + [num(get(y).r2) for y in ys])
    rows.append(["Mean outcome change"] + [num(get(y).depmean * scale(y)) for y in ys])
    rows.append(["$N$"] + [num(get(y).N, 0) for y in ys])
    return rows

AGE = [("Under 30", "age_u30"), ("30 to 49", "age_30_49"), ("50 to 64", "age_50_64")]
EDU = [("Less than a bachelor's degree", "edu_no_ba"), ("Bachelor's degree or more", "edu_ba_plus")]
AGEEDU = [("Under 30, less than a bachelor's degree", "ageedu_u30_no_ba"), ("Under 30, bachelor's degree or more", "ageedu_u30_ba_plus"),
          ("30 to 49, less than a bachelor's degree", "ageedu_30_49_no_ba"), ("30 to 49, bachelor's degree or more", "ageedu_30_49_ba_plus"),
          ("50 to 64, less than a bachelor's degree", "ageedu_50_64_no_ba"), ("50 to 64, bachelor's degree or more", "ageedu_50_64_ba_plus")]
HEADLINE = "2026Q1 vs. 2023Q1 and 2026Q2 vs. 2023Q2"
PLACEBO = "2021Q4 vs. 2018Q4 through 2022Q3 vs. 2019Q3"

def group_table(fname, caption, label, window, system, ys, notes_extra):
    k = len(ys); body = [panel("A. By age", k)]
    for i, (lab, g) in enumerate(AGE):
        if i: body.append(rule(k))
        body += fd_block(fd(g, window, system=system), ys, lab)
    body += ["\\midrule", panel("B. By education", k)]
    for i, (lab, g) in enumerate(EDU):
        if i: body.append(rule(k))
        body += fd_block(fd(g, window, system=system), ys, lab)
    table(fname, caption, label, ys, body, FD_NOTES + "Each group coefficient comes from its own regression on occupation-by-group cells, weighted by the group's "
          "base-period employment in the occupation, with the full-occupation composition controls. " + notes_extra + " " + STARS)

def ageedu_table(fname, caption, label, window, exp, ys, notes_extra):
    k = len(ys); body = []
    for i, (lab, g) in enumerate(AGEEDU):
        if i: body.append(rule(k))
        body += fd_block(fd(g, window, exp), ys, lab)
    table(fname, caption, label, ys, body, FD_NOTES + "Each coefficient comes from its own regression on occupation-by-group cells, weighted by the group's "
          "base-period employment in the occupation, with the full-occupation composition controls. " + notes_extra + " " + STARS)

# Table 3
k = 5; body = [panel("A. Headline window: " + HEADLINE, k)] + fd_block(fd("all", "headline"), FD_PRIMARY, "Exposure change, stage 1 to 4") + \
    ["\\midrule", panel("B. Pre-AI placebo window: " + PLACEBO, k)] + fd_block(fd("all", "placebo_pre"), FD_PRIMARY, "Exposure change, stage 1 to 4")
table("tab3-headline.tex", "Three-year differences in the main outcomes: headline window and pre-AI placebo window", "tab:headline", FD_PRIMARY, body,
      FD_NOTES + "Panel A stacks the two headline windows; Panel B stacks the four placebo windows. " + STARS)
# Table 4, G.1, F.10
group_table("tab4-by-group.tex", "Three-year differences in the main outcomes, by age and by education", "tab:cell_fd_main_4", "headline", "occ2010", FD_PRIMARY,
            "Windows: " + HEADLINE + ".")
group_table("tabG1-placebo-groups.tex", "Three-year differences in the main outcomes, by age and by education: pre-AI placebo window", "tab:cell_fd_main_11",
            "placebo_pre", "occ2010", FD_PRIMARY, "Windows: " + PLACEBO + ".")
group_table("tabF10-fd-cps-groups.tex", "Three-year differences in the main outcomes, by age and by education: 2018 census occupation codes", "tab:cell_fd_main_17",
            "headline", "cps_code", FD_PRIMARY, "Windows: " + HEADLINE + ". Occupations are the 2018 census codes rather than the harmonized codes.")
# D.1, D.2, D.3, G.2
ageedu_table("tabD1-ageedu-s4.tex", "Three-year differences in the main outcomes, by age and education jointly", "tab:cell_fd_main_5", "headline", "s4_s1", FD_PRIMARY, "Windows: " + HEADLINE + ".")
ageedu_table("tabD2-ageedu-s3.tex", "Three-year differences in the main outcomes, by age and education jointly: stage 1 to 3 exposure change", "tab:cell_fd_main_6",
             "headline", "s3_s1", FD_PRIMARY, "Windows: " + HEADLINE + ". The regressor is the standardized change in exposure from stage 1 to stage 3.")
ageedu_table("tabD3-ageedu-secondary.tex", "Three-year differences in the secondary outcomes, by age and education jointly", "tab:cell_fd_secondary_5",
             "headline", "s4_s1", FD_SECONDARY, "Windows: " + HEADLINE + ".")
ageedu_table("tabG2-placebo-ageedu.tex", "Three-year differences in the main outcomes, by age and education jointly: pre-AI placebo window", "tab:cell_fd_main_7",
             "placebo_pre", "s4_s1", FD_PRIMARY, "Windows: " + PLACEBO + ".")
# C.2 and F.9: four (two) panels with both exposures
def full_table(fname, caption, label, system, panels):
    k = 5; body = []
    for i, (title, unit, window) in enumerate(panels):
        if i: body.append("\\midrule")
        body.append(panel(title, k))
        body += fd_block(fd("all", window, unit=unit, system=system), FD_PRIMARY, None,
                         exps=[("Exposure change, stage 1 to 4", fd("all", window, "s4_s1", unit, system)), ("Exposure change, stage 1 to 3", fd("all", window, "s3_s1", unit, system))])
    table(fname, caption, label, FD_PRIMARY, body, FD_NOTES + "Quarter cells stack the quarters of each window; six-month averages stack the two half-years ending in the "
          "same quarters. " + ("Occupations are the 2018 census codes rather than the harmonized codes. " if system == "cps_code" else "") + STARS)
full_table("tabC2-fd-full.tex", "Three-year differences in the main outcomes: headline and placebo windows, quarter cells and six-month averages", "tab:cell_fd_main_1", "occ2010",
           [("A. Headline window, occupation-quarter cells: " + HEADLINE, "q", "headline"), ("B. Headline window, six-month averages", "6m", "headline"),
            ("C. Pre-AI placebo window, occupation-quarter cells: " + PLACEBO, "q", "placebo_pre"), ("D. Pre-AI placebo window, six-month averages", "6m", "placebo_pre")])
full_table("tabF9-fd-cps-code.tex", "Three-year differences in the main outcomes: headline window, 2018 census occupation codes", "tab:cell_fd_main_14", "cps_code",
           [("A. Occupation-quarter cells: " + HEADLINE, "q", "headline"), ("B. Six-month averages", "6m", "headline")])

# ------------------------------------------------------------------ C.4: within part-time and within full-time
C = E["fd_composition"]
def comp_cell(status, window, y):
    if y == "count": r = one(FD, system="occ2010", group="all", unit="q", window=window, exposure="s4_s1", outcome=f"d_log_{status}_emp"); return coef(r, 100)
    return coef(one(C, status=status, window=window, outcome=y))
def comp_n(status, y):
    if y == "count": return num(one(FD, system="occ2010", group="all", unit="q", window="headline", exposure="s4_s1", outcome=f"d_log_{status}_emp").N, 0)
    return num(one(C, status=status, window="headline", outcome=y).N, 0)
cols = ["\\shortstack{Log\\\\count}", "\\shortstack{Mean\\\\hours}", "\\shortstack{Log real\\\\hourly wage}", "\\shortstack{Under-30\\\\share (pp)}", "\\shortstack{BA+\\\\share (pp)}", "\\shortstack{Economic-reasons\\\\share (pp)}"]
ys = ["count", "d_hours_main", "d_log_hrearn_real", "d_share_under30", "d_share_baplus", "d_share_pt_econ"]
body = []
for i, (status, title) in enumerate([("pt", "A. Part-time workers"), ("ft", "B. Full-time workers")]):
    if i: body.append("\\midrule")
    body.append(panel(title, 6))
    yy = ys if status == "pt" else ys[:-1]
    body.append(["Three years: " + HEADLINE] + [comp_cell(status, "headline", y) for y in yy] + (["\\textemdash"] if status == "ft" else []))
    body.append(["Three-year placebo across the pandemic: " + PLACEBO] + [comp_cell(status, "placebo_pre", y) for y in yy] + (["\\textemdash"] if status == "ft" else []))
    body.append(["$N$, three years"] + [comp_n(status, y) for y in yy] + (["\\textemdash"] if status == "ft" else []))
table("tabC4-composition.tex", "What changed within the part-time and within the full-time workforce", "tab:composition", cols, body,
      "Three-year first differences of outcomes measured among the part-time (Panel A) and the full-time (Panel B) workers of each occupation, on the standardized "
      "stage 1 to 4 exposure change, weighted by the occupation's base-period employment, with the twelve composition controls and period effects; standard errors "
      "clustered by occupation in parentheses. The log count is log part-time or log full-time employment. The economic-reasons share is the share of part-time "
      "workers who work part time for economic reasons and is defined only for part-time workers. Logs and shares are multiplied by 100. " + STARS,
      colspec="p{4.6cm}cccccc")

# ------------------------------------------------------------------ fixed effects: Table 5, C.3, D.4
FE = E["fe_main"]
def fe(window, panel_, group, spec, c, y): return one(FE, window=window, panel=panel_, group=group, spec=spec, coef=c, outcome=y)
def fe_rows(window, panel_, group, ys, with_mean=True):
    rows = [["Step"] + [coef(fe(window, panel_, group, "pooled", "step", y)) for y in ys],
            ["Interpolated step"] + [coef(fe(window, panel_, group, "interp", "interp", y)) for y in ys],
            ["Before 2025Q1"] + [coef(fe(window, panel_, group, "shift", "before", y)) for y in ys],
            ["Shift at 2025Q1"] + [coef(fe(window, panel_, group, "shift", "shift", y)) for y in ys],
            ["From 2025Q1"] + [coef(fe(window, panel_, group, "shift", "from", y)) for y in ys]]
    if with_mean: rows.append(["Outcome mean"] + [num(fe(window, panel_, group, "pooled", "step", y).depmean * mean_scale(y)) for y in ys])
    rows.append(["$N$"] + [num(fe(window, panel_, group, "pooled", "step", y).N, 0) for y in ys])
    return rows
FE_NOTES = ("Each coefficient is for a one-standard-deviation increase in the exposure score of the quarter (the score of the capability stage prevailing in the "
            "quarter, or the interpolated score), standardized within the window, in occupation-quarter regressions with occupation and quarter fixed effects, weighted by "
            "the occupation's 2019 employment, with standard errors clustered by occupation in parentheses. The era split reports the coefficient before 2025Q1, the shift at "
            "the reasoning-model inflection, and the coefficient from 2025Q1 on. Log outcomes and shares are multiplied by 100; hours are in hours. ")
# Table 5
k = 5; body = [panel("A. All workers, 2023Q1 to 2026Q2", k),
               ["Pooled"] + [coef(fe("W2023", "aggregate", "all", "pooled", "step", y)) for y in FE_PRIMARY],
               "\\addlinespace", "\\multicolumn{6}{@{}l}{\\emph{Era split}} \\\\",
               ["Before 2025Q1"] + [coef(fe("W2023", "aggregate", "all", "shift", "before", y)) for y in FE_PRIMARY],
               ["Shift at 2025Q1"] + [coef(fe("W2023", "aggregate", "all", "shift", "shift", y)) for y in FE_PRIMARY],
               ["From 2025Q1"] + [coef(fe("W2023", "aggregate", "all", "shift", "from", y)) for y in FE_PRIMARY],
               rule(k), ["$N$"] + [num(fe("W2023", "aggregate", "all", "pooled", "step", y).N, 0) for y in FE_PRIMARY],
               "\\midrule", panel("B. Pooled coefficient by group", k)]
for lab, p, g in [("Under 30", "age3", "u30"), ("30 to 49", "age3", "30_49"), ("50 to 64", "age3", "50_64"), ("Less than a bachelor's degree", "edu2", "no_ba"), ("Bachelor's degree or more", "edu2", "ba_plus")]:
    body.append([lab] + [coef(fe("W2023", p, g, "pooled", "step", y)) for y in FE_PRIMARY])
table("tab5-fe.tex", "Occupation fixed-effects estimates, 2023Q1 to 2026Q2", "tab:fe-body", FE_PRIMARY, body,
      FE_NOTES + "Panel B reports the pooled coefficient of the same regression estimated by age group and by education, weighted by the group's 2019 employment in the "
      "occupation, with occupation-by-group and quarter-by-group fixed effects. " + STARS)
# C.3
I = E["individual_fe"]; IY = ["Demp", "ahrswork1", "ln_hrearn_tc_real", "parttime_usual"]
def ife(window, spec, c, y): return one(I, window=window, spec=spec, coef=c, outcome=y)
body = [panel("A. Occupation fixed effects", 5), "\\multicolumn{6}{@{}l}{\\emph{2023Q1 to 2026Q2}} \\\\"] + fe_rows("W2023", "aggregate", "all", FE_PRIMARY) + \
       [rule(5), "\\multicolumn{6}{@{}l}{\\emph{2021Q3 to 2026Q2}} \\\\"] + fe_rows("W2021", "aggregate", "all", FE_PRIMARY)
table("tabC3-fe-windows-A.tex", "Fixed-effects estimates over two windows: occupation level", "tab:fe-main", FE_PRIMARY, body,
      FE_NOTES + "The window from 2021Q3 adds the chatbot era before 2023. " + STARS)
def ife_rows(window):
    rows = [["Step"] + [coef(ife(window, "pooled", "step", y)) for y in IY], ["Interpolated step"] + [coef(ife(window, "interp", "interp", y)) for y in IY],
            ["Before Jan. 2025"] + [coef(ife(window, "shift", "before", y)) for y in IY], ["Shift at Jan. 2025"] + [coef(ife(window, "shift", "shift", y)) for y in IY],
            ["From Jan. 2025"] + [coef(ife(window, "shift", "from", y)) for y in IY],
            ["Outcome mean"] + [num(ife(window, "pooled", "step", y).depmean * mean_scale(y)) for y in IY],
            ["$N$ (person-months)"] + [num(ife(window, "pooled", "step", y).N, 0) for y in IY]]
    return rows
body = ["\\multicolumn{5}{@{}l}{\\emph{January 2023 to June 2026}} \\\\"] + ife_rows("W2023") + [rule(4), "\\multicolumn{5}{@{}l}{\\emph{October 2021 to June 2026}} \\\\"] + ife_rows("W2021")
table("tabC3-fe-windows-B.tex", "Fixed-effects estimates over two windows: individual level", "tab:fe-main-individual", IY, body,
      "Individual-level regressions on the linked monthly CPS records of each worker, with individual and month fixed effects, controls for age, age squared, sex, race, "
      "education, and region, CPS person weights, and standard errors clustered by occupation in parentheses. The exposure score of a month is the score of the stage prevailing "
      "in that month (step) or the interpolated score, standardized within the window. Employment and part-time status are multiplied by 100; hours are in hours; earnings are "
      "log real hourly earnings times 100. The era split is at January 2025. " + STARS)
# D.4
body = []
for i, (title, p, groups) in enumerate([("A. By age group", "age3", [("Under 30", "u30"), ("30 to 49", "30_49"), ("50 to 64", "50_64")]), ("B. By education", "edu2", [("Less than a bachelor's degree", "no_ba"), ("Bachelor's degree or more", "ba_plus")])]):
    if i: body.append("\\midrule")
    body += [panel(title, 5), "\\multicolumn{6}{@{}l}{\\emph{Pooled}} \\\\"]
    for lab, g in groups: body.append([lab] + [coef(fe("W2023", p, g, "pooled", "step", y)) for y in FE_PRIMARY])
    body += [rule(5), "\\multicolumn{6}{@{}l}{\\emph{Era split}} \\\\"]
    for lab, g in groups:
        body.append([lab + ": before 2025Q1"] + [coef(fe("W2023", p, g, "shift", "before", y)) for y in FE_PRIMARY])
        body.append(["\\quad shift at 2025Q1"] + [coef(fe("W2023", p, g, "shift", "shift", y)) for y in FE_PRIMARY])
    g0 = groups[0][1]
    body += [rule(5), ["$R^{2}$"] + [num(fe("W2023", p, g0, "pooled", "step", y).r2) for y in FE_PRIMARY],
             ["Outcome mean"] + [num(fe("W2023", p, g0, "pooled", "step", y).depmean * mean_scale(y)) for y in FE_PRIMARY],
             ["$N$"] + [num(fe("W2023", p, g0, "pooled", "step", y).N, 0) for y in FE_PRIMARY]]
table("tabD4-fe-groups.tex", "Occupation fixed-effects estimates by age group and by education, 2023Q1 to 2026Q2", "tab:cellfe-polished-primary-occ2010-groups", FE_PRIMARY, body,
      FE_NOTES + "Each panel is one regression per outcome on occupation-by-group-by-quarter cells, weighted by the group's 2019 employment in the occupation, with "
      "occupation-by-group and quarter-by-group fixed effects and the exposure terms interacted with group indicators; the group coefficients are the sums of the base "
      "terms and the interactions. $R^{2}$, the outcome mean, and $N$ refer to the pooled regression of the panel. " + STARS)

# ------------------------------------------------------------------ specification checks: F.1, F.2, F.3
S = E["fd_specification"]
SPEC_ROWS = [("A. Reference, weighting, and additional controls", [("Baseline", "baseline"), ("Unweighted", "unweighted"), ("Major group $\\times$ quarter effects", "mgroup_x_quarter"),
              ("Add base-quarter industry shares", "industry_ctrl"), ("Industry shares $\\times$ quarter effects", "industry_x_quarter"), ("Region shares $\\times$ quarter effects", "region_x_quarter")]),
             ("B. Sample restrictions", [("Drop computer/math occupations", "drop_csmath"), ("Drop computer/math and science", "drop_cs_science"), ("Trim 1\\% exposure tails", "trim_dE_1pct"),
              ("At least 30 base-quarter respondents", "mincell_30"), ("One-to-one harmonized codes only", "one_to_one")])]
def spec_table(fname, caption, label, cells, df, rows_def, sizes_label):
    """cells: list of (column header, lookup kwargs selecting the unit/outcome); df: the specification file; rows_def: panels of (label, spec)."""
    k = len(cells); cols = [c[0] for c in cells]
    def g(kw, spec): return one(df, spec=spec, **kw)
    body = []
    for title, rows in rows_def:
        body.append(panel(title, k))
        for lab, spec in rows:
            body.append([lab] + [f"{g(kw, spec).b * scale(kw['outcome']):.2f}{stars(g(kw, spec).p)}" for _, kw in cells])
            body.append([""] + [f"({g(kw, spec).se * scale(kw['outcome']):.2f})" for _, kw in cells])
        body.append("\\midrule")
    body.append(panel("C. Leave-one-major-group-out coefficient ranges", k))
    for lab, f in [("Minimum", min), ("Maximum", max)]:
        body.append([lab] + [f"{f(df[(df.spec.str.startswith('logo_')) & (df[list(kw)[0]] == list(kw.values())[0]) & (df.outcome == kw['outcome'])].b) * scale(kw['outcome']):.2f}" for _, kw in cells])
    body += ["\\midrule", panel("D. Sample sizes: observations [" + sizes_label + "]", k)]
    for lab, spec in [("Baseline sample", "baseline")] + rows_def[1][1]:
        body.append([lab] + [f"{num(g(kw, spec).N, 0)} [{num(g(kw, spec).N_clust, 0)}]" for _, kw in cells])
    return body
NOTES_SPEC = ("Each entry re-estimates the headline three-year first difference (2026Q1 vs. 2023Q1 and 2026Q2 vs. 2023Q2; standardized stage 1 to 4 exposure change; "
              "base-period employment weights; twelve composition controls; period effects; standard errors clustered by occupation, in parentheses) under the change named in the row. "
              "Panel C reports the smallest and largest coefficient across the 22 regressions that each drop one major occupation group. Logs and shares are multiplied by 100. ")
cells = [(head(y), {"unit": "all", "outcome": y}) for y in FD_PRIMARY]
table("tabF1-fd-spec-primary.tex", "Specification checks: main outcomes", "tab:spec-primary", [c[0] for c in cells], spec_table("", "", "", cells, S, SPEC_ROWS, "occupations"), NOTES_SPEC + STARS)
cells = [(head("d_log_pt_emp"), {"unit": "all", "outcome": "d_log_pt_emp"}), (head("d_log_ft_emp"), {"unit": "all", "outcome": "d_log_ft_emp"}), ("\\shortstack{Log employment,\\\\under 30}", {"unit": "age_u30", "outcome": "d_log_emp"})]
table("tabF2-fd-spec-secondary.tex", "Specification checks: part-time, full-time, and under-30 employment", "tab:spec-secondary", [c[0] for c in cells], spec_table("", "", "", cells, S, SPEC_ROWS, "occupations"), NOTES_SPEC + STARS)
FS = E["fe_specification"]
FE_SPEC_ROWS = [("A. Reference, weighting, and additional controls", [("Baseline", "baseline"), ("Unweighted", "unweighted"), ("Major group $\\times$ quarter effects", "mgroup_xq"),
                 ("2019 industry shares $\\times$ quarter", "industry2019_xq"), ("2019 region shares $\\times$ quarter", "region2019_xq")]),
                ("B. Sample restrictions", [("Drop computer/math occupations", "drop_csmath"), ("Drop computer/math and science", "drop_cs_science"), ("Trim 1\\% exposure tails", "trim_delta1"),
                 ("Occupation-quarter count $\\geq 30$", "mincell30"), ("One-to-one harmonized codes only", "one_to_one")])]
cells = [(head(y), {"panel": "aggregate", "outcome": y}) for y in FE_PRIMARY]
table("tabF3-fe-spec.tex", "Specification checks: occupation fixed-effects era split, shift at 2025Q1", "tab:spec-fe", [c[0] for c in cells], spec_table("", "", "", cells, FS, FE_SPEC_ROWS, "occupation clusters"),
      "Each entry is the shift at 2025Q1 in the era-split occupation fixed-effects regression over 2023Q1 to 2026Q2 (standardized step exposure; 2019 employment weights; occupation "
      "and quarter fixed effects; standard errors clustered by occupation, in parentheses), re-estimated under the change named in the row. Panel C reports the smallest and largest shift "
      "across the 22 regressions that each drop one major occupation group. Logs and shares are multiplied by 100. " + STARS)
# F.4, F.5: leave one major group out, by group
MG = pd.read_csv(CROSSWALKS / "occ2010_major_groups.csv")
def logo_table(fname, caption, label, lo, hi):
    cells = [(head("d_log_pt_emp"), {"unit": "all", "outcome": "d_log_pt_emp"}), (head("d_log_ft_emp"), {"unit": "all", "outcome": "d_log_ft_emp"}), ("\\shortstack{Log employment,\\\\under 30}", {"unit": "age_u30", "outcome": "d_log_emp"})]
    body = [["Baseline (no group omitted)"] + [coef(one(S, spec="baseline", **kw)) for _, kw in cells], "\\midrule"]
    for _, r in MG[(MG.mgroup >= lo) & (MG.mgroup <= hi)].iterrows():
        body.append([f"{int(r.mgroup)}. {r['name']} ({int(r.occ2010_low)}--{int(r.occ2010_high)})"] + [coef(one(S, spec=f"logo_{int(r.mgroup)}", **kw)) for _, kw in cells])
        body.append(["\\quad $N$ [occupations]"] + [f"{num(one(S, spec=f'logo_{int(r.mgroup)}', **kw).N, 0)} [{num(one(S, spec=f'logo_{int(r.mgroup)}', **kw).N_clust, 0)}]" for _, kw in cells])
    table(fname, caption, label, [c[0] for c in cells], body, NOTES_SPEC.replace("Panel C reports the smallest and largest coefficient across the 22 regressions that each drop one major occupation group. ", "")
          + "Each row drops the named major occupation group (2010 census occupation code range in parentheses). " + STARS, colspec="p{7.2cm}ccc")
logo_table("tabF4-logo-1-11.tex", "Leave one major occupation group out: groups 1 to 11", "tab:logo-1", 1, 11)
logo_table("tabF5-logo-12-22.tex", "Leave one major occupation group out: groups 12 to 22", "tab:logo-2", 12, 22)

# ------------------------------------------------------------------ remote work: F.6, F.7, F.8
T = E["fd_telework"]
def tw_table(fname, caption, label, group):
    def g(spec, c, y): return one(T, group=group, spec=spec, outcome=y, coef=c)
    k = 5; body = [panel("A. CPS remote-work controls", k)]
    for lab, spec in [("Baseline", "baseline"), ("Add base-quarter telework share", "cps_base"), ("Add change in telework share", "cps_change"), ("Add base share and change", "cps_both"), ("Add hours share: base and change", "hours_both")]:
        body.append([lab] + [coef(g(spec, "z_d_s4_s1", y)) for y in FD_PRIMARY])
    body += ["\\midrule", panel("B. Dingel--Neiman teleworkability", k)]
    for lab, spec in [("Baseline, Dingel--Neiman sample", "baseline_dn"), ("Add Dingel--Neiman teleworkability", "dn_only"), ("Add all three remote-work controls", "all_three")]:
        body.append([lab] + [coef(g(spec, "z_d_s4_s1", y)) for y in FD_PRIMARY])
    body += ["\\midrule", panel("C. Remote-work coefficients from the augmented regressions", k)]
    for lab, spec, c in [("Base-quarter telework share", "cps_both", "z_tw_base"), ("Change in telework share", "cps_both", "z_tw_change"), ("Base-quarter remote-hours share", "hours_both", "z_tw_hours_base"),
                         ("Change in remote-hours share", "hours_both", "z_tw_hours_change"), ("Dingel--Neiman teleworkability", "dn_only", "z_dingel")]:
        body.append([lab] + [coef(g(spec, c, y)) for y in FD_PRIMARY])
    body += ["\\midrule", panel("D. Sample statistics", k),
             ["Mean outcome change, baseline sample"] + [num(g("baseline", "z_d_s4_s1", y).depmean * scale(y)) for y in FD_PRIMARY],
             ["Occupations, baseline sample"] + [num(g("baseline", "z_d_s4_s1", y).N_clust, 0) for y in FD_PRIMARY],
             ["Mean outcome change, Dingel--Neiman sample"] + [num(g("baseline_dn", "z_d_s4_s1", y).depmean * scale(y)) for y in FD_PRIMARY],
             ["Occupations, Dingel--Neiman sample"] + [num(g("baseline_dn", "z_d_s4_s1", y).N_clust, 0) for y in FD_PRIMARY]]
    table(fname, caption, label, FD_PRIMARY, body, "Rows of Panels A and B are the coefficient on the standardized stage 1 to 4 exposure change in the headline three-year first difference "
          "(2026Q1 vs. 2023Q1 and 2026Q2 vs. 2023Q2) with the named remote-work controls added; Panel C reports the coefficients on those controls. The CPS telework share and the share of hours worked "
          "from home describe the whole occupation and are standardized over the all-worker occupation-quarter cells of the window; Dingel--Neiman teleworkability is standardized within the "
          "estimation sample. Weights, composition controls, period effects, and clustering are those of the headline regression. Logs and shares are multiplied by 100. " + STARS, colspec="p{5.2cm}ccccc")
tw_table("tabF6-fd-telework.tex", "Three-year first differences with remote-work controls", "tab:fd-telework", "all")
tw_table("tabF7-fd-telework-u30.tex", "Three-year first differences with remote-work controls: workers under 30", "tab:fd-telework-u30", "age_u30")
FT = E["fe_telework"]
def ft(spec, model, c, y): return one(FT, spec=spec, model=model, coef=c, outcome=y)
body = []
for i, (title, specs) in enumerate([("A. CPS remote-work controls", [("Baseline", "baseline"), ("Add quarterly telework share", "cps_share"), ("Add remote-hours share", "hours_share")]),
                                     ("B. Dingel--Neiman teleworkability", [("Baseline, Dingel--Neiman sample", "baseline_dn"), ("Dingel--Neiman $\\times$ 2025Q1 onward", "dn_post"), ("Add both remote-work controls", "all")])]):
    if i: body.append("\\midrule")
    body.append(panel(title, 5))
    for lab, spec in specs:
        body.append([lab + ", pooled"] + [coef(ft(spec, "pooled", "pooled", y)) for y in FE_PRIMARY])
        body.append(["\\quad shift at 2025Q1"] + [coef(ft(spec, "shift", "shift", y)) for y in FE_PRIMARY])
body += ["\\midrule", panel("C. Estimation sample", 5),
         ["$N$: baseline and CPS samples"] + [num(ft("baseline", "pooled", "pooled", y).N, 0) for y in FE_PRIMARY],
         ["$N$: Dingel--Neiman sample"] + [num(ft("baseline_dn", "pooled", "pooled", y).N, 0) for y in FE_PRIMARY],
         ["Occupations: baseline and CPS samples"] + [num(ft("baseline", "pooled", "pooled", y).N_clust, 0) for y in FE_PRIMARY],
         ["Occupations: Dingel--Neiman sample"] + [num(ft("baseline_dn", "pooled", "pooled", y).N_clust, 0) for y in FE_PRIMARY]]
table("tabF8-fe-telework.tex", "Occupation fixed-effects estimates with remote-work controls, 2023Q1 to 2026Q2", "tab:cellfe-tw-aggregate-main", FE_PRIMARY, body,
      "Each pair of rows is the pooled coefficient on the standardized step exposure and the shift at 2025Q1 of the era-split specification, in the occupation fixed-effects "
      "regressions over 2023Q1 to 2026Q2 (2019 employment weights; occupation and quarter fixed effects; standard errors clustered by occupation, in parentheses) with the named "
      "control added: the quarterly CPS telework share or remote-hours share of the occupation (standardized), or Dingel--Neiman teleworkability (standardized across occupations) "
      "interacted with an indicator for 2025Q1 onward. Logs and shares are multiplied by 100. " + STARS, colspec="p{5.4cm}ccccc")
print("done")
