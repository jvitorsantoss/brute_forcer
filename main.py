import requests
from pathlib import Path


def wd():
    cd = input("Put the path of your wordlist: \n")
    cd = cd.strip('"\'')
    cdR = Path(cd)

    if cdR.exists():
        return cdR
    else:
        return None

rs = wd()

if rs == None:
    print("Couldn't find your path, try it again")
else:
    with open (rs,"r") as file:
        pssw = file.read().splitlines()
