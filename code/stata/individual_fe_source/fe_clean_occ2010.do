/****************************************************************************************
Project: Advancing AI Capabilities and Evolving Labor Outcomes
Repository: aaicelo
File: fe_clean_occ2010.do
Purpose: Clean the OCC2010 exposure extract for individual-level FE analysis

Inputs: AAICELO/cps_w_occ2010exp_june26.dta
        AAICELO/indices.dta
Outputs: AAICELO/individual_fe/cps_fe_analysis_jan2017_occ2010.dta
         AAICELO/individual_fe/cps_fe_analysis_oct2021_occ2010.dta

Notes:
- Cleaning only: no graphs, regressions, or tables. Compact diagnostics are written to the log.
- Main clean preserves January 2017 onward; a second clean is also saved for October 2021 onward.
- Ages 18 to 64.
- Exposure is assigned at the OCC2010 occupation level.
- Earnings variables are taken directly from the source data and only sample-cleaned here.
- This file is intentionally parallel to fe_clean.do. It does not merge to or force
  sample support to match the CPS-code clean.
- Retains original CPS telework fields, Dingel--Neiman WFH score, and eligible-person telework dummy.
- Regression-specific missingness is left to downstream estimation files.
****************************************************************************************/

clear all
set more off

/****************************************************************************************
0. Paths

Expected repository structure:
    aaicelo/
        code/individual_fe/clean/
        log/individual_fe/clean/

Expected Google Drive structure:
    Shared drives/AAICELO/
        cps_w_exp_june26.dta
        cps_w_occ2010exp_june26.dta
        indices.dta
        individual_fe/
****************************************************************************************/

************************************* Paths ************************************

* If Tyler
if "`c(username)'" == "tylerboes" {
    global project_path "/Users/tylerboes/Library/Mobile Documents/com~apple~CloudDocs/Documents/GitHub/aaicelo"
    global data_path "/Users/tylerboes/Library/CloudStorage/GoogleDrive-tboes2@nd.edu/Shared drives/AAICELO"
}

* If Jacob
if "`c(username)'" == "jdomins2" {
    * Add Jacob's project_path and data_path here.
}

* If Cassie
/*
if "`c(hostname)'" == "tpureka1-DL-24" {

}
*/

* If Yong
/*
if "`c(username)'" == "" {

}
*/

if "${project_path}" == "" | "${data_path}" == "" {
    di as error "ERROR: project_path and data_path must be defined."
    di as error "Fill in your setup block at the top of this file."
    exit 198
}

cap mkdir "${project_path}/log"
cap mkdir "${project_path}/log/individual_fe"
cap mkdir "${project_path}/log/individual_fe/clean"
cap mkdir "${data_path}/individual_fe"

cap confirm file "${data_path}/cps_w_occ2010exp_june26.dta"
if _rc {
    di as error "ERROR: Could not find ${data_path}/cps_w_occ2010exp_june26.dta"
    exit 601
}

cap confirm file "${data_path}/indices.dta"
if _rc {
    di as error "ERROR: Could not find ${data_path}/indices.dta"
    exit 601
}

cap log close _all
log using "${project_path}/log/individual_fe/clean/fe_clean_occ2010.log", replace text

di as text "Repository: ${project_path}"
di as text "AAICELO data root: ${data_path}"

/****************************************************************************************
1. Load data
****************************************************************************************/

use "${data_path}/cps_w_occ2010exp_june26.dta", clear

/****************************************************************************************
2. Keep variables needed for individual FE analysis
****************************************************************************************/

keep year serial month hwtfinl cpsid asecflag mish region statefip county metfips ///
     metarea metro pernum wtfinl cpsidv cpsidp ///
     age sex race marst popstat asian qage qmarst qsex vetstat qrace ///
     bpl yrimmig citizen nativity hispan empstat labforce ///
     cps_code occ2010 occ1990 ind1990 ind classwkr ///
     uhrsworkt uhrswork1 uhrswork2 ahrsworkt ahrswork1 ahrswork2 ///
     durunem2 durunemp whyunemp wkstat empsame ///
     qahrswork1 quhrsworkt quhrswork1 multjob numjob qempstat qahrsworkt ///
     qind qlabforc qocc actsame educ qeduc diffany ///
     earnwt qearnwee earnweek earnweek2 earnweek2_cpiu_2010 ///
     hourwage2 hourwage2_cpiu_2010 ///
     log_earn log_hrearn log_earn_tc log_hrearn_tc ///
     log_earn_real log_hrearn_real log_earn_tc_real log_hrearn_tc_real ///
     jtyears jtyearago jtsame jtype jtclass jtind jtocc jtsuppwt ///
     paidhour union uhrsworkorg wksworkorg eligorg otpay ///
     quhrsworkorg qhourwag covidtelew telwrkpay telwrkhr ///
     wfh_dingle_occ2010 ///
     ensemble3_s1_occ2010 ensemble3_s2_occ2010 ensemble3_s3_occ2010 ensemble3_s4_occ2010

