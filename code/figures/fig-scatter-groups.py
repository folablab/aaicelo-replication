# Raw and residualized occupation scatters for every age group and for total employment.
# For each sample (all workers, under 30, 30 to 49, 50 to 64) two figures, drawn exactly as Figure 1 (raw: change in the log count
# against the stage-1 to stage-4 exposure change in points, fitted line weighted by base-period employment of the group) and as
# Appendix Figure E.1 (residualized: deviations after the twelve composition controls and the period effect, slope = coefficient of Eq. (group)).
# Inputs: the cleaned first-difference files (data/regression_inputs/cell_fd/), one per group. Outputs (output/figures/): fig-scatter-raw-<group>.png
# and fig-scatter-resid-<group>.png, the four-panel figures fig1-raw-panels.png and fig6-resid-panels.png (Appendix Figure E.1), the two-panel
# fig1-raw-intro.png (Figure 1), and the eight-panel sheet fig-scatter-all-groups.png; the plotted data go to output/estimates/. Run from anywhere: python3 code/figures/fig-scatter-groups.py
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import re, numpy as np, pandas as pd, statsmodels.api as sm, warnings, matplotlib
warnings.filterwarnings("ignore"); matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Patch
plt.style.use(str(ROOT/"code/figures/restat.mplstyle"))
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
SAMPLES={"all":("fd_baseline_3m_occ2010.dta","all workers","employment"),
         "30plus":(("fd_baseline_3m_occ2010_age_30_49.dta","fd_baseline_3m_occ2010_age_50_64.dta"),"workers aged 30 to 64","the count of workers aged 30 to 64"),
         "u30":("fd_baseline_3m_occ2010_age_u30.dta","workers under 30","the count of workers under 30"),
         "30-49":("fd_baseline_3m_occ2010_age_30_49.dta","workers aged 30 to 49","the count of workers aged 30 to 49"),
         "50-64":("fd_baseline_3m_occ2010_age_50_64.dta","workers aged 50 to 64","the count of workers aged 50 to 64")}
def load(fname):
    t=pd.read_stata(G+fname, convert_categoricals=False, convert_dates=False)
    return t[(t.horizon_years==3)&t.later_period.isin([264,265])&(t.base_emp>0)].dropna(subset=["d_log_emp","d_s4_s1","z_d_s4_s1","base_emp"]+ctrl).copy()
def combine(f1,f2):
    # workers aged 30 to 64, built from the two older groups' levels: later employment is base_emp*exp(d_log_emp) in each file;
    # occupation-windows present in both files only. The composition controls and the exposure change are occupation-level, so identical.
    a=load(f1); b=load(f2); keys=["occ2010","later_period"]
    m=a.merge(b[keys+["base_emp","d_log_emp"]],on=keys,suffixes=("","_b"))
    base=m.base_emp+m.base_emp_b; later=m.base_emp*np.exp(m.d_log_emp)+m.base_emp_b*np.exp(m.d_log_emp_b)
    m["base_emp"]=base; m["d_log_emp"]=np.log(later/base)
    return m.drop(columns=["base_emp_b","d_log_emp_b"])
