/*------------------------------------------------------------------------------
06_fe_specification.do -- specification checks on the occupation fixed-effects era split.

The shift specification of 05_fe_main.do over 2023Q1 to 2026Q2 (all workers, seven outcomes; by age
group, log employment) is re-estimated under each change below. The posted coefficient is the shift at
2025Q1 (for the age panel, the shift for workers under 30: base shift plus its under-30 interaction).
    baseline            the shift specification
    unweighted          no employment weights
    mgroup_xq           add major occupation group by quarter fixed effects
    industry2019_xq     add the occupation's 2019 shares in ten industries, each interacted with quarter indicators
    region2019_xq       add the occupation's 2019 shares in three regions, each interacted with quarter indicators
    drop_csmath         drop computer and mathematical occupations (major group 3)
    drop_cs_science     drop computer, mathematical, and life, physical, and social science occupations (3 and 5)
    trim_delta1         drop occupations in the top and bottom 1 percent of the stage 1 to 4 exposure change
    mincell30           keep occupation-quarters with at least 30 respondents
    one_to_one          keep harmonized occupations that map to exactly one 2018 census code
    eloundou_xq         add the standardized Eloundou et al. (2024) measure interacted with quarter indicators
    logo_1 to logo_22   leave one major occupation group out
Quarter interactions are explicit indicators for 2023Q2 to 2026Q2 (2023Q1 omitted).

Inputs   data/cell_fe/cell_fe_baseline_occ2010.dta, cell_fe_age3_occ2010.dta
         data/cell_fe/cell_fe_specification_inputs_occ2010.dta  (one row per occupation: major group,
         one-to-one indicator, 2019 industry and region shares, Eloundou et al. measure)
Output   output/estimates/fe_specification.csv: panel outcome spec omitted b se p N N_clust r2 depmean
Exhibit  Appendix Table F.3.
Runtime  about three minutes.
------------------------------------------------------------------------------*/
do code/stata/00_setup.do

local start = yq(2023,1)
local end   = yq(2026,2)

