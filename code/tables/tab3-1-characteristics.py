# Appendix Table B.3: occupation characteristics by quartile of exposure change. Run from anywhere:
#   python3 code/tables/tab3-1-characteristics.py      (writes output/tables/tab3-1-characteristics.tex)
# Inputs: the AAICELO pipeline's harmonized occupation quarter panel (occ2010_quarter_panel_v2.dta), which carries
# the exposure scores. Quartiles of the stage-1 to stage-4 change are unweighted across the harmonized occupations,
# as in Appendix Figures B.2 to B.4. Levels are 2023 averages (the first year of the generative AI era and the base year of
# the headline window), weighted by 2023 employment within the group. Growth rows compare the first half of 2026
# with the first half of 2023 (the headline window) and the first half of 2019 with the first half of 2017 (before
# the pandemic and before generative AI); rates and means use fixed 2023 employment weights, employment is the
# group's monthly-average total.
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import pandas as pd, numpy as np, warnings
warnings.filterwarnings("ignore")
p=pd.read_stata(PIPELINE/"occ2010_quarter_panel_v2.dta",convert_categoricals=False)
p["t"]=pd.to_datetime(p.qdate); p["year"]=p.t.dt.year; p["q"]=p.t.dt.quarter
p["emp_m"]=p.emp/3; p["pt_m"]=p.pt_emp/3            # monthly averages from quarterly sums of weights
p["ft_m"]=p.emp_m-p.pt_m
p["pt_sh"]=100*p.pt_share; p["ur"]=100*p.unemp_rate; p["lw100"]=100*p.log_hrearn
for c in ["prop_fem","prop_30less","prop_50plus","prop_white","prop_black","prop_asian","prop_educ_q1","prop_educ_q3","prop_educ_q4","prop_south","prop_midwest","prop_northeast"]:
    p[c+"_pct"]=100*p[c]
occ=p.groupby("occ2010")[["d_ens_s4_s1","d_ens_s3_s1","ens_s1","ens_s4"]].first().dropna()
occ["quart"]=pd.qcut(occ.d_ens_s4_s1.rank(method="first"),4,labels=[1,2,3,4]).astype(int)
p=p.merge(occ[["quart"]],left_on="occ2010",right_index=True)
def period(df,sel): 
    d=df[sel]; return d.groupby("occ2010").mean(numeric_only=True)
y23=period(p,p.year==2023); w23=y23.emp_m
h23=period(p,(p.year==2023)&(p.q<=2)); h26=period(p,(p.year==2026)&(p.q<=2))
h17=period(p,(p.year==2017)&(p.q<=2)); h19=period(p,(p.year==2019)&(p.q<=2))
groups={"Bottom quartile":occ.index[occ.quart==1],"All occupations":occ.index,"Top quartile":occ.index[occ.quart==4]}
def wmean(s,w,idx):
    s=s.reindex(idx); w=w.reindex(idx); m=s.notna()&w.notna(); return np.average(s[m],weights=w[m])
rows=[]
def add(label,fn,fmt="{:.1f}"):
    vals=[fn(idx) for idx in groups.values()]
    def f(v):
        t=fmt.format(v); return "0.0" if t in ("-0.0","-0") else t
    rows.append((label,[f(v) for v in vals],f(vals[2]-vals[0]) if label!="Occupations" else ""))
# exposure
add("Exposure change, stage 1 to 4",lambda i: wmean(occ.d_ens_s4_s1,w23,i))
add("Exposure change, stage 1 to 3",lambda i: wmean(occ.d_ens_s3_s1,w23,i))
add("Exposure level, stage 1",lambda i: wmean(occ.ens_s1,w23,i))
add("Exposure level, stage 4",lambda i: wmean(occ.ens_s4,w23,i))
add("Occupations",lambda i: len(i),"{:.0f}")
rows.append(("__sep__Outcomes, 2023",None,None))
add("Employment (millions)",lambda i: y23.emp_m.reindex(i).sum()/1e6)
add("Unemployment rate (\\%)",lambda i: wmean(y23.ur,w23,i))
add("Hours worked last week",lambda i: wmean(y23.ahrsworkt,w23,i))
add("Real hourly wage (January 2020 dollars)",lambda i: wmean(y23.hr_earn,w23,i))
add("Part-time share (\\%)",lambda i: wmean(y23.pt_sh,w23,i))
add("Part-time employment (millions)",lambda i: y23.pt_m.reindex(i).sum()/1e6)
add("Full-time employment (millions)",lambda i: y23.ft_m.reindex(i).sum()/1e6)
rows.append(("__sep__Composition, 2023 (percent of employment)",None,None))
for lab,c in [("Female","prop_fem_pct"),("Under 30","prop_30less_pct"),("Aged 50 to 64","prop_50plus_pct"),("White","prop_white_pct"),("Black","prop_black_pct"),("Asian","prop_asian_pct"),
              ("High school or less","prop_educ_q1_pct"),("Bachelor's degree","prop_educ_q3_pct"),("Post-bachelor's degree","prop_educ_q4_pct")]:
    add(lab,lambda i,c=c: wmean(y23[c],w23,i))
