/****************************************************************************************
Project: Advancing AI Capabilities and Evolving Labor Outcomes
Repository: aaicelo
File: fe_run_occ2010.do
Purpose: Production person-level fixed-effects regressions for OCC2010 occupation assignment.

Specification target: September 30 final draft.

CORE DESIGN
- Clean data may extend through July 2026; all regressions end in June 2026.
- Table 5.5 windows:
      W2023 = January 2023 to June 2026 (main era window)
      W2021 = October 2021 to June 2026 (longer comparison window)
- Era split: January 2025.
- Main person-level regressions: occupation FE + month FE + region effects + individual controls.
- Heterogeneity regressions: occupation FE + group x month FE + region effects + individual controls.
- Standard errors clustered by occupation.
- CPS final person weights, except earnings outcomes use EARNWT.
- Step switches in March 2023, January 2025, and January 2026 in the clean file.
- Step and interpolated-step treatments are standardized within the relevant estimation window
  over UNIQUE OCCUPATION x MONTH cells, so occupation size does not determine the normalization.
- IMPORTANT: standard deviations are computed with summarize WITHOUT meanonly. Stata's
  summarize, meanonly does not provide the SD needed here.

OUTCOMES
Primary:
    Demp
    ahrswork1
    log_hrearn_tc_real
    parttime_usual
Secondary:
    D_other_job_HW
    ahrsworkt
    ahrswork2
    log_earn_tc_real

HETEROGENEITY
- Age: 18-29, 30-49, 50-64.
- Education: less than BA, BA or more.
- Age x education: six cells.
- Each heterogeneity cut has its own toggle below.
****************************************************************************************/

version 17.0
clear all
set more off

/****************************************************************************************
0. USER TOGGLES
****************************************************************************************/

* October 3 refresh: re-estimate only second-job hours after moving it to the employed sample.
local RUN_W2023 1
local RUN_W2021 1

* Re-estimate the W2021 interpolated-step second-job-hours specification as well.
local RUN_W2021_LINEAR 1

* Re-estimate the W2023 heterogeneity specifications for second-job hours only.
local RUN_HET_W2023   1
local RUN_HET_AGE3    1
local RUN_HET_EDU2    1
local RUN_HET_AGEEDU6 1

* Primary outcomes: the usual part-time refresh has already been estimated.
local RUN_DEMP             0
local RUN_AHRSWORK1        0
local RUN_LOG_HREARN_REAL  0
local RUN_PARTTIME_USUAL   0

* Secondary outcomes: only second-job hours needs new estimates.
local RUN_OTHER_JOB        0
local RUN_AHRSWORKT        0
local RUN_AHRSWORK2        1
local RUN_LOG_EARN_REAL    0

/****************************************************************************************
1. DEPENDENCIES
****************************************************************************************/

cap which reghdfe
if _rc {
    ssc install reghdfe, replace
}

cap which estadd
if _rc {
    ssc install estout, replace
}

/****************************************************************************************
2. PATHS
****************************************************************************************/

* Tyler.
if "`c(username)'" == "tylerboes" {
    global project_path "/Users/tylerboes/Library/Mobile Documents/com~apple~CloudDocs/Documents/GitHub/aaicelo"
    global data_path "/Users/tylerboes/Library/CloudStorage/GoogleDrive-tboes2@nd.edu/Shared drives/AAICELO"
}

* Jacob.
if "`c(username)'" == "jdomins2" {
    * Add Jacob's project_path and data_path here.
}

if "${project_path}" == "" | "${data_path}" == "" {
    di as error "ERROR: project_path and data_path must be defined."
    exit 198
}

local data_file "${data_path}/individual_fe/cps_fe_analysis_jan2017_occ2010.dta"
local est_dir   "${project_path}/est/individual_fe/occ2010"
local log_dir   "${project_path}/log/individual_fe/run"

cap mkdir "${project_path}/est"
cap mkdir "${project_path}/est/individual_fe"
cap mkdir "`est_dir'"
cap mkdir "${project_path}/log"
cap mkdir "${project_path}/log/individual_fe"
cap mkdir "`log_dir'"

cap confirm file "`data_file'"
if _rc {
    di as error "ERROR: Could not find `data_file'."
    exit 601
}

