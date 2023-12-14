#!/usr/bin/python3
import requests
import sys
import os

def parseArgs() -> dict:
    listTypeArgs = {"-C": "courses", "-A": "assignments"} # Arguments dictating what the program will output
    paramArgs = {"-c": "course", "-l": "limit", "-o": "offset"} # Parameter arguments followed by values
    argbook = dict()
    i = 0
    while i < (len(sys.argv) - 1):
        i += 1
        if sys.argv[i] in listTypeArgs:
            argbook["list_type"] = listTypeArgs[sys.argv[i]]
        elif sys.argv[i] in paramArgs:
            argbook[paramArgs[sys.argv[i]]] = sys.argv[i + 1]
            i += 1
    return argbook

# Requests a configuration value from the message broker, which forwards the request to config.py.
def getConfigItem(setting: str) -> str: 
    mbpipe = os.open(".getter_fifo", os.O_WRONLY)
    os.write(mbpipe, str.encode("config get " + setting))
    os.close(mbpipe)
    mbpipe = os.open(".getter_fifo", os.O_RDONLY)
    # the [2:-1] strips the b'value' wrapping Python uses when reading bytes objects
    value = str(os.read(mbpipe, 1023))[2:-1] 
    os.close(mbpipe)
    return value

# Returns an empty string if a value in a dict does not exist or is None.
def noneAndDNEToEmptyStr(obj: dict, key):
    if (key not in obj) or (obj[key] is None):
        return ""
    else:
        return obj[key]

# Requests the user's credentials from the message broker.
def getCredbook() -> dict:
    credbook = dict()
    credbook["url"] = getConfigItem("api_url")
    credbook["key"] = getConfigItem("api_key")
    return credbook

def printCourses(courses: list) -> None:
    infoKeys = ("id", "course_code")
    gradeKeys = ("computed_current_score", "computed_current_grade")
    for course in courses:
        for key in infoKeys:
            print(noneAndDNEToEmptyStr(course, key), end="\t")
        for key in gradeKeys:
            print(noneAndDNEToEmptyStr(course["enrollments"][0], key), 
            end="\n" if key == gradeKeys[-1] else "\t")

def printAssignments(assignments: list) -> None:
    keys = ("id", "name", "due_at", "points_possible")
    for assignment in assignments:
        for key in keys:
            print(noneAndDNEToEmptyStr(assignment, key), 
            end="\n" if key == keys[-1] else "\t")

# Prints up to <limit> courses that the user identified by <credbook> is
# enrolled in, starting <offset> courses after the first one.
def get_courses(credbook: dict, limit: int, offset: int) -> None:
    get_url = credbook["url"] + "/api/v1/courses"
    rqData = {"per_page": limit, "offset": offset, 
        "enrollment_state": "active", "include[]": ("total_scores",)}
    rqHeaders = {"Authorization": ("Bearer " + credbook["key"])}
    response = requests.get(get_url, data=rqData, headers=rqHeaders)
    response.raise_for_status() # this throws an exception for an HTTP 4xx or 5xx code
    courses = response.json() # converts HTTP response JSON to a list
    printCourses(courses)

# Prints up to <limit> assignments that the user identified by <credbook> has
# in course <courseid>, starting <offset> assignments after the first one.
def get_assignments(credbook: dict, courseid, limit: int, offset: int) -> None:
    get_url = credbook["url"] + "/api/v1/courses/" + str(courseid) + "/assignments"
    rqData = {"per_page": limit, "offset": offset}
    rqHeaders = {"Authorization": ("Bearer " + credbook["key"])}
    response = requests.get(get_url, data=rqData, headers=rqHeaders)
    response.raise_for_status() # this throws an exception for an HTTP 4xx or 5xx code
    assignments = response.json() # converts HTTP response JSON to a list
    printAssignments(assignments)

def executeQuery(credbook: dict, argbook: dict) -> None:
    limit = int(argbook["limit"]) if "limit" in argbook else 100
    offset = int(argbook["offset"]) if "offset" in argbook else 0
    if argbook["list_type"] == "courses":
        get_courses(credbook, limit, offset)
    elif argbook["list_type"] == "assignments" and "course" in argbook:
        get_assignments(credbook, argbook["course"], limit, offset)
    else:
        badArgsErr()

def badArgsErr() -> None:
    print("Usage: " + sys.argv[0] + " -C|{-c course_id -A} -l limit -o offset", file=sys.stderr)
    exit(1)

def main():
    argbook = parseArgs()
    credbook = getCredbook()
    if "list_type" in argbook:
        executeQuery(credbook, argbook)
    else:
        badArgsErr()
main()


