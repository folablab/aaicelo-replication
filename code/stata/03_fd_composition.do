/*------------------------------------------------------------------------------
03_fd_composition.do -- what changed within the part-time and within the full-time workforce.

Three-year first differences, as in 01_fd_main.do, of outcomes measured separately among the
part-time and among the full-time workers of each occupation: mean hours, log real hourly wage,
the under-30 share, the share with a bachelor's degree or more, and (part-time only) the share
working part time for economic reasons. The regressor, weights (full-occupation base-period
employment), controls, period effects, and clustering are those of the headline regression.
The log count rows of the table (log part-time and log full-time employment) are the
d_log_pt_emp and d_log_ft_emp rows of output/estimates/fd_main.csv.

Windows   headline      2026Q1 vs 2023Q1 and 2026Q2 vs 2023Q2
          placebo_pre   2021Q4 vs 2018Q4 through 2022Q3 vs 2019Q3

Input    data/cell_fd/fd_table56_status_outcomes_3m_occ2010.dta
Output   output/estimates/fd_composition.csv: status window outcome b se p N N_clust r2 depmean
Exhibit  Appendix Table C.4.
------------------------------------------------------------------------------*/
do code/stata/00_setup.do

tempname H
tempfile results
postfile `H' str2 status str12 window str20 outcome double(b se p N N_clust r2 depmean) using "`results'", replace

foreach status in pt ft {
    local outcomes d_hours_main d_log_hrearn_real d_share_under30 d_share_baplus
    if "`status'" == "pt" local outcomes `outcomes' d_share_pt_econ
    foreach w in headline placebo_pre {
        if "`w'" == "headline" {
            local start = yq(2026,1)
            local end   = yq(2026,2)
        }
        else {
            local start = yq(2021,4)
            local end   = yq(2022,3)
        }
        use "$DATA/cell_fd/fd_table56_status_outcomes_3m_occ2010.dta", clear
        keep if status == "`status'" & horizon_years == 3 & inrange(later_period, `start', `end')
        keep if base_emp > 0 & !missing(base_emp)
        foreach y of local outcomes {
            local ctrl ""
            foreach cv of global FD_CONTROLS {
                quietly summarize `cv' if !missing(`y', z_d_s4_s1)
                if r(N) > 0 & r(min) < r(max) local ctrl "`ctrl' `cv'"
            }
            quietly regress `y' z_d_s4_s1 `ctrl' i.later_period [aw=base_emp], vce(cluster occ2010)
            quietly summarize `y' if e(sample) [aw=base_emp], meanonly
            post_result, handle(`H') x(z_d_s4_s1) depmean(`r(mean)') keys(("`status'") ("`w'") ("`y'"))
        }
    }
}
postclose `H'
use "`results'", clear
export delimited using "$EST/fd_composition.csv", replace
di as result "`c(N)' regressions written to output/estimates/fd_composition.csv"
