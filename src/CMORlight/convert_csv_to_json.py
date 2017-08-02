import os
import sys
import csv
import json

varfile = "/mnt/lustre01/work/bb0931/CMOR/cmorlight/Config/CORDEX_CMOR_CCLM_variables_table.csv"
jsonfile = open('/mnt/lustre01/work/bb0931/CMOR/cmorlight/Config/CORDEX_CMOR_CCLM_variables_table.json', 'w')
with open(varfile,'r') as csvfile:
    reader = csv.reader(csvfile,delimiter=';')
    for row in reader:
       json.dump(row, jsonfile)