def growth(a,b,col,idx,kind):
    if kind=="logsum": return 100*(np.log(b[col].reindex(idx).sum())-np.log(a[col].reindex(idx).sum()))
    return wmean(b[col],w23,idx)-wmean(a[col],w23,idx)
pre=[]   # the 2017-2019 panel is computed but not written
for title,a,b in [("Change, first half of 2023 to first half of 2026",h23,h26),("Change, first half of 2017 to first half of 2019",h17,h19)]:
    if title.endswith("2019"): main_rows=rows; rows=pre
    else: rows.append((f"__sep__{title}",None,None))
    add("Log employment (log points)",lambda i,a=a,b=b: growth(a,b,"emp_m",i,"logsum"))
    add("Unemployment rate (percentage points)",lambda i,a=a,b=b: growth(a,b,"ur",i,"w"))
    add("Hours worked last week",lambda i,a=a,b=b: growth(a,b,"ahrsworkt",i,"w"))
    add("Log real hourly wage (log points)",lambda i,a=a,b=b: growth(a,b,"lw100",i,"w"))
    add("Part-time share (percentage points)",lambda i,a=a,b=b: growth(a,b,"pt_sh",i,"w"))
    add("Log part-time employment (log points)",lambda i,a=a,b=b: growth(a,b,"pt_m",i,"logsum"))
    add("Log full-time employment (log points)",lambda i,a=a,b=b: growth(a,b,"ft_m",i,"logsum"))
rows,pre=main_rows,rows
# write LaTeX
L=[]
L.append("% Table 3.1: occupation characteristics by quartile of exposure change.")
L.append("% Generated by code/tables/tab3-1-characteristics.py from the occupation-by-quarter panel. Do not edit by hand.")
L.append("\\begin{table}[htbp]\n\\centering\n\\begin{threeparttable}\n\\caption{Occupation characteristics by quartile of exposure change}\n\\label{tab:characteristics}\n\\footnotesize\\setlength{\\tabcolsep}{5pt}\n\\begin{spacing}{1}\\scriptsize\n\\begin{tabular}{@{}lrrrr@{}}\n\\toprule\n & Bottom quartile & All occupations & Top quartile & Top minus bottom \\\\\n\\midrule")
for lab,vals,diff in rows:
    if lab.startswith("__sep__"): L.append("\\addlinespace\n\\multicolumn{5}{@{}l}{\\emph{"+lab[7:]+"}} \\\\"); continue
    def neg(v): return v.replace("-","$-$") if v.startswith("-") else v
    L.append(f"{lab} & {' & '.join(neg(v) for v in vals)} & {neg(diff)} \\\\")
L.append("\\bottomrule\n\\end{tabular}\n\\end{spacing}\n\\begin{tablenotes}\\notesize\n\\item Notes: Quartiles of the stage-1 to stage-4 change in exposure across the harmonized census occupations, as in Figures~\\ref{fig:outcomes} and~\\ref{fig:gapsage}. Levels are 2023 averages, the first year of the generative AI era and the base year of the three-year window in Section~\\ref{sec:findings}, weighted by 2023 employment within each group; employment counts are monthly averages. The outcomes are those of Section~\\ref{sec:cps} and the composition shares are the controls of Section~\\ref{sec:data}. The change rows compare the first half of 2026 with the first half of 2023, the headline window, i.e., 2026Q1 and 2026Q2 against 2023Q1 and 2023Q2 as in Table~\\ref{tab:cell_fd_main_1}; rates and means use fixed 2023 employment weights and employment is the group total. Wages are in January 2020 dollars.\n\\end{tablenotes}\n\\end{threeparttable}\n\\end{table}")
open(TABLES/"tab3-1-characteristics.tex","w").write("\n".join(L)+"\n")
for lab,vals,diff in rows: print(f"{lab[7:] if lab.startswith('__sep__') else lab:46s} {' | '.join(vals) if vals else ''} {diff or ''}")
