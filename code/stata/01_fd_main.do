/*------------------------------------------------------------------------------
01_fd_main.do -- stacked three-year first differences on occupation cells (Eq. 1 of the paper).

For each occupation (and group) and each window, the regression is
    d_y  =  beta * z_d_sX_s1  +  twelve base-period composition controls  +  period effects
weighted by base-period employment of the occupation (or of the group within the occupation),
standard errors clustered by occupation. The exposure change is standardized across
occupations (z_d_s4_s1: stage 1 to 4; z_d_s3_s1: stage 1 to 3).

Windows (later period t, base period t minus 3 years):
    headline        2026Q1 vs 2023Q1 and 2026Q2 vs 2023Q2, stacked
    placebo_pre     2021Q4 vs 2018Q4 through 2022Q3 vs 2019Q3, stacked (pre-AI placebo)
    base2022        2025Q1 vs 2022Q1 through 2025Q4 vs 2022Q4, stacked (robustness, Figure 6)
    end<YYYY>q<Q>   a single end quarter (Figure 7 and Appendix Figure G.1)
Units: q = occupation-quarter cells; 6m = six-month averages (Appendix Table C.2, panels B and D).

Inputs   data/cell_fd/fd_baseline_3m_<system>[_<group>].dta, fd_baseline_6m_<system>.dta
Output   output/estimates/fd_main.csv, one row per regression:
         system group unit horizon window start end exposure outcome b se p N N_clust r2 depmean
Exhibits Tables 3 and 4; Appendix Tables C.2, D.1 to D.3, F.9, F.10, G.1, G.2; Figures 1, 3, 6, 7, G.1.
Runtime  about four minutes.
------------------------------------------------------------------------------*/
do code/stata/00_setup.do

/*------------------------------------------------------------------------------
fd_window -- estimate one stacked window for every exposure and outcome, post results.
------------------------------------------------------------------------------*/
capture program drop fd_window
program define fd_window
    syntax, File(string) SYStem(string) Group(string) Unit(string) Horizon(integer) ///
        Start(integer) End(integer) Window(string) EXPosures(string) Outcomes(string) Handle(name)
    use "`file'", clear
    keep if horizon_years == `horizon' & inrange(later_period, `start', `end')
    keep if base_emp > 0 & !missing(base_emp)
    * Every requested later period must be present; otherwise the window is not estimated.
    quietly levelsof later_period, local(periods)
    local want = `end' - `start' + 1
    if `: word count `periods'' != `want' {
        di as text "skip: `system' `group' `unit' h`horizon' `window' (periods available: `periods')"
        exit
    }
    local occvar occ2010
    if "`system'" == "cps_code" local occvar cps_code
    foreach exp of local exposures {
        local x z_d_`exp'
        foreach y of local outcomes {
            quietly count if !missing(`y', `x')
            if r(N) == 0 continue
            * Composition controls that are constant in this sample are dropped (none is, in practice).
            local ctrl ""
            foreach cv of global FD_CONTROLS {
                quietly summarize `cv' if !missing(`y', `x')
                if r(N) > 0 & r(min) < r(max) local ctrl "`ctrl' `cv'"
            }
            quietly regress `y' `x' `ctrl' i.later_period [aw=base_emp], vce(cluster `occvar')
            quietly summarize `y' if e(sample) [aw=base_emp], meanonly
            post_result, handle(`handle') x(`x') depmean(`r(mean)') ///
                keys(("`system'") ("`group'") ("`unit'") (`horizon') ("`window'") (`start') (`end') ("`exp'") ("`y'"))
        }
    }
end

tempname H
tempfile results
postfile `H' str8 system str20 group str2 unit horizon str12 window start end str5 exposure str20 outcome ///
    double(b se p N N_clust r2 depmean) using "`results'", replace

local all_outcomes $FD_PRIMARY $FD_SECONDARY
local age3  age_u30 age_30_49 age_50_64
local edu2  edu_no_ba edu_ba_plus
local age6  ageedu_u30_no_ba ageedu_u30_ba_plus ageedu_30_49_no_ba ageedu_30_49_ba_plus ageedu_50_64_no_ba ageedu_50_64_ba_plus

local headline_start = yq(2026,1)
local headline_end   = yq(2026,2)
local placebo_start  = yq(2021,4)
local placebo_end    = yq(2022,3)
local base22_start   = yq(2025,1)
local base22_end     = yq(2025,4)

foreach system in occ2010 cps_code {
    local q  "$DATA/cell_fd/fd_baseline_3m_`system'"
    local m6 "$DATA/cell_fd/fd_baseline_6m_`system'"

    * All workers: quarter cells and six-month averages, both exposures, all outcomes.
    foreach unit in q 6m {
        local f = cond("`unit'" == "q", "`q'.dta", "`m6'.dta")
        fd_window, file("`f'") system(`system') group(all) unit(`unit') horizon(3) ///
            start(`headline_start') end(`headline_end') window(headline) exposures(s4_s1 s3_s1) ///
            outcomes(`all_outcomes') handle(`H')
        fd_window, file("`f'") system(`system') group(all) unit(`unit') horizon(3) ///
            start(`placebo_start') end(`placebo_end') window(placebo_pre) exposures(s4_s1 s3_s1) ///
            outcomes(`all_outcomes') handle(`H')
    }

    * Groups: quarter cells. Age and education separately; age by education jointly.
    foreach g in `age3' `edu2' `age6' {
        fd_window, file("`q'_`g'.dta") system(`system') group(`g') unit(q) horizon(3) ///
            start(`headline_start') end(`headline_end') window(headline) exposures(s4_s1 s3_s1) ///
            outcomes(`all_outcomes') handle(`H')
        fd_window, file("`q'_`g'.dta") system(`system') group(`g') unit(q) horizon(3) ///
            start(`placebo_start') end(`placebo_end') window(placebo_pre) exposures(s4_s1 s3_s1) ///
            outcomes(`all_outcomes') handle(`H')
    }

    if "`system'" == "occ2010" {
        * Three-year differences with the base period in 2022 (Figure 6), all workers and by age.
        fd_window, file("`q'.dta") system(`system') group(all) unit(q) horizon(3) ///
            start(`base22_start') end(`base22_end') window(base2022) exposures(s4_s1) ///
            outcomes($FD_PRIMARY) handle(`H')
        foreach g in `age3' {
            fd_window, file("`q'_`g'.dta") system(`system') group(`g') unit(q) horizon(3) ///
                start(`base22_start') end(`base22_end') window(base2022) exposures(s4_s1) ///
                outcomes($FD_PRIMARY) handle(`H')
        }
        * Single end quarters 2021Q4 to 2026Q2 (Figure 7 and Appendix Figure G.1), all workers and by age.
        forvalues t = `=yq(2021,4)'/`=yq(2026,2)' {
            local tag end`=year(dofq(`t'))'q`=quarter(dofq(`t'))'
            foreach g in all `age3' {
                local f = cond("`g'" == "all", "`q'.dta", "`q'_`g'.dta")
                fd_window, file("`f'") system(`system') group(`g') unit(q) horizon(3) ///
                    start(`t') end(`t') window(`tag') exposures(s4_s1) outcomes($FD_PRIMARY) handle(`H')
            }
        }
    }
}

postclose `H'
use "`results'", clear
format b se p depmean %12.6g
format N N_clust %9.0f
export delimited using "$EST/fd_main.csv", replace
di as result "`c(N)' regressions written to output/estimates/fd_main.csv"
