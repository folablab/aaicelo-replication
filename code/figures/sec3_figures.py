"""Appendix Figures B.2 to B.4: ten years of outcomes by quartile of exposure change, and the exposure gap in outcomes by age and
by education. Figure notes are typeset in LaTeX, not drawn.
Inputs: data/pipeline/fig31_series_s41.csv and data/pipeline/{occ2010_measures,occ2010_q_age3,occ2010_q_edu2}.dta.
Run from anywhere: python3 code/figures/sec3_figures.py"""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); from paths import *   # repository-relative paths (code/paths.py)
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
D = PIPELINE; FIG = FIGURES
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"; GRAY, LGRAY, INK, INK2 = "#7a7974", "#d9d8d3", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "axes.edgecolor": INK2, "axes.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "grid.color": LGRAY, "grid.linewidth": 0.5, "legend.frameon": False, "legend.fontsize": 8, "figure.dpi": 100, "savefig.dpi": 200, "savefig.facecolor": "white", "axes.facecolor": "white"})
STAGES = [2023.25, 2025.0, 2026.0]
def qnum(v):
    if hasattr(v, "year"): return v.year + (v.month - 1) / 12
    v = int(v); return 1960 + v // 4 + (v % 4) / 4
def xaxis(ax):
    ax.set_xlim(2017, 2026.6); ax.set_xticks(range(2017, 2027)); ax.set_xticklabels([str(y) for y in range(2017, 2027)], fontsize=7.5, rotation=45)
    ax.set_xticks([y + q / 4 for y in range(2017, 2027) for q in (1, 2, 3)], minor=True); ax.tick_params(axis="x", which="minor", length=2)
def save(fig, name): fig.tight_layout(); fig.savefig(FIG / name, bbox_inches="tight"); plt.close(fig); print("wrote", name)

def outcomes():   # Figure 3.2: ten years of outcomes, top versus bottom quartile
    df = pd.read_csv(PIPELINE / "fig31_series_s41.csv"); df["t"] = df["year"] + (df["quarter"] - 1) / 4
    panels = [("empidx", "Employment (index, 2022Q4 = 100)"), ("unemp", "Unemployment rate (pp from 2022Q4)"), ("hours", "Hours, main job (from 2022Q4)"),
              ("lwage", "Log real hourly earnings (×100, from 2022Q4)"), ("ptsh", "Part-time share (pp from 2022Q4)")]
    T0 = 2022.75; vlines = [2022.875, 2023.0, 2024.625, 2025.0, 2025.375, 2026.0]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.4)); axes = axes.flatten()
    for ax, (v, ttl) in zip(axes, panels):
        for q, lab, col, ls in [(4, "Top quartile of the change in exposure, stage 1 to 4", "#1f3d7a", "-"), (1, "Bottom quartile", "#a03030", "--")]:
            s_ = df[df["expq41"] == q].sort_values("t"); base = float(s_.loc[np.isclose(s_.t, T0), v].iloc[0])
            y = s_[v] / base * 100 if v == "empidx" else (s_[v] - base) * (100 if v == "lwage" else 1)
            ax.plot(s_.t, y, ls, color=col, lw=1.6, label=lab)
        ax.axhline(100 if v == "empidx" else 0, color="black", lw=0.6)
        for x in vlines: ax.axvline(x, color="red", lw=0.6, ls=":", alpha=0.6)
        ax.axvline(T0, color="black", lw=0.9, ls="--", alpha=0.7); ax.set_title(ttl, fontsize=10.5); xaxis(ax); ax.tick_params(axis="y", labelsize=8.5)
    axes[5].axis("off"); h_, l_ = axes[0].get_legend_handles_labels(); axes[5].legend(h_, l_, loc="center", fontsize=11, frameon=False)
    save(fig, "fig3-3-outcomes-quartiles.png")

def gaps(byfile, byvar, groups, fname, title):   # Figure 3.3 and Appendix Figure B.2: the exposure gap by group
    m = pd.read_stata(D / "occ2010_measures.dta", convert_categoricals=False).dropna(subset=["d_ens_s4_s1"]).copy()
    m["q"] = pd.qcut(m["d_ens_s4_s1"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    g = pd.read_stata(D / byfile, convert_dates=False, convert_categoricals=False).merge(m[["occ2010", "q"]], on="occ2010"); g = g[g.q.isin([1, 4])].dropna(subset=[byvar])
    agg = g.groupby([byvar, "q", "qdate"]).agg(empwt=("empwt", "sum"), lfw=("lfw", "sum"), unw=("unw", "sum"), hrsw=("hrsw", "sum"), hrsd=("hrsd", "sum"), ptw=("ptw", "sum"), ftvw=("ftvw", "sum"), wgw=("wgw", "sum"), wgd=("wgd", "sum")).reset_index()
    agg["x"] = agg.qdate.map(qnum); agg["emp"] = agg.empwt; agg["unemp"] = agg.unw / agg.lfw * 100; agg["hours"] = agg.hrsw / agg.hrsd; agg["lwage"] = agg.wgw / agg.wgd * 100; agg["ptsh"] = agg.ptw / agg.ftvw * 100
    panels = [("emp", "Employment (index gap, 2022Q4 = 100)"), ("unemp", "Unemployment rate gap (pp)"), ("hours", "Hours gap (from 2022Q4)"), ("lwage", "Log real wage gap (×100, from 2022Q4)"), ("ptsh", "Part-time share gap (pp, from 2022Q4)")]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.4)); axes = axes.flat
    for ax, (v, ttl) in zip(axes, panels):
        for lev, lab, col in groups:
            top = agg[(agg[byvar] == lev) & (agg.q == 4)].set_index("x")[v].sort_index(); bot = agg[(agg[byvar] == lev) & (agg.q == 1)].set_index("x")[v].sort_index()
            if v == "emp": top = top / top.loc[np.isclose(top.index, 2022.75)].iloc[0] * 100; bot = bot / bot.loc[np.isclose(bot.index, 2022.75)].iloc[0] * 100
            else: top = top - top.loc[np.isclose(top.index, 2022.75)].iloc[0]; bot = bot - bot.loc[np.isclose(bot.index, 2022.75)].iloc[0]
            ax.plot(top.index, (top - bot).values, color=col, lw=1.6, label=lab)
        ax.axhline(0, color=INK2, lw=0.6, zorder=1)
        for x in STAGES: ax.axvline(x, color=GRAY, lw=0.7, ls=(0, (3, 3)), zorder=0)
        ax.axvline(2022.75, color=INK, lw=0.9, ls="--", alpha=0.7); ax.set_title(ttl, fontsize=10); ax.grid(axis="y", alpha=0.4); xaxis(ax)
    axes[5].axis("off"); h_, l_ = axes[0].get_legend_handles_labels(); axes[5].legend(h_, l_, loc="center", fontsize=12, frameon=False, title=title)
    save(fig, fname)

outcomes()
gaps("occ2010_q_age3.dta", "age_g3", [(1, "18–29", C1), (2, "30–49", C2), (3, "50–64", C3)], "fig3-4-gaps-age.png", "Age group")
gaps("occ2010_q_edu2.dta", "edu2", [(0, "Less than BA", C2), (1, "BA or more", C1)], "fig3-5-gaps-edu.png", "Education")