def build(fname):
    df=combine(*fname) if isinstance(fname,tuple) else load(fname)
    df=df.rename(columns={"z_d_s4_s1":"z","base_emp":"w"}); df["dy"]=100*df.d_log_emp; df["x"]=df.d_s4_s1; df["later"]=(df.later_period==265).astype(int)
    fit=sm.WLS(df.dy,sm.add_constant(df[["z"]+ctrl+["later"]]),weights=df.w).fit(cov_type="cluster",cov_kwds={"groups":df.occ2010})
    raw=sm.WLS(df.dy,sm.add_constant(df[["x"]]),weights=df.w).fit(cov_type="cluster",cov_kwds={"groups":df.occ2010})
    sd=float(np.polyfit(df.z,df.x,1)[0])
    W=df.w.values; Xc=sm.add_constant(df[ctrl+["later"]])
    df["rz"]=sm.WLS(df.z,Xc,weights=W).fit().resid.values; df["ry"]=sm.WLS(df.dy,Xc,weights=W).fit().resid.values
    df["contrib"]=W*df.rz*df.ry/(W*df.rz**2).sum()
    df["group"]=df.occ2010.apply(grp); df["title"]=df.occ2010.map(titles)
    o=df.groupby("occ2010").apply(lambda g: pd.Series({"x":g.x.iloc[0],"y":np.average(g.dy,weights=g.w),"rx":np.average(g.rz,weights=g.w),"ry":np.average(g.ry,weights=g.w),
                                                       "w":g.w.sum(),"contrib":g.contrib.sum(),"group":g.group.iloc[0],"title":g.title.iloc[0]})).reset_index()
    xb=np.average(o.x,weights=o.w); yb=np.average(o.y,weights=o.w); o["c"]=o.w*(o.x-xb)*(o.y-yb)/(o.w*(o.x-xb)**2).sum()   # raw contribution, for choosing labels
    return o.sort_values("w",ascending=False).reset_index(drop=True), fit, raw, sd

C1,C2,C3,C4,C5="#2a78d6","#eb6834","#1baf7a","#4a3aa7","#c9459c"; GRAY,LGRAY,INK,INK2="#9a9994","#e4e3de","#0b0b0b","#52514e"
SERVICE=["Healthcare support","Protective service","Food preparation and serving related","Building and grounds cleaning and maintenance","Personal care and service"]   # SOC 31 to 39, the BLS service occupations
HL={"Office and administrative support":C1,"Healthcare practitioners and technical":C2,"Computer and mathematical":C3,"Sales and related":C4,**{g:C5 for g in SERVICE}}   # SOC 43, 29, 15, 41, and 31 to 39
LEG=[("Office and administrative support (SOC 43)",C1),("Healthcare practitioners and technical (SOC 29)",C2),("Computer and mathematical (SOC 15)",C3),("Sales and related (SOC 41)",C4),("Service occupations (SOC 31 to 39)",C5),("Other major groups",GRAY)]
SHORT={"Shipping, receiving, and traffic clerks":"Shipping and receiving clerks","Secretaries and administrative assistants":"Secretaries and admin. assistants",
       "Customer service representatives":"Customer service reps","Postal service mail sorters, processors, and processing machine operators":"Postal mail sorters",
       "Janitors and building cleaners":"Janitors","Emergency medical technicians and paramedics":"EMTs and paramedics","Receptionists and information clerks":"Receptionists",
       "Software developers, applications and systems software":"Software developers","Laborers and freight, stock, and material movers, hand":"Laborers and material movers",
       "Combined food preparation and serving workers":"Fast food and counter workers","Nursing, psychiatric, and home health aides":"Nursing and home health aides",
       "Driver/sales workers and truck drivers":"Truck drivers","First-line supervisors of retail sales workers":"Retail supervisors","Miscellaneous managers":"Managers, n.e.c.",
       "Miscellaneous office and administrative support workers":"Misc. office and admin. support","Elementary and middle school teachers":"Elementary and middle school teachers","Accountants and auditors":"Accountants and auditors"}
def short(t):
    t=t[0].upper()+t[1:]; t=t.split(", including")[0]; t=SHORT.get(t,t)
    return t if len(t)<=34 else t[:32].rstrip(" ,")+"..."
