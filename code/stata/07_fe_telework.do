/*------------------------------------------------------------------------------
07_fe_telework.do -- remote-work controls in the occupation fixed-effects regressions.

The all-worker regressions of 05_fe_main.do over 2023Q1 to 2026Q2 (pooled, shift, and interpolated
specifications, eleven outcomes) with remote-work controls added:
    baseline       the regression of 05_fe_main.do
    baseline_cps   the same, on the occupation-quarters with a CPS telework share
    cps_share      add the quarterly CPS share of employed respondents who telework (standardized)
    hours_share    add the quarterly CPS share of hours worked from home (standardized)
    baseline_dn    the same as baseline, on the occupations with a Dingel and Neiman (2020) teleworkability value
    dn_post        add teleworkability (standardized across occupations) interacted with 1(quarter >= 2025Q1)
    all            add the CPS telework share and the teleworkability interaction
The posted coefficients are those on the exposure terms (step or interpolated step; before, shift, and
from 2025Q1 for the shift specification).

Inputs   data/cell_fe/cell_fe_baseline_occ2010.dta
Output   output/estimates/fe_telework.csv: spec model coef outcome b se p N N_clust r2 depmean
Exhibit  Appendix Table F.8.
------------------------------------------------------------------------------*/
do code/stata/00_setup.do

local start = yq(2023,1)
local end   = yq(2026,2)
use "$DATA/cell_fe/cell_fe_baseline_occ2010.dta", clear
keep if inrange(quarter, `start', `end') & fe_weight > 0 & !missing(fe_weight, occ2010, quarter)
quietly summarize exposure_step_raw
local step_mean = r(mean)
local step_sd   = r(sd)
quietly summarize exposure_interp_raw
local interp_mean = r(mean)
local interp_sd   = r(sd)
tempfile window
save `window'

tempname H
tempfile results
postfile `H' str14 spec str6 model str6 coef str20 outcome double(b se p N N_clust r2 depmean) using "`results'", replace

foreach spec in baseline baseline_cps cps_share hours_share baseline_dn dn_post all {
    foreach model in pooled shift interp {
        local z = cond("`model'" == "interp", "z_interp", "z_step")
        foreach y in $FE_PRIMARY $FE_SECONDARY {
            use `window', clear
            gen double z_step   = (exposure_step_raw - `step_mean') / `step_sd'
            gen double z_interp = (exposure_interp_raw - `interp_mean') / `interp_sd'
            gen byte post = quarter >= yq(2025,1)
            if inlist("`spec'", "baseline_cps", "cps_share", "all") drop if missing(telework_share)
            if "`spec'" == "hours_share"                           drop if missing(telework_hours_share)
            if inlist("`spec'", "baseline_dn", "dn_post", "all")   drop if missing(wfh_dingle_occ2010)
            keep if !missing(`y', `z')
            local controls ""
            if inlist("`spec'", "cps_share", "all") {
                quietly summarize telework_share
                gen double z_tw = (telework_share - r(mean)) / r(sd)
                local controls c.z_tw
            }
            if "`spec'" == "hours_share" {
                quietly summarize telework_hours_share
                gen double z_twh = (telework_hours_share - r(mean)) / r(sd)
                local controls c.z_twh
            }
            if inlist("`spec'", "dn_post", "all") {
                egen byte occ_tag = tag(occ2010)
                quietly summarize wfh_dingle_occ2010 if occ_tag
                gen double z_dn = (wfh_dingle_occ2010 - r(mean)) / r(sd)
                local controls `controls' 1.post#c.z_dn
            }
            local rhs c.`z'
            if "`model'" == "shift" local rhs c.`z' 1.post#c.`z'
            quietly reghdfe `y' `rhs' `controls' [aw=fe_weight], absorb(occ2010 quarter) vce(cluster occ2010)
            quietly summarize `y' [aw=fe_weight] if e(sample), meanonly
            local depmean = r(mean)
            if "`model'" != "shift" {
                post_result, handle(`H') x(`z') depmean(`depmean') keys(("`spec'") ("`model'") ("`model'") ("`y'"))
            }
            else {
                foreach c in before shift from {
                    if "`c'" == "before" local expr c.`z'
                    if "`c'" == "shift"  local expr 1.post#c.`z'
                    if "`c'" == "from"   local expr c.`z' + 1.post#c.`z'
                    quietly lincom `expr'
                    post `H' ("`spec'") ("`model'") ("`c'") ("`y'") (r(estimate)) (r(se)) (r(p)) (e(N)) (e(N_clust)) (e(r2)) (`depmean')
                }
            }
        }
    }
}
postclose `H'
use "`results'", clear
export delimited using "$EST/fe_telework.csv", replace
di as result "`c(N)' coefficients written to output/estimates/fe_telework.csv"
