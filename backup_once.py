"""Save the current state of the savegames to the database once."""

import savegame_manager


def main():
    """Run the backp script."""
    savegame_manager.watch_files_caller()


if __name__ == '__main__':
    main()
