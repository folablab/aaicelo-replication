/*------------------------------------------------------------------------------
04_fd_telework.do -- remote-work controls in the headline three-year first difference.

The headline regression of 01_fd_main.do (2026Q1 vs 2023Q1 and 2026Q2 vs 2023Q2, stage 1 to 4
exposure change) with remote-work controls added, for all workers and for each age and
education group. The controls describe the whole occupation, also in the group regressions:
    base_telework_share         share of employed respondents teleworking in the base quarter (CPS)
    d_telework_share            its three-year change
    base_telework_hours_share   share of hours worked from home in the base quarter (CPS)
    d_telework_hours_share      its three-year change
    wfh_dingle_occ2010          Dingel and Neiman (2020) teleworkability
The four CPS measures are standardized with their mean and standard deviation over the
all-worker occupation-quarter cells of the headline window; teleworkability is standardized
within each estimation sample.

Specifications
    baseline       the headline regression
    baseline_cps   the headline regression on the cells with CPS telework measures
    cps_base       add the base-quarter telework share
    cps_change     add the change in the telework share
    cps_both       add both
    hours_both     add the base-quarter remote-hours share and its change
    baseline_dn    the headline regression on the cells with a teleworkability value
    dn_only        add teleworkability
    all_three      add the base-quarter telework share, its change, and teleworkability

Inputs   data/cell_fd/fd_baseline_3m_occ2010.dta and the five group files (_age_*, _edu_*)
Output   output/estimates/fd_telework.csv, one row per regression and coefficient:
         group spec outcome coef b se p N N_clust r2 depmean
         (coef is z_d_s4_s1 or one of z_tw_base z_tw_change z_tw_hours_base z_tw_hours_change z_dingel)
Exhibits Appendix Tables F.6 and F.7.
Runtime  about one minute.
------------------------------------------------------------------------------*/
do code/stata/00_setup.do

local tw_vars base_telework_share d_telework_share base_telework_hours_share d_telework_hours_share
local tw_z    z_tw_base z_tw_change z_tw_hours_base z_tw_hours_change

* Reference moments of the CPS telework measures: all-worker cells of the headline window.
use "$DATA/cell_fd/fd_baseline_3m_occ2010.dta", clear
keep if horizon_years == 3 & inlist(later_period, yq(2026,1), yq(2026,2))
forvalues k = 1/4 {
    local v : word `k' of `tw_vars'
    quietly summarize `v'
    local mean_`k' = r(mean)
    local sd_`k'   = r(sd)
}
keep occ2010 later_period `tw_vars'
tempfile fullocc
save `fullocc'

tempname H
tempfile results
postfile `H' str12 group str14 spec str20 outcome str20 coef double(b se p N N_clust r2 depmean) ///
    using "`results'", replace

foreach grp in all age_u30 age_30_49 age_50_64 edu_no_ba edu_ba_plus {
    local f "$DATA/cell_fd/fd_baseline_3m_occ2010"
    if "`grp'" != "all" local f "`f'_`grp'"
    use "`f'.dta", clear
    keep if horizon_years == 3 & inlist(later_period, yq(2026,1), yq(2026,2))
    if "`grp'" != "all" {
        * Replace the group's own telework measures with the whole occupation's.
        drop `tw_vars'
        merge 1:1 occ2010 later_period using `fullocc', keep(master match) assert(match using) nogenerate
    }
    forvalues k = 1/4 {
        local v : word `k' of `tw_vars'
        local z : word `k' of `tw_z'
        gen double `z' = (`v' - `mean_`k'') / `sd_`k''
    }
    foreach spec in baseline baseline_cps cps_base cps_change cps_both hours_both baseline_dn dn_only all_three {
        foreach y in $FD_PRIMARY $FD_SECONDARY {
            gen byte eligible = !missing(`y', z_d_s4_s1, base_emp) & base_emp > 0
            foreach cv of global FD_CONTROLS {
                quietly replace eligible = 0 if missing(`cv')
            }
            if inlist("`spec'", "baseline_cps", "cps_base", "cps_change", "cps_both", "all_three") ///
                quietly replace eligible = 0 if missing(base_telework_share, d_telework_share)
            if inlist("`spec'", "baseline_dn", "dn_only", "all_three") ///
                quietly replace eligible = 0 if missing(wfh_dingle_occ2010)
            if "`spec'" == "hours_both" ///
                quietly replace eligible = 0 if missing(base_telework_hours_share, d_telework_hours_share)
            local added ""
            if inlist("`spec'", "cps_base", "cps_both", "all_three")   local added `added' z_tw_base
            if inlist("`spec'", "cps_change", "cps_both", "all_three") local added `added' z_tw_change
            if "`spec'" == "hours_both"                                local added z_tw_hours_base z_tw_hours_change
            if inlist("`spec'", "dn_only", "all_three") {
                quietly summarize wfh_dingle_occ2010 if eligible
                gen double z_dingel = (wfh_dingle_occ2010 - r(mean)) / r(sd) if eligible
                local added `added' z_dingel
            }
            local ctrl ""
            foreach cv of global FD_CONTROLS {
                quietly summarize `cv' if eligible
                if r(N) > 0 & r(min) < r(max) local ctrl "`ctrl' `cv'"
            }
            quietly regress `y' z_d_s4_s1 `added' `ctrl' i.later_period if eligible [aw=base_emp], vce(cluster occ2010)
            quietly summarize `y' if e(sample) [aw=base_emp], meanonly
            local depmean = r(mean)
            foreach c in z_d_s4_s1 `added' {
                post_result, handle(`H') x(`c') depmean(`depmean') keys(("`grp'") ("`spec'") ("`y'") ("`c'"))
            }
            drop eligible
            capture drop z_dingel
        }
    }
}
postclose `H'
use "`results'", clear
export delimited using "$EST/fd_telework.csv", replace
di as result "`c(N)' coefficients written to output/estimates/fd_telework.csv"
