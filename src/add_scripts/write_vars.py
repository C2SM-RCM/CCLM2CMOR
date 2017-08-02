#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 21 15:17:37 2017


To write model variables for each outXX stream from INPUT_IO file to post.job.tmpl file

@author: mgoebel
"""

import itertools
import numpy as np


path="/home/mgoebel/CMOR/misc/"
var=open(path+"INPUT_IO.1949","r")

def listit(v):
    s=v.replace(" ","").replace("'","").replace("=","")
    if s=="" or s==",":
        return []
    else:
        return s.split(",")
    
"""Read variables for each output stream from file and put it into list"""    
outvar=[]
outvarp=[]
stop=False
outs=7
i=0
j=0
while True:
    line=var.readline()
    v=[]
    vp=[]
    if line[:8]=="  yvarml":
        v.extend(listit(line[9:-2]))
        while True:
            line=var.readline()
            if line[:8]=="  yvarpl":
                vp.extend(listit(line[9:-2]))
                break
       

            v.extend(listit(line[:-2]))

        outvar.append(v)   
        outvarp.append(vp)
        if i==outs:
            break
        i=i+1
    if j>1000:
        break
    j=j+1

var.close()

"""Write file in format of post.job.tmpl"""

#Determine largest variable name
flat_l=list(itertools.chain(*(outvar+outvarp)))        
lenmax=len(max(flat_l, key=len))

#    
#jobf=open(path+"jobf","w")
#
#for o,out in enumerate(outvar):
#    for var in out:
#        jobf.write("timeseries  {:{width}s} out{:02d
#                   }\n".format(var,o+1,width=lenmax))
#    for varp in outvarp[o]:
#        jobf.write("timeseriesp {:{width}s} out{:02d}\n".format(varp,o+1,width=lenmax))
#        
#    jobf.write("#\n")
#
#jobf.close()


accu_list="AEVAP_S ALHFL_S ALWD_S ALWU_S ASHFL_S ASOB_S ASOB_T ASOD_T\
 ASWDIFD_S ASWDIFU_S ASWDIR_S ATHB_S ATHB_T DURSUN\
 RAIN_CON RAIN_GSP RUNOFF_G RUNOFF_S SNOW_CON SNOW_GSP SNOW_MELT\
 TMAX_2M TMIN_2M TOT_PREC VABSMX_10M VMAX_10M"
accu_list=np.array(accu_list.split(" "))
           
inst_list="ALB_RAD CLCH CLCL CLCM CLCT FI200p FI500p FI850p FI925p HPBL H_SNOW\
 PMSL PS QV_2M QV200p QV500p QV850p QV925p RELHUM_2M RELHUM200p\
 RELHUM500p RELHUM850p RELHUM925p T_2M T200p T500p T850p T925p\
 TQC TQI TQV T_S U_10M U200p U500p U850p U925p V_10M V200p V500p\
 V850p V925p W_SNOW W_SO_ICE W_SO"
inst_list=np.array(inst_list.split(" "))

accu_list2=" ".join(list(accu_list[np.in1d(accu_list,flat_l)]))
inst_list2=" ".join(list(inst_list[np.in1d(inst_list,flat_l)]))
print(accu_list2)
print(inst_list2)



