/****************************************************************************************
3. Time variables and analysis sample
****************************************************************************************/

gen time = ym(year, month)
format time %tm
label var time "Year-month"

gen ntime = time - ym(2022, 12)
label var ntime "Months since 2022m12"

gen ntime_s2_start = time - ym(2022, 11)
label var ntime_s2_start "Months since 2022m11"

gen ntime_s3_start = time - ym(2024, 9)
label var ntime_s3_start "Months since 2024m9"

gen ntime_s4_start = time - ym(2025, 5)
label var ntime_s4_start "Months since 2025m5"

gen ntime_s2_infl = time - ym(2023, 3)
label var ntime_s2_infl "Months since 2023m3"

* Preserve the full OCC2010 source support through July 2026.
* July 2026 is retained in the clean even though production FE regressions end in June 2026.
keep if inrange(time, ym(2017, 1), ym(2026, 7))

* Main working-age sample.
keep if age >= 18 & age <= 64

/****************************************************************************************
4. Employment status outcomes
****************************************************************************************/

gen Demp = .
replace Demp = 1 if inlist(empstat, 10, 12)
replace Demp = 0 if empstat == 21
label var Demp "Employment dummy"

gen Dunemp = .
replace Dunemp = 1 if empstat == 21
replace Dunemp = 0 if inlist(empstat, 10, 12)
label var Dunemp "Unemployment dummy"

* Employed sample for status outcomes that do not require reported hours.
gen byte sample_employed_status = inlist(empstat, 10, 12)
label var sample_employed_status "Employed sample for status outcomes"

* CPS supplement: telework for pay in the previous week (not COVID-only telework).
* Codes 1=yes / 2=no; 0, 7, 8, 9 and missing are NOT recoded to zero.
* Keep this separate from the outcome-specific estimation sample.
gen byte telework_paid = .
replace telework_paid = 1 if sample_employed_status == 1 & telwrkpay == 1
replace telework_paid = 0 if sample_employed_status == 1 & telwrkpay == 2
label define telework_paid_lbl 0 "No paid telework" 1 "Paid telework", replace
label values telework_paid telework_paid_lbl
label var telework_paid "CPS paid telework in previous week (1/0; eligible employed)"

* Hours at home are retained separately; non-teleworkers have zero home hours.
* 99/999 and otherwise out-of-range entries remain missing.
gen double telework_hours = .
replace telework_hours = 0 if telework_paid == 0
replace telework_hours = telwrkhr if telework_paid == 1 & inrange(telwrkhr,0,98)
label var telework_hours "Hours worked at home for pay in previous week (eligible sample)"


