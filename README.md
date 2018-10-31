Wasnnu
======

From the german expression "Was 'n nu?" - "what's next?".

The most minimalistic time tracking software.

Please keep in mind that I wrote this tool
for personal use. It is not clean, it is not nice
to use but it keeps track of your damn time.

Want to know how many hours you spent on that damn
task yet?
Love plain text files?
Wasnnu might just be what you want.

Installing
----------

To install wasnnu enter the commands below and
hope for the best:

    $ sudo apt install python3-rfc3339

    $ sudo cp wasnnu.py /usr/local/bin/wasnnu
    $ sudo chmod +x /usr/local/bin/wasnnu

Setup
-----

You will most likely want to use `git` to manage
your timetables to keep them synchronized and
minimize damage, should wasnnu decide to eat your data.

This is how you setup up a test project:

    $ mkdir -p "Wasnnus/test 1"
    $ cd Wasnnus
    $ git init
    Initialized empty Git repository in Wasnnus/.git/

    $ cd "test 1"
    $ wasnnu init
    Timezone [Europe/Berlin]:
    Description [None]: A test project

    $ git add -A
    $ git commit -m "New"
    [master (root-commit) e558d74] New
    1 file changed, 3 insertions(+)
    create mode 100644 test 1/timetable

Usage
-----

Wasnnu comes with a few subcommands that
operate on a `timetable` file in the current directory.

- `wasnnu init` - sets up an empty timetable file (as seen above)
- `wasnnu in` - start a new session
- `wasnnu out <comment>` - end a session and add a comment of what you did
- `wasnnu total` - the total time logged
- `wasnnu days` - output a summary of the hours worked.

The example below shows these commands in action:

    $ cd "Wasnnus/test 1"

    $ wasnnu in
    $ cat timetable
    Description: A test project
    TimeZone: Europe/Berlin

    # 2017 2 21 Tuesday
    Start: 2017-02-21T14:55:31+01:00
    UUID: a9bc1642-acb3-4299-92dc-f1ec715f1661

    $ wasnnu out "Github demo"
    $ cat timetable
    Description: A test project
    TimeZone: Europe/Berlin

    # 2017 2 21 Tuesday
    Start: 2017-02-21T14:55:31+01:00
    End: 2017-02-21T14:56:16+01:00
    Description: Github demo
    UUID: a9bc1642-acb3-4299-92dc-f1ec715f1661

    $ wasnnu days
    2017 2 21 Tuesday: 0:00:45
    month 2: 00:00:45

    Total time spent: 00:00:45

    $ wasnnu total
    Total time spent: 00:00:45

That was it, no magic involved.
