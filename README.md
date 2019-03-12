# Savegame Controller
Version control made for VisualBoyAdvance savegames, but should work for every game that has one (or a limited number of) save files that it overrides

## Usage

### backup_savegames.py

Copy this file in the folder that contains your savegame files. On Execution, it will Generate a Folder that stores one folder for every savegame in your folder. A timestamp of the execution time will be appended. Your file will not be altered.

If the last backup-file is identical to the original file, no new backup will be created.

### savegame_manager.py

This is a version control manager for savegames that comes with a gui. From there, previous savestates can be restored directly. Data is saved in a sqlite database.
The Manager checks for file changes every few seconds and saves a new version if there is a change. backup_once does the lookup once without calling the gui and starting the continuous lookup.

## Todo

Option to ignore certain savegames from auto-updating and have a button that force-updates on these.
