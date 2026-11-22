# Figures 4 and 5 (and two variants the paper does not use): the decomposition of the young-worker coefficient drawn instead of tabulated
# (the table is Appendix Table E.1, code/tables/tab8-decomposition.py).
# The scatter (fig4-decomposition-two-panels.png: workers under 30 and young workers without a degree side by side; fig6-decomposition-scatter.png
# and figE-decomposition-scatter-nograd.png are the one-panel versions) is the added-variable plot behind the Frisch-Waugh decomposition: each
# occupation's residualized exposure change (x, standard deviations, after the twelve composition controls and the period effect) against its
# residualized change in the log count of young workers (y, log points), bubble area proportional to base-period young employment.
# The weighted regression line through the origin has slope beta. An occupation's contribution to beta is w*x*y / sum(w*x^2), so
# bubbles in the shaded quadrants (upper left, lower right) push the coefficient below zero and the others pull it toward zero.
# One point per occupation: the two stacked windows' residuals are averaged with the weights; contributions are summed (exact).
# Figure 5 (fig-decomposition-groups-vertical.png; fig6-decomposition-groups.png is the horizontal version) is the contribution column of the
# table by major group, both samples.
# Inputs: the cleaned first-difference files (data/cell_fd/), as in code/tables/tab8-decomposition.py. Run from anywhere:
#   python3 code/figures/fig6-decomposition.py
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import re, numpy as np, pandas as pd, statsmodels.api as sm, warnings, matplotlib
warnings.filterwarnings("ignore"); matplotlib.use("Agg"); import matplotlib.pyplot as plt
G=str(CELL_FD)+"/"; D=str(PIPELINE)+"/"   # data/cell_fd/ and data/pipeline/
_mg=pd.read_csv(CROSSWALKS/"occ2010_major_groups.csv")   # the 22 major groups of the 2010 census classification, with their code ranges
groups=[(int(r.mgroup),r["name"],int(r.occ2010_low),int(r.occ2010_high)) for _,r in _mg.iterrows()]
NAMES={}
def grp(code):
    for n,name,a,b in groups:
        if a<=code<=b: return NAMES.get(name,name)
    return "Unmapped"
ctrl=["base_share_female","base_share_under30","base_share_age50plus","base_share_white","base_share_black","base_share_asian","base_share_hs_less","base_share_ba","base_share_postba","base_share_south","base_share_midwest","base_share_northeast"]
titles=next(iter(pd.read_stata(D+"occ2010_q_age3.dta", iterator=True).value_labels().values()))
def build(fname):
    t=pd.read_stata(G+fname, convert_categoricals=False, convert_dates=False)
    df=t[(t.horizon_years==3)&t.later_period.isin([264,265])&(t.base_emp>0)].dropna(subset=["d_log_emp","z_d_s4_s1","base_emp"]+ctrl).copy()
    df=df.rename(columns={"z_d_s4_s1":"z","base_emp":"w"}); df["dy"]=100*df.d_log_emp; df["later"]=(df.later_period==265).astype(int)
    fit=sm.WLS(df.dy,sm.add_constant(df[["z"]+ctrl+["later"]]),weights=df.w).fit(cov_type="cluster",cov_kwds={"groups":df.occ2010})
    W=df.w.values; Xc=sm.add_constant(df[ctrl+["later"]])
    df["rz"]=sm.WLS(df.z,Xc,weights=W).fit().resid.values; df["ry"]=sm.WLS(df.dy,Xc,weights=W).fit().resid.values
    den=(W*df.rz**2).sum(); df["contrib"]=W*df.rz*df.ry/den
    df["group"]=df.occ2010.apply(grp); df["title"]=df.occ2010.map(titles)
    o=df.groupby("occ2010").apply(lambda g: pd.Series({"x":np.average(g.rz,weights=g.w),"y":np.average(g.ry,weights=g.w),"w":g.w.sum(),
                                                       "contrib":g.contrib.sum(),"group":g.group.iloc[0],"title":g.title.iloc[0]})).reset_index()
    return o, fit.params["z"], fit.bse["z"], df.groupby("group").contrib.sum()

