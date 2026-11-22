# Figure 2 of the journal version (Figure 2.1 of the working paper): left panel, each model's mean composite exposure by stage; right panel, the three
# prompt-based ratings and the composite for the three-model average. Run from anywhere:
#   python3 code/figures/fig2-2-raters-dimensions.py
# Input: the task-level score file of the exposure pipeline (path below), 19,281 O*NET tasks.
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use(str(ROOT/"code/figures/restat.mplstyle"))
TK=SCORING/"master_task_scores.csv"
R={"claude":"Claude Haiku 4.5 (Anthropic)","gpt_luna":"GPT-5.6-luna (OpenAI)","gemini_flash_lite":"Gemini 3.1 Flash-Lite (Google)"}
S=(1,2,3,4)
hdr=pd.read_csv(TK,nrows=0).columns.tolist()
def ccol(r,s):
    c=[x for x in hdr if x.startswith(f"{r}_c_s{s}") and not x.endswith("_z")]; return c[0]
cols={}
for r in R:
    for s in S:
        cols[(r,"comp",s)]=f"{r}_composite_s{s}"
        cols[(r,"a",s)]=f"{r}_a_s{s}_feasible"
        cols[(r,"b",s)]=f"{r}_b_s{s}_feasible"
        cols[(r,"c",s)]=ccol(r,s)
print("C columns:",[cols[(r,"c",4)] for r in R])
df=pd.read_csv(TK,usecols=sorted(set(cols.values())))
comp={r:[df[cols[(r,"comp",s)]].mean() for s in S] for r in R}
avg=[sum(comp[r][i] for r in R)/3 for i in range(4)]
dim={}
for d in ("a","b","c"):
    dim[d]=[df[[cols[(r,d,s)] for r in R]].mean(axis=1).mean() for s in S]
dim["cinv"]=[100-v for v in dim["c"]]
# the stage dates (release and inflection month, with the quarter each is assigned to)
# now sit under each stage name, so the table is no longer needed in the paper.
xl=["Stage 1\nPre-generative\nmachine learning\nBaseline",
    "Stage 2\nChatbots\n2022Q4 to\n2023Q2",
    "Stage 3\nReasoning\nmodels\n2024Q3 to\n2025Q1",
    "Stage 4\nAI agents\n2025Q2 to\n2026Q1"]   # release quarter to inflection quarter; the months are in the notes   # release quarter to inflection quarter; the months are in the notes   # release quarter to inflection quarter; the months are in the notes
x=[0,1,2,3]
NAVY,AMBER,GREEN,RED="#1f3d7a","#c07820","#3a8a5f","#a03030"
fig,(ax1,ax2)=plt.subplots(1,2,figsize=(7.5,5.0),sharey=True)
for ax in (ax1,ax2):
    ax.set_xticks(x); ax.set_xticklabels(xl,fontsize=9.5,linespacing=1.2); ax.set_xlim(-0.45,3.6); ax.tick_params(axis="y",labelsize=9.5); ax.set_ylim(0,52)
    ax.spines[["top","right"]].set_visible(False); ax.yaxis.grid(True,color="#e6e6e6",lw=0.8); ax.set_axisbelow(True)
# left: models
sty={"claude":dict(color=NAVY,marker="o"),"gpt_luna":dict(color=AMBER,marker="s"),"gemini_flash_lite":dict(color=GREEN,marker="^")}
for r,lab in R.items():
    ax1.plot(x,comp[r],ms=6,lw=1.6,label=lab,**sty[r])
ax1.plot(x,avg,ms=6,lw=2.8,marker="D",color=RED,label="Three-model average")
for r,dy in (("claude",-2),("gpt_luna",-6),("gemini_flash_lite",-8)):
    ax1.annotate(f"{comp[r][3]:.0f}",(3,comp[r][3]),textcoords="offset points",xytext=(9,dy),fontsize=9.5,color="black")
ax1.annotate(f"{avg[3]:.0f}",(3,avg[3]),textcoords="offset points",xytext=(9,5),fontsize=9.5,color="black")
ax1.set_ylabel("Mean score across tasks (0 to 100)",fontsize=10.5)
ax1.set_title("A. Exposure score, by model",fontsize=11.5,loc="left")
ax1.legend(frameon=False,fontsize=9.5,loc="upper left")
# right: dimensions for the three-model average
for k,lab,c,mk,dy in (("a","Time AI could save",NAVY,"o",-13),("b","Share AI could complete on its own",AMBER,"s",3),
                      ("cinv","Share with no durable human advantage",GREEN,"^",-5)):
    ax2.plot(x,dim[k],ms=6,lw=1.6,ls="--",marker=mk,color=c,label=lab)
ax2.plot(x,avg,ms=6,lw=2.8,marker="D",color=RED,label="Exposure score (average of the three)")
for k,dy in (("a",-13),("b",4),("cinv",-5)):
    ax2.annotate(f"{dim[k][3]:.0f}",(3,dim[k][3]),textcoords="offset points",xytext=(9,dy),fontsize=9.5,color="black")
ax2.annotate(f"{avg[3]:.0f}",(3,avg[3]),textcoords="offset points",xytext=(9,5),fontsize=9.5,color="black")
ax2.set_title("B. The three ratings, three-model average",fontsize=11.5,loc="left")
ax2.legend(frameon=False,fontsize=9.5,loc="lower right")
fig.tight_layout(w_pad=1.0)
fig.savefig(FIGURES/"fig2-2-raters-dimensions.png",dpi=200); plt.close(fig)
for r in R: print(r,[round(v,1) for v in comp[r]])
print("average",[round(v,1) for v in avg])
for k in ("a","b","cinv"): print(k,[round(v,1) for v in dim[k]])
