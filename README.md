# Savegame Controller
Version control made for VisualBoyAdvance savegames, but should work for every game that has one (or a limited number of) save files that it overrides

## Usage

Copy this file in the folder that contains your savegame files. On Execution, it will Generate a Folder that stores one folder for every savegame in your folder. A timestamp of the execution time will be appended. Your file will not be altered.

If the last backup-file is identical to the original file, no new backup will be created.

## Todo

Use sqlite to store the savegames and keep better metadata and some better interface to restore archived savegames.
