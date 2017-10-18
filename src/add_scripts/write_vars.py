#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

This python script uses the CORDEX variables table to determine which variables are needed for CORDEX
and on which pressure level (if any). The INPUT_IO file of the CCLM model is used
to find out in which output stream (outXX) the variables are located.
All this information is written to a file that is executed in the first step
of the post-processing (first.sh).
If variables occur more than once in the INPUT_IO file only the first appearance is taken into account.

@author: Matthias Göbel, 08/2017
"""

import numpy as np
import csv
import operator

path="../../misc/"
varfile="../CMORlight/Config/CORDEX_CMOR_CCLM_variables_table.csv" #variables table
infile=open(path+"INPUT_IO.1949","r") #gribout file of CCLM

path_cclm="../cclm_post/"  # the output file is placed here

cordex_only=True #only process variables needed for CORDEX

#additionally needed variables to calculate CORDEX variables
add=["SNOW_GSP","SNOW_CON","RAIN_CON","RUNOFF_G","ASOB_T","ASWDIR_S","ASWDIFD_S","TQC"]

def listit(v):
    s=v.replace(" ","").replace("'","").replace("=","")
    if s=="" or s==",":
        return []
    else:
        return s.split(",")

"""Read variables for each output stream from file and put it into list"""
outvar = {} #CCLM output variables on model levels
outvarp = {} #CCLM output varoables on pressure levels
res = [] #time resolution of each output stream
i=0
j=0
while True:
    line=infile.readline()
    #get number of output streams
    if "ngribout" in line:
        outs = int(line[13:-2])
    #get resolution for current stream
    elif "hcomb" in line:
        hcomb = listit(line[line.find("=")+2:-2])
        res.append(hcomb[-1])
    #read out variables
    elif "yvarml" in line:
        v=[]
        vp=[]
        v.extend(listit(line[9:-2]))
        stop = False
        #read following lines
        while True:
            line=infile.readline()
            if "yvarpl" in line:
            #now variables on pressure levels
                 while True:
                     vp.extend(listit(line[9:-2]))
                     line=infile.readline()
                     if "yvarzl" in line or "plev" in line:
                    #on z levels not needed
                         stop = True
                         break 
            if stop:
                break
            v.extend(listit(line[:-2]))
        
        #append to dict if not yet in dict or if time resolution is lower
        for var in v:
            if var not in outvar or res[i] < res[outvar[var]]:
                outvar[var] = i
        for var in vp:
            if var not in outvarp or res[i] < res[outvarp[var]]:
                outvarp[var] = i
        
        if outs and i==outs:
            break
        i=i+1
    if j>1000:
        break
    j=j+1

infile.close()

"""Write file in format of post.job.tmpl"""

#Determine largest variable name
joint_l=list(outvar.keys())+list(outvarp.keys())
lenmax=len(max(joint_l, key=len))

#Get variables needed for cordex from csv file
mlvar=[]
pvar={}
with open(varfile,'rt') as csvfile:
    reader = csv.reader(csvfile,delimiter=';')
    for i,row in enumerate(reader):
        if i != 0 and row[1]!="":
            #write requested pressure levels into dict
            if row[1] != row[0]:
                if row[1] in pvar:
                    pvar[row[1]].append(row[0][-4:-1])
                else:
                    pvar[row[1]]=[row[0][-4:-1]]
            else:
                mlvar.append(row[1])

    mlvar.extend(add)

#write into file
timeseries=open(path_cclm+"timeseries.sh","w")
outvar_sorted = sorted(outvar.items(), key=operator.itemgetter(1))
outvarp_sorted = sorted(outvarp.items(), key=operator.itemgetter(1))

for var in outvar_sorted:
    if var[0] in mlvar or not cordex_only:
        timeseries.write("timeseries  {:{width}s} out{:02d}\n".format(var[0],var[1]+1,width=lenmax))
       
timeseries.write("#\n")

for varp in outvarp_sorted:
    if varp[0] in pvar or not cordex_only:
        plev=str(pvar[varp[0]]).replace("[","(").replace("]",")").replace(",","").replace("0'","0.").replace("'","")
        timeseries.write("PLEVS=%s \n" % plev)
        timeseries.write("timeseriesp {:{width}s} out{:02d} \n".format(varp[0],varp[1]+1,width=lenmax))

timeseries.close()

cordex_vars = mlvar + list(pvar.keys())
#write proc_list into file (can be used for the seconds processing step if desired)
proc_list=open(path_cclm+"proc_list","w")

for var in sorted(joint_l):
    if var in cordex_vars or not cordex_only:
        proc_list.write("{:s} ".format(var))

proc_list.close()



#which cordex variables are not yet processed:
cordex_vars=np.array(cordex_vars)
mask=np.in1d(cordex_vars,joint_l)
ava=np.ma.masked_where(mask, cordex_vars)
print("Variables required by CORDEX but not yet delivered by CCLM (have to be calculated in the postprocessing):\n"+str(ava[~ava.mask]))














