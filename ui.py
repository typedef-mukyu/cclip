#!/usr/bin/python3
import os
import csv
import time
import dateutil
import dateutil.parser
from msgstrings import msgStrings

clrscr = lambda: print("\033c\033[3J", end='') # prints escape characters to clear the terminal

# Opens the FIFO between this and the message broker service, writes into it, and closes it
# Using this function ensures the FIFO is not inadvertently left open.
def writeToFifo(msg: str) -> None:
    mbPipe = os.open(".ui_fifo", os.O_WRONLY)
    os.write(mbPipe, str.encode(msg))
    os.close(mbPipe)

# Prepares a message requesting to submit the file at `fileName` to `assignment`.
# This is later sent to the message broker using writeToFifo().
def createSubmitCommand(assignment: dict, fileName: str) -> str:
    return ("submit " + 
            str(assignment["courseId"]) + " " + 
            str(assignment["asgnId"]) + " " + 
            str(fileName))

def waitForFile(fileName: str, delay: float=8) -> None:
    while(1):
        time.sleep(delay)
        if os.path.isfile(fileName): 
            return

def removeFileIfExists(fileName: str) -> None:
    if os.path.exists("output.tsv"):
        os.remove("output.tsv")

# Converts a tab-delimited data file at fileName to a list of dicts corresponding to each row.
# fieldNames contains the key names for each column of data.
def tsvToList(fileName: str, fieldNames: tuple or list) -> list:
    output = list()
    with open(fileName, newline="") as csvFile:
        reader = csv.DictReader(csvFile, fieldnames=fieldNames, delimiter="\t") 
        for row in reader:
            output.append(row)
    return output

def execWithMessage(message: str, execFunction, *args):
    clrscr()
    print(message)
    output = execFunction(*args)
    clrscr()
    return output

# Converts an ISO 8601 UTC time stamp string to the local time of the system.
# For example: convUTCTimeStamp("2024-01-01T00:00:00Z") would return
# "2023-12-31 16:00" on a system set to Pacific Standard Time.
def convUTCTimeStamp(timeStamp: str) -> str:
    if timeStamp == "": 
        return ""
    isoTimeObj = dateutil.parser.parse(timeStamp) # convert the UTC timestamp to a datetime object
    isoTimeObj = isoTimeObj.replace(tzinfo=dateutil.tz.tzutc()) # set the object's time zone to UTC
    isoTimeObj = isoTimeObj.astimezone(dateutil.tz.tzlocal()) # convert the object to local system time
    outputTimeStamp = isoTimeObj.isoformat() # create an ISO 8601 format string from the datetime object
    outputTimeStamp = (outputTimeStamp[:10] + " " + outputTimeStamp[11:16]) # extract only the date and time from the string
    return outputTimeStamp


def submitPrompt(assignment: dict) -> None:
    fileName = ""
    while not os.access(str(fileName), os.R_OK):
        print(msgStrings["FilePrompt"])
        fileName = input("> ")
        if os.access(str(fileName), os.R_OK):
            writeToFifo(createSubmitCommand(assignment, fileName))
            time.sleep(5)
        elif fileName == "" or fileName == None: # no input returns to assignment lists
            return
        else:
            print(msgStrings["FileErr"])
        
def getCourses() -> list[dict]:
    removeFileIfExists("output.tsv")
    writeToFifo("get courses")    
    waitForFile("output.tsv")
    courses = tsvToList("output.tsv", ("courseId", "name", "score", "grade"))
    os.remove("output.tsv")
    return courses

def getAssignments(courseId: int or str) -> list[dict]:
    removeFileIfExists("output.tsv")
    writeToFifo("get assignments "+ str(courseId))
    waitForFile("output.tsv")
    assignments = tsvToList("output.tsv", ("asgnId", "name", "dueDate", "points"))
    for a in assignments:
        a["courseId"] = courseId # this is not shown directly, but is used in the submit() call
    os.remove("output.tsv")
    return assignments

def printAsgnEntries(asgnList: list[dict]) -> None:
    print(" #", msgStrings["Name"].ljust(50), msgStrings["DueDate"].ljust(16), msgStrings["Points"])
    for i in range(len(asgnList)):
        print(str(i + 1).rjust(2), # selection number, padded with spaces to 2 digits and right-aligned
             asgnList[i]["name"][:50].ljust(50), # assignment name, truncated or padded to 50 chars
             convUTCTimeStamp(asgnList[i]["dueDate"]).ljust(16), # due date/time, padded to 16 chars
             # Some assignments will be undated, so padding an empty string keeps alignment in the UI.
             str(asgnList[i]["points"]).rjust(5)) # Points an assignment is worth

# "90" -> "90.00"
def fixTwoDecimals(n: str) -> str:
    if n == "":
        return ""
    else: 
        return ("%.2f" % float(n))

def printCourseEntries(courseList: list[dict]) -> None:
    print(" #", msgStrings["Name"].ljust(60), msgStrings["Score"], msgStrings["Grade"]) # UI header
    for i in range(len(courseList)):
        print(str(i + 1).rjust(2), # 
            courseList[i]["name"][:60].ljust(60), 
            (fixTwoDecimals(courseList[i]["score"])).rjust(6), # The numeric score of a course (e.g., 97.12)
            courseList[i]["grade"]) # The letter grade of a course (A, A-, etc.)

# Prompts until a nonnegative number not higher than maxValue is entered.
def validateInput(inputPrompt: str, errPrompt: str, maxValue: int) -> int:
    while 1:
        buffer = input(inputPrompt % str(maxValue))
        if (not buffer.isnumeric()) or int(buffer) > maxValue:
            print(errPrompt)
        else:
            return int(buffer)

def asgnMenu(courseId: int or str) -> None:
    while 1:
        asgnList = execWithMessage(msgStrings["AsgnLoad"], getAssignments, courseId)
        if len(asgnList) == 0:
            print(msgStrings["NoAsgn"])
            return
        printAsgnEntries(asgnList)
        asgnChoice = validateInput(msgStrings["AsgnPrompt"], msgStrings["BadEntry"], len(asgnList))
        if asgnChoice == 0:
            return
        submitPrompt(asgnList[asgnChoice-1]) # prompts for file to submit to selected assignment
            
def courseMenu() -> None:
    while 1:
        courseList = execWithMessage(msgStrings["CourseLoad"], getCourses) # loading courses message
        if len(courseList) == 0:
            print(msgStrings["NoCourse"])
            exit(0)
        printCourseEntries(courseList)
        courseChoice = validateInput(msgStrings["CoursePrompt"], msgStrings["BadEntry"], len(courseList))
        if courseChoice == 0: # menu choices are one-indexed, 0 exits program
            exit(0)
        asgnMenu(int(courseList[courseChoice - 1]["courseId"])) # shows assignments of selected course

def main():
    courseMenu()

if __name__ == "__main__":        
    main()
