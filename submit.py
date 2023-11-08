#!/usr/bin/python3
import requests
import sys
import os
from http.client import responses
#import json
def get_credbook():
    mbpipe = os.open(".submit_fifo", os.O_WRONLY)
    os.write(mbpipe, str.encode("config get api_url"))
    os.close(mbpipe)

    mbpipe = os.open(".submit_fifo", os.O_RDONLY)
    credbook = {"url": str(os.read(mbpipe, 1023))[2:-1]}
    os.close(mbpipe)

    mbpipe = os.open(".submit_fifo", os.O_WRONLY)
    os.write(mbpipe, str.encode("config get api_key"))
    os.close(mbpipe)

    mbpipe = os.open(".submit_fifo", os.O_RDONLY)
    credbook["key"] = str(os.read(mbpipe, 1023))[2:-1]
    os.close(mbpipe)

    return credbook
def get_upload_token(credbook, argbook):
    if not os.path.isfile(argbook["filename"]): # verify the filename
        raise ValueError("Invalid filename")
    form_flags = {"name": os.path.basename(argbook["filename"]), "size": str(os.path.getsize(argbook["filename"]))}
    post_url = (credbook["url"] + "/api/v1/courses/" + argbook["course"] + "/assignments/" + argbook["assignment"] + "/submissions/self/files")
    response = requests.post(post_url, data=form_flags, headers={"Authorization": "Bearer " + credbook["key"]}) # request the bucket to upload to
    if response.status_code > 399:
        print("Upload request failed.", response.status_code, responses[response.status_code])
        exit(1)
    return response
def upload_file(credbook, argbook, token):
    token_dict = token.json()
    form_flags = token_dict["upload_params"]
    subfile = open(argbook["filename"], "rb")
    response = requests.post(token_dict["upload_url"], data=form_flags, files={"file": subfile})
    subfile.close()

    #if response.status_code == 301:
    response.raise_for_status()
    location = response.headers["Location"]
    response = requests.get(location, headers={"Content-Length": "0", "Authorization": "Bearer " + credbook["key"]})
    #response.raise_for_status()
    if response.status_code > 399:
        print("File upload failed.", response.status_code, responses[response.status_code])
        exit(2)
    return response
def submit(credbook, file_id):
    post_url = (credbook["url"] + "/api/v1/courses/" + argbook["course"] + "/assignments/" + argbook["assignment"] + "/submissions")
    response = requests.post(post_url, params=os.path.basename(argbook["filename"]), data={"submission[submission_type]": "online_upload", "submission[file_ids][]": [file_id]}, headers={"Authorization": ("Bearer " + credbook["key"])})
    # response.raise_for_status()
    if response.status_code > 399:
        print("Canvas submission failed.", response.status_code, responses[response.status_code])
        exit(3)
    return response
def parse_args():
    argbook = dict()
    i = 0
    while i < (len(sys.argv) - 1):
        i += 1
        if sys.argv[i] == "-c":
            argbook["course"] = sys.argv[i+1]
            i += 1
            continue
        elif sys.argv[i] == "-a":
            argbook["assignment"] = sys.argv[i+1]
            i += 1
            continue
        else:
            argbook["filename"] = sys.argv[i]
            continue
    return argbook

credbook = get_credbook()
argbook = parse_args()
if len(argbook) < 3:
    print("Usage: ./submit -c courseid -a assignmentid filename")
    exit()
token = get_upload_token(credbook, argbook)
token.raise_for_status()
ulstat = upload_file(credbook, argbook, token)
file_id = int(ulstat.json()["id"])
sstat = submit(credbook, file_id)

if sstat.status_code == 201:
    print(argbook["filename"] + " submitted successfully")
