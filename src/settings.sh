
post_step=0 #to limit post processing to step 1 or 2, for all other values both steps are executed

#Simulation details

GCM=HadGEM2-ES     
EXP=RCP85

EXPPATH=${GCM}/${EXP}
ARCH_SUB=${GCM}_Hist_RCP85/${EXP}  #subdirectory where data of this simulation are archived
#ARCH_SUB=HadGEM2-ES_Hist_RCP85/RCP85

# time settings
SIM_START=1949120100 # start date of simulation YYYYMMDDHH[mmss]: needed for constant file

#for step 1:
START_DATE=202102      #Start year and month for processing (if not given in command line) YYYYMM
STOP_DATE=210012     #End year and month for processing (if not given in command line)  YYYYMM
#SIM_STOP=2099123000  # end date of simulation YYYYMMDDHH[mmss]

#for step 2:
YYA=  #Start year for processing 
YYE= #End year for processing 

#... directory path settings
BASEDIR=/scratch/snx1600/mgoebel/CMOR
ARCH_BASE=/store/c2sm/ch4/ssilje/Archive_cosmo_runs # directory where the raw data of the simulations are archived
ARCHDIR=${ARCH_BASE}/${ARCH_SUB} # join archive paths
SRCDIR=${BASEDIR}/src/cclm_post           # directory where the post processing scripts are stored
WORKDIR=${SCRATCH}/work/post # work directory, CAUTION: WITH OPTION "--clean" ALL FILES IN THIS FOLDER WILL BE DELETED!

#input/output directory for first step
INPUTPOST=${BASEDIR}/input     # directory to where the raw data archives are extracted
OUTPUTPOST=${BASEDIR}/work/outputpost # output directory of the first step

#for second step
INDIR_BASE=${OUTPUTPOST}
OUTDIR_BASE=${BASEDIR}/work/input_CMORlight


#Variable settings

# all CCLM variables representing a time interval (min,max,average, accumulated)
accu_list="AEVAP_S ALHFL_BS ALHFL_PL ALHFL_S ALWD_S ALWU_S APAB_S ASHFL_S ASOB_S ASOB_T ASOD_T ASWDIFD_S ASWDIFU_S ASWDIR_S ATHB_S ATHB_T AUMFL_S AUSTRSSO AVDISSSO AVMFL_S AVSTRSSO DURSUN DURSUN_M DURSUN_R GRAU_GSP HAIL_GSP RAIN_CON RAIN_GSP RUNOFF_G RUNOFF_S SNOW_CON SNOW_GSP SNOW_MELT T_2M_AV TD_2M_AV TDIV_HUM TMAX_2M TMIN_2M TOT_PREC U_10M_AV V_10M_AV VABSMX_10M VGUST_CON VGUST_DYN VMAX_10M"
  
#all instantaneous variables
inst_list="AER_BC AER_DUST AER_ORG AER_SO4 AER_SS ALB_DIF ALB_DRY ALB_RAD ALB_SAT BAS_CON BRN C_T_LK CAPE_3KM CAPE_CON CAPE_ML CAPE_MU CEILING CIN_ML CIN_MU CLC CLC_CON CLC_SGS CLCH CLCL CLCM CLCT CLCT_MOD CLDEPTH CLW_CON DBZ DBZ_850 DBZ_CMAX DD_ANAI DEPTH_LK DP_BS_LK DPSDT DQC_CON DQI_CON DQV_CON DQVDT DT_CON DT_SSO DTKE_CON DTKE_HSH DTKE_SSO DU_CON DU_SSO DV_CON DV_SSO EDR EMIS_RAD EVATRA_SUM FC FETCH_LK FF_ANAI FI FI_ANAI FIS FOR_D FOR_E FR_ICE FR_LAKE FRESHSNW GAMSO_LK H_B1_LK H_ICE H_ML_LK H_SNOW H_SNOW_M HBAS_CON HBAS_SC HHL HMO3 HORIZON HPBL HTOP_CON HTOP_DC HTOP_SC HZEROCL LAI LAI_MN LAI_MX LCL_ML LFC_ML LHFL_S LWD_S LWU_S MFLX_CON MSG_RAD MSG_RADC MSG_TB MSG_TBC O3 OMEGA P P_ANAI PABS_RAD PLCOV PLCOV_MN PLCOV_MX PMSL PMSL_ANAI POT_VORTIC PP PRG_GSP PRH_GSP PRR_CON PRR_GSP PRS_CON PRS_GSP PS Q_SEDIM QC QC_ANAI QC_RAD QCVG_CON QG QH QI QI_RAD QNCLOUD QNGRAUPEL QNHAIL QNICE QNRAIN QNSNOW QR QRS QS QV QV_2M QV_ANAI QV_S QVSFLX RCLD RELHUM RELHUM_2M RESID_WSO RHO_SNOW RHO_SNOW_M RLAT RLON ROOTDP RSMIN RSTOM SDI_1 SDI_2 SHFL_S SI SKYVIEW SLI SLO_ANG SLO_ASP SNOWLMT SOBS_RAD SOBT_RAD SOD_T SOHR_RAD SOILTYP SP_10M SSO_GAMMA SSO_SIGMA SSO_STDH SSO_THETA SWDIFD_S SWDIFU_S SWDIR_COR SWDIR_S SWISS00 SWISS12 SYNME5 SYNME6 SYNME7 SYNMSG T T_2M T_ANAI T_B1_LK T_BOT_LK T_BS_LK T_CL T_G T_ICE T_M T_MNW_LK T_S T_SNOW T_SNOW_M T_SO T_WML_LK TCH TCM TD_2M THBS_RAD THBT_RAD THHR_RAD TINC_LH TKE TKE_CON TKETENS TKVH TKVM TO3 TOP_CON TOT_PR TOTFORCE_S TQC TQC_ANAI TQG TQH TQI TQR TQS TQV TQV_ANAI TRA_SUM TWATER U U_10M UMFL_S USTR_SSO V V_10M VDIS_SSO VIO3 VMFL_S VORTIC_U VORTIC_V VORTIC_W VSTR_SSO W W_CL W_G1 W_G2 W_G3 W_I W_SNOW W_SNOW_M W_SO W_SO_ICE WLIQ_SNOW Z0 ZHD ZTD ZWD"

# constant variables
const_list="FR_LAND HSURF"



#Special settings for first step

NBOUNDCUT=10 # number of boundary lines to be cut off in the time series data 
IE_TOT=101 # number of gridpoints in zonal direction?
JE_TOT=111 # number of gridpoints in meridional direction
PLEVS=(200. 500. 850. 925.)  # list of pressure levels to output.The list must be the same as or a subset	of the list in the specific GRIBOUT. 
ZLEVS=(100. 1000. 2000. 5000.) # list of height levels to output (similar to PLEVS)

#Special settings for second step

LASTDAY=30   #Last day of each month (e.g. 30 or 31) TODO: some gcms use greogorian calendar!
proc_list="V" #which variables to process (set proc_all=false for this to take effect)
proc_all=true  #process all available variables (not only those in proc_list)

LFILE=0  # Set LFILE=1 if only primary fields (given out by COSMO) should be created and =2 for only secondary fields (additionally calculated for CORDEX); for any other number both types of fields are calculated

PERM=755 #Permission settings for output files