S={"Workers under 30":build("fd_baseline_3m_occ2010_age_u30.dta"), "Under 30, less than a bachelor's degree":build("fd_baseline_3m_occ2010_ageedu_u30_no_ba.dta")}

C1,C2,C3,C4,C5="#2a78d6","#eb6834","#1baf7a","#4a3aa7","#c9459c"; GRAY,LGRAY,INK,INK2="#9a9994","#e4e3de","#0b0b0b","#52514e"
SERVICE=["Healthcare support","Protective service","Food preparation and serving related","Building and grounds cleaning and maintenance","Personal care and service"]   # SOC 31 to 39, the BLS service occupations
HL={"Office and administrative support":C1,"Healthcare practitioners and technical":C2,"Computer and mathematical":C3,"Sales and related":C4,**{g:C5 for g in SERVICE}}   # SOC 43, 29, 15, 41, and 31 to 39
LEG=[("Office and administrative support (SOC 43)",C1),("Healthcare practitioners and technical (SOC 29)",C2),("Computer and mathematical (SOC 15)",C3),("Sales and related (SOC 41)",C4),("Service occupations (SOC 31 to 39)",C5),("Other major groups",GRAY)]
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.edgecolor":INK2,"axes.linewidth":0.6,"axes.spines.top":False,"axes.spines.right":False,
    "xtick.color":INK2,"ytick.color":INK2,"xtick.labelsize":8,"ytick.labelsize":8,"legend.frameon":False,"legend.fontsize":8,"savefig.dpi":200,"savefig.facecolor":"white"})
SHORT={"Software developers, applications and systems software":"Software developers","Shipping, receiving, and traffic clerks":"Shipping and receiving clerks","Secretaries and administrative assistants":"Secretaries and admin. assistants",
       "Customer service representatives":"Customer service reps","Postal service mail sorters, processors, and processing machine operators":"Postal mail sorters",
       "Janitors and building cleaners":"Janitors","Emergency medical technicians and paramedics":"EMTs and paramedics","Receptionists and information clerks":"Receptionists"}
def short(t):
    t=t[0].upper()+t[1:]; t=t.split(", including")[0]; t=SHORT.get(t,t)
    return t if len(t)<=34 else t[:32].rstrip(" ,")+"..."
def place_labels(ax,rows,XL,YL):
    # greedy placement: labels sorted by y; a label within 1.1 s.d. and 6 log points of an earlier one is pushed up.
    # Points beyond the vertical range are drawn at the edge and tagged "off scale"; their labels start 4 points inside the edge.
    placed=[]
    for _,r in rows.sort_values("y").iterrows():
        off=abs(r.y)>YL; x=float(np.clip(r.x,-XL,XL)); y=float(np.clip(r.y,-YL,YL)); ly=y+(4 if r.y<-YL else -4 if r.y>YL else 0)
        for px,py in placed:
            if abs(px-x)<1.1 and abs(py-ly)<6: ly=py+6
        placed.append((x,ly)); ha="left" if x<XL*0.45 else "right"; dx=0.06 if ha=="left" else -0.06
        txt=f"{short(r.title)} ({r.contrib:+.2f}{', off scale' if off else ''})"
        ax.annotate(txt,(x,y),xytext=(x+dx,ly),textcoords="data",fontsize=7,color=INK,ha=ha,va="center",
                    arrowprops=dict(arrowstyle="-",color=INK2,lw=0.5,shrinkA=0,shrinkB=3) if abs(ly-y)>0.5 else None,zorder=7,
                    bbox=dict(boxstyle="round,pad=0.15",fc="white",ec="none",alpha=0.75))

