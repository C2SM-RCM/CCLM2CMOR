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

import itertools
import numpy as np
import csv

path="../../misc/"
varfile=path+"CORDEX_CMOR_CCLM_variables_table.csv"
infile=open(path+"INPUT_IO.1949","r")

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
outvar=[]
outvarp=[]
stop=False
outs=7
i=0
j=0
while True:
    line=infile.readline()
    v=[]
    vp=[]
    if line[:8]=="  yvarml":
        v.extend(listit(line[9:-2]))
        while True:
            line=infile.readline()
            if line[:8]=="  yvarpl":
                vp.extend(listit(line[9:-2]))
                break


            v.extend(listit(line[:-2]))

        for var in v:
            if any(var in sl for sl in outvar):
                print("Variable %s already appended! Skipping..." % var)
                v.remove(var)
        for varp in vp:
            if any(varp in sl for sl in outvarp):
                print("Variable %s already appended! Skipping..." % varp)
                vp.remove(varp)
        outvar.append(v)
        outvarp.append(vp)
        if i==outs:
            break
        i=i+1
    if j>1000:
        break
    j=j+1

infile.close()

"""Write file in format of post.job.tmpl"""

#Determine largest variable name
flat_l=list(itertools.chain(*(outvar+outvarp)))
lenmax=len(max(flat_l, key=len))

#Get variables needed for cordex from csv file
cordex_vars=[]
PLEVS={}
with open(varfile,'rt') as csvfile:
    reader = csv.reader(csvfile,delimiter=';')
    for row in reader:
        if row[1]!="":
            cordex_vars.append(row[1])
            #write requested pressure levels into dict
            if row[1]!=row[0]:
                if row[1] in PLEVS:
                    PLEVS[row[1]].append(row[0][-4:-1])
                else:
                    PLEVS[row[1]]=[row[0][-4:-1]]

cordex_vars.extend(add)

#write into file
timeseries=open(path_cclm+"timeseries.sh","w")

for o,out in enumerate(outvar):
    for var in out:
        if var in cordex_vars or not cordex_only:
            timeseries.write("timeseries  {:{width}s} out{:02d}\n".format(var,o+1,width=lenmax))

       # else:
        #    print("Variable %s not needed!" % var)
    for varp in outvarp[o]:
        if varp in cordex_vars or not cordex_only:

            plev=str(PLEVS[varp]).replace("[","(").replace("]",")").replace(",","").replace("0'","0.").replace("'","")
            timeseries.write("PLEVS=%s \n" % plev)
            timeseries.write("timeseriesp {:{width}s} out{:02d} \n \n".format(varp,o+1,width=lenmax))
     #   else:
      #      print("Variable %s not needed!" % varp)
    timeseries.write("#\n")

timeseries.close()


#write proc_list into file (can be used for the seconds processing step if desired)
proc_list=open(path_cclm+"proc_list","w")

for var in sorted(flat_l):
    if var in cordex_vars or not cordex_only:
        proc_list.write("{:s} ".format(var))

proc_list.close()



#which cordex variables are not yet processed:
cordex_vars=np.array(cordex_vars)
mask=np.in1d(cordex_vars,flat_l)
ava=np.ma.masked_where(mask, cordex_vars)
print("Variables required by CORDEX but not yet delivered by CCLM (have to be calculated in the postprocessing):\n"+str(ava[~ava.mask]))














