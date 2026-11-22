/*------------------------------------------------------------------------------
05_fe_main.do -- occupation-by-quarter fixed-effects regressions (Eqs. 2 and 3 of the paper).

Panel of occupation-quarter cells (all workers) or occupation-group-quarter cells (by age group,
by education). The exposure score of a quarter is the score of the capability stage prevailing in
that quarter (the step), or the score interpolated from the release of a stage to its inflection
(interpolated step); both are standardized with the mean and standard deviation of the all-worker
occupation-quarter cells in the estimation window.

Specifications (weights: fixed 2019 employment of the occupation, or of the group within the
occupation; standard errors clustered by occupation)
    pooled   y = b * z_step   + occupation FE + quarter FE
    shift    y = b_before * z_step + b_shift * z_step x 1(quarter >= 2025Q1) + FE
             (b_from = b_before + b_shift is the coefficient from 2025Q1 on)
    interp   y = b * z_interp + FE
Group panels interact the exposure terms with group indicators and use occupation-by-group and
group-by-quarter fixed effects; the posted coefficient of each group is the sum of the base term and
its interaction (lincom).

Windows   W2023  2023Q1 to 2026Q2       W2021  2021Q3 to 2026Q2

Inputs   data/cell_fe/cell_fe_baseline_occ2010.dta, cell_fe_age3_occ2010.dta, cell_fe_edu2_occ2010.dta
Output   output/estimates/fe_main.csv, one row per coefficient:
         window panel group spec coef outcome b se p N N_clust r2 depmean
         coef is step | interp | before | shift | from; depmean is the weighted outcome mean over the
         estimation sample (all groups of the panel).
Exhibits Table 5; Appendix Tables C.3 (Panel A), D.4; Figure 6.
Runtime  about two minutes.
------------------------------------------------------------------------------*/
do code/stata/00_setup.do

tempname H
tempfile results
postfile `H' str5 window str9 panel str8 group str6 spec str6 coef str20 outcome double(b se p N N_clust r2 depmean) ///
    using "`results'", replace

* post_lincom: evaluate a linear combination of the current reghdfe estimates and post it.
capture program drop post_lincom
program define post_lincom
    syntax, Handle(name) EXPression(string) Keys(string asis) DEPmean(real)
    quietly lincom `expression'
    post `handle' `keys' (r(estimate)) (r(se)) (r(p)) (e(N)) (e(N_clust)) (e(r2)) (`depmean')
end

foreach W in W2023 W2021 {
    local start = cond("`W'" == "W2023", yq(2023,1), yq(2021,3))
    * Window-specific standardization of the two exposure measures, on all-worker cells.
    use "$DATA/cell_fe/cell_fe_baseline_occ2010.dta", clear
    keep if inrange(quarter, `start', yq(2026,2)) & fe_weight > 0 & !missing(fe_weight, occ2010, quarter)
    quietly summarize exposure_step_raw
    local step_mean = r(mean)
    local step_sd   = r(sd)
    quietly summarize exposure_interp_raw
    local interp_mean = r(mean)
    local interp_sd   = r(sd)

    foreach panel in aggregate age3 edu2 {
        local file "$DATA/cell_fe/cell_fe_baseline_occ2010.dta"
        if "`panel'" != "aggregate" local file "$DATA/cell_fe/cell_fe_`panel'_occ2010.dta"
        foreach y in $FE_PRIMARY $FE_SECONDARY {
            use "`file'", clear
            keep if inrange(quarter, `start', yq(2026,2)) & fe_weight > 0 & !missing(fe_weight, occ2010, quarter)
            if "`panel'" != "aggregate" keep if !missing(`panel')
            gen double z_step   = (exposure_step_raw - `step_mean') / `step_sd'
            gen double z_interp = (exposure_interp_raw - `interp_mean') / `interp_sd'
            gen byte post = quarter >= yq(2025,1)

            if "`panel'" == "aggregate" {
                local absorb occ2010 quarter
                local groups all
                local dummies ""
            }
            if "`panel'" == "age3" {
                gen byte g_u30   = age3 == 1
                gen byte g_older = age3 == 3
                local absorb occ2010#age3 age3#quarter
                local groups u30 30_49 50_64
                local dummies g_u30 g_older
            }
            if "`panel'" == "edu2" {
                gen byte g_ba = edu2 == 2
                local absorb occ2010#edu2 edu2#quarter
                local groups no_ba ba_plus
                local dummies g_ba
            }

            foreach spec in pooled shift interp {
                local z = cond("`spec'" == "interp", "z_interp", "z_step")
                local rhs c.`z'
                foreach d of local dummies {
                    local rhs `rhs' 1.`d'#c.`z'
                }
                if "`spec'" == "shift" {
                    local rhs `rhs' 1.post#c.`z'
                    foreach d of local dummies {
                        local rhs `rhs' 1.`d'#1.post#c.`z'
                    }
                }
                quietly reghdfe `y' `rhs' [aw=fe_weight], absorb(`absorb') vce(cluster occ2010)
                quietly summarize `y' [aw=fe_weight] if e(sample), meanonly
                local depmean = r(mean)

                foreach g of local groups {
                    * The group's interaction term, if any.
                    local d ""
                    if "`g'" == "u30"     local d g_u30
                    if "`g'" == "50_64"   local d g_older
                    if "`g'" == "ba_plus" local d g_ba
                    local base   c.`z'
                    local shiftt 1.post#c.`z'
                    if "`d'" != "" {
                        local base   `base' + 1.`d'#c.`z'
                        local shiftt `shiftt' + 1.`d'#1.post#c.`z'
                    }
                    if "`spec'" != "shift" {
                        local cname = cond("`spec'" == "pooled", "step", "interp")
                        post_lincom, handle(`H') expression(`base') depmean(`depmean') ///
                            keys(("`W'") ("`panel'") ("`g'") ("`spec'") ("`cname'") ("`y'"))
                    }
                    else {
                        post_lincom, handle(`H') expression(`base') depmean(`depmean') ///
                            keys(("`W'") ("`panel'") ("`g'") ("`spec'") ("before") ("`y'"))
                        post_lincom, handle(`H') expression(`shiftt') depmean(`depmean') ///
                            keys(("`W'") ("`panel'") ("`g'") ("`spec'") ("shift") ("`y'"))
                        post_lincom, handle(`H') expression(`base' + `shiftt') depmean(`depmean') ///
                            keys(("`W'") ("`panel'") ("`g'") ("`spec'") ("from") ("`y'"))
                    }
                }
            }
        }
    }
}
postclose `H'
use "`results'", clear
export delimited using "$EST/fe_main.csv", replace
di as result "`c(N)' coefficients written to output/estimates/fe_main.csv"