def place_labels(ax,rows,xcol,ycol,XLO,XHI,YL,near,textcol=None,right_frac=0.72):
    placed=[]
    for _,r in rows.sort_values(ycol).iterrows():
        off=abs(r[ycol])>YL; x=float(np.clip(r[xcol],XLO,XHI)); y=float(np.clip(r[ycol],-YL,YL)); ly=y+(4 if r[ycol]<-YL else -4 if r[ycol]>YL else 0)
        for px,py in placed:
            if abs(px-x)<near and abs(py-ly)<6: ly=py+6
        placed.append((x,ly)); ha="left" if x<XLO+(XHI-XLO)*right_frac else "right"; dx=(XHI-XLO)*0.012*(1 if ha=="left" else -1)
        txt=short(r.title)+(f" ({r[textcol]:+.2f})" if textcol else "")+(", off scale" if off else "")
        ax.annotate(txt,(x,y),xytext=(x+dx,ly),textcoords="data",fontsize=7,color=INK,ha=ha,va="center",
                    arrowprops=dict(arrowstyle="-",color=INK2,lw=0.5,shrinkA=0,shrinkB=3) if abs(ly-y)>0.5 else None,zorder=7,
                    bbox=dict(boxstyle="round,pad=0.15",fc="white",ec="none",alpha=0.75))
def bubbles(ax,o,xcol,ycol,XLO,XHI,YL,MINW,scale=1.0):
    big=o.w>=MINW; size=scale*1300*o.w/o.w.max()+8*scale**0.5; off=o[ycol].abs()>YL; mk=np.where(o[ycol]<-YL,"v","^")
    o=o.assign(col=o.group.map(HL).fillna(GRAY), hl=o.group.isin(HL))
    ax.scatter(o[xcol][~big&~off].clip(XLO,XHI),o[ycol][~big&~off],s=6*scale**0.5,c=LGRAY,zorder=2)
    for hl,z,alpha in [(False,3,0.5),(True,4,0.85)]:
        m=big&(o.hl==hl)&~off; ax.scatter(o[xcol][m].clip(XLO,XHI),o[ycol][m],s=size[m],c=o.col[m],alpha=alpha,edgecolors="white",linewidths=0.7,zorder=z)
    for mkr in ("v","^"):
        m=off&(mk==mkr); ax.scatter(o[xcol][m].clip(XLO,XHI),o[ycol][m].clip(-YL,YL),s=np.where(big[m],size[m]*0.6,10*scale**0.5),c=o.col[m],marker=mkr,alpha=0.85,edgecolors="white",linewidths=0.5,zorder=4)
    return big