# ---------------- Figure 6.4 (under 30) and Appendix Figure E (young non-graduates): the added-variable plot, one panel each
MINW=50000   # base-period young workers summed over the two windows (25,000 monthly average); smaller occupations are faint dots
OUT={"Workers under 30":FIGURES/"fig6-decomposition-scatter.png","Under 30, less than a bachelor's degree":FIGURES/"figE-decomposition-scatter-nograd.png"}
from matplotlib.patches import Patch
h=[plt.Line2D([],[],marker="o",ls="",color=c,alpha=0.85,ms=8,label=l) for l,c in LEG]+[plt.Line2D([],[],marker="o",ls="",color=LGRAY,ms=3,label="Fewer than 25,000 young workers"),Patch(facecolor="#e9e8e2",edgecolor="none",label="Shaded: exposure and young employment deviate in opposite directions, pulling the coefficient below zero"),plt.Line2D([],[],marker="v",ls="",color=GRAY,ms=6,label="Beyond the vertical range, drawn at the edge")]
for k,(o,b,se,bg) in S.items():
    fig,ax=plt.subplots(figsize=(8.5,6.4)); fig.subplots_adjust(bottom=0.2)
    o=o.sort_values("w",ascending=False).reset_index(drop=True); XL,YL=2.6,70;   # larger bubbles drawn first so smaller ones stay visible ax.set_xlim(-XL,XL); ax.set_ylim(-YL,YL)
    for (x0,x1,y0,y1) in [(-XL,0,0,YL),(0,XL,-YL,0)]: ax.add_patch(plt.Rectangle((x0,y0),x1-x0,y1-y0,color="#f3f2ee",zorder=0))
    ax.axhline(0,color=INK2,lw=0.6,zorder=1); ax.axvline(0,color=INK2,lw=0.6,zorder=1)
    xs=np.linspace(-XL,XL,2); ax.plot(xs,b*xs,color=INK,lw=1.3,ls="--",zorder=2)
    ax.text(XL*0.97,b*XL*0.97-5,f"slope = coefficient = {b:.2f}",ha="right",va="top",fontsize=8,color=INK)
    o["col"]=o.group.map(HL).fillna(GRAY); o["hl"]=o.group.isin(HL); big=o.w>=MINW; size=1300*o.w/o.w.max()+8
    off=o.y.abs()>YL; mk=np.where(o.y<-YL,"v","^")
    ax.scatter(o.x[~big&~off].clip(-XL,XL),o.y[~big&~off],s=6,c=LGRAY,zorder=2)
    for hl,z,alpha in [(False,3,0.5),(True,4,0.85)]:
        m=big&(o.hl==hl)&~off; ax.scatter(o.x[m].clip(-XL,XL),o.y[m],s=size[m],c=o.col[m],alpha=alpha,edgecolors="white",linewidths=0.7,zorder=z)
    for mkr in ("v","^"):   # off-scale occupations: a triangle at the edge, sized like the bubbles
        m=off&(mk==mkr); ax.scatter(o.x[m].clip(-XL,XL),o.y[m].clip(-YL,YL),s=np.where(big[m],size[m]*0.6,10),c=o.col[m],marker=mkr,alpha=0.85,edgecolors="white",linewidths=0.5,zorder=4)
    lab=pd.concat([o.reindex(o.contrib.abs().sort_values(ascending=False).index).head(6), o.sort_values("w",ascending=False).head(1)]).drop_duplicates("occ2010")
    place_labels(ax,lab,XL,YL)
    ax.set_xlabel("Exposure change, deviation from prediction (standard deviations)",fontsize=8.5)
    ax.set_ylabel("Change in log count of young workers,\ndeviation from prediction (log points)",fontsize=8.5)
    fig.legend(handles=h,loc="lower center",bbox_to_anchor=(0.5,0.0),ncol=2,fontsize=7.5,handletextpad=0.4,columnspacing=1.5)
    fig.savefig(OUT[k],bbox_inches="tight"); plt.close(fig); print("wrote",OUT[k])

