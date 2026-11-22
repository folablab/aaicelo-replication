# Figure 3.1: workers ranked by the exposure of their occupation, one curve per capability stage.
# Run from anywhere:  python3 code/figures/fig3-1-frontier.py
# Inputs: the AAICELO pipeline's harmonized occupation scores (occ2010_measures.dta) and the occupation
# quarter panel (occ2010_quarter_panel_v2.dta) for employment weights, averaged over the four quarters
# of 2023, the first year generative AI was in use at work. Each curve is the employment-weighted quantile function of
# the score at that stage; where it crosses 50 is the share of workers whose occupation AI could do
# about half of. Weighting by 2019, 2024, or 2026 employment instead changes the shares by about a point.
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
A=str(PIPELINE); YEAR=2023
m=pd.read_stata(f"{A}/occ2010_measures.dta",convert_categoricals=False)
p=pd.read_stata(f"{A}/occ2010_quarter_panel_v2.dta",convert_categoricals=False)[["occ2010","qdate","emp"]]
p["year"]=pd.to_datetime(p.qdate).dt.year
w=p[p.year==YEAR].groupby("occ2010")["emp"].mean().rename("w").reset_index()
d=m.merge(w,on="occ2010").dropna(subset=["ens_s1","ens_s2","ens_s3","ens_s4","w"]); W=(d.w/d.w.sum()).values
COL={1:"#8a8a8a",2:"#1f3d7a",3:"#c07820",4:"#a03030"}
LAB={1:"Stage 1: pre-generative machine learning",2:"Stage 2: chatbots",3:"Stage 3: reasoning models",4:"Stage 4: AI agents"}
fig,ax=plt.subplots(figsize=(8.5,4.9))
stats={}
for s in (1,2,3,4):
    x=d[f"ens_s{s}"].values; o=np.argsort(x); cw=np.cumsum(W[o])
    share=W[x>=50].sum(); q=lambda c: x[o][np.searchsorted(cw,c)]
    stats[s]={"share50":share,"p10":q(.1),"p50":q(.5),"p90":q(.9)}
    lab=LAB[s]+(f"  ({share*100:.0f}% of workers at 50 or more)" if s>1 else "  (none at 50 or more)")
    ax.step(np.concatenate([[0],cw]),np.concatenate([[x[o][0]],x[o]]),where="pre",color=COL[s],lw=2.4 if s==4 else 1.7,label=lab)
    if share>0: ax.plot([1-share],[50],marker="o",ms=5,color=COL[s],zorder=5)
ax.axhline(50,color="k",lw=0.8,ls=":")
ax.text(0.01,46.5,"Score of 50: AI could do about half the occupation's work",fontsize=8,color="#444")
ax.set_xlim(0,1); ax.set_ylim(0,85)
ax.set_xlabel(f"Workers ranked from least to most exposed, cumulative share of {YEAR} employment")
ax.set_ylabel("Exposure score of the worker's occupation"); ax.spines[["top","right"]].set_visible(False)
ax.legend(frameon=False,fontsize=8.5,loc="upper left"); ax.yaxis.grid(True,color="#e6e6e6"); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(FIGURES/"fig3-1-frontier.png",dpi=200); plt.close(fig)
print(len(d),"occupations")
for s,v in stats.items(): print(f"stage {s}: share>=50 {v['share50']*100:.1f}%  p10 {v['p10']:.1f}  median {v['p50']:.1f}  p90 {v['p90']:.1f}")