* Global high-hours exclusion for employment outcomes.
gen byte sample_drop_hours98 = 0
foreach v in ahrswork1 ahrswork2 ahrsworkt {
    replace sample_drop_hours98 = 1 if Demp == 1 ///
        & `v' > 98 ///
        & `v' != 999 ///
        & !missing(`v')
}
label var sample_drop_hours98 "Drop: employed and reported actual hours > 98"

replace Demp   = . if sample_drop_hours98 == 1
replace Dunemp = . if sample_drop_hours98 == 1

* Common sample for non-employment outcomes.
gen byte sample_nonemp_outcomes = 1
replace sample_nonemp_outcomes = 0 if sample_drop_hours98 == 1
replace sample_nonemp_outcomes = 0 if Demp != 1
replace sample_nonemp_outcomes = 0 if missing(ahrsworkt)
replace sample_nonemp_outcomes = 0 if inlist(ahrsworkt, 99, 999)
replace sample_nonemp_outcomes = 0 if ahrsworkt > 98 & !missing(ahrsworkt)
label var sample_nonemp_outcomes "Sample for non-employment outcomes: employed with valid total hours < 99"

/****************************************************************************************
5. Hours and job-related outcomes
****************************************************************************************/

* Part-time outcomes: exact flips of the original full-time definitions.
* Use the employed status sample; unlike hours outcomes, do not require valid reported hours.
tempvar fulltime_usual_old fulltime_LW_old

gen byte `fulltime_usual_old' = .
replace `fulltime_usual_old' = 1 if inlist(wkstat, 11, 12, 13, 21)
replace `fulltime_usual_old' = 0 if inlist(wkstat, 14, 15, 22, 41, 42)
replace `fulltime_usual_old' = . if sample_employed_status == 0

gen byte parttime_usual = 1 - `fulltime_usual_old' if !missing(`fulltime_usual_old')
label var parttime_usual "Usually part-time: exact flip of original full-time outcome"
* Production FE tables use parttime_usual to match the current draft/outline.

gen byte `fulltime_LW_old' = .
replace `fulltime_LW_old' = 1 if inlist(wkstat, 11, 14, 15)
replace `fulltime_LW_old' = 0 if inlist(wkstat, 12, 13, 20, 21, 22, 41, 42)
replace `fulltime_LW_old' = . if sample_employed_status == 0

gen byte parttime_LW = 1 - `fulltime_LW_old' if !missing(`fulltime_LW_old')
label var parttime_LW "Part-time last week: exact flip of original full-time outcome"

* Mechanical verification of the flip.
assert parttime_LW == 1 - `fulltime_LW_old' if !missing(`fulltime_LW_old')

* Do not carry temporary full-time construction variables into the saved clean.
drop `fulltime_usual_old' `fulltime_LW_old'

gen D_other_job_SR = .
replace D_other_job_SR = 1 if multjob == 2
replace D_other_job_SR = 0 if multjob == 1
replace D_other_job_SR = . if sample_nonemp_outcomes == 0
label var D_other_job_SR "Second job, self-reported"

* Clean main-job and total actual-hours variables on the common hours sample.
foreach v in ahrswork1 ahrsworkt {
    replace `v' = . if inlist(`v', 99, 999)
    replace `v' = . if sample_nonemp_outcomes == 0
}
label var ahrswork1 "Actual hours worked, main job"
label var ahrsworkt "Actual hours worked, total"

* Second-job hours use the employed sample rather than the common hours sample.
* Employed workers with one job contribute zero; multiple-job workers contribute
* reported actual second-job hours when available.
replace ahrswork2 = . if inlist(ahrswork2, 99, 999)
replace ahrswork2 = . if ahrswork2 > 98 & !missing(ahrswork2)
replace ahrswork2 = 0 if sample_employed_status == 1 & multjob == 1
replace ahrswork2 = . if sample_employed_status == 0
label var ahrswork2 "Actual hours worked, second job; employed sample, zero if one job"

* Hours-based second-job outcome.
gen D_other_job_HW = .
replace D_other_job_HW = 0 if sample_nonemp_outcomes == 1
replace D_other_job_HW = 1 if sample_nonemp_outcomes == 1 & ///
    ((ahrswork2 > 0 & !missing(ahrswork2)) | ///
     (uhrswork2 > 0 & !missing(uhrswork2) & !inlist(uhrswork2, 99, 999)))
label var D_other_job_HW "Second job, hours-based"

* Other job-related outcomes.
gen D_sameacts = .
replace D_sameacts = 1 if actsame == 1
replace D_sameacts = 0 if actsame == 2
replace D_sameacts = . if sample_nonemp_outcomes == 0
label var D_sameacts "Same work activities as last month"

gen D_newacts = .
replace D_newacts = 0 if actsame == 1
replace D_newacts = 1 if actsame == 2
replace D_newacts = . if sample_nonemp_outcomes == 0
label var D_newacts "New work activities in the past month"

gen D_sameemp = .
replace D_sameemp = 1 if empsame == 1
replace D_sameemp = 0 if empsame == 2
replace D_sameemp = . if sample_nonemp_outcomes == 0
label var D_sameemp "Same employer as last month"

gen D_newemp = .
replace D_newemp = 1 if empsame == 2
replace D_newemp = 0 if empsame == 1
replace D_newemp = . if sample_nonemp_outcomes == 0
label var D_newemp "New employer in the past month"

gen D_newemp_old = .
replace D_newemp_old = 0 if empsame == 2
replace D_newemp_old = 1 if empsame == 1
replace D_newemp_old = . if sample_nonemp_outcomes == 0
label var D_newemp_old "Old-code employer variable, 1 if empsame == 1"

/****************************************************************************************
6. Earnings outcomes

Both AAICELO source files already contain the finalized earnings variables. This section
only applies the common FE outcome-sample and allocated-earnings restrictions. It does
not reconstruct or diagnose the earnings measures.
****************************************************************************************/

local earnings_outcomes ///
    log_earn log_hrearn log_earn_tc log_hrearn_tc ///
    log_earn_real log_hrearn_real log_earn_tc_real log_hrearn_tc_real

foreach v of local earnings_outcomes {
    cap confirm variable `v'
    if _rc {
        di as error "ERROR: Required earnings variable not found: `v'"
        exit 111
    }

    replace `v' = . if sample_nonemp_outcomes == 0
    replace `v' = . if qearnwee != 0 & !missing(qearnwee)
}

foreach v in log_hrearn log_hrearn_tc log_hrearn_real log_hrearn_tc_real {
    replace `v' = . if missing(ahrswork1) | ahrswork1 <= 0
}

label var log_earn           "Log nominal weekly earnings"
label var log_hrearn         "Log nominal hourly earnings"
label var log_earn_tc        "Log nominal weekly earnings, top-coded values multiplied by 1.5"
label var log_hrearn_tc      "Log nominal hourly earnings, top-coded values multiplied by 1.5"
label var log_earn_real      "Log real weekly earnings, January 2020 dollars"
label var log_hrearn_real    "Log real hourly earnings, January 2020 dollars"
label var log_earn_tc_real   "Log real weekly earnings, top-coded x 1.5, January 2020 dollars"
label var log_hrearn_tc_real "Log real hourly earnings, top-coded x 1.5, January 2020 dollars"

/****************************************************************************************
7. AI exposure measures: OCC2010 occupation assignment
****************************************************************************************/

gen ai_stage = 1
replace ai_stage = 2 if time >= ym(2023, 3)
replace ai_stage = 3 if time >= ym(2025, 1)
replace ai_stage = 4 if time >= ym(2026, 1)

label define ai_stage_lbl ///
    1 "Stage 1" ///
    2 "Stage 2 adoption inflection" ///
    3 "Stage 3 adoption inflection" ///
    4 "Stage 4 adoption inflection", replace
label values ai_stage ai_stage_lbl
label var ai_stage "AI capability stage based on adoption inflection timing"

gen double ensemble3_step = .
replace ensemble3_step = ensemble3_s1_occ2010 if ai_stage == 1
replace ensemble3_step = ensemble3_s2_occ2010 if ai_stage == 2
replace ensemble3_step = ensemble3_s3_occ2010 if ai_stage == 3
replace ensemble3_step = ensemble3_s4_occ2010 if ai_stage == 4
label var ensemble3_step "Ensemble exposure, OCC2010 occupation, step timing"

local s2_start = ym(2022, 11)
local s2_infl  = ym(2023, 3)
local s3_start = ym(2024, 9)
local s3_infl  = ym(2025, 1)
local s4_start = ym(2025, 5)
local s4_infl  = ym(2026, 1)

gen double ensemble3_linear = .
replace ensemble3_linear = ensemble3_s1_occ2010 if time < `s2_start'

gen double s2_weight = (time - `s2_start') / (`s2_infl' - `s2_start') ///
    if time >= `s2_start' & time < `s2_infl'
replace ensemble3_linear = ///
    (1 - s2_weight) * ensemble3_s1_occ2010 + s2_weight * ensemble3_s2_occ2010 ///
    if time >= `s2_start' & time < `s2_infl'

replace ensemble3_linear = ensemble3_s2_occ2010 if time >= `s2_infl' & time < `s3_start'

gen double s3_weight = (time - `s3_start') / (`s3_infl' - `s3_start') ///
    if time >= `s3_start' & time < `s3_infl'
replace ensemble3_linear = ///
    (1 - s3_weight) * ensemble3_s2_occ2010 + s3_weight * ensemble3_s3_occ2010 ///
    if time >= `s3_start' & time < `s3_infl'

replace ensemble3_linear = ensemble3_s3_occ2010 if time >= `s3_infl' & time < `s4_start'

gen double s4_weight = (time - `s4_start') / (`s4_infl' - `s4_start') ///
    if time >= `s4_start' & time < `s4_infl'
replace ensemble3_linear = ///
    (1 - s4_weight) * ensemble3_s3_occ2010 + s4_weight * ensemble3_s4_occ2010 ///
    if time >= `s4_start' & time < `s4_infl'

replace ensemble3_linear = ensemble3_s4_occ2010 if time >= `s4_infl'
label var ensemble3_linear "Ensemble exposure, OCC2010 occupation, linear interpolation"

drop s2_weight s3_weight s4_weight

/****************************************************************************************
8. Controls
****************************************************************************************/

gen age2 = age * age
label var age2 "Age squared"

gen age_18_21 = age >= 18 & age <= 21 if age < .
gen age_22_29 = age >= 22 & age <= 29 if age < .
gen age_30_49 = age >= 30 & age <= 49 if age < .
gen age_50_64 = age >= 50 & age <= 64 if age < .

label var age_18_21 "Age 18 to 21"
label var age_22_29 "Age 22 to 29"
label var age_30_49 "Age 30 to 49"
label var age_50_64 "Age 50 to 64"

gen age_30_39 = age >= 30 & age <= 39 if age < .
gen age_40_49 = age >= 40 & age <= 49 if age < .
gen age_50_59 = age >= 50 & age <= 59 if age < .
gen age_60_64 = age >= 60 & age <= 64 if age < .

label var age_30_39 "Age 30 to 39"
label var age_40_49 "Age 40 to 49"
label var age_50_59 "Age 50 to 59"
label var age_60_64 "Age 60 to 64"

gen age_18_29 = age >= 18 & age <= 29 if age < .
gen age30to50 = age >= 30 & age < 50 if age < .
gen age50plus = age >= 50 & age <= 64 if age < .

label var age_18_29 "Age 18 to 29"
label var age30to50 "Age 30 to 49"
label var age50plus "Age 50 to 64"

gen age30less = age_18_29
label var age30less "Age 18 to 29"

gen Dfem = 0
replace Dfem = 1 if sex == 2
replace Dfem = . if missing(sex)
label var Dfem "Female"

gen Dmale = .
replace Dmale = 1 if sex == 1
replace Dmale = 0 if sex == 2
label var Dmale "Male"

gen race_white = race == 100 if race < .
gen race_black = race == 200 if race < .
gen race_native = race == 300 if race < .
gen race_asian = race == 651 if race < .
gen race_mixed_other = race >= 652 if race < .

label var race_white "White"
label var race_black "Black"
label var race_native "Native American"
label var race_asian "Asian"
label var race_mixed_other "Mixed race or other race"

gen race_other_combined = .
replace race_other_combined = 1 if race_native == 1 | race_mixed_other == 1
replace race_other_combined = 0 if race_white == 1 | race_black == 1 | race_asian == 1
label var race_other_combined "Native, mixed, or other race"

gen Dhispanic = .
replace Dhispanic = 0 if hispan == 0
replace Dhispanic = 1 if hispan > 0 & hispan < .
label var Dhispanic "Hispanic"

gen hs_less = educ <= 73 if educ < .
gen SC_AD = educ > 73 & educ < 111 if educ < .
gen bachelors = educ == 111 if educ < .
gen masters_plus = educ > 111 if educ < .

label var hs_less "High school or less"
label var SC_AD "Some college or associate degree"
label var bachelors "Bachelor's degree"
label var masters_plus "Master's degree or more"

gen college_plus = educ >= 111 if educ < .
label var college_plus "Bachelor's degree or more"

gen married = inlist(marst, 1, 2) if marst < .
label var married "Married"

gen metro_dummy = inlist(metro, 2, 3, 4) if metro < .
replace metro_dummy = . if metro == 0
label var metro_dummy "Metropolitan area"

/****************************************************************************************
9. Broad industry groups

Keep the derived industry variables used by the FE analysis, but do not print industry
diagnostics from the cleaning files.
****************************************************************************************/

cap confirm numeric variable ind1990
if _rc {
    destring ind1990, replace ignore(" ")
}
replace ind1990 = . if ind1990 <= 0

gen byte broad_industry = 0
replace broad_industry = 1  if inrange(ind1990, 10, 32)
replace broad_industry = 2  if inrange(ind1990, 40, 50)
replace broad_industry = 3  if ind1990 == 60
replace broad_industry = 4  if inrange(ind1990, 100, 222)
replace broad_industry = 5  if inrange(ind1990, 230, 392)
replace broad_industry = 6  if inrange(ind1990, 400, 432)
replace broad_industry = 7  if inrange(ind1990, 440, 472)
replace broad_industry = 8  if inrange(ind1990, 500, 532)
replace broad_industry = 9  if inrange(ind1990, 540, 571)
replace broad_industry = 10 if inrange(ind1990, 580, 691)
replace broad_industry = 11 if inrange(ind1990, 700, 712)
replace broad_industry = 12 if inrange(ind1990, 721, 760)
replace broad_industry = 13 if inrange(ind1990, 761, 791)
replace broad_industry = 14 if inrange(ind1990, 800, 810)
replace broad_industry = 15 if inrange(ind1990, 812, 840)
replace broad_industry = 16 if inrange(ind1990, 842, 860)
replace broad_industry = 17 if inrange(ind1990, 861, 881)
replace broad_industry = 18 if ind1990 == 841
replace broad_industry = 18 if inrange(ind1990, 882, 893)
replace broad_industry = 19 if inrange(ind1990, 900, 932)

label define broad_industry_lbl ///
    0  "Other/unassigned" ///
    1  "Agriculture, forestry, fisheries" ///
    2  "Mining" ///
    3  "Construction" ///
    4  "Manufacturing: nondurable" ///
    5  "Manufacturing: durable" ///
    6  "Transportation" ///
    7  "Communications/utilities" ///
    8  "Wholesale: durable" ///
    9  "Wholesale: nondurable/n.s." ///
    10 "Retail trade" ///
    11 "Finance, insurance, real estate" ///
    12 "Business and repair services" ///
    13 "Personal services" ///
    14 "Entertainment/recreation" ///
    15 "Health services" ///
    16 "Education services" ///
    17 "Social/religious/membership/nonprofit" ///
    18 "Professional/technical/legal/management" ///
    19 "Public administration", replace
label values broad_industry broad_industry_lbl
label var broad_industry "Broad 1990 Census/SIC industry group"

label define yesno_ind_lbl 0 "No" 1 "Yes", replace

gen byte ind_agriculture       = broad_industry == 1
gen byte ind_mining            = broad_industry == 2
gen byte ind_construction      = broad_industry == 3
gen byte ind_mfg_nondur        = broad_industry == 4
gen byte ind_mfg_dur           = broad_industry == 5
gen byte ind_transport         = broad_industry == 6
gen byte ind_comm_util         = broad_industry == 7
gen byte ind_wholesale_dur     = broad_industry == 8
gen byte ind_wholesale_nond    = broad_industry == 9
gen byte ind_retail_trade      = broad_industry == 10
gen byte ind_fire              = broad_industry == 11
gen byte ind_bus_repair        = broad_industry == 12
gen byte ind_personal_serv     = broad_industry == 13
gen byte ind_entertainment     = broad_industry == 14
gen byte ind_health_serv       = broad_industry == 15
gen byte ind_educ_serv         = broad_industry == 16
gen byte ind_social_serv       = broad_industry == 17
gen byte ind_prof_mgmt         = broad_industry == 18
gen byte ind_public_admin      = broad_industry == 19

foreach v in ind_agriculture ind_mining ind_construction ind_mfg_nondur ind_mfg_dur ///
             ind_transport ind_comm_util ind_wholesale_dur ind_wholesale_nond ///
             ind_retail_trade ind_fire ind_bus_repair ind_personal_serv ///
             ind_entertainment ind_health_serv ind_educ_serv ind_social_serv ///
             ind_prof_mgmt ind_public_admin {
    label values `v' yesno_ind_lbl
}

gen byte ind_manufacturing = inlist(broad_industry, 4, 5)
label var ind_manufacturing "Industry: manufacturing"
label values ind_manufacturing yesno_ind_lbl

gen byte ind_personal_services = broad_industry == 13
label var ind_personal_services "Industry: personal services"
label values ind_personal_services yesno_ind_lbl

gen byte ind_prof_services = inlist(broad_industry, 15, 16, 17, 18)
label var ind_prof_services "Industry: professional and related services"
label values ind_prof_services yesno_ind_lbl

/****************************************************************************************
10. Canonical task indices

indices.dta is stored in the AAICELO shared-drive root and is keyed by CPS occupation
code. The merge is used only to add the canonical task indices and their top-quartile
indicators. Unmatched CPS observations remain in the analysis data.
****************************************************************************************/

cap confirm numeric variable cps_code
if _rc {
    destring cps_code, replace ignore(" ")
}
replace cps_code = . if cps_code <= 0

preserve
    use "${data_path}/indices.dta", clear

    cap confirm numeric variable cps_code
    if _rc {
        destring cps_code, replace ignore(" ")
    }

    replace cps_code = . if cps_code <= 0
    drop if missing(cps_code)

    isid cps_code
    keep cps_code NR_CA NR_CI RC RM NRMP offshore

    tempfile canonical_indices
    save `canonical_indices', replace
restore

merge m:1 cps_code using `canonical_indices', keep(master match) gen(merge_aa_routine)

label define merge_aa_routine_lbl ///
    1 "CPS only: no canonical task-index match" ///
    3 "Matched to indices.dta", replace
label values merge_aa_routine merge_aa_routine_lbl
label var merge_aa_routine "Merge status with indices.dta"

/****************************************************************************************
10A. Canonical task-index merge diagnostics
****************************************************************************************/

di as text "============================================================"
di as text "INDICES.DTA MERGE DIAGNOSTICS"
di as text "============================================================"

di as text "Person-month merge status:"
tab merge_aa_routine, missing

di as text ""
di as text "Unique CPS occupation codes by merge status:"
preserve
    keep cps_code merge_aa_routine
    drop if missing(cps_code)
    duplicates drop
    tab merge_aa_routine, missing
restore

di as text ""
di as text "Canonical task indices after merge:"
foreach v in NR_CA NR_CI RC RM NRMP offshore {
    summarize `v'
}

di as text "============================================================"


* Define top quartile at the occupation-code level rather than weighting occupations
* by their frequency in repeated CPS person-month observations.
preserve
    keep cps_code NR_CA NR_CI RC RM NRMP offshore
    keep if !missing(cps_code)
    duplicates drop cps_code, force

    foreach v in NR_CA NR_CI RC RM NRMP offshore {
        quietly summarize `v' if !missing(`v'), detail
        scalar p75_`v' = r(p75)
    }
restore

foreach v in NR_CA NR_CI RC RM NRMP offshore {
    gen byte high_`v' = .
    replace high_`v' = 0 if !missing(`v')
    replace high_`v' = 1 if !missing(`v') & `v' >= scalar(p75_`v')
}

label var high_NR_CA    "Top quartile non-routine cognitive analytical canonical task index"
label var high_NR_CI    "Top quartile non-routine cognitive interpersonal canonical task index"
label var high_RC       "Top quartile routine cognitive canonical task index"
label var high_RM       "Top quartile routine manual canonical task index"
label var high_NRMP     "Top quartile non-routine manual physical canonical task index"
label var high_offshore "Top quartile offshorability canonical task index"

label define high_task_lbl 0 "Below top quartile" 1 "Top quartile", replace
foreach v in NR_CA NR_CI RC RM NRMP offshore {
    label values high_`v' high_task_lbl
}

/****************************************************************************************
11. Occupation heterogeneity indicators
****************************************************************************************/

cap confirm numeric variable cps_code
if _rc {
    destring cps_code, replace ignore(" ")
}
replace cps_code = . if cps_code <= 0

gen managerial = 0 if cps_code < .
replace managerial = 1 if inrange(cps_code, 10, 430)
label var managerial "Managerial occupation"

gen operations = 0 if cps_code < .
replace operations = 1 if inrange(cps_code, 500, 960)
label var operations "Operations occupation"

gen mgmt_or_ops = .
replace mgmt_or_ops = 1 if managerial == 1
replace mgmt_or_ops = 0 if operations == 1
label var mgmt_or_ops "Managerial versus operations occupation"

gen collar3 = .
replace collar3 = 1 if inrange(cps_code, 10, 3550)
replace collar3 = 2 if inrange(cps_code, 3601, 5940)
replace collar3 = 3 if inrange(cps_code, 6005, 9760)
label define collar3_lbl 1 "White collar" 2 "Grey collar" 3 "Blue collar", replace
label values collar3 collar3_lbl
label var collar3 "Collar group from CPS occupation code"

gen whitecollar = .
replace whitecollar = 1 if collar3 == 1
replace whitecollar = 0 if inlist(collar3, 2, 3)
label var whitecollar "White collar"

gen greycollar = .
replace greycollar = 1 if collar3 == 2
replace greycollar = 0 if inlist(collar3, 1, 3)
label var greycollar "Grey collar"

gen bluecollar = .
replace bluecollar = 1 if collar3 == 3
replace bluecollar = 0 if inlist(collar3, 1, 2)
label var bluecollar "Blue collar"

/****************************************************************************************
12. COVID and timing indicators
****************************************************************************************/

gen Dcovid_may = 0
replace Dcovid_may = 1 if time >= ym(2020, 3) & time <= ym(2021, 5)
label var Dcovid_may "COVID period through May 2021"

gen Dcovid_dec = 0
replace Dcovid_dec = 1 if time >= ym(2020, 3) & time <= ym(2021, 12)
label var Dcovid_dec "COVID period through December 2021"

gen post_chatgpt = time >= ym(2022, 11)
label var post_chatgpt "Post ChatGPT release period"

gen byte post_s2_start = time >= ym(2022, 11) if !missing(time)
label var post_s2_start "Post Stage 2 start, Nov. 2022+"

gen byte post_s3_start = time >= ym(2024, 9) if !missing(time)
label var post_s3_start "Post Stage 3 start, Sept. 2024+"

gen byte post_s4_start = time >= ym(2025, 5) if !missing(time)
label var post_s4_start "Post Stage 4 start, May 2025+"

gen post_s2_infl = time >= ym(2023, 3)
label var post_s2_infl "Post Stage 2 adoption inflection"

gen post_s3_infl = time >= ym(2025, 1)
label var post_s3_infl "Post Stage 3 adoption inflection"

gen post_s4_infl = time >= ym(2026, 1)
label var post_s4_infl "Post Stage 4 adoption inflection"


/****************************************************************************************
13. Compact cleaning diagnostics
****************************************************************************************/

local primary_outcomes ///
    Demp ///
    parttime_usual ///
    ahrswork1 ///
    log_hrearn_tc_real

local secondary_outcomes ///
    D_other_job_HW ///
    ahrsworkt ///
    ahrswork2 ///
    log_earn_tc_real

local exposure_vars ///
    ensemble3_step ///
    ensemble3_linear

local task_vars ///
    NR_CA NR_CI RC RM NRMP offshore ///
    high_NR_CA high_NR_CI high_RC high_RM high_NRMP high_offshore

di as text "============================================================"
di as text "FINAL CLEANING DIAGNOSTICS"
di as text "============================================================"

quietly count
di as text "Total person-months: " as result %12.0fc r(N)

quietly summarize time, meanonly
di as text "First month: " as result %tm r(min)
di as text "Last month:  " as result %tm r(max)

quietly summarize age, meanonly
di as text "Age range: " as result r(min) " to " r(max)

di as text ""
di as text "PRIMARY MAIN-RESULTS OUTCOMES"
di as text "Part-time is treated as a primary outcome in these diagnostics."
foreach v of local primary_outcomes {
    di as text "------------------------------------------------------------"
    di as text "`v'"
    summarize `v'
}

di as text ""
di as text "SECONDARY MAIN-RESULTS OUTCOMES"
foreach v of local secondary_outcomes {
    di as text "------------------------------------------------------------"
    di as text "`v'"
    summarize `v'
}

di as text ""
di as text "EXPOSURE MEASURES"
foreach v of local exposure_vars {
    di as text "------------------------------------------------------------"
    di as text "`v'"
    summarize `v'
}

di as text ""
di as text "CANONICAL TASK VARIABLES"
foreach v of local task_vars {
    di as text "------------------------------------------------------------"
    di as text "`v'"
    summarize `v'
}

di as text "============================================================"

quietly count
di as text "Total person-months: " as result %12.0fc r(N)

quietly summarize time, meanonly
di as text "First month: " as result %tm r(min)
di as text "Last month:  " as result %tm r(max)

quietly count if !missing(Demp)
di as text "Demp nonmissing: " as result %12.0fc r(N)

quietly count if sample_nonemp_outcomes == 1
di as text "sample_nonemp_outcomes == 1: " as result %12.0fc r(N)

foreach y in log_earn_tc_real log_hrearn_tc_real {
    quietly count if !missing(`y')
    di as text "`y' nonmissing: " as result %12.0fc r(N)
}

foreach x in ensemble3_step ensemble3_linear {
    quietly count if !missing(`x')
    di as text "`x' nonmissing: " as result %12.0fc r(N)
}

quietly count if !missing(cps_code)
di as text "cps_code nonmissing: " as result %12.0fc r(N)

quietly count if !missing(occ2010)
di as text "occ2010 nonmissing: " as result %12.0fc r(N)

di as text "============================================================"

/****************************************************************************************
14. Save cleaned FE data
****************************************************************************************/

compress

* Full OCC2010 support: January 2017 onward.
save "${data_path}/individual_fe/cps_fe_analysis_jan2017_occ2010.dta", replace
di as result "Saved: ${data_path}/individual_fe/cps_fe_analysis_jan2017_occ2010.dta"

* Common-window OCC2010 clean: October 2021 onward.
preserve
keep if time >= ym(2021, 10)
save "${data_path}/individual_fe/cps_fe_analysis_oct2021_occ2010.dta", replace
di as result "Saved: ${data_path}/individual_fe/cps_fe_analysis_oct2021_occ2010.dta"
restore

di as text "fe_clean_occ2010.do completed successfully."
log close
