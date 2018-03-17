## OVERVIEW

Pensive is a CLI program for organizing knowledge similar to a wiki.
In this tool organization means to view, edit or remove information without leaving
the CLI.

## DESCRIPTION

The overall idea is to manage information with tags like 'pacman',
'python' or 'python.sqlite3'. As there are different types of information
you might want to use, three essential formats are employed in pensive:

    Format 0: Plain text, shows everything at once, e.g. command references
    Format 1: Separate entries which can be unfolded, e.g. some scripts
    Format 2: Attachments, e.g. URLs, files or other tags

In pensive, one can create categories which are linked to the mentioned format
numbers. In case any information about a specific tag is saved in a category, 
it will be displayed in the precise order, in which the categories have
been installed.

Categories also determine the way one interacts with pensive:
They can be addressed by appropriate upper case letters starting from
'A' in the pensive shell.

Please note that there is a tutorial included, which can be viewed at
the initial start of the program.

## INSTALLATION

    git clone https://github.com/g-murzik/pensive

## USAGE

    cd pensive
    python3 pensive.py

## FILES

    o pensive.py        the program
    o pensive.conf      plain text configuration file
    o pensive.sqlite    sqlite database, which will be created at the first start
    o pensive.temp      a plain text dump file for editing that might be created
    o LICENSE           GPLv3

## SCREENSHOTS
### Help view
![Figure 4](https://github.com/g-murzik/miscellaneous/blob/master/pensive04.png "help")
### Format 0 example - plain text
![Figure 1](https://github.com/g-murzik/miscellaneous/blob/master/pensive01.png "Format 0")
### Format 1 example - separate entries
![Figure 2](https://github.com/g-murzik/miscellaneous/blob/master/pensive02.png "Format 1")
### Format 2 example - attachments
![Figure 3](https://github.com/g-murzik/miscellaneous/blob/master/pensive03.png "Format 2")
