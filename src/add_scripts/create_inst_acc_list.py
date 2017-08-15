#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  8 14:48:16 2017

Create one list for instantaneous and one for accumulated variables
of CCLM respectively using the output variables from the CCLM
website.


@author: mgoebel
"""

import csv
varfile="/project/pr04/mgoebel/CMOR/misc/cclm_variables.csv"
vardict={}
with open(varfile,'r') as csvfile:
    reader = csv.reader(csvfile,delimiter=';')
    for row in reader:
        try:
            vardict[row[0]]=int(row[-2])
        except:
            print(row)


inst_list=""
acc_list=""
for key in vardict.keys():
    if vardict[key]==0:
        inst_list+=" "+ key
    else:
        acc_list+=" "+key

print(inst_list)

print(acc_list)
