#!/usr/bin/python3
import os
import sys
from collections import defaultdict
import csv
import time
import dateutil
import dateutil.parser
clrscr = lambda: print("\033c\033[3J", end='')
class course:
    course_id = None
    name = ""
    score = ""
    grade = ""
    assignments = list()
def convUTCTimeStamp(ts):
    if ts == "":
        return ""
    it = dateutil.parser.parse(ts)
    it = it.replace(tzinfo=dateutil.tz.tzutc())
    isots = it.astimezone(dateutil.tz.tzlocal()).isoformat()
    ots = (isots[:10] + " " + isots[11:16])
    return (ots)

def submit_prompt(assignment):
    buffer = ""
    while not os.access(str(buffer), os.R_OK):
        print("Please enter the path to the file you want to submit, or press Enter to cancel")
        buffer = input("> ")
        if os.access(str(buffer), os.R_OK):
            mbpipe = os.open(".ui_fifo", os.O_WRONLY)
            os.write(mbpipe, str.encode("submit " + str(assignment["course_id"]) + " " + str(assignment["asgn_id"]) + " " + str(buffer)))
            os.close(mbpipe)
            time.sleep(5)
        elif buffer == "" or buffer == None:
            return
        else:
            print("The selected file could not be read. Please try another file.")
        



def get_courses():
    mbpipe = os.open(".ui_fifo", os.O_WRONLY)
    line = ""
    if os.path.exists("output.csv"):
        os.remove("output.csv")
    os.write(mbpipe, str.encode("get courses 100 0"))
    os.close(mbpipe)
    while 1:
        courses = list()
        time.sleep(5)
        if os.path.isfile("output.csv"): #I'd use a do-while loop here, but there is no such thing in Python.
            break
    with open("output.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames = ("course_id", "name", "score", "grade"))
        for row in reader:
            courses.append(row)
    return courses


def get_assignments(course_id):
    mbpipe = os.open(".ui_fifo", os.O_WRONLY)
    line = ""
    if os.path.exists("output.csv"):
        os.remove("output.csv")
    os.write(mbpipe, str.encode("get assignments "+ str(course_id) +" 100 0"))
    os.close(mbpipe)
    while 1:
        assignments = list()
        time.sleep(5)
        if os.path.isfile("output.csv"): #I'd use a do-while loop here, but there is no such thing in Python.
            break
    with open("output.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames = ("asgn_id", "name", "duedate", "points"))
        for row in reader:
            row["course_id"] = course_id
            assignments.append(row)
    return assignments
def asgn_menu(course_id):
    while 1:
        clrscr()
        print("Loading assignments, please wait...")
        asgn_list = get_assignments(course_id)
        clrscr()
        if len(asgn_list) == 0:
            print("No assignments are available for this course.")
            return
        print(" #", "Name".ljust(50), "Due Date".ljust(16), "Pts")
        for i in range(len(asgn_list)):
            print(str(i + 1).rjust(2), asgn_list[i]["name"][:50].ljust(50), convUTCTimeStamp(asgn_list[i]["duedate"]).ljust(16), str(asgn_list[i]["points"]).rjust(5))
        while 1:
            buffer = input("\nPlease enter an assignment number 1 ~ " + str(len(asgn_list)) + ", or 0 to return to the course menu > ")
            if (not buffer.isnumeric()) or int(buffer) > len(asgn_list):
                print("Invalid entry, please try again.")
            elif int(buffer) == 0:
                return
            else:
                break
        submit_prompt(asgn_list[i-1])
            
        

def course_menu():
    while 1:
        clrscr()
        print("Loading courses, please wait...")
        course_list = get_courses()
        clrscr()
        if len(course_list) == 0:
            print("You are not enrolled in any active courses. Exiting...")
            exit(0)
        print(" #", "Name".ljust(60), "Score", "Grade")
        for i in range(len(course_list)):
            print(str(i + 1).rjust(2), course_list[i]["name"][:60].ljust(60), ("" if course_list[i]["score"] == "" else ("%.2f" % float(course_list[i]["score"]))).rjust(6), course_list[i]["grade"])
        while 1:
            buffer = input("\nPlease enter a course number 1 ~ " + str(len(course_list)) + ", or 0 to exit > ")
            if (not buffer.isnumeric()) or int(buffer) > len(course_list):
                print("Invalid entry, please try again.")
            elif int(buffer) == 0:
                exit(0)
            else:
                break
        asgn_menu(int(course_list[int(buffer)-1]["course_id"]))

        
        
course_menu()