hleg=[plt.Line2D([],[],marker="o",ls="",color=c,alpha=0.85,ms=8,label=l) for l,c in LEG]
R={}
for key,(fname,who,what) in SAMPLES.items():
    o,fit,raw,sd=build(fname); R[key]=(o,fit,raw,sd); b,se=fit.params["z"],fit.bse["z"]
    MINW=50000 if key=="u30" else 100000   # faint dots: fewer than 25,000 young workers; 50,000 workers for the other samples
    print(f"{key:6s} coefficient {b:6.2f} ({se:.2f})   raw weighted slope {raw.params['x']*sd:6.2f} ({raw.bse['x']*sd:.2f}) per sd   sd {sd:.1f} points   occupations {len(o)}")
    # raw
    fig,ax=plt.subplots(figsize=(8.5,6.4)); fig.subplots_adjust(bottom=0.2); XLO,XHI,YL=5,70,70
    ax.set_xlim(XLO,XHI); ax.set_ylim(-YL,YL); ax.axhline(0,color=INK2,lw=0.5,zorder=1)
    big=bubbles(ax,o,"x","y",XLO,XHI,YL,MINW)
    xs=np.array([XLO,XHI]); ax.plot(xs,raw.params["const"]+raw.params["x"]*xs,color=INK,lw=1.1,ls="--",zorder=6)
    lab=pd.concat([o.reindex(o.c.abs().sort_values(ascending=False).index).head(8), o.head(3), o[o.title.str.contains("Software developers|customer service",case=False)]]).drop_duplicates("occ2010")
    place_labels(ax,lab,"x","y",XLO,XHI,YL,near=14)
    ax.set_xlabel("Change in AI exposure from stage 1 to stage 4 (points on the 100-point scale)")
    ax.set_ylabel(f"Change in the log of {what},\n2023 to 2026 (log points)")
    h=hleg+[plt.Line2D([],[],marker="o",ls="",color=LGRAY,ms=3,label=f"Fewer than {MINW//2:,.0f} {'young ' if key=='u30' else ''}workers"),
            plt.Line2D([],[],marker="v",ls="",color=GRAY,ms=5,label="Beyond the vertical range, drawn at the edge"),
            plt.Line2D([],[],ls="--",color=INK,label=f"Fitted line (weighted by {'young ' if key=='u30' else ''}employment)")]
    fig.legend(handles=h,loc="lower center",bbox_to_anchor=(0.5,0.0),ncol=2,fontsize=7.5,handletextpad=0.4,columnspacing=1.5)
    out=FIGURES/f"fig-scatter-raw-{key}.png"; fig.savefig(out); plt.close(fig)
    # residualized
    fig,ax=plt.subplots(figsize=(8.5,6.4)); fig.subplots_adjust(bottom=0.2); XL,YL=2.6,70
    ax.set_xlim(-XL,XL); ax.set_ylim(-YL,YL)
    for (x0,x1,y0,y1) in [(-XL,0,0,YL),(0,XL,-YL,0)]: ax.add_patch(plt.Rectangle((x0,y0),x1-x0,y1-y0,color="#f3f2ee",zorder=0))
    ax.axhline(0,color=INK2,lw=0.6,zorder=1); ax.axvline(0,color=INK2,lw=0.6,zorder=1)
    xs=np.linspace(-XL,XL,2); ax.plot(xs,b*xs,color=INK,lw=1.3,ls="--",zorder=2)
    ax.text(0.02,0.03,f"slope = coefficient = {b:.2f} ({se:.2f})",transform=ax.transAxes,ha="left",va="bottom",fontsize=8,color=INK,bbox=dict(boxstyle="round,pad=0.2",fc="white",ec="none",alpha=0.85),zorder=8)
    bubbles(ax,o,"rx","ry",-XL,XL,YL,MINW)
    lab=pd.concat([o.reindex(o.contrib.abs().sort_values(ascending=False).index).head(6), o.head(1)]).drop_duplicates("occ2010")
    place_labels(ax,lab,"rx","ry",-XL,XL,YL,near=1.1,textcol="contrib")
    ax.set_xlabel("Exposure change, deviation from prediction (standard deviations)")
    ax.set_ylabel(f"Change in the log of {what},\ndeviation from prediction (log points)")
    h=hleg+[plt.Line2D([],[],marker="o",ls="",color=LGRAY,ms=3,label=f"Fewer than {MINW//2:,.0f} {'young ' if key=='u30' else ''}workers"),
            Patch(facecolor="#e9e8e2",edgecolor="none",label="Shaded: deviations of opposite sign, pulling the coefficient below zero"),
            plt.Line2D([],[],marker="v",ls="",color=GRAY,ms=6,label="Beyond the vertical range, drawn at the edge")]
    fig.legend(handles=h,loc="lower center",bbox_to_anchor=(0.5,0.0),ncol=2,fontsize=7.5,handletextpad=0.4,columnspacing=1.5)
    out=FIGURES/f"fig-scatter-resid-{key}.png"; fig.savefig(out); plt.close(fig)
    o.to_csv(ESTIMATES/f"fig-scatter-{key}-data.csv",index=False,float_format="%.4f")

