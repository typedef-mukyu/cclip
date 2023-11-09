# Canvas Command-Line Interface Project (CCLIP)
This project allows a user to connect to their Canvas instances over a terminal session, including listing courses and listing and submitting assignments.
## Building
Simply run `make` on the provided `Makefile` to build the files needed.
## Usage
Start the program by entering `./run.py`. You will then be prompted to enter the URL to your Canvas site. (e.g., `https://canvas.instructure.com`). Then, generate an access token from `Account` > `Settings` > `New Access Token`. You will then be presented with a list of your active courses, with the left column indicating the number you must enter to access it. The program will then load a list of assignments for the selected course, where you can enter its index to start a submission. Enter the path of what you want to submit (relative paths are supported) and press enter. Note that the submission will fail if you wouldn't be able to submit your file on the Canvas website (e.g., not a file-upload assignment, against filetype restrictions, past "available until" date, exceeded attempt limit)
## Manual command usage
The program can be used manually by executing some of the Python files with command-line arguments. Make sure to first start the message broker (`./msgbroker`) before doing this:
### Submitting an assignment
`./submit.py -c course_id -a assignment_id filename`
where course_id and assignment_id are the numbers in the assignment page URL after `/courses/` and `/assignments/`, respectively.
### Listing courses
`./get_items.py -C`
This will list all active courses' IDs, names, and grades in a CSV format. You may wish to redirect stdout to a .csv file here.
### Listing assignments for a course
`./get_items.py -c course_id -A`
This will list all assignments for the given course, with IDs, names, due dates, and values in a CSV format. `course_id` is as defined in *Submitting an assignment*. You may wish to redirect stdout to a .csv file here.