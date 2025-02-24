# Canvas Command-Line Interface Project (CCLIP)

This project allows a user to connect to their Canvas instances over a terminal session, including listing courses and listing and submitting assignments.

## Building

A `Makefile` has been provided to easily build the C++-based message broker service; simply run in the directory:

```bash
make
```

Please note that this service was verified to build properly with GCC's C++ compiler; the use of other compilers is at your own risk.

## Usage

1. Go to your institution's Canvas instance URL (e.g., `https://canvas.instructure.com`), then generate a new access token by going to *Account > Settings > New Access Token*.

2. Start the program by entering `./run.py`. When prompted, enter the Canvas instance URL you accessed in Step 1 and paste the corresponding access token. 

3. You will then be presented with a list of your active courses. Enter the index of the desired course to select it.

4. The program will then load a list of assignments for the selected course, where you can enter its index to submit to an assignment.

5. Enter the path to the file you wish to submit (e.g., `~/cs456/assignment1.pdf`), then press enter to attempt to submit it.

If your submission fails, make sure that:
  - The assignment you are submitting to accepts file upload submissions (and allows the specific file type you are submitting)
  - You are submitting before the assignment's `Available Until` date/time and after the `Available From` date/time if applicable
  - If the assignment only allows a finite number of submissions/attempts, you have not exhausted all of them

## Manual command usage

The program can be used manually by executing some of the Python files with command-line arguments. Make sure to first start the message broker and configuration services before doing this:

```bash
./msgbroker &
./config.py &
```

### Submitting an assignment

To submit an assignment, run:

```bash
./submit.py -c course_id -a assignment_id filename
```

where course_id and assignment_id are the numbers in the assignment page URL after `/courses/` and `/assignments/`, respectively.

### Listing courses

To list all active courses' IDs, names, and grades in a CSV format, run:

```bash
./get_items.py -C
```
 
### Listing assignments for a course

To list all assignments for a given course, with IDs, names, due dates, and values in a CSV format:

```bash
./get_items.py -c course_id -A
```

where `course_id` is as defined in *Submitting an assignment*.

### Redirecting output to a CSV file

Since the `get_items` function outputs in a CSV format, you may wish to save a list of courses or assignments into a file to view them with a spreadsheet program or other CSV viewer. To do this, simply redirect the standard output.

For example, if you want to save a list of a course's assignments, run:

```bash
./get_items.py -c course_id -A > assignments.csv
```

where `course_id` is as defined in *Submitting an assignment*.