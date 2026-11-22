# Appendix Figure G.1: the three-year first difference by end quarter (2021Q4 to 2026Q2) for each age group and each of the five main
# outcomes, one regression per end quarter and group, with 95 percent intervals, from the single-end-quarter rows of
# output/estimates/fd_main.csv (written by code/stata/01_fd_main.do). Run from anywhere: python3 code/figures/figG1-byquarter-groups.py
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
C1,C2,C3="#2a78d6","#eb6834","#1baf7a"; GRAY,LGRAY,INK2="#7a7974","#d9d8d3","#52514e"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.titlesize":10,"axes.labelsize":9,"axes.edgecolor":INK2,"axes.linewidth":0.6,
    "axes.spines.top":False,"axes.spines.right":False,"xtick.color":INK2,"ytick.color":INK2,"xtick.labelsize":8,"ytick.labelsize":8,
    "grid.color":LGRAY,"grid.linewidth":0.5,"legend.frameon":False,"legend.fontsize":8,"figure.dpi":100,"savefig.dpi":200,"savefig.facecolor":"white","axes.facecolor":"white"})
Z=1.96; STAGES=[2023.25,2025.0,2026.0]   # inflection quarters 2023Q2, 2025Q1, 2026Q1
LAB={"d_log_emp":"Log employment ×100","d_unemp_rate":"Unemployment rate (pp)","d_pt_share":"Part-time share (pp)","d_hours_main":"Weekly hours","d_log_hrearn_real":"Log real wage ×100"}
SCALE={"d_hours_main":1}
d=pd.read_csv(ESTIMATES/"fd_main.csv")
d=d[(d.system=="occ2010")&(d.unit=="q")&(d.window.str.startswith("end"))&(d.exposure=="s4_s1")&(d.group.isin(["age_u30","age_30_49","age_50_64"]))].copy()
d["x"]=d.window.map(lambda s:int(s[3:7])+(int(s[8])-1)/4)
d["b"]=d.b*d.outcome.map(lambda y:SCALE.get(y,100)); d["se"]=d.se*d.outcome.map(lambda y:SCALE.get(y,100))
series=[("age_u30",C1,"18–29"),("age_30_49",C2,"30–49"),("age_50_64",C3,"50–64")]
outs=["d_log_emp","d_pt_share","d_hours_main","d_log_hrearn_real","d_unemp_rate"]
fig,axes=plt.subplots(2,3,figsize=(13,7)); axes=axes.flat
for ax,y in zip(axes,outs):
    for g,col,lab in series:
        s=d[(d.outcome==y)&(d.group==g)].sort_values("x"); assert len(s)==19,(y,g,len(s))
        ax.fill_between(s.x,s.b-Z*s.se,s.b+Z*s.se,color=col,alpha=0.10,lw=0); ax.plot(s.x,s.b,color=col,lw=1.4,marker="o",ms=2.2,label=lab)
    ax.axhline(0,color=INK2,lw=0.6,zorder=1)
    for x in STAGES: ax.axvline(x,color=GRAY,lw=0.7,ls=(0,(3,3)),zorder=0)
    ax.set_title(LAB[y],fontsize=10); ax.grid(axis="y",alpha=0.4); ax.set_xlim(2021.7,2026.6); ax.tick_params(labelsize=8)
    maj=[yr+q/4 for yr in range(2021,2027) for q in range(0,4,2) if 2021.7<yr+q/4<=2026.3]
    ax.set_xticks(maj); ax.set_xticklabels([f"{int(v)}Q{int(round((v-int(v))*4))+1}" for v in maj],rotation=90,fontsize=6.5)
    ax.set_xticks([yr+q/4 for yr in range(2021,2027) for q in range(4) if 2021.7<yr+q/4<=2026.3],minor=True)
    # vertical scale from the placebo stretch (pre-pandemic bases) and the end quarters from 2024 on
    s2=d[(d.outcome==y)&(d.x.between(2021.75,2022.99)|(d.x>=2024.0))]
    lo,hi=(s2.b-Z*s2.se).min(),(s2.b+Z*s2.se).max(); pad=0.1*(hi-lo); ax.set_ylim(lo-pad,hi+pad)
axes[5].axis("off"); axes[5].legend(*axes[0].get_legend_handles_labels(),loc="upper left",fontsize=11,title="Age group")
fig.tight_layout(); fig.savefig(FIGURES/"figG1-byquarter-groups.png",bbox_inches="tight"); print("wrote figures/figG1-byquarter-groups.png")
