# Figure 2.3 (main text, two panels) and Appendix Figure B.x (six panels): adoption against the
# exposure measures, one occupation at a time. Run from anywhere:
#   python3 code/figures/fig2-3-adoption.py
# Input: the occupation measures file of the AAICELO pipeline (path below). Same construction as
# the September draft's figure: measures standardized with RPS respondent weights, bubbles sized
# by respondents, weighted least-squares fit, weighted correlation in the panel title.
# These correlations are 0.7147 (S4-S1) and 0.7347 (Eloundou); Table 2.4 prints 0.72 and 0.74, so the table's
# source computation differs slightly (weights or sample) and should be checked against this script.
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
M=PIPELINE/"occ_measures.csv"
m=pd.read_csv(M)
COLS=["rps_adoption","rps_n","d_ens_s4_s1","d_ens_s3_s1","d_ens_s3_s2","d_ens_s4_s3","felten_aioe","dv_rating_gamma"]
for c in COLS: m[c]=pd.to_numeric(m[c],errors="coerce")
m=m.dropna(subset=["rps_adoption","rps_n"]); m=m[(m.rps_adoption>=0)&(m.rps_adoption<=1)&(m.rps_n>=20)]
def wz(x,w):
    mu=np.average(x,weights=w); sd=np.sqrt(np.average((x-mu)**2,weights=w)); return (x-mu)/sd
def wcorr(x,y,w):
    mx,my=np.average(x,weights=w),np.average(y,weights=w)
    return np.average((x-mx)*(y-my),weights=w)/np.sqrt(np.average((x-mx)**2,weights=w)*np.average((y-my)**2,weights=w))
def panel(ax,v,lab,ylabel=True):
    d=m.dropna(subset=[v]); z=wz(d[v].values,d.rps_n.values); y=d.rps_adoption.values; w=d.rps_n.values
    ax.scatter(z,y,s=8+w/3,facecolors="none",edgecolors="#1f3d7a",alpha=.6,linewidths=.9)
    b,a=np.polyfit(z,y,1,w=np.sqrt(w)); xs=np.linspace(z.min(),z.max(),50); ax.plot(xs,a+b*xs,color="#a03030",lw=1.8)
    r=wcorr(z,y,w); ax.set_title(f"{lab}   (correlation {r:.2f}, n = {len(d)})",fontsize=10)
    ax.set_xlabel("Standardized measure",fontsize=9); ax.tick_params(labelsize=9)
    ax.spines[["top","right"]].set_visible(False)
    if ylabel: ax.set_ylabel("Share using generative AI at work",fontsize=9.5)
    return r
out={}
# main text: two panels
fig,axes=plt.subplots(1,2,figsize=(10,4.3),sharey=True)
out["s4_s1"]=panel(axes[0],"d_ens_s4_s1","Change in our score, stage 1 to stage 4")
out["eloundou"]=panel(axes[1],"dv_rating_gamma","Eloundou et al. (2024)",ylabel=False)
fig.tight_layout(); fig.savefig(FIGURES/"fig2-3-adoption-main.png",dpi=200); plt.close(fig)
# appendix: six panels
fig,axes=plt.subplots(2,3,figsize=(13,8),sharey=True)
PANELS=[("d_ens_s4_s1","Our score, stage 1 to stage 4"),("d_ens_s3_s1","Our score, stage 1 to stage 3"),
        ("d_ens_s3_s2","Our score, stage 2 to stage 3"),("d_ens_s4_s3","Our score, stage 3 to stage 4"),
        ("felten_aioe","Felten et al. (2021)"),("dv_rating_gamma","Eloundou et al. (2024)")]
for i,(ax,(v,lab)) in enumerate(zip(axes.flatten(),PANELS)):
    out[v]=panel(ax,v,lab,ylabel=(i%3==0))
fig.tight_layout(); fig.savefig(FIGURES/"figB-adoption-all.png",dpi=200); plt.close(fig)
print({k:round(v,3) for k,v in out.items()})
