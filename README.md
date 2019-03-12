# Savegame Controller
Version control made for VisualBoyAdvance savegames, but should work for every game that has one (or a limited number of) save files that it overrides

## Usage

Copy this file in the folder that contains your savegame files. On Execution, it will Generate a Folder that stores one folder for every savegame in your folder. A timestamp of the execution time will be appended. Your file will not be altered.

If the last backup-file is identical to the original file, no new backup will be created.

The Manager checks for file changes every few seconds and saves a new version to a database if there is a change. backup_once does the lookup once without calling the gui.

## Todo

Option to ignore certain savegames from auto-updating and have a button that force-updates on these.
