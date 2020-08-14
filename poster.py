#! /usr/bin/env python3


import requests
import json
from os import fsencode, listdir, fsdecode

from dotenv import load_dotenv

load_dotenv()

SRV = os.getenv("SRV")

HEADERS = {'Content-type': 'application/json'}

def get_files_in_dir(directory_in_str, file_pattern=""):
    list_files = []
    directory = fsencode(directory_in_str)
    for logfile in listdir(directory):
        if file_pattern in fsdecode(logfile):
            list_files.append(f"{directory_in_str}/{fsdecode(logfile)}")
    return list_files


lsfiles = get_files_in_dir("mybsdlogs/", ".bsd")

for lsf in lsfiles:
    with open(lsf) as bsdf:
        allfile = bsdf.read() 
        lines = allfile.split('\n')
        for line in lines:
            linejson = json.loads(line)
            response = requests.post(SRV, data=json.dumps(linejson),headers=HEADERS)
            print(response.content)

