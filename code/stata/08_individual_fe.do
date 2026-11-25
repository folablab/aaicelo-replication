/*------------------------------------------------------------------------------
08_individual_fe.do -- individual-level fixed-effects estimates (Appendix Table C.3, Panel B).

The individual-level regressions are estimated on the linked monthly CPS records of each worker
(about 1.7 million person-months), which IPUMS terms do not allow the package to redistribute. The
package therefore ships the saved Stata estimates of those regressions (data/individual_fe/estimates/,
written by the estimation do-file in code/stata/individual_fe_source/) and this script reads them.

Regressions (reghdfe; occupation and month fixed effects; controls for age, age squared, sex, race,
education, and region; CPS person weights; standard errors clustered by occupation), for the windows
W2023 (January 2023 to June 2026) and W2021 (October 2021 to June 2026):
    fe_<W>_baseline_<y>.ster          pooled step            (coef step)
    fe_<W>_baseline_<y>_linear.ster   interpolated step      (coef interp)
    fe_<W>_post_<y>.ster              era split at Jan. 2025 (coefs before, shift, from)
Outcomes: Demp (employed), ahrswork1 (hours, main job), ln_hrearn_tc_real (log real hourly earnings),
parttime_usual (usually part time).

Output   output/estimates/individual_fe.csv: window spec coef outcome b se p N N_clust r2 depmean
------------------------------------------------------------------------------*/
do code/stata/00_setup.do

tempname H
tempfile results
postfile `H' str5 window str6 spec str6 coef str20 outcome double(b se p N N_clust r2 depmean) using "`results'", replace

foreach W in W2023 W2021 {
    foreach y in Demp ahrswork1 ln_hrearn_tc_real parttime_usual {
        estimates use "$DATA/individual_fe/estimates/fe_`W'_baseline_`y'.ster"
        post_result, handle(`H') x(z_step) depmean(`e(depvar_mean)') keys(("`W'") ("pooled") ("step") ("`y'"))
        estimates use "$DATA/individual_fe/estimates/fe_`W'_baseline_`y'_linear.ster"
        post_result, handle(`H') x(z_linear) depmean(`e(depvar_mean)') keys(("`W'") ("interp") ("interp") ("`y'"))
        estimates use "$DATA/individual_fe/estimates/fe_`W'_post_`y'.ster"
        local depmean = e(depvar_mean)
        foreach c in before shift from {
            if "`c'" == "before" local expr c.z_step
            if "`c'" == "shift"  local expr 1.post2025#c.z_step
            if "`c'" == "from"   local expr c.z_step + 1.post2025#c.z_step
            quietly lincom `expr'
            post `H' ("`W'") ("shift") ("`c'") ("`y'") (r(estimate)) (r(se)) (r(p)) (e(N)) (e(N_clust)) (e(r2)) (`depmean')
        }
    }
}
postclose `H'
use "`results'", clear
export delimited using "$EST/individual_fe.csv", replace
di as result "`c(N)' coefficients written to output/estimates/individual_fe.csv"
