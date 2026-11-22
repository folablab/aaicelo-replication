# Figure 6: the under-30 employment estimate across windows and designs, with the two older age groups beside it. The three-year
# first differences (placebo window, base period in 2022, headline window) come from output/estimates/fd_main.csv and the occupation
# fixed-effects estimates (pooled, before 2025Q1, from 2025Q1 on) from output/estimates/fe_main.csv, both written by the Stata scripts.
# Run from anywhere: python3 code/figures/fig-timing-designs.py
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.style.use(str(ROOT/"code/figures/restat.mplstyle"))
FD=pd.read_csv(ESTIMATES/"fd_main.csv"); FE=pd.read_csv(ESTIMATES/"fe_main.csv")
def fd(group,window):
    r=FD[(FD.system=="occ2010")&(FD.group==group)&(FD.unit=="q")&(FD.window==window)&(FD.exposure=="s4_s1")&(FD.outcome=="d_log_emp")]
    assert len(r)==1,(group,window); return 100*float(r.b.iloc[0]),100*float(r.se.iloc[0])
def fe(group,spec,coef):
    r=FE[(FE.window=="W2023")&(FE.panel=="age3")&(FE.group==group)&(FE.spec==spec)&(FE.coef==coef)&(FE.outcome=="log_emp")]
    assert len(r)==1,(group,spec,coef); return 100*float(r.b.iloc[0]),100*float(r.se.iloc[0])
GROUPS=[("Under 30","age_u30","u30","#2a78d6"),("30 to 49","age_30_49","30_49","#9a9994"),("50 to 64","age_50_64","50_64","#52514e")]
ROWS=[("Three-year first differences","Placebo window: 2021Q4--2022Q3 vs. three years earlier",lambda g,h: fd(g,"placebo_pre")),
      ("Three-year first differences","Base period before ChatGPT: 2025Q1--Q4 vs. 2022Q1--Q4",lambda g,h: fd(g,"base2022")),
      ("Three-year first differences","Headline window: 2026Q1--Q2 vs. 2023Q1--Q2",lambda g,h: fd(g,"headline")),
      ("Occupation fixed effects, 2023Q1--2026Q2","Pooled coefficient",lambda g,h: fe(h,"pooled","step")),
      ("Occupation fixed effects, 2023Q1--2026Q2","Before the reasoning-model inflection (2025Q1)",lambda g,h: fe(h,"shift","before")),
      ("Occupation fixed effects, 2023Q1--2026Q2","From the reasoning-model inflection on",lambda g,h: fe(h,"shift","from"))]
INK,INK2="#0b0b0b","#52514e"
fig,ax=plt.subplots(figsize=(7,4.0)); fig.subplots_adjust(left=0.45,right=0.98,top=0.94,bottom=0.22)
y=0; ticks=[]; labels=[]; heads=[]; last=None; data=[]
for sec,lab,get in ROWS:
    if sec!=last:
        if last is not None: y-=0.6   # a gap before each new block so its heading clears the row above
        heads.append((sec,y+0.5)); last=sec
    for k,(gname,gfd,gfe,col) in enumerate(GROUPS):
        b,se=get(gfd,gfe); yy=y+0.25-0.25*k; data.append((sec,lab,gname,b,se))
        ax.errorbar(b,yy,xerr=1.96*se,fmt="o",color=col,ms=4.5 if k==0 else 3.8,lw=1.2 if k==0 else 1.0,capsize=0,zorder=3-k)
        if k==0: ax.text(10.6,yy,f"{b:.2f} ({se:.2f})",va="center",fontsize=7.5,color=INK)
        print(f"{lab[:40]:42s} {gname:9s} {b:6.2f} ({se:.2f})")
    ticks.append(y); labels.append(lab); y-=1.0
ax.axvline(0,color=INK2,lw=0.6); ax.set_yticks(ticks); ax.set_yticklabels(labels,fontsize=8); ax.set_ylim(y+0.5,0.9); ax.set_xlim(-14,14)
for sec,yy in heads: ax.text(-13.8,yy,sec,fontsize=8.5,style="italic",va="bottom")
ax.set_xlabel("Change in the log count of workers per sd of exposure (log points)",fontsize=8.5)
h=[plt.Line2D([],[],marker="o",ls="",color=c,ms=5,label=g) for g,_,_,c in GROUPS]
fig.legend(handles=h,loc="lower center",bbox_to_anchor=(0.6,0.0),ncol=3,fontsize=8,handletextpad=0.4)
fig.savefig(FIGURES/"fig-timing-designs.png"); print("wrote figures/fig-timing-designs.png")
pd.DataFrame(data,columns=["design","window","group","b","se"]).to_csv(ESTIMATES/"fig-timing-designs-data.csv",index=False)