* Standardization of the step exposure, and the trimming thresholds, on the all-worker window.
use "$DATA/cell_fe/cell_fe_baseline_occ2010.dta", clear
keep if inrange(quarter, `start', `end') & fe_weight > 0 & !missing(fe_weight, exposure_step_raw, occ2010, quarter)
quietly summarize exposure_step_raw
local step_mean = r(mean)
local step_sd   = r(sd)
preserve
    collapse (mean) exposure_s1 exposure_s4, by(occ2010)
    gen double delta_s4_s1 = exposure_s4 - exposure_s1
    quietly _pctile delta_s4_s1, p(1 99)
    scalar cut_lo = r(r1)
    scalar cut_hi = r(r2)
    gen byte trim_keep = delta_s4_s1 > scalar(cut_lo) & delta_s4_s1 < scalar(cut_hi)
    keep occ2010 trim_keep
    tempfile trim
    save `trim'
restore
* Occupation-quarter respondent counts of the whole occupation, for the mincell30 check in the age panel.
keep occ2010 quarter n_person
rename n_person agg_n_person
tempfile counts
save `counts'

* Occupation characteristics; the Eloundou et al. measure standardized across the 450 occupations.
use "$DATA/cell_fe/cell_fe_specification_inputs_occ2010.dta", clear
quietly summarize eloundou_raw
gen double z_eloundou = (eloundou_raw - r(mean)) / r(sd)
keep occ2010 mgroup one2one z_eloundou share_ind*_2019 share_reg*_2019
merge 1:1 occ2010 using `trim', assert(match) nogenerate
tempfile inputs
save `inputs'

tempname H
tempfile results
postfile `H' str9 panel str20 outcome str16 spec omitted double(b se p N N_clust r2 depmean) using "`results'", replace

local checks baseline unweighted mgroup_xq industry2019_xq region2019_xq drop_csmath drop_cs_science ///
    trim_delta1 mincell30 one_to_one eloundou_xq
forvalues g = 1/22 {
    local checks `checks' logo_`g'
}

foreach panel in aggregate age3 {
    local file "$DATA/cell_fe/cell_fe_baseline_occ2010.dta"
    local outcomes $FE_PRIMARY log_pt_emp log_ft_emp
    if "`panel'" == "age3" {
        local file "$DATA/cell_fe/cell_fe_age3_occ2010.dta"
        local outcomes log_emp
    }
    foreach y of local outcomes {
        foreach chk of local checks {
            local omitted = 0
            if substr("`chk'", 1, 5) == "logo_" local omitted = real(substr("`chk'", 6, .))
            use "`file'", clear
            keep if inrange(quarter, `start', `end') & fe_weight > 0 & !missing(fe_weight, occ2010, quarter)
            if "`panel'" == "age3" keep if !missing(age3)
            merge m:1 occ2010 using `inputs', keep(master match) nogenerate
            merge m:1 occ2010 quarter using `counts', keep(master match) nogenerate
            gen double z_step = (exposure_step_raw - `step_mean') / `step_sd'
            gen byte post = quarter >= yq(2025,1)
            local rhs c.z_step 1.post#c.z_step
            local absorb occ2010 quarter
            local shift 1.post#c.z_step
            if "`panel'" == "age3" {
                gen byte g_u30   = age3 == 1
                gen byte g_older = age3 == 3
                local rhs c.z_step 1.g_u30#c.z_step 1.g_older#c.z_step 1.post#c.z_step 1.g_u30#1.post#c.z_step 1.g_older#1.post#c.z_step
                local absorb occ2010#age3 age3#quarter
                local shift 1.post#c.z_step + 1.g_u30#1.post#c.z_step
            }
            if "`chk'" == "drop_csmath"     keep if mgroup != 3
            if "`chk'" == "drop_cs_science" keep if !inlist(mgroup, 3, 5)
            if "`chk'" == "trim_delta1"     keep if trim_keep == 1
            if "`chk'" == "mincell30"       keep if agg_n_person >= 30 & !missing(agg_n_person)
            if "`chk'" == "one_to_one"      keep if one2one == 1
            if `omitted' > 0                keep if mgroup != `omitted'
            if "`chk'" == "mgroup_xq"       local absorb `absorb' mgroup#quarter
            local extra ""
            if "`chk'" == "industry2019_xq" {
                forvalues k = 1/10 {
                    forvalues q = `=`start'+1'/`end' {
                        gen double x_i`k'_q`q' = share_ind`k'_2019 * (quarter == `q')
                        local extra `extra' x_i`k'_q`q'
                    }
                }
            }
            if "`chk'" == "region2019_xq" {
                forvalues k = 1/3 {
                    forvalues q = `=`start'+1'/`end' {
                        gen double x_r`k'_q`q' = share_reg`k'_2019 * (quarter == `q')
                        local extra `extra' x_r`k'_q`q'
                    }
                }
            }
            if "`chk'" == "eloundou_xq" {
                forvalues q = `=`start'+1'/`end' {
                    gen double x_e_q`q' = z_eloundou * (quarter == `q')
                    local extra `extra' x_e_q`q'
                }
            }
            local weight [aw=fe_weight]
            if "`chk'" == "unweighted" local weight ""
            quietly reghdfe `y' `rhs' `extra' `weight', absorb(`absorb') vce(cluster occ2010)
            quietly summarize `y' [aw=fe_weight] if e(sample), meanonly
            local depmean = r(mean)
            quietly lincom `shift'
            post `H' ("`panel'") ("`y'") ("`chk'") (`omitted') (r(estimate)) (r(se)) (r(p)) (e(N)) (e(N_clust)) (e(r2)) (`depmean')
        }
    }
}
postclose `H'
use "`results'", clear
export delimited using "$EST/fe_specification.csv", replace
di as result "`c(N)' regressions written to output/estimates/fe_specification.csv"