# ---------------- The two four-panel figures: the raw one, the residualized one
# for the empirics section. Canvas 7 inches wide, close to the printed width, so the type is not shrunk; bubbles scaled to the panel.
ORDER={"u30":"A. Workers under 30","all":"B. All workers","30-49":"C. Workers aged 30 to 49","50-64":"D. Workers aged 50 to 64"}
OUT4={"raw":FIGURES/"fig1-raw-panels.png","resid":FIGURES/"fig6-resid-panels.png"}
for kind in ["raw","resid"]:
    fig,axes=plt.subplots(2,2,figsize=(7,7.6),sharex=True,sharey=True); fig.subplots_adjust(bottom=0.17,hspace=0.2,wspace=0.08,left=0.1,right=0.98,top=0.96)
    pw=7*(0.98-0.1)/2/(1+0.08/2); scale=2.2*(pw/8.5)**2   # area scaled to the panel, then enlarged so the bubbles stay legible at this size
    for ax,(key,title) in zip(axes.flat,ORDER.items()):
        o,fit,raw,sd=R[key]; b,se=fit.params["z"],fit.bse["z"]; MINW=50000 if key=="u30" else 100000; YL=70
        if kind=="raw":
            XLO,XHI=5,70; ax.set_xlim(XLO,XHI); ax.set_ylim(-YL,YL); ax.axhline(0,color=INK2,lw=0.5,zorder=1)
            bubbles(ax,o,"x","y",XLO,XHI,YL,MINW,scale); xs=np.array([XLO,XHI]); ax.plot(xs,raw.params["const"]+raw.params["x"]*xs,color=INK,lw=1.0,ls="--",zorder=6)
            lab=pd.concat([o.reindex(o.c.abs().sort_values(ascending=False).index).head(3), o[o.title.str.contains("Software developers|customer service",case=False)]]).drop_duplicates("occ2010")
            place_labels(ax,lab,"x","y",XLO,XHI,YL,near=45,right_frac=0.5)
            ax.text(0.03,0.04,f"slope = {raw.params['x']*sd:.2f} ({raw.bse['x']*sd:.2f}) per sd",transform=ax.transAxes,ha="left",va="bottom",fontsize=7,color=INK,bbox=dict(boxstyle="round,pad=0.2",fc="white",ec="none",alpha=0.85),zorder=8)
        else:
            XL=2.6; ax.set_xlim(-XL,XL); ax.set_ylim(-YL,YL)
            for (x0,x1,y0,y1) in [(-XL,0,0,YL),(0,XL,-YL,0)]: ax.add_patch(plt.Rectangle((x0,y0),x1-x0,y1-y0,color="#f3f2ee",zorder=0))
            ax.axhline(0,color=INK2,lw=0.6,zorder=1); ax.axvline(0,color=INK2,lw=0.6,zorder=1)
            xs=np.linspace(-XL,XL,2); ax.plot(xs,b*xs,color=INK,lw=1.2,ls="--",zorder=2)
            bubbles(ax,o,"rx","ry",-XL,XL,YL,MINW,scale)
            lab=pd.concat([o.reindex(o.contrib.abs().sort_values(ascending=False).index).head(3), o[o.title.str.contains("customer service",case=False)]]).drop_duplicates("occ2010")
            place_labels(ax,lab,"rx","ry",-XL,XL,YL,near=3.5,textcol="contrib",right_frac=0.5)
            ax.text(0.03,0.04,f"slope = coefficient = {b:.2f} ({se:.2f})",transform=ax.transAxes,ha="left",va="bottom",fontsize=7,color=INK,bbox=dict(boxstyle="round,pad=0.2",fc="white",ec="none",alpha=0.85),zorder=8)
        ax.set_title(title,fontsize=9,loc="left")
    xl="Change in AI exposure from stage 1 to stage 4 (points)" if kind=="raw" else "Exposure change, deviation from prediction (standard deviations)"
    yl="Change in the log count of workers,\n2023 to 2026 (log points)" if kind=="raw" else "Change in the log count of workers,\ndeviation from prediction (log points)"
    for ax in axes[1]: ax.set_xlabel(xl,fontsize=8)
    for ax in axes[:,0]: ax.set_ylabel(yl,fontsize=8)
    h=[plt.Line2D([],[],marker="o",ls="",color=c,alpha=0.85,ms=6,label=l) for l,c in LEG]+[plt.Line2D([],[],marker="o",ls="",color=LGRAY,ms=2.5,label="Fewer than 25,000 young workers or 50,000 workers"),
            plt.Line2D([],[],marker="v",ls="",color=GRAY,ms=4,label="Beyond the vertical range, drawn at the edge")]
    h+=[plt.Line2D([],[],ls="--",color=INK,label="Fitted line, weighted by the group's employment")] if kind=="raw" else [Patch(facecolor="#e9e8e2",edgecolor="none",label="Shaded: deviations of opposite sign, pulling the coefficient below zero")]
    fig.legend(handles=h,loc="lower center",bbox_to_anchor=(0.5,0.0),ncol=2,fontsize=7,handletextpad=0.4,columnspacing=1.2,labelspacing=0.35)
    fig.savefig(OUT4[kind]); plt.close(fig); print("wrote",OUT4[kind])

