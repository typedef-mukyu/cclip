#!/usr/bin/python3
import requests
import sys
import os
from http.client import responses
from msgstrings import msgStrings

# raise_for_status() throws an exception on HTTP 4xx and 5xx codes

# Requests the user's credentials from the message broker.
def getCredBook() -> dict:
    credBook = dict()
    credBook["url"] = getConfigItem("api_url")
    credBook["key"] = getConfigItem("api_key")
    return credBook

# Requests a configuration value from the message broker, which forwards the request to config.py.
def getConfigItem(setting: str) -> str: 
    mbpipe = os.open(".getter_fifo", os.O_WRONLY)
    os.write(mbpipe, str.encode("config get " + setting))
    os.close(mbpipe)
    mbpipe = os.open(".getter_fifo", os.O_RDONLY)
    # the [2:-1] strips the b'value' wrapping Python uses when converting a bytes into a str
    value = str(os.read(mbpipe, 1023))[2:-1] 
    os.close(mbpipe)
    return value

def getUploadToken(credBook: dict, argBook: dict) -> object:
    if not os.path.isfile(argBook["filename"]): # verify the filename
        raise ValueError("Invalid filename") 
    rqData = {"name": os.path.basename(argBook["filename"]), # pass filename and size to HTTP request
                    "size": str(os.path.getsize(argBook["filename"]))}
    targetUrl = (credBook["url"] + "/api/v1/courses/" + argBook["course"] + 
                "/assignments/" + argBook["assignment"] + "/submissions/self/files")
    headers = {"Authorization": "Bearer " + credBook["key"]}
    response = requests.post(targetUrl, data=rqData, headers=headers)
    response.raise_for_status()
    return response

def uploadFile(credBook: dict, argBook: dict, token: dict) -> object:
    rqData = token["upload_params"] # to upload the file, the request parameters must match the token
    headers = {"Content-Length": "0", "Authorization": "Bearer " + credBook["key"]}
    fileData = open(argBook["filename"], "rb") # open the file and upload it (line below)
    response = requests.post(token["upload_url"], data=rqData, files={"file": fileData}) 
    fileData.close()
    response.raise_for_status()
    location = response.headers["Location"] # location of newly uploaded file
    response = requests.get(location, headers=headers) # verify that the file is there
    response.raise_for_status()
    return response

def submit(credBook, argBook: dict, file_id) -> object:
    targetUrl = (credBook["url"] + "/api/v1/courses/" + argBook["course"] + "/assignments/" +
                 argBook["assignment"] + "/submissions")
    rqData = {"submission[submission_type]": "online_upload", "submission[file_ids][]": [file_id]}
    headers = {"Authorization": ("Bearer " + credBook["key"])}
    # the line below links the file uploaded earlier to the assignment endpoint in targetUrl
    response = requests.post(targetUrl, data=rqData, headers=headers)
    response.raise_for_status()
    return response

def parseArgs(argBook: dict=dict()) -> dict:
    paramArgs = {"-c": "course", "-a": "assignment"} # Parameter arguments followed by values
    i = 0 # in Python, I can't do `for i ...` and also increment i externally
    while i < (len(sys.argv) - 1):
        i += 1
        if sys.argv[i] in paramArgs:
            argBook[paramArgs[sys.argv[i]]] = sys.argv[i + 1]
            i += 1
        else:
            argBook["filename"] = sys.argv[i]
    return argBook

def verifyArgs(argBook: dict) -> None:
    if len(argBook) < 3:
        print("Usage: ./submit -c courseid -a assignmentid filename")
        exit()

def main() -> int:
    credBook = getCredBook() # Canvas instance URL and API key
    argBook = parseArgs()
    verifyArgs(argBook)
    # The Canvas API has a three-step process for submitting file uploads:
    token = getUploadToken(credBook, argBook) # 1: request an upload token, which points to a destination endpoint
    ulstat = uploadFile(credBook, argBook, token.json()) # 2: upload the file to the designated endpoint, and get its location
    fileId = int(ulstat.json()["id"])
    sstat = submit(credBook, argBook, fileId) # 3: submit with the ID of the newly uploaded file
    if sstat.status_code == 201:
        print(msgStrings["SubmitOK"] % argBook["filename"])

if __name__ == "__main__":        
    main()