# ---------------- Figure 6.5: contributions by major group, both samples
bgU=S["Workers under 30"][3]; bgN=S["Under 30, less than a bachelor's degree"][3]
order=bgU.sort_values().index; y=np.arange(len(order)); hgt=0.38
fig,ax=plt.subplots(figsize=(10,6.2))
ax.barh(y+hgt/2,bgU.reindex(order),height=hgt,color=C1,label="Workers under 30")
ax.barh(y-hgt/2,bgN.reindex(order),height=hgt,color=C2,label="Under 30, less than a bachelor's degree")
ax.set_yticks(y); ax.set_yticklabels(list(order),fontsize=8); ax.invert_yaxis()
ax.axvline(0,color=INK2,lw=0.6); ax.xaxis.grid(True,color=LGRAY,lw=0.5); ax.set_axisbelow(True)
ax.set_xlabel("Contribution to the coefficient (log points)",fontsize=9)
ax.legend(loc="lower left",fontsize=8.5)
for yy,v in zip(y+hgt/2,bgU.reindex(order)): ax.text(v-(0.03 if v<0 else -0.03),yy,f"{v:.2f}",va="center",ha="right" if v<0 else "left",fontsize=7,color=INK2)
for yy,v in zip(y-hgt/2,bgN.reindex(order)): ax.text(v-(0.03 if v<0 else -0.03),yy,f"{v:.2f}",va="center",ha="right" if v<0 else "left",fontsize=7,color=C2)
fig.tight_layout(); fig.savefig(FIGURES/"fig6-decomposition-groups.png",bbox_inches="tight"); plt.close(fig); print("wrote figures/fig6-decomposition-groups.png")
for k,(o,b,se,bg) in S.items(): print(k, round(b,2), round(se,2), "sum of contributions", round(o.contrib.sum(),2))

# ---------------- Figure 4: the two decompositions side by side at print width
plt.style.use(str(ROOT/"code/figures/restat.mplstyle"))
fig,axes=plt.subplots(1,2,figsize=(7,4.6),sharey=True); fig.subplots_adjust(bottom=0.3,wspace=0.08,left=0.1,right=0.98,top=0.93)
pw=7*(0.98-0.1)/2/(1+0.08/2); scale=2.2*(pw/8.5)**2
for ax,(k,title) in zip(axes,[("Workers under 30","A. Workers under 30"),("Under 30, less than a bachelor's degree","B. Under 30, less than a bachelor's degree")]):
    o,b,se,bg=S[k]; o=o.sort_values("w",ascending=False).reset_index(drop=True); XL,YL=2.6,75   # y-limit 75 so that registered nurses (+72 in Panel B) are inside the chart
    ax.set_xlim(-XL,XL); ax.set_ylim(-YL,YL)
    for (x0,x1,y0,y1) in [(-XL,0,0,YL),(0,XL,-YL,0)]: ax.add_patch(plt.Rectangle((x0,y0),x1-x0,y1-y0,color="#f3f2ee",zorder=0))
    ax.axhline(0,color=INK2,lw=0.6,zorder=1); ax.axvline(0,color=INK2,lw=0.6,zorder=1)
    xs=np.linspace(-XL,XL,2); ax.plot(xs,b*xs,color=INK,lw=1.2,ls="--",zorder=2)
    o["col"]=o.group.map(HL).fillna(GRAY); o["hl"]=o.group.isin(HL); big=o.w>=MINW; size=scale*1300*o.w/o.w.max()+8*scale**0.5
    off=o.y.abs()>YL; mk=np.where(o.y<-YL,"v","^")
    ax.scatter(o.x[~big&~off].clip(-XL,XL),o.y[~big&~off],s=6*scale**0.5,c=LGRAY,zorder=2)
    for hl,z,alpha in [(False,3,0.5),(True,4,0.85)]:
        m=big&(o.hl==hl)&~off; ax.scatter(o.x[m].clip(-XL,XL),o.y[m],s=size[m],c=o.col[m],alpha=alpha,edgecolors="white",linewidths=0.7,zorder=z)
    for mkr in ("v","^"):
        m=off&(mk==mkr); ax.scatter(o.x[m].clip(-XL,XL),o.y[m].clip(-YL,YL),s=np.where(big[m],size[m]*0.6,10*scale**0.5),c=o.col[m],marker=mkr,alpha=0.85,edgecolors="white",linewidths=0.5,zorder=4)
    lab=pd.concat([o.reindex(o.contrib.abs().sort_values(ascending=False).index).head(3), o[o.title.str.contains("customer service|registered nurses|software developers",case=False)]]).drop_duplicates("occ2010")   # the three largest contributions plus three named occupations
    o.assign(panel=title).to_csv(ESTIMATES/f"fig4-decomposition-data-{'A' if title.startswith('A') else 'B'}.csv",index=False)
    placed=[]
    for _,r in lab.sort_values("y").iterrows():
        offr=abs(r.y)>YL; x=float(np.clip(r.x,-XL,XL)); y=float(np.clip(r.y,-YL,YL)); ly=y+(4 if r.y<-YL else -4 if r.y>YL else 0)
        if -YL<r.y<-45: ly=y+7   # keep labels near the bottom edge clear of the slope text
        for px,py in placed:
            if abs(py-ly)<6: ly=py+6
        placed.append((x,ly)); ha="left" if x<0 else "right"; dx=0.08 if ha=="left" else -0.08
        ax.annotate(f"{short(r.title)} ({r.contrib:+.2f}{', off scale' if offr else ''})",(x,y),xytext=(x+dx,ly),textcoords="data",fontsize=7,color=INK,ha=ha,va="center",
                    arrowprops=dict(arrowstyle="-",color=INK2,lw=0.5,shrinkA=0,shrinkB=3) if abs(ly-y)>0.5 else None,zorder=7,bbox=dict(boxstyle="round,pad=0.12",fc="white",ec="none",alpha=0.8))
    ax.text(0.03,0.04,f"slope = coefficient = {b:.2f} ({se:.2f})",transform=ax.transAxes,ha="left",va="bottom",fontsize=7,color=INK,bbox=dict(boxstyle="round,pad=0.2",fc="white",ec="none",alpha=0.85),zorder=8)
    ax.set_title(title,fontsize=9,loc="left"); ax.set_xlabel("Exposure change, deviation from prediction (sd)",fontsize=8)