# ---------------- Figure 1: raw, two panels, workers under 30 and workers aged 30 to 64
fig,axes=plt.subplots(1,2,figsize=(7,4.4),sharey=True); fig.subplots_adjust(bottom=0.3,wspace=0.08,left=0.1,right=0.98,top=0.93)
pw=7*(0.98-0.1)/2/(1+0.08/2); scale=2.2*(pw/8.5)**2
for ax,(key,title) in zip(axes,[("u30","A. Workers under 30"),("30plus","B. Workers aged 30 to 64")]):
    o,fit,raw,sd=R[key]; MINW=50000 if key=="u30" else 100000; YL=70; XLO,XHI=5,70
    ax.set_xlim(XLO,XHI); ax.set_ylim(-YL,YL); ax.axhline(0,color=INK2,lw=0.5,zorder=1)
    bubbles(ax,o,"x","y",XLO,XHI,YL,MINW,scale); xs=np.array([XLO,XHI]); ax.plot(xs,raw.params["const"]+raw.params["x"]*xs,color=INK,lw=1.0,ls="--",zorder=6)
    lab=pd.concat([o.reindex(o.c.abs().sort_values(ascending=False).index).head(3), o[o.title.str.contains("Software developers|customer service",case=False)]]).drop_duplicates("occ2010")
    place_labels(ax,lab,"x","y",XLO,XHI,YL,near=45,right_frac=0.5)
    ax.text(0.03,0.04,f"slope = {raw.params['x']*sd:.2f} ({raw.bse['x']*sd:.2f}) per sd",transform=ax.transAxes,ha="left",va="bottom",fontsize=7,color=INK,bbox=dict(boxstyle="round,pad=0.2",fc="white",ec="none",alpha=0.85),zorder=8)
    ax.set_title(title,fontsize=9,loc="left"); ax.set_xlabel("Change in AI exposure from stage 1 to stage 4 (points)",fontsize=8)
axes[0].set_ylabel("Change in the log count of workers,\n2023 to 2026 (log points)",fontsize=8)
h=[plt.Line2D([],[],marker="o",ls="",color=c,alpha=0.85,ms=6,label=l) for l,c in LEG]+[plt.Line2D([],[],marker="o",ls="",color=LGRAY,ms=2.5,label="Fewer than 25,000 young workers or 50,000 workers"),
   plt.Line2D([],[],marker="v",ls="",color=GRAY,ms=4,label="Beyond the vertical range, drawn at the edge"),plt.Line2D([],[],ls="--",color=INK,label="Fitted line, weighted by the group's employment")]
fig.legend(handles=h,loc="lower center",bbox_to_anchor=(0.5,0.0),ncol=2,fontsize=7,handletextpad=0.4,columnspacing=1.2,labelspacing=0.35)
fig.savefig(FIGURES/"fig1-raw-intro.png"); plt.close(fig); print("wrote figures/fig1-raw-intro.png")

