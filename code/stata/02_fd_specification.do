/*------------------------------------------------------------------------------
02_fd_specification.do -- specification checks on the headline three-year first difference.

The headline regression of 01_fd_main.do (2026Q1 vs 2023Q1 and 2026Q2 vs 2023Q2, stage 1 to 4
exposure change) is re-estimated under each of the following changes, for all workers (seven
outcomes) and for workers under 30 (log employment):
    baseline            the headline specification
    unweighted          no employment weights
    mgroup_x_quarter    major occupation group by period effects in place of period effects
    industry_ctrl       add eleven base-quarter industry shares
    industry_x_quarter  add ten industry shares interacted with period effects
    region_x_quarter    the three region shares interacted with period effects
    drop_csmath         drop computer and mathematical occupations (major group 3)
    drop_cs_science     drop computer, mathematical, and life, physical, and social science occupations (3 and 5)
    trim_dE_1pct        drop occupations in the top and bottom 1 percent of the exposure change
    mincell_30          keep occupations with at least 30 base-quarter respondents
    one_to_one          keep harmonized occupations that map to exactly one 2018 census code
    rival_eloundou      add the standardized Eloundou et al. (2024) exposure measure
    rival_felten        add the standardized Felten et al. (2023) language-modeling exposure measure
    alone_eloundou      the Eloundou et al. measure in place of the stage 1 to 4 change
    alone_felten        the Felten et al. measure in place of the stage 1 to 4 change
    logo_1 to logo_22   leave one major occupation group out
Major groups are the 22 groups of the 2010 census occupation classification, defined by code ranges.

Inputs   data/cell_fd/fd_baseline_3m_occ2010.dta, fd_baseline_3m_occ2010_age_u30.dta
         data/cell_fd/fd_robustness_inputs_occ2010.dta   (industry shares, respondent counts, rival measures,
                                                           one row per occupation and base quarter)
         data/crosswalks/occ_to_occ2010_2020_2026.dta     (2018 census codes to harmonized codes)
Output   output/estimates/fd_specification.csv, one row per regression:
         unit outcome spec omitted b se p N N_clust r2 depmean rival_b rival_se
         (rival_b and rival_se are the coefficient on the added measure in the rival_* rows)
Exhibits Appendix Tables F.1, F.2, F.4, F.5; Figure 8.
Runtime  about one minute.
------------------------------------------------------------------------------*/
do code/stata/00_setup.do

* Harmonized occupations that correspond to exactly one 2018 census code.
use occ2010 cps_code using "$DATA/crosswalks/occ_to_occ2010_2020_2026.dta", clear
drop if occ2010 == 9999
duplicates drop occ2010 cps_code, force
bysort occ2010: gen int n_2018 = _N
bysort occ2010: keep if _n == 1
gen byte one2one = n_2018 == 1
keep occ2010 one2one
tempfile mapping
save `mapping'

tempname H
tempfile results
postfile `H' str8 unit str20 outcome str20 spec omitted double(b se p N N_clust r2 depmean rival_b rival_se) ///
    using "`results'", replace

