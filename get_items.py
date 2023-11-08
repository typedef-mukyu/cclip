#!/usr/bin/python3
import requests
import sys
import os
from collections import defaultdict
def parse_args():
    argbook = dict()
    i = 0
    while i < (len(sys.argv) - 1):
        i += 1
        if sys.argv[i] == "-C":
            argbook["list_type"] = "courses"
            continue
        if sys.argv[i] == "-A":
            argbook["list_type"] = "assignments"
            continue
        elif sys.argv[i] == "-c":
            argbook["course"] = sys.argv[i+1]
            i += 1
            continue
        elif sys.argv[i] == "-l":
            argbook["limit"] = sys.argv[i+1]
            i += 1
            continue
        elif sys.argv[i] == "-o":
            argbook["offset"] = sys.argv[i+1]
            i += 1
            continue
        
    return argbook
def get_credbook():
    mbpipe = os.open(".getter_fifo", os.O_WRONLY)
    os.write(mbpipe, str.encode("config get api_url"))
    os.close(mbpipe)

    mbpipe = os.open(".getter_fifo", os.O_RDONLY)
    credbook = {"url": str(os.read(mbpipe, 1023))[2:-1]}
    os.close(mbpipe)

    mbpipe = os.open(".getter_fifo", os.O_WRONLY)
    os.write(mbpipe, str.encode("config get api_key"))
    os.close(mbpipe)

    mbpipe = os.open(".getter_fifo", os.O_RDONLY)
    credbook["key"] = str(os.read(mbpipe, 1023))[2:-1]
    os.close(mbpipe)

    return credbook
def get_courses(credbook, l=20, o = 0):
    get_url = credbook["url"] + "/api/v1/courses"
    response = requests.get(get_url, data={"per_page": l, "offset": o, "enrollment_state": "active", "include[]": ("total_scores",)}, headers={"Authorization": ("Bearer " + credbook["key"])})
    response.raise_for_status()

    courses = response.json()
    for c in courses:
        print("" if c["id"] is None else c["id"], ","
            , "" if c["course_code"] is None else c["course_code"], "," 
            , "" if ("computed_current_score" not in c["enrollments"][0]) or (c["enrollments"][0]["computed_current_score"] is None) else c["enrollments"][0]["computed_current_score"] , "," 
            , "" if ("computed_current_grade" not in c["enrollments"][0]) or (c["enrollments"][0]["computed_current_grade"] is None) else c["enrollments"][0]["computed_current_grade"] , sep="")
def get_assignments(credbook, courseid, l = 20, o = 0):
    get_url = credbook["url"] + "/api/v1/courses/" + str(courseid) + "/assignments"
    response = requests.get(get_url, data={"per_page": l, "offset": o}, headers={"Authorization": ("Bearer " + credbook["key"])})
    response.raise_for_status()
    assignments = response.json()
    for a in assignments:
        print("" if a["id"] is None else a["id"], ","
            , "" if a["name"] is None else a["name"], "," 
            , "" if a["due_at"] is None else a["due_at"], "," 
            , "" if a["points_possible"] is None else a["points_possible"] , sep="")
def main():
    argbook = parse_args()
    credbook = get_credbook()

    if "list_type" in argbook:
        
        if argbook["list_type"] == "courses":
            get_courses(credbook, l = int(argbook["limit"]) if "limit" in argbook else None, o = int(argbook["offset"]) if "offset" in argbook else None)
        elif argbook["list_type"] == "assignments" and "course" in argbook:
            get_assignments(credbook, argbook["course"], l = argbook["limit"] if "limit" in argbook else None, o = argbook["offset"] if "offset" in argbook else None)
        else:
            print("Usage: " + sys.argv[0] + " -C|{-c course_id -A} -l limit -o offset", file=sys.stderr)
            exit(1)
    else:
        print("Usage: " + sys.argv[0] + " -C|{-c course_id -A} -l limit -o offset", file=sys.stderr)
        exit(1)
main()


