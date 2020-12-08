The Directory "Batch" contains scripts written to do the actual CMOR-process and, if necessary, the
subsequent chunking of CMORized files with the help of batch-jobs.

Note:
these scripts are only applicable for the second step (see README.rst), the actual CMORization process.
They are alternaives to the "job" scheduler in "src" directory (see also README.rst)

Originally, the scripts had been written by Ch. Steger, DWD.
Modification into the present form by H.-J. Panitz, IMK-TRO/KIT

Note:
Before you can apply these scripts you have to edit the file
"control_cmor.ini" in "src/CMORlight" according to your needs!

The list of scripts in "Batch" consists of:

run_cmor.sh:
 the script steering the actual CMORization and for the setup of the batch-job(s)
 the script has to be edit according to your needs taking into account the computing environment
 the script is written to allow
 - the CMORization of several variables
 - over a user-defined period of time which can be several years

 For each variable a separate jobs is submitted CMORizing the variables over the whole range of years
 The output will be yearly time-series for the chosen variable
 When considering several year it is recommended to use the "-M" option of "cmorlight.py"

 After the correct editing, just run "run_cmor.sh".

cmor.job.tmpl.sh:
 a template for the CMOR batch-job
 it has to be edit once according to the batch-environment of your computer system
 after the editing, and if everything is correct, nothing else has to done with this template
 the batch job itself is submitted within "run_cmor.sh"

run_cmor_chunk.sh:
 the script steering for the chunking of already CMORized fikes and for the setup of the batch-job(s)
 the script has to be edit according to your needs taking into account the computing environment
 the script is written to allow
 - the chunking of several variables
 the chunk-ranges for different time-frequencies has to be defined in "control_cmor.ini" in "src/CMORlight"
 it is recommended to use the ranges already been defined there; they coorespond to those prescribed by CORDEX
 teh chunking itself occurs according to the CORDEX requirements

 For each variable a separate jobs is submitted
 The output will be the chunked time-series

 Note:
 Usage of "-M" option of "cmorlight.py" makes no sense for chunking!

 After the correct editing, just run "run_cmor_chunk.sh".

cmor_chunk.job.tmpl.sh:
 a template for the chunk batch-job
 it has to be edit once according to the batch-environment of your computer system
 after the editing, and if everything is correct, nothing else has to done with this template
 the batch job itself is submitted within "run_cmor_chunk.sh"

Last Note:
 the chunking has to be done after the actual CMORization!
