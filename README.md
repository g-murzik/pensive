#OVERVIEW

    pensive is a CLI program for organizing knowledge in a wiki similar style.
    Organizing means here to view, edit or remove information without leaving
    the CLI.

#DESCRIPTION

    The overall idea is to manage information with tags like 'pacman',
    'python' or 'python.sqlite3'. As there are different kinds of information
    you might want to use, there are three essential formats used in pensive:

    Format 0: Plain Text, show everything at once, e.g. command reference
    Format 1: Separate entries, which can be opened, e.g. some scripts
    Format 2: Attachments, e.g. URLs, files or other tags

    In pensive, one can create categories, which are linked to these format
    numbers. If there is any information of a tag saved in such a category, 
    it will be displayed in the precise order, in which the categories have
    been installed. If no information is available, a category information of
    a tag will be skipped.

    Categories also determine the way of how you interact with pensive:
    They can be addressed by appropriate upper case letters starting from
    'A' in the pensive shell.

    Please notice that there is a tutorial included, which can be viewed at
    the initial start of the program.

#INSTALLATION

    $ cd pensive
    $ python3 pensive.py

#FILES

    o pensive.py        the program
    o pensive.conf      plain text configuration file
    o pensive.sqlite    sqlite database, which will be created after first start
    o pensive.temp      a plain text dump file for editing that might be created