foreach unit in all age_u30 {
    local f "$DATA/cell_fd/fd_baseline_3m_occ2010"
    if "`unit'" == "age_u30" local f "`f'_age_u30"
    use "`f'.dta", clear
    keep if horizon_years == 3 & inlist(later_period, yq(2026,1), yq(2026,2))
    merge m:1 occ2010 base_period using "$DATA/cell_fd/fd_robustness_inputs_occ2010.dta", ///
        keep(master match) assert(match using) nogenerate
    merge m:1 occ2010 using `mapping', keep(master match) assert(match using) nogenerate

    * The 22 major occupation groups of the 2010 census classification.
    gen byte mgroup = .
    local lo 10   500 1000 1300 1600 2000 2100 2200 2600 3000 3600 3700 4000 4200 4300 4700 5000 6005 6200 7000 7700 9000
    local hi 430  950 1240 1560 1980 2060 2160 2550 2960 3540 3655 3955 4160 4250 4650 4965 5940 6130 6940 7630 8965 9750
    forvalues g = 1/22 {
        replace mgroup = `g' if inrange(occ2010, `: word `g' of `lo'', `: word `g' of `hi'')
    }
    assert !missing(mgroup)

    local outcomes $FD_PRIMARY d_log_pt_emp d_log_ft_emp
    if "`unit'" == "age_u30" local outcomes d_log_emp
    local checks baseline unweighted mgroup_x_quarter industry_ctrl industry_x_quarter region_x_quarter ///
        drop_csmath drop_cs_science trim_dE_1pct mincell_30 one_to_one rival_eloundou rival_felten ///
        alone_eloundou alone_felten
    forvalues g = 1/22 {
        local checks `checks' logo_`g'
    }

    foreach y of local outcomes {
        local x z_d_s4_s1
        gen byte eligible = !missing(`y', `x', base_emp) & base_emp > 0
        * Trimming: an occupation is kept if its exposure change lies strictly inside the 1st and 99th
        * percentiles of the exposure change across the eligible occupations (an occupation exactly at a
        * threshold is dropped). The occupation's score is its mean over its eligible cells (the change
        * does not vary across cells, so this is the score itself).
        egen byte occ_tag = tag(occ2010) if eligible
        bysort occ2010: egen double trim_score = mean(cond(eligible, `x', .))
        quietly _pctile trim_score if occ_tag == 1, p(1 99)
        scalar z1 = r(r1)
        scalar z99 = r(r2)
        gen byte trim_keep = trim_score > scalar(z1) & trim_score < scalar(z99)

        foreach chk of local checks {
            local omitted = 0
            if substr("`chk'", 1, 5) == "logo_" local omitted = real(substr("`chk'", 6, .))
            preserve
            keep if eligible
            if "`chk'" == "drop_csmath"     keep if mgroup != 3
            if "`chk'" == "drop_cs_science" keep if !inlist(mgroup, 3, 5)
            if "`chk'" == "trim_dE_1pct"    keep if trim_keep == 1
            if "`chk'" == "mincell_30"      keep if base_n_person >= 30 & !missing(base_n_person)
            if "`chk'" == "one_to_one"      keep if one2one == 1
            if `omitted' > 0                keep if mgroup != `omitted'

            local ctrl ""
            foreach cv of global FD_CONTROLS {
                quietly summarize `cv'
                if r(N) > 0 & r(min) < r(max) local ctrl "`ctrl' `cv'"
            }
            local extra ""
            local time i.later_period
            local rival ""
            local reg `x'
            if "`chk'" == "mgroup_x_quarter"   local time i.mgroup#i.later_period
            if "`chk'" == "industry_ctrl" {
                forvalues k = 1/11 {
                    local extra `extra' base_share_ind`k'
                }
            }
            if "`chk'" == "industry_x_quarter" {
                forvalues k = 1/10 {
                    local extra `extra' c.base_share_ind`k'#i.later_period
                }
            }
            if "`chk'" == "region_x_quarter"   local extra c.base_share_south#i.later_period c.base_share_midwest#i.later_period c.base_share_northeast#i.later_period
            if "`chk'" == "rival_eloundou"     local rival z_rival_eloundou
            if "`chk'" == "rival_felten"       local rival z_rival_felten
            if "`chk'" == "alone_eloundou"     local reg z_rival_eloundou
            if "`chk'" == "alone_felten"       local reg z_rival_felten
            local weight [aw=base_emp]
            if "`chk'" == "unweighted" local weight ""

            quietly regress `y' `reg' `rival' `ctrl' `extra' `time' `weight', vce(cluster occ2010)
            quietly summarize `y' if e(sample) [aw=base_emp], meanonly
            local depmean = r(mean)
            local rb = .
            local rse = .
            if "`rival'" != "" {
                local rb = _b[`rival']
                local rse = _se[`rival']
            }
            post_result, handle(`H') x(`reg') depmean(`depmean') ///
                keys(("`unit'") ("`y'") ("`chk'") (`omitted')) extra((`rb') (`rse'))
            restore
        }
        drop eligible occ_tag trim_score trim_keep
    }
}
postclose `H'
use "`results'", clear
export delimited using "$EST/fd_specification.csv", replace
di as result "`c(N)' regressions written to output/estimates/fd_specification.csv"
