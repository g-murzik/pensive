"""
    pensive is a CLI program for organizing knowledge in a wiki similar style.
    Copyright (C) 2015 Georg Alexander Murzik (murzik@mailbox.org)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import os
import os.path
import sys
import time
import subprocess
import shutil
import sqlite3
from string import ascii_letters, digits

# global variables
HOME = subprocess.getoutput('echo $HOME')
TERMINAL_WIDTH = shutil.get_terminal_size()[0]
BLUE = '\033[94m'
RED = '\033[31m'
DEL_COLOR = '\033[0m'

def display_help():
    """Print help."""
    print("""basic functions:
    add TAG [TAG2]      - add tag(s)
    rm TAG [TAG2]       - remove tag(s) with all its entries
    mv TAG1 TAG2        - rename TAG1 as TAG2
    ls [*PAT*ERN*]      - list all tags [matching * globbed pattern]
    ?TAG                - query tag, activates tag mode
    ??PATTERN           - search for pattern in all tags and their entries

additional tag mode functions:
    A                   - show result of the 1st category
    B0                  - open entry/attachment of a category (format 1, 2)
    *A                  - edit or create entry of a category (format 0)
    *B0                 - edit or create entry of a category (format 1, 2)
    -A                  - remove existing entry (format 0)
    -B0                 - remove existing entry (format 1, 2)
    mv A E              - move entry to category with equal format
    mv B0 F             - move entry to category with equal format
    mv B0 F@TAG         - move entry to category with equal format of TAG

