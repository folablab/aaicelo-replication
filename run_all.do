/*------------------------------------------------------------------------------
run_all.do -- estimate every regression of the paper and write the results to output/estimates/.

Run from the repository root (the folder that holds data/, code/, output/):
    stata-se -b do run_all.do          (batch; the log is run_all.log and one log per script)
or open Stata, `cd' to the repository root, and `do run_all.do'.
Requires Stata 17 or later with reghdfe and ftools (ssc install reghdfe ftools). About ten minutes.
Then python3 run_all.py builds the tables and figures from these results.
------------------------------------------------------------------------------*/
version 17.0
clear all
capture confirm file "data/cell_fd/fd_baseline_3m_occ2010.dta"
if _rc {
    di as error "Run from the repository root (the folder that holds data/ and code/). Current directory: `c(pwd)'"
    exit 601
}
foreach s in 01_fd_main 02_fd_specification 03_fd_composition 04_fd_telework ///
             05_fe_main 06_fe_specification 07_fe_telework 08_individual_fe {
    di as result _n "==== code/stata/`s'.do"
    do "code/stata/`s'.do"
}
di as result _n "All regression results are in output/estimates/."
