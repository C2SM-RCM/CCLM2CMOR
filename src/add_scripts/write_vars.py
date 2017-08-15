#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 21 15:17:37 2017


To write model variables for each outXX stream from INPUT_IO file to post.job.tmpl file

@author: mgoebel
"""

import itertools
import numpy as np
import csv

path="/project/pr04/mgoebel/CMOR/misc/"
path_cclm="/project/pr04/mgoebel/CMOR/src/cclm_post/"
infile=open(path+"INPUT_IO.1949","r")
varfile=path+"CORDEX_CMOR_CCLM_variables_table.csv"
cordex_only=True #only process variables needed for CORDEX

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
with open(varfile,'rt') as csvfile:
    reader = csv.reader(csvfile,delimiter=';')
    for row in reader:
        if row[1]!="":
            cordex_vars.append(row[1])
#additionally needed variables to calculate CORDEX variables
add=["SNOW_GSP","SNOW_CON","RAIN_CON","RUNOFF_G","ASOB_T","ASWDIR_S","ASWDIFD_S","TQC"]
cordex_vars.extend(add)

#write into file
jobf=open(path_cclm+"jobf.sh","w")

for o,out in enumerate(outvar):
    for var in out:
        if var in cordex_vars or not cordex_only:
            jobf.write("timeseries  {:{width}s} out{:02d}\n".format(var,o+1,width=lenmax))
       # else:
        #    print("Variable %s not needed!" % var)
    for varp in outvarp[o]:
        if varp in cordex_vars or not cordex_only:
            jobf.write("timeseriesp {:{width}s} out{:02d}\n".format(varp,o+1,width=lenmax))
     #   else:
      #      print("Variable %s not needed!" % varp)
    jobf.write("#\n")

jobf.close()



#which cordex variables are not yet processed:
cordex_vars=np.array(cordex_vars)
mask=np.in1d(cordex_vars,flat_l)
ava=np.ma.masked_where(mask, cordex_vars)
print(ava[~ava.mask])














