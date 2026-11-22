# Figure 7: the three-year difference in the log count of workers under 30 by end quarter, one regression per end quarter from 2021Q4 to
# 2026Q2, with 95 percent intervals, from the single-end-quarter rows of output/estimates/fd_main.csv (written by code/stata/01_fd_main.do).
# Run from anywhere: python3 code/figures/fig-timing-byquarter.py
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.style.use(str(ROOT/"code/figures/restat.mplstyle"))
d=pd.read_csv(ESTIMATES/"fd_main.csv")
d=d[(d.system=="occ2010")&(d.group=="age_u30")&(d.unit=="q")&(d.window.str.startswith("end"))&(d.exposure=="s4_s1")&(d.outcome=="d_log_emp")].copy()
d["x"]=d.window.map(lambda s:int(s[3:7])+(int(s[8])-1)/4); d=d.sort_values("x"); d["b"]=100*d.b; d["se"]=100*d.se
assert len(d)==19, len(d)
INK,INK2,GRAY,C1="#0b0b0b","#52514e","#9a9994","#2a78d6"
fig,ax=plt.subplots(figsize=(7,3.4))
ax.axvspan(2021.75-0.125,2022.5+0.125,color="0.95",lw=0,zorder=0)   # placebo windows: end quarters 2021Q4 to 2022Q3, base 2018Q4 to 2019Q3
ax.fill_between(d.x,d.b-1.96*d.se,d.b+1.96*d.se,color=C1,alpha=0.15,lw=0)
ax.plot(d.x,d.b,color=C1,lw=1.5,marker="o",ms=3.5)
ax.axhline(0,color=INK2,lw=0.6)
for x,lab in [(2023.25,"Chatbots"),(2025.0,"Reasoning\nmodels"),(2026.0,"Agents")]:
    ax.axvline(x,color=GRAY,lw=0.8,ls=(0,(3,3))); ax.text(x+0.05,14.0,lab,fontsize=7.5,color=INK2,va="top")
ax.text(2022.125,14.0,"Placebo\nwindows",fontsize=7.5,color=INK2,va="top",ha="center")
ax.set_ylim(-16,15); ax.set_xlim(2021.4,2026.6)
maj=[y+q/4 for y in range(2021,2027) for q in range(4) if 2021.4<y+q/4<=2026.3]
ax.set_xticks(maj); ax.set_xticklabels([f"{int(v)}Q{int(round((v-int(v))*4))+1}" for v in maj],rotation=90,fontsize=7.5)
ax.set_xlabel("End quarter of the three-year window"); ax.set_ylabel("Change in the log count of workers under 30\nper sd of the exposure change (log points)",fontsize=8.5)
fig.tight_layout(); fig.savefig(FIGURES/"fig-timing-byquarter.png"); print("wrote figures/fig-timing-byquarter.png")