cap log close _all
log using "`log_dir'/fe_run_occ2010.log", replace text

/****************************************************************************************
3. VARIABLES, OUTCOMES, CONTROLS, AND NAMING
****************************************************************************************/

local raw_step   ensemble3_step
local raw_linear ensemble3_linear

local outcomes ""
if `RUN_DEMP'            == 1 local outcomes "`outcomes' Demp"
if `RUN_AHRSWORK1'       == 1 local outcomes "`outcomes' ahrswork1"
if `RUN_LOG_HREARN_REAL' == 1 local outcomes "`outcomes' log_hrearn_tc_real"
if `RUN_PARTTIME_USUAL'  == 1 local outcomes "`outcomes' parttime_usual"
if `RUN_OTHER_JOB'       == 1 local outcomes "`outcomes' D_other_job_HW"
if `RUN_AHRSWORKT'       == 1 local outcomes "`outcomes' ahrsworkt"
if `RUN_AHRSWORK2'       == 1 local outcomes "`outcomes' ahrswork2"
if `RUN_LOG_EARN_REAL'   == 1 local outcomes "`outcomes' log_earn_tc_real"

if "`outcomes'" == "" {
    di as error "ERROR: No outcomes selected."
    exit 198
}

local earnings_outcomes log_hrearn_tc_real log_earn_tc_real

local eststem_Demp               "Demp"
local eststem_ahrswork1          "ahrswork1"
local eststem_log_hrearn_tc_real "ln_hrearn_tc_real"
local eststem_parttime_usual     "parttime_usual"
local eststem_D_other_job_HW     "D_other_job_HW"
local eststem_ahrsworkt          "ahrsworkt"
local eststem_ahrswork2          "ahrswork2"
local eststem_log_earn_tc_real   "ln_earn_tc_real"

* Detailed education categories:
*   hs_less      = high school or less
*   SC_AD        = some college / associate
*   omitted      = bachelor's
*   masters_plus = post-BA
*
* Race controls match the final replication appendix:
*   omitted white; Black; Asian; Native/mixed/other.
local controls_base ///
    c.age ///
    c.age2 ///
    Dfem ///
    race_black ///
    race_asian ///
    race_other_combined ///
    hs_less ///
    SC_AD ///
    masters_plus ///
    i.region

* For broad education-group FE, one detailed category within each broad group must be omitted:
*   within <BA: hs_less omitted, SC_AD included
*   within BA+: BA omitted, masters_plus included
local controls_eduhet ///
    c.age ///
    c.age2 ///
    Dfem ///
    race_black ///
    race_asian ///
    race_other_combined ///
    SC_AD ///
    masters_plus ///
    i.region

local weight_var          wtfinl
local earnings_weight_var earnwt
local cluster_var         occ2010
local sample_end          ym(2026, 6)

/****************************************************************************************
4. REQUIRED-VARIABLE CHECK
****************************************************************************************/

use "`data_file'", clear

foreach v in `raw_step' `raw_linear' `outcomes' ///
             `weight_var' `earnings_weight_var' `cluster_var' time ///
             age age2 educ Dfem race_black race_asian race_other_combined ///
             hs_less SC_AD masters_plus region ///
             age_18_29 age30to50 age50plus {
    cap confirm variable `v'
    if _rc {
        di as error "ERROR: Required variable not found: `v'"
        exit 111
    }
}

quietly summarize time
local data_min = r(min)
local data_max = r(max)
local data_min_label : display %tmMon_CCYY `data_min'
local data_max_label : display %tmMon_CCYY `data_max'

di as text "============================================================"
di as text "OCC2010 source file loaded."
di as text "Observed clean-file support: `data_min_label' to `data_max_label'"
di as text "Selected outcomes: `outcomes'"
di as text "RUN_W2021_LINEAR: " as result `RUN_W2021_LINEAR'
di as text "============================================================"

/****************************************************************************************
5. TABLE 5.5 REGRESSIONS, BY WINDOW
****************************************************************************************/

local windows ""
if `RUN_W2023' == 1 local windows "`windows' W2023"
if `RUN_W2021' == 1 local windows "`windows' W2021"