manage pensive functions:
    category show       - show all defined categories
    category add NAME 0 - add category NAME with the formatting 0 to pensive
    category rm NAME    - remove the category NAME from pensive
    category mv OLD NEW - renames a category from OLDNAME to NEWNAME
    backup [NAME]       - backup pensive's current state [as NAME]
    restore             - restore pensive by choosing backup out of a list
    export              - export each tag with its entries to a plain text file
    """)


def display_license():
    """Open license with grep or browser"""
    if os.path.exists('LICENSE'):
        os.system('cat LICENSE | less')
    else:
        URL = 'http://www.gnu.org/licenses/gpl.txt'
        os.system('%s %s > /dev/null 2>&1 &' % (BROWSER, URL))


def get_configuration():
    global DB, BACKUPDIR, EXPORTDIR, EDITOR, BROWSER, HIGHLIGHT_TAGS, FORM2MODE
    DB = 'pensive.sqlite'
    BACKUPDIR = 'backups'
    EXPORTDIR = 'exports'
    EDITOR = 'vi'
    BROWSER = 'firefox'
    HIGHLIGHT_TAGS = True
    FORM2MODE = 0

    red_error = RED + "Error:" + DEL_COLOR
    if os.path.exists('pensive.conf'):
        fin = open('pensive.conf')
        with fin:
            for line in fin:
                line = line.strip()
                if line.startswith('DB = ') and line.endswith('.sqlite'):
                    DB = line.split('DB = ')[1]
                elif line.startswith('BACKUPDIR = '):
                    BACKUPDIR = line.split('BACKUPDIR = ')[1]
                elif line.startswith('EXPORTDIR = '):
                    EXPORTDIR = line.split('EXPORTDIR = ')[1]
                elif line.startswith('EDITOR = '):
                    EDITOR = line.split('EDITOR = ')[1]
                elif line.startswith('BROWSER = '):
                    BROWSER = line.split('BROWSER = ')[1]
                elif line.startswith('HIGHLIGHT_TAGS = '):
                    line = line.split('HIGHLIGHT_TAGS = ')[1]
                    if line == 'True' or line == 'False':
                        HIGHLIGHT_TAGS = line
                    else:
                        print(
                            "%s Invalid configuration of HIGHLIGHT_TAGS. "
                            "Using fallback value True instead.\n" % red_error)
                        HIGHLIGHT_TAGS = True
                elif line.startswith('FORM2MODE = '):
                    line = line.split('FORM2MODE = ')[1]
                    if line == '0' or line == '1':
                        FORM2MODE = line
                    else:
                        print(
                            "%s Invalid configuration of FORM2MODE. "
                            "Using fallback value 0 instead.\n" % red_error)
                        FORM2MODE = 0
    else:
        print(
            "%s Configuration file doesn't exist. "
            "Using fallack values.\n" % red_error)


def get_categories():
    """Retrieves defined categories from pensive.sqlite and writes them to
    global variable catconf = [(categoryname, categoryformatid, categoryid)].
    """
    global catconf
    catconf = []
    query = 'SELECT * FROM pensive_conf'
    cursor.execute(query)
    result = cursor.fetchall()
    for catid, category, catformatid in result:
        catconf.append((category, int(catformatid), int(catid)))


def display_categories():
    """Print defined categories."""
    print('defined categories:')
    for category, catformatid, catid in catconf:
        print("    %s = %s (%s)" % (chr(65 + catid), category, catformatid))


def add_category_format0(category):
    """Expects a string and adds it as a new category with format 0."""
    sql_insert = (len(catconf), category, 0)
    cursor.execute("INSERT INTO pensive_conf VALUES(?, ?, ?)", sql_insert)
    query = (
        "CREATE TABLE %s( "
        "tag TEXT, "
        "description TEXT, "
        "UNIQUE(tag), "
        "FOREIGN KEY(tag) REFERENCES pensive_tags)" % category)
    cursor.execute(query)
    con.commit()
    get_categories()


def add_category_format1(category):
    """Expects a string and adds it as a new category with format 1."""
    sql_insert = (len(catconf), category, 1)
    cursor.execute("INSERT INTO pensive_conf VALUES(?, ?, ?)", sql_insert)
    query = (
        "CREATE TABLE %s( "
        "tag TEXT, "
        "posnr INTEGER, "
        "title TEXT, "
        "description TEXT, "
        "PRIMARY KEY(tag, title, description), "
        "FOREIGN KEY(tag) REFERENCES pensive_tags)" % category)
    cursor.execute(query)
    con.commit()
    get_categories()


def add_category_format2(category):
    """Expects a string and adds it as a new category with format 2."""
    sql_insert = (len(catconf), category, 2)
    cursor.execute("INSERT INTO pensive_conf VALUES(?, ?, ?)", sql_insert)
    query = (
        "CREATE TABLE %s( "
        "tag TEXT, "
        "posnr INTEGER, "
        "title TEXT, "
        "description TEXT, "
        "attachment TEXT, "
        "PRIMARY KEY(tag, title, description, attachment), "
        "FOREIGN KEY(tag) REFERENCES pensive_tags)" % category)
    cursor.execute(query)
    con.commit()
    get_categories()


def remove_category(category):
    """Expects a defined category (string) removes it with all its entries. In
    this process, pensive_conf will be recreated in order to close possible
    gaps in the column catid and therefore ensure, that one can interact with
    categories normally."""
    cursor.execute("DROP TABLE %s" % category)
    cursor.execute("DELETE FROM pensive_conf WHERE category = '%s'" % category)
    get_categories()
    cursor.execute("DROP TABLE pensive_conf")
    cursor.execute((
        "CREATE TABLE pensive_conf( "
        "catid INT, "
        "category TEXT, "
        "catformatid INT, "
        "PRIMARY KEY(catid))"))
    for i, (category, catformatid, *__) in enumerate(catconf):
        sql_insert = (i, category, catformatid)
        cursor.execute("INSERT INTO pensive_conf VALUES(?, ?, ?)", sql_insert)
    con.commit()
    get_categories()


def rename_category(old_category, new_category):
    """Renames a existing category name to a new, unused one."""
    query = (
        "UPDATE pensive_conf "
        "SET category = '%s' "
        "WHERE category = '%s'" % (new_category, old_category))
    cursor.execute(query)
    query = "ALTER TABLE %s RENAME TO %s" % (old_category, new_category)
    cursor.execute(query)
    con.commit()
    get_categories()


def get_tags():
    """Retrieves defined tags from pensive.sqlite and writes them to the
    global list defined_tags."""
    global defined_tags
    defined_tags = []
    cursor.execute("SELECT tag FROM pensive_tags")
    result = cursor.fetchall()
    for tag, *__ in result:
        defined_tags.append(tag)
    defined_tags.sort()


def display_tags():
    """Print defined_tags ins rows."""
    global TERMINAL_WIDTH
    TERMINAL_WIDTH = terminalwidth = shutil.get_terminal_size()[0]
    print('tags:')
    lines = ['']
    i = 0
    for tag in defined_tags:
        if len(lines[i] + ' ' + tag) < TERMINAL_WIDTH - 4:
            if lines[i] != '':
                lines[i] = '{old}{new}'.format(old=lines[i], new=' '+tag)
            else:
                lines[i] = '{old}{new}'.format(old=lines[i], new=tag)
        else:
            i += 1
            lines.append(tag)
    for line in lines:
        print('   ', line)


def get_specific_tags(pattern):
    """Filter all defined tags, which match the globbed pattern containing '*'.
    A given string like '*a*t*a' and would return pasta, if its within
    defined_tags. The gerneral idea is to seperate the pattern by '*' and to
    search for the slices in the right order in each tag."""
    slices = pattern.split('*')
    matching_tags = []
    for tag in defined_tags:
        slices_found = 0
        last_pos = 0
        for slice in slices:
            start_pos = last_pos + 0
            end_pos = last_pos + len(slice)
            i = 0
            while end_pos <= len(tag):
                if tag[start_pos:end_pos] == slice:
                    slices_found += 1
                    last_pos = end_pos
                    break
                i += 1
                start_pos += 1
                end_pos += 1
        if slices_found == len(slices):
            cond0 = pattern.startswith('*') and tag.endswith(slices[len(slices)-1])
            cond1 = pattern.endswith('*') and tag.startswith(slices[0])
            cond2 = tag.startswith(slices[0]) and tag.endswith(slices[-1])
            if ((cond0 and not cond1) or (not cond0 and cond1) or
                    (cond0 and cond1) or (cond2)):
                matching_tags.append(tag)
    return matching_tags


def display_specific_tags(pattern):
    """Print all defined tags, which match the globbed pattern containing '*'s
    (case sensitive)."""
    print('tags:')
    matching_tags = get_specific_tags(pattern)
    if matching_tags:
        for tag in matching_tags:
            print('   ', tag)


def add_tag_to_db(tag):
    """Adds a tag to pensive if not existing."""
    tag = (tag,)
    # deleate unwanted spaces
    if tag[0] == ' ':
        tag = tag[1:]
    if tag[-1] == ' ':
        tag = tag[:-1]
    if tag not in defined_tags:
        cursor.execute("INSERT INTO pensive_tags(tag) VALUES(?);", tag)
        con.commit()
        get_tags()


def remove_tag_from_db(tag):
    """Removes a tag with all its entries from pensive if existing."""
    if ask_yes_no(name=tag, mode=0):
        for category, *__ in catconf:
            query = "DELETE FROM %s WHERE tag = '%s'" % (category, tag)
            cursor.execute(query)
        query = "DELETE FROM pensive_tags WHERE tag = '%s'" % tag
        cursor.execute(query)
        con.commit()
        get_tags()
    else:
        print('Nothing changed.')


def rename_tag(oldtag, newtag):
    """Renames a tag."""
    if newtag not in defined_tags:
        query = "UPDATE pensive_tags SET tag = '%s' WHERE tag = '%s'" % (
            newtag, oldtag)
        cursor.execute(query)
        for category, *__ in catconf:
            query = "UPDATE %s SET tag = '%s' WHERE tag = '%s'" % (
                category, newtag, oldtag)
            cursor.execute(query)
        con.commit()
        get_tags()
    else:
        print("Can't rename %s to %s: %s is already defined." % (
            oldtag, newtag, newtag))


def get_overview(tag):
    """Retrievs all information about a tag and stores the number of hits in
    the global variable tag_results like this:
    [(category, catformatid, number_of_hits)]"""
    global tag_results
    tag_results = []
    for category, catformatid, *__ in catconf:
        query = "SELECT * FROM %s WHERE tag = '%s'" % (category, tag)
        cursor.execute(query)
        tag_results.append((category, catformatid, len(cursor.fetchall())))


def display_overview(tag):
    """Prints all entries of a tag in accordance to display_overview()."""
    get_overview(tag)
    for category, catformatid, hits in tag_results:
        if hits > 0:
            if catformatid == 0:
                show_results_form_0(category, tag)
            elif catformatid == 1:
                show_results_form_1(category, tag)
            elif catformatid == 2:
                show_results_form_2(category, tag)


def show_results_form_0(category, tag):
    """Displays results of entries with format 0"""
    query = "SELECT description FROM %s WHERE tag = '%s'" % (category, tag)
    cursor.execute(query)
    result = cursor.fetchall()
    if result:
        result = result[0][0]
        lines = result.split('\n')
        print('%s:' % category)
        if HIGHLIGHT_TAGS:
            [print('   ', highlight_by_known_tags(line)) for line in lines]
        else:
            [print('   ', line) for line in lines]
    else:
        print('%s:\n' % category)


def show_results_form_1(category, tag):
    """Displays results of entries with format 1."""
    query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (category, tag)
    cursor.execute(query)
    result = cursor.fetchall()
    if result:
        print('%s:' % category)
        for i, (*__, title, __) in enumerate(result):
            if i >= 10:
                print('   [%i] %s' % (i, title))
            else:
                print('    [%i] %s' % (i, title))
        print()


def show_results_form_2(category, tag):
    """Displays results of entries with format 2."""
    query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (category, tag)
    cursor.execute(query)
    result = cursor.fetchall()
    print('%s:' % category)
    for i, (*__, title, description, attachment) in enumerate(result):
        # add description if existing
        if description != '':
            description = ' - %s' % description
        else:
            description = ''

        # guess type and existance of attachment
        attachment_type = ''
        attachment_exists = None
        if '://' not in attachment and '/' in attachment:
            attachment_type = 'File'
            if os.path.exists(attachment) or (attachment.startswith('~/') and
                    os.path.exists(HOME + attachment[1:])):
                attachment_exists = True
            else:
                attachment_exists = False
        elif '://' not in attachment and '/' not in attachment:
            attachment_type = 'Tag'
            if attachment in defined_tags:
                attachment_exists = True
            elif attachment[:-1] in defined_tags and attachment.endswith('.'):
                attachment_exists = True
            else:
                attachment_exists = False
        else:
            attachment_type = 'URL'
            attachment_exists = True

        # print title and attachment in seperate lines
        if FORM2MODE == 0:
            attachment_blue = BLUE + '        ' + attachment + DEL_COLOR
            attachment_red = RED + '        ' + attachment + DEL_COLOR
            if i >= 10:
                print('   [%i] %s%s' % (i, title, description))
            else:
                print('    [%i] %s%s' % (i, title, description))
            if attachment_exists:
                print(attachment_blue)
            else:
                print(attachment_red)

        # print everything in one line
        elif FORM2MODE == 1:
            attachment_blue = BLUE + '√' + DEL_COLOR + '] %s%s' % (
                title, description)
            attachment_red = RED + 'X' + DEL_COLOR + '] %s%s' % (
                title, description)
            attachment_URL = BLUE + '→' + DEL_COLOR + '] %s%s' % (
                title, description)
            if 1 >= 10:
                index = '   [%s|' % i
            else:
                index = '    [%s|' % i
            if attachment_exists:
                if attachment_type is 'URL':
                    print(index, attachment_URL, sep='')
                else:
                    print(index, attachment_blue, sep='')
            else:
                print(index, attachment_red, sep='')
    print()


def show_single_entry_form_1(category, tag, entry_nr):
    """Displays single entry with format 1."""
    query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (category, tag)
    cursor.execute(query)
    result = cursor.fetchall()
    if result:
        title = result[entry_nr][2]
        description = result[entry_nr][3]
        lines = description.split('\n')
        print('%s:' % title)
        if HIGHLIGHT_TAGS:
            [print('   ', highlight_by_known_tags(line)) for line in lines]
        else:
            [print('   ', line) for line in lines]
        print()


def open_attachment_form_2(category, tag, entry_nr):
    """Opens a single attachment of format 2."""
    query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (category, tag)
    cursor.execute(query)
    result = cursor.fetchall()
    if result:
        attachment = result[entry_nr][4]
        # escape spaces if present
        if ' ' in attachment:
            attachment = attachment.split(' ')
            attachment = '\ '.join(attachment)
        # open attachment
        if '://' in attachment:
            attachment = '%s %s > /dev/null 2>&1 &' % (BROWSER, attachment)
            os.system(attachment)
        elif '://' not in attachment and '/' in attachment:
            attachment = 'xdg-open %s > /dev/null 2>&1 &' % attachment
            os.system(attachment)
        else:
            if attachment in defined_tags:
                os.system('clear')
                get_overview(attachment)
                pensive_shell(attachment)
            elif attachment[:-1] in defined_tags and attachment.endswith('.'):
                os.system('clear')
                display_specific_tags(attachment)
            else:
                print(
                    "Tag '%s' is not defined yet. "
                    "How about adding it with 'add %s'?" % (
                        attachment, attachment))
                pensive_shell(tag)


def edit_and_update_form_0(category, tag):
    """Edite entry with format 0 with EDITOR and save updates, if any."""
    temp_file = str(os.getcwd()) + '/pensive.temp'
    query = "SELECT description FROM %s WHERE tag = '%s'" % (category, tag)
    cursor.execute(query)
    result = cursor.fetchall()
    if result:
        old_description = result[0][0]
    else:
        old_description = ''

    # paste into temp file and call editor
    fout = open(temp_file, mode='w')
    with fout:
        lines = old_description.split('\n')
        for i, line in enumerate(lines):
            if i < len(lines)-1:
                fout.write(line + '\n')
            else:
                fout.write(line)
    mod_time_before = os.path.getmtime(temp_file)
    subprocess.call([EDITOR, temp_file])
    mod_time_after = os.path.getmtime(temp_file)

    if mod_time_before != mod_time_after:
        fin = open(temp_file)
        description = fin.read()
        fin.close()
        if old_description == '':
            sql_insert = (tag, description)
            query = "INSERT INTO %s VALUES(?, ?)" % category
        else:
            sql_insert = (description, tag)
            query = "UPDATE %s SET description = ? WHERE tag = ?" % category
        cursor.execute(query, sql_insert)
        con.commit()


def edit_and_update_form_1(category, tag, entry_nr=None):
    """Edite entry with format 1 with EDITOR and save updates, if any."""
    temp_file = str(os.getcwd()) + '/pensive.temp'
    new_entry = False
    if entry_nr is not None:
        query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (
            category, tag)
        cursor.execute(query)
        result = cursor.fetchall()
        __, old_posnr, old_title, old_description = result[entry_nr]
        tempcontent = [
            "[posnr]: %s\n" % old_posnr,
            "[title]: %s\n" % old_title,
            "[description]:\n",
            old_description]
    else:
        new_entry = True
        tempcontent = [
            "[posnr]: 0\n",
            "[title]: title\n",
            "[description]: (This line will be skipped)\n"]

    # paste into temp file and call editor
    fout = open(temp_file, mode='w')
    with fout:
        for line in tempcontent:
            fout.write(line)
    mod_time_before = os.path.getmtime(temp_file)
    subprocess.call([EDITOR, temp_file])
    mod_time_after = os.path.getmtime(temp_file)

    if mod_time_before != mod_time_after:
        # read temp file
        fin = open(temp_file)
        lines = []
        for line in fin:
            line = line.strip('\n')
            if line.startswith('[posnr]: '):
                posnr = line.split('[posnr]: ')[1]
            elif line.startswith('[title]: '):
                title = line.split('[title]: ')[1]
            elif line.startswith('[description]:'):
                pass
            else:
                lines.append(line)
        fin.close()
        description = '\n'.join(lines)

        if new_entry:
            sql_insert = (tag, posnr, title, description)
            query = "INSERT INTO %s VALUES(?, ?, ?, ?)" % category
        else:
            sql_insert = (posnr, title, description, old_title, old_description)
            query = (
                "UPDATE %s "
                "SET posnr = ?, title = ?, description = ? "
                "WHERE title = ? AND description = ?" % category)
        cursor.execute(query, sql_insert)
        con.commit()


def edit_and_update_form_2(category, tag, entry_nr=None):
    """Edite entry with format 2 with EDITOR and save updates, if any."""
    temp_file = str(os.getcwd()) + '/pensive.temp'
    new_entry = False
    if entry_nr is not None:
        query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (
            category, tag)
        cursor.execute(query)
        result = cursor.fetchall()
        (
            __, old_posnr, old_title, old_description, old_attachment
        ) = result[entry_nr]
        tempcontent = [
            "[posnr]: %s\n" % old_posnr,
            "[title]: %s\n" % old_title,
            "[attachment]: %s\n" % old_attachment,
            "[description]: %s\n" % old_description]

    else:
        new_entry = True
        tempcontent = [
            "[posnr]: 0\n",
            "[title]: title\n",
            "[attachment]: /path/to/file, URL or tag\n",
            "[description]: \n"]

    # paste into temp file and call editor
    fout = open(temp_file, mode='w')
    with fout:
        for line in tempcontent:
            fout.write(line)
    mod_time_before = os.path.getmtime(temp_file)
    subprocess.call([EDITOR, temp_file])
    mod_time_after = os.path.getmtime(temp_file)

    if mod_time_before != mod_time_after:
        fin = open(temp_file)
        for line in fin:
            line = line.strip('\n')
            if line.startswith('[posnr]: '):
                posnr = line.split('[posnr]: ')[1]
            elif line.startswith('[title]: '):
                title = line.split('[title]: ')[1]
            elif line.startswith('[attachment]: '):
                attachment = line.split('[attachment]: ')[1]
            elif line.startswith('[description]: '):
                description = line.split('[description]: ')[1]
        fin.close()
        if new_entry:
            sql_insert = (tag, posnr, title, description, attachment)
            query = "INSERT INTO %s VALUES(?, ?, ?, ?, ?)" % category
        else:
            sql_insert = (
                posnr, title, description, attachment, 
                tag, old_title, old_attachment)
            query = (
                "UPDATE %s "
                "SET posnr = ?, title = ?, description = ?, "
                "attachment = ? "
                "WHERE tag = ? AND title = ? AND attachment = ?" % category)
        cursor.execute(query, sql_insert)
        con.commit()


def move_format_0_entry(org_cat, org_tag, target_cat, target_tag):
    query = "SELECT description FROM %s WHERE tag = '%s';" % (
        target_cat, target_tag)
    cursor.execute(query)
    target_description = cursor.fetchall()
    query = "SELECT description FROM %s WHERE tag = '%s'" % (org_cat, org_tag)
    cursor.execute(query)
    description = cursor.fetchall()[0][0]
    if len(target_description) == 0:
        sql_insert = (target_tag, description)
        query = "INSERT INTO %s VALUES(?, ?)" % target_cat
    else:
        # attach description to existing description
        description = target_description[0][0] + '\n' + description
        sql_insert = (description, target_tag)
        query = "UPDATE %s SET description = ? WHERE tag = ?" % target_cat

    cursor.execute(query, sql_insert)
    con.commit()
    remove_form_0(org_cat, org_tag)


def move_format_1_entry(org_cat, org_tag, org_entry_nr, target_cat, target_tag):
    query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (
        org_cat, org_tag)
    cursor.execute(query)
    result = cursor.fetchall()
    posnr = result[org_entry_nr][1]
    title = result[org_entry_nr][2]
    description = result[org_entry_nr][3]
    sql_insert = (target_tag, posnr, title, description)
    query = "INSERT INTO %s VALUES(?, ?, ?, ?)" % target_cat
    try:
        cursor.execute(query, sql_insert)
        con.commit()
        remove_form_1(org_cat, org_tag, org_entry_nr)
    except sqlite3.IntegrityError:
        print('An identical entry arleady exists, operation canceled.')


def move_format_2_entry(org_cat, org_tag, org_entry_nr, target_cat, target_tag):
    query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (
        org_cat, org_tag)
    cursor.execute(query)
    result = cursor.fetchall()
    posnr = result[org_entry_nr][1]
    title = result[org_entry_nr][2]
    description = result[org_entry_nr][3]
    attachment = result[org_entry_nr][4]
    sql_insert = (target_tag, posnr, title, description, attachment)
    query = "INSERT INTO %s VALUES(?, ?, ?, ?, ?);" % target_cat
    try:
        cursor.execute(query, sql_insert)
        con.commit()
        remove_form_2(org_cat, org_tag, org_entry_nr)
    except sqlite3.IntegrityError:
        print('An identical entry arleady exists, operation canceled.')


def export_results_form_0(category, tag):
    """Returns a string for exporting."""
    query = "SELECT description FROM %s WHERE tag = '%s'" % (category, tag)
    cursor.execute(query)
    result = cursor.fetchall()
    export = []
    if result:
        result = result[0][0]
        lines = result.split('\n')
        export.append('%s:\n' % category)
        [export.append('    ' + line + '\n') for line in lines]
    return ''.join(export)


def export_results_form_1(category, tag):
    """Returns a string for exporting with unfolded entries."""
    query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (category, tag)
    cursor.execute(query)
    result = cursor.fetchall()
    export = []
    if result:
        export.append('%s:' % category)
        for i, (*__, title, description) in enumerate(result):
            if i >= 10:
                export.append('   [%i] %s' % (i, title))
            else:
                export.append('    [%i] %s' % (i, title))
            lines = description.split('\n')
            [export.append('        ' + line) for line in lines]
            export.append('')
        export.append('')
    return '\n'.join(export)


def export_results_form_2(category, tag):
    """Returns a string for exporting."""
    query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (category, tag)
    cursor.execute(query)
    result = cursor.fetchall()
    export = []
    if result:
        export.append('%s:' % category)
        for i, (*__, title, description, attachment) in enumerate(result):
            # add description if existing
            if description != '':
                description = ' - %s' % description
            if i >= 10:
                export.append('   [%i] %s%s' % (i, title, description))
            else:
                export.append('    [%i] %s%s' % (i, title, description))
            export.append('        %s' % attachment)
            export.append('')
        export.append('')
    return '\n'.join(export)


def remove_form_0(category, tag):
    """Removes a entry of tag in a category (format 0)."""
    query = "DELETE FROM %s WHERE tag = '%s';" % (category, tag)
    cursor.execute(query)
    con.commit()


def remove_form_1(category, tag, entry_nr):
    """Removes a entry with a certain position of tag in a category of
    format 1."""
    query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (category, tag)
    cursor.execute(query)
    result = cursor.fetchall()[entry_nr]
    *__, posnr, title, description = result
    sql_insert = (tag, title, description)
    query = (
        "DELETE FROM %s "
        "WHERE tag = ? and title = ? and description = ?" % category)
    cursor.execute(query, sql_insert)
    con.commit()


def remove_form_2(category, tag, entry_nr):
    """Removes a entry with a certain position of tag in a category of
    format 2."""
    query = "SELECT * FROM %s WHERE tag = '%s' ORDER BY posnr" % (category, tag)
    cursor.execute(query)
    result = cursor.fetchall()[entry_nr]
    __, posnr, title, __, attachment = result
    sql_insert = (tag, title, attachment)
    query = (
        "DELETE FROM %s "
        "WHERE tag = ? and title = ? and attachment = ?" % category)
    cursor.execute(query, sql_insert)
    con.commit()


def backup_db(backupname=None):
    """Performs full backup (a copy) of the pensive database, create
    backupfolder if not existing and returns the backup file name."""
    if not os.path.exists(BACKUPDIR) and not os.path.isdir(BACKUPDIR):
        os.mkdir(BACKUPDIR)
    if backupname is None:
        timestamp = str(int(time.time()))
        fout = BACKUPDIR + '/' + timestamp + '.sqlite'
    else:
        fout = BACKUPDIR + '/' + backupname + '.sqlite'
    shutil.copyfile(DB, fout)
    return fout


def get_reversed_orderd_files_by_modified_time(wd):
    """Expects a directory and returns a reversed ordered list of its files
    (newest first)."""
    files = os.listdir(wd)
    for i in range(len(files)):
        date = str(os.path.getmtime(wd + '/' + files[i]))
        files[i] = date + '|' + files[i]
    files.sort(reverse=True)
    files = map(lambda i: i.split('|')[1], files)
    return files


def get_backups():
    """Gets all backups from BACKUPDIR and returns valid .sqlite files where
    the table pensive_conf exists in a list."""
    if os.path.exists(BACKUPDIR) and os.path.isdir(BACKUPDIR):
        files = get_reversed_orderd_files_by_modified_time(BACKUPDIR)
        # ensure that only .sqlite files are visible for restore and test them
        backups = []
        for file in files:
            if file.endswith('.sqlite'):
                try:
                    test_con = sqlite3.connect(BACKUPDIR + '/' + file)
                    test_cursor = test_con.cursor()
                    query = "SELECT * FROM pensive_conf"
                    test_cursor.execute(query)
                    test_con.close()
                    backups.append(file)
                except:
                    pass
        return backups
    return None


def restore_db():
    """Restore the db with existing backups and user input."""
    backups = get_backups()
    if backups:
        for i, backup in enumerate(backups):
            mod_time = os.path.getmtime(BACKUPDIR + '/' + backup)
            mod_time = time.gmtime(mod_time)
            mod_time = time.asctime(mod_time)
            if i < 10:
                print('    [%s] %s | %s' % (i, mod_time, backup))
            else:
                print('   [%s] %s | %s' % (i, mod_time, backup))
        print()
        restore_number = input('Which backup would you like to restore? : ')
        cond0 = (len(restore_number) == 1 and restore_number in digits)
        cond1 = (
            len(restore_number) == 2 and restore_number[0] in digits and
            restore_number[1] in digits)
        if cond0 or cond1:
            restore_number = int(restore_number)
            if restore_number >= 0 and restore_number <= len(backups)-1:
                restore_file = BACKUPDIR + '/' + backups[restore_number]
                shutil.copyfile(restore_file, DB)
                global con, cursor
                con.close()
                con = sqlite3.connect(DB)
                cursor = con.cursor()
                get_categories()
                get_tags()
                os.system('clear')
                print("Successfully restored.")
        else:
            print("Invalid input, restore canceled.")
    elif len(backups) == 0:
        print("No valid backups found in '%s'." % BACKUPDIR)
    else:
        print("Backup folder '%s' does not exist." % BACKUPDIR)


def export_db():
    """Exports the pensive database to simple txt files."""
    # check if export folder exsists
    if not os.path.exists(EXPORTDIR) and not os.path.isdir(EXPORTDIR):
        os.mkdir(EXPORTDIR)

    timestamp = str(int(time.time()))
    os.mkdir(EXPORTDIR + '/' + timestamp)
    for tag in defined_tags:
        fout = open(EXPORTDIR + '/' + timestamp + '/' + tag, mode='w')
        with fout:
            for category, catformatid, __ in catconf:
                if catformatid == 0:
                    export = export_results_form_0(category, tag)
                elif catformatid == 1:
                    export = export_results_form_1(category, tag)
                elif catformatid == 2:
                    export = export_results_form_2(category, tag)
                if export is not None and len(export.split('\n')) > 2:
                    fout.write(export)


def highlight_by_known_tags(line):
    """Expects a string without '\n', seperates it by ' ' and checks each word,
    if it appears to be a tag and highlights it blue. """
    if line is None or line == '':
        return line
    words = line.split(' ')
    new_words = []
    for word in words:
        if word == '':
            new_words.append(word)
        else:
            cond0 = word[0] not in ascii_letters
            cond1 = word[-1] not in ascii_letters
            if word in defined_tags:
                new_words.append(BLUE + word + DEL_COLOR)

            # include things like '(tag'
            elif word[1:] in defined_tags and cond0:
                new_words.append(word[0] + BLUE + word[1:] + DEL_COLOR)

            # include things like 'tag)'
            elif word[:-1] in defined_tags and cond1:
                new_words.append(BLUE + word[:-1] + DEL_COLOR + word[-1])

            # include things like '(tag)'
            elif word[1:-1] in defined_tags and cond0 and cond1:
                new_words.append(
                    word[0] + BLUE + word[1:-1] + DEL_COLOR + word[-1])
            else:
                new_words.append(word)
    return ' '.join(new_words)


def highlight_by_pattern(line, pattern):
    """Expects a string and a pattern and returns a red colored string where
    the pattern matched the string. Therefore the function firstly searches for
    indezes matching the pattern and stores them in hits als tuples. Secondly
    the line is highlighted."""
    start_pos = 0
    end_pos = len(pattern)
    hits = []

    while end_pos <= len(line):
        if line[start_pos:end_pos] == pattern:
            hits.append((start_pos, end_pos))
        start_pos += 1
        end_pos += 1

    pattern = RED + pattern + DEL_COLOR
    new_line = []
    for i in range(len(hits)):

        # the first and last match
        if i == 0 and len(hits) == 1:
            new_line.append(line[:hits[i][0]] + pattern + line[hits[i][1]:])

        # the first of some matches
        elif i == 0 and len(hits) > 1:
            new_line.append(line[:hits[i][0]] + pattern)

        # another match, but not the last one
        elif i > 0 and i != len(hits)-1:
            new_line.append(line[hits[i-1][1]:hits[i][0]] + pattern)

        # the last of serveral matches
        elif i > 0 and i == len(hits)-1:
            new_line.append(
                line[hits[i-1][1]:hits[i][0]] + pattern + line[hits[i][1]:])
    return ''.join(new_line)


def search_everything(pattern):
    """Seaches the complete pensive database (except attachments) for pattern
    (not case sensitive) and returns a dictionary with additional, case
    sensitive highlighting."""
    pattern_sql = '%' + pattern + '%'
    result = dict()
    for category, catformatid, __ in catconf:
        if catformatid == 0:
            query = "SELECT * FROM %s WHERE description LIKE ?" % category
            cursor.execute(query, (pattern_sql,))
            query_result = cursor.fetchall()
            for tag, description in query_result:
                hits = []
                lines = description.split('\n')

                # highlight case sensitive matches or use the 1st line instead
                for line in lines:
                    if pattern in line:
                        colored_line = highlight_by_pattern(line, pattern)
                        hits.append(colored_line)
                if not hits:
                    hits.append(lines[0])

                # add formatted hits to result
                for line in hits:
                    if tag not in result:
                        result[tag] = [(category, '', line)]
                    else:
                        result[tag].append((category, '', line))

        elif catformatid == 1 or catformatid == 2:
            sql_insert = (pattern_sql, pattern_sql)
            query = (
                "SELECT * FROM %s "
                "WHERE title LIKE ? OR description LIKE ? "
                "ORDER BY posnr;" % category)
            cursor.execute(query, sql_insert)
            query_result = cursor.fetchall()
            for tag, _, title, description, *__ in query_result:
                hits = []
                lines = description.split('\n')

                # highlight case sensitive matches or use the 1st line instead
                for line in lines:
                    if pattern in line:
                        colored_line = highlight_by_pattern(line, pattern)
                        hits.append(colored_line)
                if not hits:
                    hits.append(lines[0])

                # highlight title if possible
                if pattern in title:
                    title = highlight_by_pattern(title, pattern)

                # add formatted hits to result
                for line in hits:
                    if tag not in result:
                        result[tag] = [(category, title, line)]
                    else:
                        result[tag].append((category, title, line))
    return result


def display_search_everything(pattern):
    """Print results of search_everything()."""
    result = search_everything(pattern)
    if result:
        # get longest cat and tag name, sort tags
        tags = []
        len_tags = []
        len_cats = []

        for tag in result:
            tags.append(tag)
            len_tags.append(len(tag))
            for category, *__ in result[tag]:
                len_cats.append(len(category))

        tags.sort()
        max_cat_length = max(len_cats)
        max_tag_length = max(len_tags)

        for tag in tags:
            space_tag = max_tag_length - len(tag)
            for category, title, description in result[tag]:
                space_cat = max_cat_length - len(category)
                if title != '':
                    title = '(' + title + ')'
                if description != '':
                    description = ': ' + description
                str_insert = (
                    BLUE, space_tag * ' ', tag, DEL_COLOR, space_cat * ' ',
                    category, title, description)
                output = '[%s%s%s%s] %s%s %s%s' % str_insert
                print(output)


def install_pensive_base():
    """Installs pensive_conf and pensive_tags."""
    cursor.execute((
        "CREATE TABLE pensive_conf( "
        "catid INT, "
        "category TEXT, "
        "catformatid INT, "
        "UNIQUE(category), "
        "PRIMARY KEY(catid))"))
    cursor.execute((
        "CREATE TABLE pensive_tags( "
        "tag TEXT, "
        "PRIMARY KEY(tag))"))
    con.commit()
    get_categories()


def install_pensive_examples():
    """Installs some examples for the tutorial."""
    # insert categories to pensive_conf and create a table for each one
    add_category_format0('form_0_example')
    add_category_format1('form_1_example')
    add_category_format2('form_2_example')
    get_tags()

    # add some tags
    add_tag_to_db('pacman')
    add_tag_to_db('python.sqlite3')
    add_tag_to_db('python')

    # insert form 0 example
    category = 'form_0_example'
    tag = 'pacman'
    form_0_insert = (
        "»pacman is the default package manager of arch linux«\n"
        "pacman -S  [package]   update or install package\n"
        "pacman -Scc            empty cache\n"
        "pacman -Syy            update package list\n"
        "pacman -Su             system update\n"
        "pacman -Qs [package]   query search\n"
        "...")
    query = "INSERT INTO %s VALUES('%s', '%s');" % (
        category, tag, form_0_insert)
    cursor.execute(query)

    # insert form 1 examples
    category = 'form_1_example'
    tag = 'python'
    title_list = ['String methods', 'Something about lists', 'Tuple examples']
    for i in range(3):
        posnr = i
        title = title_list[i]
        if i == 0:
            desc = (
                ".lower()        returns string in lower case letters\n"
                ".upper()        returns string in upper case letters\n"
                ".find(pattern)  returns the first index position of pattern\n"
                ".strip()        removes ''\\n'' of lines\n"
                ".replace()      ...\n"
                ".capitalize()   ...\n"
                ".split(sep)     ...\n"
                "...")
        else:
            desc = 'blah %s' % str(i)
        query = "INSERT INTO %s VALUES('%s', %s, '%s', '%s')" % (
            category, tag, posnr, title, desc)
        cursor.execute(query)

    # insert form 2 examples
    category = 'form_2_example'
    tag = 'python'
    insert = [
        ('Python style guide', 'this is a description', '/path/to/file'),
        ('some tutorial', 'descriptions are optional', 'http://tutorial.org'),
        ('Existing python tag', '', 'python.sqlite3'),
        ('Not existing python tag', '', 'python.tkinter')]

    for i, (title, description, attachment) in enumerate(insert):
        query = "INSERT INTO %s VALUES('%s', %s, '%s', '%s', '%s');" % (
            category, tag, i, title, description, attachment)
        cursor.execute(query)
    con.commit()


def uninstall_pensive_examples():
    """Removes everything and installs pensive_base once more."""
    cursor.execute("DROP TABLE form_0_example")
    cursor.execute("DROP TABLE form_1_example")
    cursor.execute("DROP TABLE form_2_example")
    cursor.execute("DROP TABLE pensive_tags")
    cursor.execute("DROP TABLE pensive_conf")
    con.commit()


def do_tutorial():
    """Intruduces pensive in seven steps."""
    install_pensive_examples()
    os.system('clear')
    print("""[Tutorial page 1 / 7]
    Welcome to pensive, a tool for organizing information by command line.
    Organizing means here to view, edit or remove information without leaving
    the CLI. The overall idea is to manage information with tags, like 'pacman',
    'python' or 'python.sqlite3'. As there are different kinds of information
    you might want to use, there are three essential formats used in pensive:
    
    Format 0: Plain Text, show everything at once, e.g. command reference
    Format 1: Separate entries, which can be opened, e.g. some scripts
    Format 2: Attachments, e.g. URLs, files or other tags""")
    __ = input('\n[Please press any key to proceed]\n')
    os.system('clear')

    print("""[Tutorial page 2 / 7]
    Format 0 displays information as it is - with the exception of highlighting
    existing tags - similar to Wikipedia. Information with this formatting is by
    design rather important as you can see e.g. your notes of a linux command
    like pacman immediately at once:\n""")
    show_results_form_0('form_0_example', 'pacman')
    __ = input('\n[Please press any key to proceed]\n')
    os.system('clear')

    print("""[Tutorial page 3 / 7]
    Format 1 displays grouped information by titles. The idea is that there
    might be some special notes, which you won't want to see every time you
    query a tag. If you want to view such an entry, you can simply unfold it by
    typing two to three keys! Entries of format 1 are looking like this:\n""")
    show_results_form_1('form_1_example', 'python')
    print('... and here is an unfolded entry:\n')
    show_single_entry_form_1('form_1_example', 'python', 0)
    __ = input('\n[Please press any key to proceed]\n')
    os.system('clear')

    print("""[Tutorial page 4 / 7]
    Format 2 is similar to format 1. The big difference is, that you can specify
    an attachment (file, URL, tag). Files and tags are colored blue if they
    exists and can be opened (files: xdg-open) or queried. URLs are opened with
    the browser of your choice, which you can specify, among other parameters,
    in the pensive.conf file. The system messages of eventually started 
    programs will be suppressed as we do not want them to disturb your work with
    pensive. Entries of format 2 look like the following:\n""")
    show_results_form_2('form_2_example', 'python')
    print("""
    Now we have just seen all formats separate. At the next page we will have a
    look at the output of the query of 'python' would show us."""
    )
    __ = input('\n[Please press any key to proceed]\n')
    os.system('clear')

    print("[Tutorial page 5 / 7]")
    display_overview('python')
    print("""
    Please notice the headlines 'format_1_example' etc. here. These resemble
    'categories'. In pensive, categories are linked to format numbers. In
    this tutorial, we have three defined categories:
    format_0_example with format 0,
    format_1_example with format 1,
    format_2_example and with format 2.
    
    If there is any information of a tag saved in such a category, these will be
    displayed in the precise order, in which they have been installed. If no
    information is available, a category will be skipped.
    
    Categories also determine the way of how you interact with pensive:
    They can be addressed by appropriate upper case letters starting from
    'A'. To open the first entry of the category format_1_example, you will 
    have to type 'B0', because format_1_example is the second category and 
    therefore aliased with 'B'. This is probably the most complicated thing
    about Pensive and can be displayed with 'category show'. On the next page,
    you can have a look at all features of pensive presented in the help view.
    """
    )
    __ = input('\n[Please press any key to proceed]\n')
    os.system('clear')

    print("[Tutorial page 6 / 7]")
    display_help()
    __ = input('\n[Please press any key to proceed]\n')
    uninstall_pensive_examples()
    install_pensive_base()
    get_tags()
    os.system('clear')

    print("""[Tutorial page 7 / 7]
    Now you can try to add some categories on your own. The syntax is:
       category add CATEGORYNAME FORMATNUMBER
    where the FORMATNUMBER must be 0, 1 or 2. Once done, you can try to
    add some tags, query them and create some new entries in the categories, you
    have just added:
       add tag1 [tag2 tag3 ...]  # add tags
       ?tag1                     # query tag
       *A                        # create new entry of the 1st cat.
    
    If you want to display the help overview again, please type 'help'. If you
    have any questions or feedback you would like to give, feel free to contact
    me at murzik@mailbox.org.""")


def catid_exists(catletter):
    """Expects an upper case letter and checks, if it can be aliased with
    a defined category."""
    catid = ord(catletter)-65
    return catid >= 0 and catid <= len(catconf)-1


def category_exists(category):
    """Expects string and checks, if it is already used as a category."""
    for i in range(len(catconf)):
        if catconf[i][0] == category:
            return True
    return False


def entry_exists(catid, entry_nr):
    """Expects category id and an entry number and checks, if suchs an
    entry exists."""
    return entry_nr >= 0 and entry_nr <= tag_results[catid][2]-1


def ask_yes_no(name, mode):
    """Asks a yes no question and returns the True or False."""
    if mode == 0:
        question = "Do you realy want to remove everything of '%s'?" % name
    elif mode == 1:
        question = "Do you realy want to remove '%s'?" % name
    elif mode == 2:
        question = "Tag '%s' does not exist. Create it now?" % name
    answer = input(question + ' [y/N]: ')
    if answer.lower() == 'y' or answer.lower() == 'yes':
        return True
    elif answer == '' or answer.lower() == 'n' or answer.lower() == 'no':
        return False


def pensive_shell(active_tag=None):
    """Central command line interface. Sometimes the function returns itself
    without an active tag (mostly 'basic functions' as they are named in the
    help view), but generally, it returns a active tag, if possible."""
    # prompt handling
    prompt = ':'
    if active_tag is not None:
        prompt = '[%s]:' % active_tag
        uin = input(prompt)
    else:
        uin = input(prompt)

    # input handling
    if uin == 'license':
        display_license()
        return pensive_shell()

    elif uin == 'help':
        display_help()
        return pensive_shell()

    elif uin == 'ls':
        # list all tags
        display_tags()
        return pensive_shell()

    elif uin.startswith('ls '):
        # list tags matching input
        display_specific_tags(uin[3:])
        return pensive_shell()

    elif uin.startswith('add '):
        # add one or more tags to pensive
        tags = uin[4:].split(' ')
        added_tags = []
        for tag in tags:
            if tag not in defined_tags:
                add_tag_to_db(tag)
                added_tags.append(tag)
        if len(added_tags) == 0:
            print("Tag(s) already defined. You can query tags by '?tag'.")
            return pensive_shell()
        elif len(added_tags) == 1:
            os.system('clear')
            display_overview(added_tags[0])
            return pensive_shell(added_tags[0])
        elif len(added_tags) > 1:
            print('%d tags added.' % len(added_tags))
            return pensive_shell()

    elif uin.startswith('rm '):
        # remove one or more tags from pensive
        tags = uin[3:].split(' ')
        removed_tags = []
        for tag in tags:
            if tag in defined_tags:
                remove_tag_from_db(tag)
                removed_tags.append(tag)
        if len(removed_tags) == 0:
            print("Tag(s) not defined, nothing to remove.")
        elif len(removed_tags) > 1:
            print('%s tags removed.' % len(removed_tags))
        return pensive_shell()

    elif uin.startswith('mv ') and active_tag is None:
        # rename tag
        old_tag_name = uin[3:].split(' ')[0]
        new_tag_name = uin[3:].split(' ')[1]
        rename_tag(old_tag_name, new_tag_name)
        return pensive_shell()

    elif uin.startswith('?') and len(uin) > 1 and uin[1] != '?':
        # query a tag
        os.system('clear')
        if uin[1:] in defined_tags:
            display_overview(uin[1:])
            return pensive_shell(uin[1:])
        else:
            print((
                "Tag '%s' is not defined yet. "
                "How about adding it with 'add %s'?" % (uin[1:], uin[1:])))
            return pensive_shell()

    elif uin.startswith('??') and len(uin) > 2:
        # start a flull text search with a pattern
        os.system('clear')
        display_search_everything(uin[2:])
        return pensive_shell()

    elif uin == 'category show':
        # show all defined categories
        display_categories()

    elif uin.startswith('category add ') and len(uin.split(' ')) == 4:
        # add a new category
        category = uin[13:].split(' ')[0]
        catformatid = uin[13:].split(' ')[1]
        if not category_exists(category) and catformatid in digits[:3]:
            catformatid = int(catformatid)
            if catformatid == 0:
                add_category_format0(category)
            elif catformatid == 1:
                add_category_format1(category)
            elif catformatid == 2:
                add_category_format2(category)
            display_categories()
        else:
            print('Category name exists or formatid is not 0, 1 or 2.')

    elif uin.startswith('category rm '):
        # remove a category
        category = uin[12:]
        if category_exists(category):
            if ask_yes_no(name=category, mode=0):
                remove_category(category)
                display_categories()
        else:
            print("Category is not defined, nothing to deleate.")

    elif uin.startswith('category mv ') and len(uin.split(' ')) == 4:
        # rename a category
        old_category = uin[12:].split(' ')[0]
        new_category = uin[12:].split(' ')[1]
        if category_exists(old_category) and not category_exists(new_category):
            rename_category(old_category, new_category)

    elif uin.startswith('backup'):
        if len(uin) == 6:
            fout = backup_db()
        elif ' ' in uin and len(uin) > 7:
            backupname = uin[7:]
            fout = backup_db(backupname)
        print("Successfully created '%s'." % fout)

    elif uin.startswith('restore'):
        restore_db()

    elif uin.startswith('export'):
        export_db()
        print('Done.')

    elif uin == 'q' or uin == 'quit':
        con.close()
        return sys.exit()

    elif active_tag is not None and len(uin) == 1 and catid_exists(uin[0]):
        # show results of only one category
        os.system('clear')
        catformatid = catconf[(ord(uin[0])-65)][1]
        category = catconf[(ord(uin[0])-65)][0]
        tag = active_tag
        if catformatid == 0:
            show_results_form_0(category, tag)
        elif catformatid == 1:
            show_results_form_1(category, tag)
        elif catformatid == 2:
            show_results_form_2(category, tag)

    elif active_tag is not None and len(uin) >= 1 and catid_exists(uin[0]) and uin[1] in digits:
        # show singe entry form 1 or open attachment of form 2
        catformatid = catconf[(ord(uin[0])-65)][1]
        entry_nr = int(uin[1:])
        category = catconf[(ord(uin[0])-65)][0]
        tag = active_tag
        catid = ord(uin[0])-65
        if catformatid == 1 and entry_exists(catid, entry_nr):
            show_single_entry_form_1(category, tag, entry_nr)
        elif catformatid == 2 and entry_exists(catid, entry_nr):
            open_attachment_form_2(category, tag, entry_nr)
        else:
            os.system('clear')
            display_overview(tag)

    elif active_tag is not None and uin.startswith('*') and catid_exists(uin[1]):
        # edit or create entries of all kind
        catformatid = catconf[(ord(uin[1])-65)][1]
        category = catconf[(ord(uin[1])-65)][0]
        catid = ord(uin[1])-65
        tag = active_tag
        try:
            if catformatid == 0:
                edit_and_update_form_0(category, tag)
            elif catformatid == 1:
                if len(uin) > 2 and entry_exists(catid, int(uin[2:])):
                    entry_nr = int(uin[2:])
                    edit_and_update_form_1(category, tag, entry_nr)
                else:
                    edit_and_update_form_1(category, tag)
            elif catformatid == 2:
                if len(uin) > 2 and entry_exists(catid, int(uin[2:])):
                    entry_nr = int(uin[2:])
                    edit_and_update_form_2(category, tag, entry_nr)
                else:
                    edit_and_update_form_2(category, tag)
            os.system('clear')
            display_overview(tag=active_tag)
        except sqlite3.IntegrityError:
            print('An identical entry arleady exists, operation canceled.')

    elif active_tag is not None and uin.startswith('-') and catid_exists(uin[1]):
        # remove single entries
        if ask_yes_no(name=uin[1:], mode=1):
            catformatid = catconf[(ord(uin[1])-65)][1]
            category = catconf[(ord(uin[1])-65)][0]
            catid = ord(uin[1])-65
            tag = active_tag
            if catformatid == 0:
                remove_form_0(category, tag)
            elif catformatid == 1:
                if len(uin) > 2 and entry_exists(catid, int(uin[2:])):
                    entry_nr = int(uin[2:])
                    remove_form_1(category, tag, entry_nr)
            elif catformatid == 2:
                if len(uin) > 2 and entry_exists(catid, int(uin[2:])):
                    entry_nr = int(uin[2:])
                    remove_form_2(category, tag, entry_nr)
        os.system('clear')
        display_overview(active_tag)

    elif active_tag is not None and uin.startswith('mv ') and catid_exists(uin[3]):
        # move single entries between categories and or tags
        move_request = uin.split(' ')[1:]
        if catid_exists(move_request[1][0]):
            org_tag = active_tag
            org_catid = ord(move_request[0][0])-65
            org_category = catconf[(ord(move_request[0][0])-65)][0]
            org_catformatid = catconf[(ord(move_request[0][0])-65)][1]
            if len(move_request[0]) > 1:
                try:
                    org_entry_nr = int(move_request[0][1:])
                except:
                    print("You can move tags in non tag mode only!")
                    return pensive_shell(active_tag)
            else:
                org_entry_nr = None

            if '@' not in move_request[1]:
                target_tag = active_tag
                target_category = catconf[(ord(move_request[1][0])-65)][0]
                target_catformatid = catconf[(ord(move_request[1][0])-65)][1]
            elif '@' in move_request[1]:
                target_tag = move_request[1].split('@')[1]
                target_category = catconf[(ord(move_request[1].split('@')[0][0])-65)][0]
                target_catformatid = catconf[(ord(move_request[1].split('@')[0][0])-65)][1]

            if target_tag not in defined_tags:
                if not ask_yes_no(target_tag, 2):
                    return pensive_shell(active_tag)
                else:
                    add_tag_to_db(target_tag)
            cond = (
                catid_exists(move_request[1].split('@')[0][0]) and
                target_catformatid == org_catformatid)
            if not cond:
                print((
                    "Categories don't exist or don't share same format. "
                    "Operation cancelled."))
                return pensive_shell(active_tag)
            if target_catformatid == 0 and tag_results[org_catid][2] != 0:
                args = (org_category, org_tag, target_category, target_tag)
                move_format_0_entry(*args)
            elif (target_catformatid == 1 and org_entry_nr is not None and
                    entry_exists(org_catid, org_entry_nr)):
                args = (
                    org_category, org_tag, org_entry_nr,
                    target_category, target_tag)
                move_format_1_entry(*args)
            elif (target_catformatid == 2 and org_entry_nr is not None and
                    entry_exists(org_catid, org_entry_nr)):
                args = (
                    org_category, org_tag, org_entry_nr,
                    target_category, target_tag)
                move_format_2_entry(*args)
            os.system('clear')
            display_overview(active_tag)
    else:
        display_help()
    return pensive_shell(active_tag)


os.system('clear')
cwd = os.getcwd()
get_configuration()
con = sqlite3.connect(DB)
cursor = con.cursor()

print(
    "pensive Copyright (C) 2015 Georg Alexander Murzik\n"
    "This program is free software and comes with ABSOLUTELY NO WARRANTY.\n"
    "You are welcome to redistribute it under certain conditions.\n"
    "Type 'license' for distribution details, 'help' for help or 'q' to quit.")

try:
    get_categories()

except sqlite3.OperationalError:
    print('\nWelcome to pensive!')
    install_pensive_base()
    question = "Do you want to take the quick tour? [Y/n]: "
    answer = input(question)
    if answer.lower() == 'y' or answer.lower() == 'yes' or answer == '':
        do_tutorial()

finally:
    get_tags()

try:
    pensive_shell()
except KeyboardInterrupt or EOFError:
    con.close()
    sys.exit()