axes[0].set_ylabel("Change in the log count of workers,\ndeviation from prediction (log points)",fontsize=8)
h=[plt.Line2D([],[],marker="o",ls="",color=c,alpha=0.85,ms=6,label=l) for l,c in LEG]+[plt.Line2D([],[],marker="o",ls="",color=LGRAY,ms=2.5,label="Fewer than 25,000 young workers"),
   plt.Line2D([],[],marker="v",ls="",color=GRAY,ms=4,label="Beyond the vertical range, drawn at the edge"),Patch(facecolor="#e9e8e2",edgecolor="none",label="Shaded: deviations of opposite sign, pulling the coefficient below zero")]
fig.legend(handles=h,loc="lower center",bbox_to_anchor=(0.5,0.0),ncol=2,fontsize=7,handletextpad=0.4,columnspacing=1.2,labelspacing=0.35)
fig.savefig(FIGURES/"fig4-decomposition-two-panels.png"); plt.close(fig); print("wrote figures/fig4-decomposition-two-panels.png")

# ---------------- Figure 5: the contributions by major group as vertical bars on a compact canvas
order=bgU.sort_values().index; x=np.arange(len(order)); wd=0.4
fig,ax=plt.subplots(figsize=(7,3.9)); fig.subplots_adjust(bottom=0.42,left=0.09,right=0.99,top=0.97)
ax.bar(x-wd/2,bgU.reindex(order),width=wd,color=C1,label="Workers under 30")
ax.bar(x+wd/2,bgN.reindex(order),width=wd,color=C2,label="Under 30, less than a bachelor's degree")
ax.axhline(0,color=INK2,lw=0.6); ax.yaxis.grid(True,color=LGRAY,lw=0.5); ax.set_axisbelow(True)
ax.set_xticks(x); SHORTG={"Office and administrative support":"Office and administrative support","Healthcare practitioners and technical":"Healthcare practitioners","Arts, design, entertainment, sports, and media":"Arts, design, and media","Transportation and material moving":"Transportation and material moving","Food preparation and serving related":"Food preparation and serving","Installation, maintenance, and repair":"Installation and repair","Educational instruction and library":"Education and library","Business and financial operations":"Business and financial","Life, physical, and social science":"Life, physical, and social science","Building and grounds cleaning and maintenance":"Building and grounds cleaning","Sales and related":"Sales and related","Community and social service":"Community and social service"}
ax.set_xticklabels([SHORTG.get(g,g) for g in order],rotation=50,ha="right",fontsize=7.5)
ax.set_ylabel("Contribution to the coefficient\n(log points)",fontsize=8.5); ax.tick_params(axis="y",labelsize=8)
ax.legend(loc="lower right",fontsize=8)
fig.savefig(FIGURES/"fig-decomposition-groups-vertical.png"); plt.close(fig); print("wrote figures/fig-decomposition-groups-vertical.png")
