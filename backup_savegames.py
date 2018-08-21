"""Backup program to keep track of saved games that only use one savegame file.
   Creates a folder that holds a folder for every savefile.
   Adds the time of execution to the backup file name."""

import os
import filecmp
import datetime

SAVEGAME_EXTENSION = ".sav"
FOLDER = "Savegames"

def main():
    """Backup your singe-file savegames"""
    join = os.path.join
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H_%M_%S")
    key = lambda x: datetime.datetime.strptime(x[-23:-4], "%Y-%m-%dT%H_%M_%S")

    files = [save for save in os.listdir() if save.endswith(SAVEGAME_EXTENSION)]
    for filename in files:
        name, ext = (os.path.splitext(filename))
        backupname = "{} - {}{}".format(name, now, ext)

        # Generate structure
        if FOLDER not in os.listdir():
            os.mkdir(FOLDER)
        if name not in os.listdir(FOLDER):
            os.mkdir(join(FOLDER, name))

        if os.listdir(join(FOLDER, name)): # if not empty
            newest = sorted(os.listdir(join(FOLDER, name)), key=key)[-1]
            if filecmp.cmp(filename, join(FOLDER, name, newest)):
                print("No changes at {}!".format(name))
                break
        with open(filename, "rb") as base:
            with open(join(FOLDER, name, backupname), "wb") as target:
                target.write(base.read())

if __name__ == '__main__':
    main()