foreach window of local windows {

    if "`window'" == "W2023" {
        local sample_start ym(2023, 1)
        local window_label "January 2023 to June 2026"
    }
    else if "`window'" == "W2021" {
        local sample_start ym(2021, 10)
        local window_label "October 2021 to June 2026"
    }

    /************************************************************************************
    5.1 Treatment normalization for this window
    ************************************************************************************/

    use "`data_file'", clear
    keep if inrange(time, `sample_start', `sample_end')
    drop if time == ym(2025, 10)

    preserve
        keep `cluster_var' time `raw_step' `raw_linear'
        drop if missing(`cluster_var') | missing(time)
        bysort `cluster_var' time: keep if _n == 1

        quietly count if !missing(`raw_step')
        local n_step_cells = r(N)
        quietly summarize `raw_step' if !missing(`raw_step')
        local step_mean = r(mean)
        local step_sd   = r(sd)

        quietly count if !missing(`raw_linear')
        local n_linear_cells = r(N)
        quietly summarize `raw_linear' if !missing(`raw_linear')
        local linear_mean = r(mean)
        local linear_sd   = r(sd)
    restore

    if `n_step_cells' < 2 | missing(`step_sd') | `step_sd' <= 0 {
        di as error "ERROR: Invalid step normalization in `window'."
        di as error "Nonmissing unique occupation-month cells = `n_step_cells'; SD = `step_sd'"
        exit 459
    }

    if `n_linear_cells' < 2 | missing(`linear_sd') | `linear_sd' <= 0 {
        di as error "ERROR: Invalid interpolated-step normalization in `window'."
        di as error "Nonmissing unique occupation-month cells = `n_linear_cells'; SD = `linear_sd'"
        exit 459
    }

    di as text "------------------------------------------------------------"
    di as text "OCC2010: `window' (`window_label')"
    di as text "Unique occupation-month cells with step:   " as result %12.0fc `n_step_cells'
    di as text "Step mean / SD:                            " as result %9.4f `step_mean' " / " %9.4f `step_sd'
    di as text "Unique occupation-month cells with linear: " as result %12.0fc `n_linear_cells'
    di as text "Linear mean / SD:                          " as result %9.4f `linear_mean' " / " %9.4f `linear_sd'
    di as text "------------------------------------------------------------"

    /************************************************************************************
    5.2 One set of regressions per selected outcome
    ************************************************************************************/

    foreach y of local outcomes {

        local ystem "`eststem_`y''"

        local this_weight `weight_var'
        if strpos(" `earnings_outcomes' ", " `y' ") {
            local this_weight `earnings_weight_var'
        }

        use "`data_file'", clear
        * CONDITIONAL second-job hours: restrict to workers holding a second job.
        * The clean panel assigns zero hours to one-job workers; those zeros must
        * not enter this regression or its saved e(depvar_mean).
        if "`y'" == "ahrswork2" {
            replace ahrswork2 = . if multjob != 2 | missing(multjob)
            assert multjob == 2 if !missing(ahrswork2)
        }
        keep if inrange(time, `sample_start', `sample_end')
        drop if time == ym(2025, 10)

        gen double z_step   = (`raw_step'   - `step_mean')   / `step_sd'
        gen double z_linear = (`raw_linear' - `linear_mean') / `linear_sd'

        gen byte post2025 = time >= ym(2025, 1) if !missing(time)
        label var post2025 "January 2025 and later"

        di as text "Running `window': outcome=`y'"

        * -------------------------------------------------------------------------------
        * Pooled standardized inflection-dated step: equation (5)
        * -------------------------------------------------------------------------------
        quietly reghdfe `y' ///
            c.z_step ///
            `controls_base' [pw = `this_weight'], ///
            absorb(`cluster_var' time) ///
            vce(cluster `cluster_var')

        quietly summarize `y' [aw = `this_weight'] if e(sample)
        estadd scalar depvar_mean = r(mean), replace
        estadd scalar exposure_mean_raw = `step_mean', replace
        estadd scalar exposure_sd_raw   = `step_sd', replace
        estadd local window "`window'", replace
        estadd local spec "baseline", replace
        estadd local exposure_measure "step", replace
        estadd local occupation_system "occ2010", replace
        estadd local exposure_units "one SD within estimation window", replace
        estadd local parttime_definition "usual part-time (WKSTAT)", replace

        estimates save "`est_dir'/fe_`window'_baseline_`ystem'.ster", replace

        * -------------------------------------------------------------------------------
        * Era split at January 2025
        * β before 2025m1 = z_step coefficient
        * shift at 2025m1 = interaction coefficient
        * β from 2025m1   = sum of the two
        * -------------------------------------------------------------------------------
        quietly reghdfe `y' ///
            c.z_step ///
            1.post2025#c.z_step ///
            `controls_base' [pw = `this_weight'], ///
            absorb(`cluster_var' time) ///
            vce(cluster `cluster_var')

        quietly summarize `y' [aw = `this_weight'] if e(sample)
        estadd scalar depvar_mean = r(mean), replace
        estadd scalar exposure_mean_raw = `step_mean', replace
        estadd scalar exposure_sd_raw   = `step_sd', replace
        estadd local window "`window'", replace
        estadd local spec "post", replace
        estadd local exposure_measure "step", replace
        estadd local post_interaction "January 2025+", replace
        estadd local occupation_system "occ2010", replace
        estadd local exposure_units "one SD within estimation window", replace
        estadd local parttime_definition "usual part-time (WKSTAT)", replace

        estimates save "`est_dir'/fe_`window'_post_`ystem'.ster", replace

        * -------------------------------------------------------------------------------
        * Interpolated step is a Table 5.5 check on the main W2023 window.
        * -------------------------------------------------------------------------------
        if "`window'" == "W2023" {
            quietly reghdfe `y' ///
                c.z_linear ///
                `controls_base' [pw = `this_weight'], ///
                absorb(`cluster_var' time) ///
                vce(cluster `cluster_var')

            quietly summarize `y' [aw = `this_weight'] if e(sample)
            estadd scalar depvar_mean = r(mean), replace
            estadd scalar exposure_mean_raw = `linear_mean', replace
            estadd scalar exposure_sd_raw   = `linear_sd', replace
            estadd local window "`window'", replace
            estadd local spec "baseline", replace
            estadd local exposure_measure "linear", replace
            estadd local occupation_system "occ2010", replace
            estadd local exposure_units "one SD within estimation window", replace
            estadd local parttime_definition "usual part-time (WKSTAT)", replace

            estimates save "`est_dir'/fe_`window'_baseline_`ystem'_linear.ster", replace
        }
    }
}

/************************************************************************************
5.3 W2021 INTERPOLATED STEP ONLY

This block is independently toggled so the current update can add only the missing W2021
interpolated-step estimates. Existing step, era-split, and heterogeneity .ster files are not
re-estimated when RUN_W2023 = RUN_W2021 = RUN_HET_W2023 = 0.
************************************************************************************/

if `RUN_W2021_LINEAR' == 1 {

    local sample_start ym(2021, 10)

    use "`data_file'", clear
    keep if inrange(time, `sample_start', `sample_end')
    drop if time == ym(2025, 10)

    preserve
        keep `cluster_var' time `raw_linear'
        drop if missing(`cluster_var') | missing(time)
        bysort `cluster_var' time: keep if _n == 1

        quietly count if !missing(`raw_linear')
        local n_linear_cells = r(N)

        quietly summarize `raw_linear' if !missing(`raw_linear')
        local linear_mean = r(mean)
        local linear_sd   = r(sd)
    restore

    if `n_linear_cells' < 2 | missing(`linear_sd') | `linear_sd' <= 0 {
        di as error "ERROR: Invalid W2021 interpolated-step normalization."
        di as error "Nonmissing unique occupation-month cells = `n_linear_cells'; SD = `linear_sd'"
        exit 459
    }

    di as text "------------------------------------------------------------"
    di as text "OCC2010: W2021 interpolated-step-only update"
    di as text "Unique occupation-month cells with linear: " as result %12.0fc `n_linear_cells'
    di as text "Linear mean / SD:                          " as result %9.4f `linear_mean' " / " %9.4f `linear_sd'
    di as text "------------------------------------------------------------"

    foreach y of local outcomes {

        local ystem "`eststem_`y''"

        local this_weight `weight_var'
        if strpos(" `earnings_outcomes' ", " `y' ") {
            local this_weight `earnings_weight_var'
        }

        use "`data_file'", clear
        * CONDITIONAL second-job hours: restrict to workers holding a second job.
        * The clean panel assigns zero hours to one-job workers; those zeros must
        * not enter this regression or its saved e(depvar_mean).
        if "`y'" == "ahrswork2" {
            replace ahrswork2 = . if multjob != 2 | missing(multjob)
            assert multjob == 2 if !missing(ahrswork2)
        }
        keep if inrange(time, `sample_start', `sample_end')
        drop if time == ym(2025, 10)

        gen double z_linear = (`raw_linear' - `linear_mean') / `linear_sd'

        di as text "Running W2021 interpolated step only: outcome=`y'"

        quietly reghdfe `y' ///
            c.z_linear ///
            `controls_base' [pw = `this_weight'], ///
            absorb(`cluster_var' time) ///
            vce(cluster `cluster_var')

        quietly summarize `y' [aw = `this_weight'] if e(sample)
        estadd scalar depvar_mean = r(mean), replace
        estadd scalar exposure_mean_raw = `linear_mean', replace
        estadd scalar exposure_sd_raw   = `linear_sd', replace
        estadd local window "W2021", replace
        estadd local spec "baseline", replace
        estadd local exposure_measure "linear", replace
        estadd local occupation_system "occ2010", replace
        estadd local exposure_units "one SD within estimation window", replace
        estadd local parttime_definition "usual part-time (WKSTAT)", replace

        estimates save "`est_dir'/fe_W2021_baseline_`ystem'_linear.ster", replace
    }
}

/****************************************************************************************
6. TABLE 6.3 HETEROGENEITY, W2023
****************************************************************************************/

if `RUN_HET_W2023' == 1 {

    di as text "============================================================"
    di as text "Heterogeneity toggles"
    di as text "Age 3-group:       " as result `RUN_HET_AGE3'
    di as text "Education 2-group: " as result `RUN_HET_EDU2'
    di as text "Age x education:   " as result `RUN_HET_AGEEDU6'
    di as text "============================================================"

    local sample_start ym(2023, 1)

    /************************************************************************************
    6.1 Use exactly the W2023 step normalization for every heterogeneity regression
    ************************************************************************************/

    use "`data_file'", clear
    keep if inrange(time, `sample_start', `sample_end')
    drop if time == ym(2025, 10)

    preserve
        keep `cluster_var' time `raw_step'
        drop if missing(`cluster_var') | missing(time)
        bysort `cluster_var' time: keep if _n == 1

        quietly count if !missing(`raw_step')
        local n_step_cells = r(N)
        quietly summarize `raw_step' if !missing(`raw_step')
        local step_mean = r(mean)
        local step_sd   = r(sd)
    restore

    if `n_step_cells' < 2 | missing(`step_sd') | `step_sd' <= 0 {
        di as error "ERROR: Invalid W2023 step normalization for heterogeneity."
        di as error "Nonmissing unique occupation-month cells = `n_step_cells'; SD = `step_sd'"
        exit 459
    }

    /************************************************************************************
    6.2 Estimate selected heterogeneity cuts outcome by outcome
    ************************************************************************************/

    foreach y of local outcomes {

        local ystem "`eststem_`y''"

        local this_weight `weight_var'
        if strpos(" `earnings_outcomes' ", " `y' ") {
            local this_weight `earnings_weight_var'
        }

        use "`data_file'", clear
        * CONDITIONAL second-job hours: restrict to workers holding a second job.
        * The clean panel assigns zero hours to one-job workers; those zeros must
        * not enter this regression or its saved e(depvar_mean).
        if "`y'" == "ahrswork2" {
            replace ahrswork2 = . if multjob != 2 | missing(multjob)
            assert multjob == 2 if !missing(ahrswork2)
        }
        keep if inrange(time, `sample_start', `sample_end')
        drop if time == ym(2025, 10)

        gen double z_step = (`raw_step' - `step_mean') / `step_sd'
        gen byte post2025 = time >= ym(2025, 1) if !missing(time)

        * -------------------------------------------------------------------------------
        * Explicit group definitions
        * -------------------------------------------------------------------------------

        * Age groups.
        gen byte age3_group = .
        replace age3_group = 1 if age_18_29 == 1
        replace age3_group = 2 if age30to50 == 1
        replace age3_group = 3 if age50plus == 1

        * Explicit 0/1 slope dummies, with 30-49 as the reference slope.
        gen byte age_u30   = age3_group == 1 if !missing(age3_group)
        gen byte age_older = age3_group == 3 if !missing(age3_group)

        * Education groups.
        gen byte edu2_group = .
        replace edu2_group = 1 if educ < 111 & educ < .
        replace edu2_group = 2 if educ >= 111 & educ < .

        * Explicit 0/1 slope dummy, with <BA as the reference slope.
        gen byte edu_bap = edu2_group == 2 if !missing(edu2_group)

        * Six age x education cells.
        gen byte ageedu6 = .
        replace ageedu6 = 1 if age3_group == 1 & edu2_group == 1
        replace ageedu6 = 2 if age3_group == 1 & edu2_group == 2
        replace ageedu6 = 3 if age3_group == 2 & edu2_group == 1
        replace ageedu6 = 4 if age3_group == 2 & edu2_group == 2
        replace ageedu6 = 5 if age3_group == 3 & edu2_group == 1
        replace ageedu6 = 6 if age3_group == 3 & edu2_group == 2

        * Reference slope cell is 30-49, <BA (cell 3).
        gen byte ae_u30_ltba   = ageedu6 == 1 if !missing(ageedu6)
        gen byte ae_u30_bap    = ageedu6 == 2 if !missing(ageedu6)
        gen byte ae_prime_bap  = ageedu6 == 4 if !missing(ageedu6)
        gen byte ae_older_ltba = ageedu6 == 5 if !missing(ageedu6)
        gen byte ae_older_bap  = ageedu6 == 6 if !missing(ageedu6)

        * -------------------------------------------------------------------------------
        * AGE: 18-29 / 30-49 / 50-64
        * -------------------------------------------------------------------------------
        if `RUN_HET_AGE3' == 1 {

            quietly reghdfe `y' ///
                c.z_step ///
                1.age_u30#c.z_step ///
                1.age_older#c.z_step ///
                `controls_base' ///
                if !missing(age3_group) [pw = `this_weight'], ///
                absorb(`cluster_var' age3_group#time) ///
                vce(cluster `cluster_var')

            quietly summarize `y' [aw = `this_weight'] if e(sample)
            estadd scalar depvar_mean = r(mean), replace
            estadd scalar exposure_sd_raw = `step_sd', replace
            estadd local window "W2023", replace
            estadd local spec "age3", replace
            estadd local baseline_group "Age 30 to 49", replace
            estadd local group_time_fe "age group x month", replace
            estadd local occupation_system "occ2010", replace

            estimates save "`est_dir'/fe_W2023_age3_`ystem'.ster", replace

            quietly reghdfe `y' ///
                c.z_step ///
                1.age_u30#c.z_step ///
                1.age_older#c.z_step ///
                1.post2025#c.z_step ///
                1.age_u30#1.post2025#c.z_step ///
                1.age_older#1.post2025#c.z_step ///
                `controls_base' ///
                if !missing(age3_group) [pw = `this_weight'], ///
                absorb(`cluster_var' age3_group#time) ///
                vce(cluster `cluster_var')

            quietly summarize `y' [aw = `this_weight'] if e(sample)
            estadd scalar depvar_mean = r(mean), replace
            estadd scalar exposure_sd_raw = `step_sd', replace
            estadd local window "W2023", replace
            estadd local spec "post_age3", replace
            estadd local baseline_group "Age 30 to 49", replace
            estadd local post_interaction "January 2025+", replace
            estadd local group_time_fe "age group x month", replace
            estadd local occupation_system "occ2010", replace

            estimates save "`est_dir'/fe_W2023_post_age3_`ystem'.ster", replace
        }

        * -------------------------------------------------------------------------------
        * EDUCATION: <BA / BA+
        * -------------------------------------------------------------------------------
        if `RUN_HET_EDU2' == 1 {

            quietly reghdfe `y' ///
                c.z_step ///
                1.edu_bap#c.z_step ///
                `controls_eduhet' ///
                if !missing(edu2_group) [pw = `this_weight'], ///
                absorb(`cluster_var' edu2_group#time) ///
                vce(cluster `cluster_var')

            quietly summarize `y' [aw = `this_weight'] if e(sample)
            estadd scalar depvar_mean = r(mean), replace
            estadd scalar exposure_sd_raw = `step_sd', replace
            estadd local window "W2023", replace
            estadd local spec "edu2", replace
            estadd local baseline_group "Less than BA", replace
            estadd local group_time_fe "education group x month", replace
            estadd local occupation_system "occ2010", replace

            estimates save "`est_dir'/fe_W2023_edu2_`ystem'.ster", replace

            quietly reghdfe `y' ///
                c.z_step ///
                1.edu_bap#c.z_step ///
                1.post2025#c.z_step ///
                1.edu_bap#1.post2025#c.z_step ///
                `controls_eduhet' ///
                if !missing(edu2_group) [pw = `this_weight'], ///
                absorb(`cluster_var' edu2_group#time) ///
                vce(cluster `cluster_var')

            quietly summarize `y' [aw = `this_weight'] if e(sample)
            estadd scalar depvar_mean = r(mean), replace
            estadd scalar exposure_sd_raw = `step_sd', replace
            estadd local window "W2023", replace
            estadd local spec "post_edu2", replace
            estadd local baseline_group "Less than BA", replace
            estadd local post_interaction "January 2025+", replace
            estadd local group_time_fe "education group x month", replace
            estadd local occupation_system "occ2010", replace

            estimates save "`est_dir'/fe_W2023_post_edu2_`ystem'.ster", replace
        }

        * -------------------------------------------------------------------------------
        * AGE x EDUCATION: six cells
        * -------------------------------------------------------------------------------
        if `RUN_HET_AGEEDU6' == 1 {

            quietly reghdfe `y' ///
                c.z_step ///
                1.ae_u30_ltba#c.z_step ///
                1.ae_u30_bap#c.z_step ///
                1.ae_prime_bap#c.z_step ///
                1.ae_older_ltba#c.z_step ///
                1.ae_older_bap#c.z_step ///
                `controls_eduhet' ///
                if !missing(ageedu6) [pw = `this_weight'], ///
                absorb(`cluster_var' ageedu6#time) ///
                vce(cluster `cluster_var')

            quietly summarize `y' [aw = `this_weight'] if e(sample)
            estadd scalar depvar_mean = r(mean), replace
            estadd scalar exposure_sd_raw = `step_sd', replace
            estadd local window "W2023", replace
            estadd local spec "ageedu6", replace
            estadd local baseline_group "Age 30 to 49, less than BA", replace
            estadd local group_time_fe "age x education cell x month", replace
            estadd local occupation_system "occ2010", replace

            estimates save "`est_dir'/fe_W2023_ageedu6_`ystem'.ster", replace

            quietly reghdfe `y' ///
                c.z_step ///
                1.ae_u30_ltba#c.z_step ///
                1.ae_u30_bap#c.z_step ///
                1.ae_prime_bap#c.z_step ///
                1.ae_older_ltba#c.z_step ///
                1.ae_older_bap#c.z_step ///
                1.post2025#c.z_step ///
                1.ae_u30_ltba#1.post2025#c.z_step ///
                1.ae_u30_bap#1.post2025#c.z_step ///
                1.ae_prime_bap#1.post2025#c.z_step ///
                1.ae_older_ltba#1.post2025#c.z_step ///
                1.ae_older_bap#1.post2025#c.z_step ///
                `controls_eduhet' ///
                if !missing(ageedu6) [pw = `this_weight'], ///
                absorb(`cluster_var' ageedu6#time) ///
                vce(cluster `cluster_var')

            quietly summarize `y' [aw = `this_weight'] if e(sample)
            estadd scalar depvar_mean = r(mean), replace
            estadd scalar exposure_sd_raw = `step_sd', replace
            estadd local window "W2023", replace
            estadd local spec "post_ageedu6", replace
            estadd local baseline_group "Age 30 to 49, less than BA", replace
            estadd local post_interaction "January 2025+", replace
            estadd local group_time_fe "age x education cell x month", replace
            estadd local occupation_system "occ2010", replace

            estimates save "`est_dir'/fe_W2023_post_ageedu6_`ystem'.ster", replace
        }
    }
}

di as result "All selected OCC2010 production FE regressions completed successfully."
log close
