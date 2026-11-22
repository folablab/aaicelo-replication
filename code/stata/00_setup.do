/*------------------------------------------------------------------------------
00_setup.do -- paths and shared programs for every Stata script in the package.

Every script starts with  `do code/stata/00_setup.do'  and expects Stata's working
directory to be the repository root (the folder that holds data/, code/, output/).
run_all.do sets that up; to run one script alone, `cd' to the repository root first.

Globals defined here
    $ROOT   repository root
    $DATA   data/            cleaned inputs (never written to)
    $EST    output/estimates/   every regression result, as CSV
------------------------------------------------------------------------------*/
version 17.0
clear all
set more off
set varabbrev off
set type double

global ROOT "`c(pwd)'"
capture confirm file "$ROOT/data/cell_fd/fd_baseline_3m_occ2010.dta"
if _rc {
    di as error "Run from the repository root (the folder that holds data/ and code/)."
    di as error "Current directory: $ROOT"
    exit 601
}
global DATA "$ROOT/data"
global EST  "$ROOT/output/estimates"
capture mkdir "$ROOT/output"
capture mkdir "$EST"

foreach pkg in reghdfe ftools {
    capture which `pkg'
    if _rc {
        di as error "`pkg' is required: ssc install `pkg'"
        exit 111
    }
}

* The twelve base-period workforce-composition controls of every first-difference regression.
global FD_CONTROLS base_share_female base_share_under30 base_share_age50plus ///
    base_share_white base_share_black base_share_asian base_share_hs_less ///
    base_share_ba base_share_postba base_share_south base_share_midwest base_share_northeast

* Outcomes of the first-difference files, in the order of the paper's tables.
global FD_PRIMARY   d_log_emp d_unemp_rate d_hours_main d_log_hrearn_real d_pt_share
global FD_SECONDARY d_log_pt_emp d_log_ft_emp d_second_job d_hours_total d_hours_second d_log_wkearn_real

* Outcomes of the fixed-effects panels.
global FE_PRIMARY   log_emp unemp_rate hours_main log_hrearn_real pt_share
global FE_SECONDARY log_pt_emp log_ft_emp second_job hours_total hours_second log_wkearn_real

/*------------------------------------------------------------------------------
post_result -- append one regression result to the open postfile `handle'.
Columns: the keys passed in, then b se p N N_clust r2 depmean for `x', then any extra values.
depmean is the weighted mean of the dependent variable over the estimation sample
(weights as in the regression), computed by the caller and passed in.
------------------------------------------------------------------------------*/
capture program drop post_result
program define post_result
    syntax, Handle(name) Keys(string asis) X(string) DEPmean(real) [Extra(string asis)]
    local b   = _b[`x']
    local se  = _se[`x']
    local df  = e(df_r)
    local p   = 2 * ttail(`df', abs(`b' / `se'))
    local nc  = e(N_clust)
    post `handle' `keys' (`b') (`se') (`p') (e(N)) (`nc') (e(r2)) (`depmean') `extra'
end
