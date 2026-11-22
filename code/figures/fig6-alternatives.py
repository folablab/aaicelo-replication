# Figure 8: the under-30 employment estimate across the specifications that address each alternative explanation. Sources, all written
# by the Stata scripts: output/estimates/fd_telework.csv (remote-work controls, group age_u30), fd_specification.csv (the specification
# checks, the leave-one-major-group-out range, and the Eloundou and Felten measures as the regressor, unit age_u30), and fd_main.csv (the
# placebo window and the 2018 census codes). Writes output/figures/fig6-alternatives.png and output/estimates/fig6-alternatives-data.csv.
# Run from anywhere: python3 code/figures/fig6-alternatives.py
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.style.use(str(ROOT/"code/figures/restat.mplstyle"))
S=pd.read_csv(ESTIMATES/"fd_specification.csv"); S=S[(S.unit=="age_u30")&(S.outcome=="d_log_emp")]
T=pd.read_csv(ESTIMATES/"fd_telework.csv"); T=T[(T.group=="age_u30")&(T.outcome=="d_log_emp")&(T.coef=="z_d_s4_s1")]
FD=pd.read_csv(ESTIMATES/"fd_main.csv"); FD=FD[(FD.group=="age_u30")&(FD.unit=="q")&(FD.exposure=="s4_s1")&(FD.outcome=="d_log_emp")]
def one(df,**kw):
    r=df
    for k,v in kw.items(): r=r[r[k]==v]
    assert len(r)==1,(kw,len(r)); return 100*float(r.b.iloc[0]),100*float(r.se.iloc[0])
spec=lambda code: one(S,spec=code)
tw=lambda code: one(T,spec=code)
lg=S[S.spec.str.startswith("logo_")]; assert len(lg)==22, len(lg)
rows=[("Remote work","Baseline",*tw("baseline")),
      ("Remote work","Add base-quarter telework share",*tw("cps_base")),
      ("Remote work","Add change in telework share",*tw("cps_change")),
      ("Remote work","Add base share and change",*tw("cps_both")),
      ("Remote work","Add remote-hours share, base and change",*tw("hours_both")),
      ("Remote work","Add Dingel--Neiman teleworkability",*tw("dn_only")),
      ("Remote work","Add all three remote-work controls",*tw("all_three")),
      ("The technology sector","Drop computer and mathematical occupations",*spec("drop_csmath")),
      ("The technology sector","Drop computer, mathematical, and science occupations",*spec("drop_cs_science")),
      ("Industry trends","Add base-quarter industry shares",*spec("industry_ctrl")),
      ("Industry trends","Industry shares $\\times$ quarter effects",*spec("industry_x_quarter")),
      ("Educated office work","Major group $\\times$ quarter effects",*spec("mgroup_x_quarter")),
      ("Educated office work","Drop each major group in turn (range of 22 estimates)",100*float(lg.b.min()),100*float(lg.b.max())),
      ("Pre-trends","Placebo window, 2021Q4 to 2022Q3 vs. three years earlier",*one(FD,system="occ2010",window="placebo_pre")),
      ("The measure","Unweighted",*spec("unweighted")),
      ("The measure","Trim 1 percent exposure tails",*spec("trim_dE_1pct")),
      ("The measure","At least 30 base-quarter respondents",*spec("mincell_30")),
      ("The measure","One-to-one harmonized codes only",*spec("one_to_one")),
      ("The measure","2018 census codes, 513 occupations",*one(FD,system="cps_code",window="headline")),
      ("The measure","Region shares $\\times$ quarter effects",*spec("region_x_quarter")),
      ("The measure","Eloundou et al. (2024) measure as the regressor",*spec("alone_eloundou")),
      ("The measure","Felten et al. (2023) measure as the regressor",*spec("alone_felten"))]
base_b,base_se=spec("baseline"); print(f"baseline {base_b:.2f} ({base_se:.2f})")
df=pd.DataFrame(rows,columns=["group","label","b","se"]); df.to_csv(ESTIMATES/"fig6-alternatives-data.csv",index=False)
INK,INK2,GRAY,C1="#0b0b0b","#52514e","#9a9994","#2a78d6"
fig,ax=plt.subplots(figsize=(7,6.2)); fig.subplots_adjust(left=0.47,right=0.97,top=0.97,bottom=0.1)
y=0; ticks=[]; labels=[]; groups=[]
for g,sub in df.groupby("group",sort=False):
    groups.append((g,y+0.55))
    for _,r in sub.iterrows():
        if r.label.startswith("Drop each major group"):
            ax.plot(100*lg.b.values,[y]*22,"|",color=C1,ms=9,mew=1.2); ax.text(max(r.b,r.se)+0.5,y,f"{r.b:.2f} to {r.se:.2f}",va="center",fontsize=7.5)
        else:
            ax.errorbar(r.b,y,xerr=1.96*r.se,fmt="o",color=C1,ms=5.5,lw=1.3,capsize=0); ax.text(r.b+1.96*r.se+0.5,y,f"{r.b:.2f} ({r.se:.2f})",va="center",fontsize=7.5)
        ticks.append(y); labels.append(r.label.replace("$\\times$","×").replace("--","–")); y-=1
    y-=0.8
ax.axvline(0,color=INK2,lw=0.6); ax.axvline(base_b,color=GRAY,lw=0.8,ls=(0,(3,3)))
ax.text(base_b-0.3,0.9,f"Baseline {base_b:.2f}",fontsize=7.5,color=INK2,ha="right",va="bottom")
for g,yy in groups: ax.text(-19.5,yy,g,fontsize=8.5,style="italic",va="bottom")
ax.set_yticks(ticks); ax.set_yticklabels(labels,fontsize=8); ax.set_ylim(y+0.6,1.6); ax.set_xlim(-20,8)
ax.set_xlabel("Change in the log count of workers under 30, 2023 to 2026, per sd of the exposure change (log points)",fontsize=8.5)
fig.savefig(FIGURES/"fig6-alternatives.png"); plt.close(fig); print("wrote figures/fig6-alternatives.png")
print(df.to_string(index=False))
