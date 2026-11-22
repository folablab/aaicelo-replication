# Figure 3: the three-year coefficients for the log count of workers (Panel A) and the unemployment rate (Panel B) for each age group,
# each education group, and the six age-by-education cells, headline window filled and the pre-AI placebo window hollow, with 95 percent
# intervals. Numbers come from output/estimates/fd_main.csv (written by code/stata/01_fd_main.do), the same file the tables are built
# from, so the figure cannot drift from the tables. Run from anywhere: python3 code/figures/fig3-who-holds-jobs.py
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.style.use(str(ROOT/"code/figures/restat.mplstyle"))
FD=pd.read_csv(ESTIMATES/"fd_main.csv")
def est(group,window,outcome):
    r=FD[(FD.system=="occ2010")&(FD.group==group)&(FD.unit=="q")&(FD.window==window)&(FD.exposure=="s4_s1")&(FD.outcome==outcome)]
    assert len(r)==1,(group,window,outcome); return 100*float(r.b.iloc[0]),100*float(r.se.iloc[0])
ORDER=[("age_u30","Under 30"),("age_30_49","30 to 49"),("age_50_64","50 to 64"),None,
       ("edu_no_ba","Less than a bachelor's degree"),("edu_ba_plus","Bachelor's degree or more"),None,
       ("ageedu_u30_no_ba","Under 30, less than a bachelor's"),("ageedu_u30_ba_plus","Under 30, bachelor's or more"),
       ("ageedu_30_49_no_ba","30 to 49, less than a bachelor's"),("ageedu_30_49_ba_plus","30 to 49, bachelor's or more"),
       ("ageedu_50_64_no_ba","50 to 64, less than a bachelor's"),("ageedu_50_64_ba_plus","50 to 64, bachelor's or more")]
PANELS=[("A. Log count of workers","d_log_emp","Log points",-18,18),("B. Unemployment rate","d_unemp_rate","Percentage points",-1.6,2.2)]
INK,GRAY,C1="#0b0b0b","#9a9994","#2a78d6"
fig,axes=plt.subplots(1,2,figsize=(7,5.4),sharey=True); fig.subplots_adjust(bottom=0.17,left=0.3,right=0.98,top=0.96,wspace=0.08)
for ax,(title,outcome,unit,lo,hi) in zip(axes,PANELS):
    y=0; ticks=[]; labels=[]
    for item in ORDER:
        if item is None: y-=0.6; continue
        key,lab=item; b,se=est(key,"headline",outcome); pb,pse=est(key,"placebo_pre",outcome)
        ax.errorbar(b,y+0.16,xerr=1.96*se,fmt="o",color=C1,ms=5,capsize=0,lw=1.2,zorder=3)
        ax.errorbar(pb,y-0.16,xerr=1.96*pse,fmt="o",mfc="white",mec=GRAY,ecolor=GRAY,ms=5,capsize=0,lw=1.0,zorder=2)
        ax.text(hi-0.02*(hi-lo),y+0.16,f"{b:.2f} ({se:.2f})",va="center",ha="right",fontsize=6.8,color=INK,bbox=dict(boxstyle="round,pad=0.1",fc="white",ec="none",alpha=0.85),zorder=4)
        ticks.append(y); labels.append(lab); y-=1
        if outcome=="d_log_emp": print(f"{lab:34s} employment {b:6.2f} ({se:.2f})   placebo {pb:6.2f} ({pse:.2f})")
    ax.axvline(0,color="0.25",lw=0.6); ax.set_yticks(ticks); ax.set_yticklabels(labels,fontsize=8.5); ax.set_ylim(y+0.3,0.7); ax.set_xlim(lo,hi)
    ax.set_title(title,fontsize=9.5,loc="left"); ax.set_xlabel(f"{unit} per sd of the exposure change",fontsize=8)
    for yy,txt in [(0.45,"By age"),(-3.15,"By education"),(-5.75,"Age by education")]: ax.text(lo+0.02*(hi-lo),yy,txt,fontsize=8,style="italic",va="center")
h=[plt.Line2D([],[],marker="o",ls="",color=C1,ms=5,label="Headline window: first half of 2026 vs. first half of 2023"),
   plt.Line2D([],[],marker="o",ls="",mfc="white",mec=GRAY,ms=5,label="Placebo window: 2021Q4 to 2022Q3 vs. three years earlier")]
fig.legend(handles=h,loc="lower center",bbox_to_anchor=(0.6,0.0),ncol=1,fontsize=7.5,handletextpad=0.4)
fig.savefig(FIGURES/"fig3-who-holds-jobs.png"); print("wrote figures/fig3-who-holds-jobs.png")