TITLES={"all":"All workers","u30":"Workers under 30","30-49":"Workers aged 30 to 49","50-64":"Workers aged 50 to 64"}
# ---------------- one figure: four rows (all, under 30, 30 to 49, 50 to 64), raw on the left and residualized on the right
fig,axes=plt.subplots(4,2,figsize=(12,19)); fig.subplots_adjust(bottom=0.06,top=0.975,hspace=0.26,wspace=0.16,left=0.07,right=0.98)
for row,(key,title) in enumerate(TITLES.items()):
    o,fit,raw,sd=R[key]; b,se=fit.params["z"],fit.bse["z"]; MINW=50000 if key=="u30" else 100000; YL=70
    ax=axes[row,0]; XLO,XHI=5,70; ax.set_xlim(XLO,XHI); ax.set_ylim(-YL,YL); ax.axhline(0,color=INK2,lw=0.5,zorder=1)
    bubbles(ax,o,"x","y",XLO,XHI,YL,MINW); xs=np.array([XLO,XHI]); ax.plot(xs,raw.params["const"]+raw.params["x"]*xs,color=INK,lw=1.1,ls="--",zorder=6)
    lab=pd.concat([o.reindex(o.c.abs().sort_values(ascending=False).index).head(3), o[o.title.str.contains("Software developers|customer service",case=False)]]).drop_duplicates("occ2010")
    place_labels(ax,lab,"x","y",XLO,XHI,YL,near=14)
    ax.text(0.02,0.03,f"slope = {raw.params['x']*sd:.2f} ({raw.bse['x']*sd:.2f}) per sd",transform=ax.transAxes,ha="left",va="bottom",fontsize=8,color=INK,bbox=dict(boxstyle="round,pad=0.2",fc="white",ec="none",alpha=0.85),zorder=8)
    ax.set_title(f"{title}: raw",fontsize=10,loc="left")
    ax.set_xlabel("Exposure change, stage 1 to stage 4 (points)"); ax.set_ylabel("Change in log count, 2023 to 2026 (log points)")
    ax=axes[row,1]; XL=2.6; ax.set_xlim(-XL,XL); ax.set_ylim(-YL,YL)
    for (x0,x1,y0,y1) in [(-XL,0,0,YL),(0,XL,-YL,0)]: ax.add_patch(plt.Rectangle((x0,y0),x1-x0,y1-y0,color="#f3f2ee",zorder=0))
    ax.axhline(0,color=INK2,lw=0.6,zorder=1); ax.axvline(0,color=INK2,lw=0.6,zorder=1)
    xs=np.linspace(-XL,XL,2); ax.plot(xs,b*xs,color=INK,lw=1.3,ls="--",zorder=2)
    bubbles(ax,o,"rx","ry",-XL,XL,YL,MINW)
    lab=pd.concat([o.reindex(o.contrib.abs().sort_values(ascending=False).index).head(3), o[o.title.str.contains("customer service",case=False)]]).drop_duplicates("occ2010")
    place_labels(ax,lab,"rx","ry",-XL,XL,YL,near=1.1,textcol="contrib")
    ax.text(0.02,0.03,f"slope = coefficient = {b:.2f} ({se:.2f})",transform=ax.transAxes,ha="left",va="bottom",fontsize=8,color=INK,bbox=dict(boxstyle="round,pad=0.2",fc="white",ec="none",alpha=0.85),zorder=8)
    ax.set_title(f"{title}: after the composition controls",fontsize=10,loc="left")
    ax.set_xlabel("Exposure change, deviation from prediction (sd)"); ax.set_ylabel("Change in log count, deviation from prediction (log points)")
h=hleg+[plt.Line2D([],[],marker="o",ls="",color=LGRAY,ms=3,label="Fewer than 25,000 young workers or 50,000 workers"),
        plt.Line2D([],[],marker="v",ls="",color=GRAY,ms=5,label="Beyond the vertical range, drawn at the edge"),
        plt.Line2D([],[],ls="--",color=INK,label="Left: fitted line weighted by the group's employment; right: slope = coefficient"),
        Patch(facecolor="#e9e8e2",edgecolor="none",label="Shaded: deviations of opposite sign, pulling the coefficient below zero")]
fig.legend(handles=h,loc="lower center",bbox_to_anchor=(0.5,0.0),ncol=3,fontsize=8,handletextpad=0.4,columnspacing=1.5)
fig.savefig(FIGURES/"fig-scatter-all-groups.png"); plt.close(fig); print("wrote figures/fig-scatter-all-groups.png")
print("done")
