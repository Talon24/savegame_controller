"""Main file for savegame controller."""

# import json
import os
import time
import hashlib
import pathlib
import datetime
import collections
# import dateutil
import threading
import tkinter as tk
from tkinter import font
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
from tkinter.ttk import Progressbar
# import tkinter.ttk as ttk

from dateutil import tz

import database
import database_set_up

STOP_EVENT = threading.Event()
# SYNC_ALL = threading.Event()


def sha(the_bytes):
    """Hexdigest of hash of bytes."""
    hashing = hashlib.sha256()
    hashing.update(the_bytes)
    return hashing.hexdigest()


def saved_before(path, file_hash, connection):
    """Check if the savegame has been saved before."""
    cursor = connection.cursor()
    sql = ("select hash from savegame_history "
           "where path = ? ")
    cursor.execute(sql, (path,))
    result = cursor.fetchall()
    connection.commit()
    try:
        lasthashes = {row[0] for row in result}
    except TypeError:
        print("No savegame yet")
        return False
    return file_hash in lasthashes


def save_new_game(path, connection):
    """Inserts a new savegame into the database. Returns change indicator."""
    cursor = connection.cursor()
    connection.commit()
    try:
        with open(path, "rb") as file:
            content = file.read()
    except OSError:
        return False  # File cannot be read currently. Trying again later
    file_hash = sha(content)
    if not saved_before(path, file_hash, connection):
        mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(path))
        # TODO: gpbierdgerdpayhjgögdhidfuhg sommerzeit ikdulgdh utc ikuegeg
        sql = "insert into savegame_history values (?, ?, ?, ?)"
        cursor.execute(sql, (path, mtime, content, file_hash))
        connection.commit()
        return True
    else:
        return False


def get_paths(cursor):
    """Get the currently watched paths."""
    sql = "select path from games"
    try:
        cursor.execute(sql)
    except database.sqlite3.OperationalError:
        # database locked
        return []
    paths = [row[0] for row in cursor.fetchall()]
    return paths


def to_local_time(date):
    """Convert a utc datetime to local time."""
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    # Tell the datetime object that it's in UTC time zone since
    # datetime objects are 'naive' by default
    date = date.replace(tzinfo=from_zone)

    # Convert time zone
    return date.astimezone(to_zone)


def check_db(connection):
    """See if the database is set up"""
    cursor = connection.cursor()
    try:
        cursor.execute("select * from games limit 1")
    except database.sqlite3.OperationalError:
        database_set_up.setup(cursor)
        print("Setting up Database!")


def center(win):
    """Move a window to the center of the screen"""
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x_pos = (win.winfo_screenwidth() // 2) - (width // 2)
    y_pos = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry('{}x{}+{}+{}'.format(width, height, x_pos, y_pos))


class GameSelect(tk.Frame):  # pylint: disable=R0901
    """The listbox that contains the games."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        label = tk.Label(self, text="Games")
        label.grid(row=0, column=0, sticky="NEWS")
        scrollbar = tk.Scrollbar(self, orient="vertical")
        scrollbar.grid(row=1, column=1, sticky="NES")
        listbox = tk.Listbox(self, width=40, yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        listbox.configure(exportselection=False)
        listbox.bind("<<ListboxSelect>>",
                     # lambda x: self.update_savegame_list())
                     lambda x: self.parent.trigger_update(1))
        listbox.grid(row=1, column=0, sticky="NEWS")
        tk.Grid.rowconfigure(self, 1, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=0)
        listbox.popup_menu = tk.Menu(listbox, tearoff=0)
        listbox.popup_menu.add_command(
            label="Delete", command=lambda x: print("Delete"))
        listbox.popup_menu.add_command(
            label="Select All", command=lambda x: print("Select"))
        listbox.bind("<Button-3>", lambda x: self.parent.popup(listbox, x))

        button = tk.Button(self, text="Insert new Game",
                           command=self.new_game_dialog)
        button.grid(row=2, column=0, sticky="NEWS")

        self.listbox = listbox
        self.data = None

    def new_game_dialog(self):
        """Insert new game and savegame into database."""
        new_game = simpledialog.askstring(
            "Game Name", "Please insert name of new Game", parent=self)
        if new_game is not None and new_game != "":
            new_savegame = filedialog.askopenfilename(
                parent=self, initialdir=os.getcwd(),
                title="Select a savegame of {} to watch.".format(new_game))
            if new_savegame is not None and new_savegame != "":
                sql = "insert into games (game, path) values (?, ?)"
                self.parent.cursor.execute(sql, (new_game, new_savegame))
                self.parent.connection.commit()
                self.parent.trigger_update(2)

    def update_content(self):
        """Refresh the contents of the listbox."""
        cursor = self.parent.cursor
        sql = "select distinct game from games order by game asc"
        cursor.execute(sql)
        self.data = cursor.fetchall()
        self.listbox.delete(0, tk.END)
        for item in [row[0] for row in self.data]:
            self.listbox.insert(tk.END, item)
        self.listbox.select_set(0)
        self.parent.connection.commit()

    def get_selected(self):
        """Get the currently selected items in the listbox."""
        selected = self.listbox.curselection()
        if selected == tuple():
            return None
        return self.data[selected[0]]


class SavegameSelect(tk.Frame):  # pylint: disable=R0901
    """The listbox that contains the games."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        label = tk.Label(self, text="Savegames")
        label.grid(row=0, column=0, sticky="NEWS")
        scrollbar = tk.Scrollbar(self, orient="vertical")
        scrollbar.grid(row=1, column=1, sticky="NS")
        listbox = tk.Listbox(self, width=40, yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        listbox.configure(exportselection=False)
        # for item in ["Savegame1", "Savegame2", "Savegame3", "Savegame4"]:
        #     listbox.insert(tk.END, item)
        listbox.bind("<<ListboxSelect>>",
                     # lambda x: self.update_savegame_states_box())
                     lambda x: self.parent.trigger_update(0))
        listbox.grid(row=1, column=0, sticky="NEWS")
        tk.Grid.rowconfigure(self, 1, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=0)

        listbox.popup_menu = tk.Menu(listbox, tearoff=0)
        listbox.popup_menu.add_command(
            label="Delete", command=lambda x: print("Delete"))
        listbox.popup_menu.add_command(
            label="Select All", command=lambda x: print("Select"))
        listbox.bind("<Button-3>", lambda x: self.parent.popup(listbox, x))

        button = tk.Button(self, text="New Savegame location",
                           command=self.new_savegame_dialog)
        button.grid(row=2, column=0, sticky="NEWS")

        self.listbox = listbox
        self.data = None

    def new_savegame_dialog(self):
        """Insert new savegame into database."""
        # current_game = self.gamebox.get(self.gamebox.curselection()[0])
        current_game = self.parent.games.get_selected()[0]
        new_savegame = filedialog.askopenfilename(
            parent=self, initialdir=os.getcwd(),
            title="Select a savegame of {} to watch.".format(current_game))
        if new_savegame is not None and new_savegame != "":
            sql = "insert into games (game, path) values (?, ?)"
            self.parent.cursor.execute(sql, (current_game, new_savegame))
            self.parent.connection.commit()
            self.parent.trigger_update(1)

    def update_content(self):
        """Refresh the contents of the listbox."""
        cursor = self.parent.cursor
        listbox = self.listbox
        gamename = self.parent.games.get_selected()  # all selected
        if gamename is None or len(gamename) > 1:
            return
        gamename = gamename[0]  # first selected
        sql = ("select path from games "
               "where game like ? "
               "order by path asc")
        cursor.execute(sql, (gamename,))
        self.data = cursor.fetchall()
        listbox.delete(0, tk.END)
        filename_counter = collections.Counter(
            [pathlib.Path(row[0]).parts[-1] for row in self.data])
        filenames = dict(filename_counter.items())
        for path in [row[0] for row in self.data]:
            shortname = pathlib.Path(path).parts[-1]
            if filenames[shortname] == 1:
                filename = pathlib.Path(path).parts[-1]
            else:
                filename = path
            listbox.insert(tk.END, filename)
        listbox.select_set(0)
        self.parent.connection.commit()
        # self.update_savegame_states_box()

    def get_selected(self):
        """Get the currently selected items in the listbox."""
        return self.listbox.curselection()

    def get_selected_path(self):
        """Return the Path of the currently selected item"""
        # return self.data[self.get_selected()[0]]
        selected = self.listbox.curselection()
        if selected == tuple():
            return None
        return self.data[selected[0]]


class SavegameStateSelect(tk.Frame):  # pylint: disable=R0901
    """The listbox that contains the games."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        label = tk.Label(self, text="Saved game states")
        label.grid(row=0, column=0, sticky="NEWS")
        scrollbar = tk.Scrollbar(self, orient="vertical")
        listbox = tk.Listbox(self, width=(10 + 1 + 8 + 4),
                             selectmode='extended',
                             yscrollcommand=scrollbar.set)
        listbox.configure(exportselection=False)
        scrollbar.config(command=listbox.yview)
        scrollbar.grid(row=1, column=1, sticky="NES")
        # for item in ["2015", "2016", "2017", "2018"]:
        #     listbox.insert(tk.END, item)
        # listbox.bind(
        #     "<<ListboxSelect>>",
        #     lambda x: print(self.get_identifier()))
        listbox.grid(row=1, column=0, sticky="NEWS")
        tk.Grid.rowconfigure(self, 1, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=0)

        button = tk.Button(self, text="Refresh",
                           command=lambda: self.parent.trigger_update(0))
        button.grid(row=2, column=0, sticky="NEWS")

        listbox.popup_menu = tk.Menu(listbox, tearoff=0)
        listbox.popup_menu.add_command(label="Abort")
        listbox.popup_menu.add_separator()
        listbox.popup_menu.add_command(
            label="Delete", command=self.delete)
        listbox.popup_menu.add_command(
            label="Export...", command=self.export)
        # listbox.popup_menu.add_command(
        #     label="Select All", command=lambda: print())
        listbox.bind("<Button-3>", lambda x: self.parent.popup(listbox, x))

        self.listbox = listbox
        self.data = None

    def delete(self):
        """Delete an entry."""
        savegame_idxs = self.get_selected()
        path = self.parent.savegames.get_selected_path()  # all selected
        if path is None or len(path) > 1:
            return
        path = path[0]  # first path
        dates = [self.data[i][0] for i in savegame_idxs]
        if savegame_idxs is None:
            return
        message = ("Do you really want to delete these {} elements?"
                   "".format(len(dates)))
        if not messagebox.askokcancel("Confirm deletion", message):
            return
        conn = self.parent.connection
        try:
            with conn:
                cursor = conn.cursor()
                for date in dates:
                    delete(cursor, "data", date, path)
                for idx in sorted(savegame_idxs, reverse=True):
                    # Reversed to start removing from the bottom as delete
                    # starts counting from the top
                    self.listbox.delete(idx)
            # conn.execute("VACUUM")
        except AssertionError:
            pass

    def export(self):
        """Download a savegame file from the database."""
        selection = self.get_selected()
        if len(selection) != 1:
            messagebox.showerror(title="Multiple Entries are selected",
                                 message="You cannot yet export "
                                 "multiple savegames.")
            return
        row = self.data[selection[0]]
        path = pathlib.Path(row["path"]).parent
        name = pathlib.Path(row["path"]).name
        suffix = pathlib.Path(row["path"]).suffix
        target = filedialog.asksaveasfilename(
            parent=self, initialdir=path, initialfile=name,
            defaultextension=suffix,
            title="Select a name to save the savegame state as.")
        if target:
            cursor = self.parent.cursor
            sql = ("select savegame from savegame_history "
                   "where date = ? and path = ?")
            cursor.execute(sql, (row["date"], row["path"]))
            data = cursor.fetchall()
            if len(data) > 1:
                messagebox.showerror(
                    title="Database Inconsistency!",
                    message="Double entries in savegame_history table!")
                return
            data = data[0][0]
            with open(target, "wb") as file:
                file.write(data)

    def update_content(self):
        """Refresh the contents of the listbox."""
        cursor = self.parent.cursor
        path = self.parent.savegames.get_selected_path()  # all selected
        if path is None or len(path) > 1:
            return
        path = path[0]  # first path
        listbox = self.listbox
        # path = self.data[selection[0]]
        listbox.delete(0, tk.END)
        sql = ("select date, path from savegame_history "
               "where path = ? "
               "order by date desc")
        cursor.execute(sql, (path,))
        self.data = cursor.fetchall()
        titles = [row[0] for row in self.data]
        for item in titles:
            item = to_local_time(item)
            item = item.strftime("%y-%m-%d %H:%M:%S")
            self.listbox.insert(tk.END, item)
        self.listbox.select_set(0)
        self.parent.connection.commit()

    def get_selected(self):
        """Get the currently selected index in the listbox."""
        return self.listbox.curselection()

    # def get_identifier(self):
    #     """Get the date and the path of the current selection."""
    #     if len(self.get_selected()) != 1:
    #         messagebox.showerror(title="Multiple Entries are selected",
    #                              message="You cannot restore "
    #                              "multiple file versions!")
    #         return None
    #     row = self.data[self.get_selected()[0]]
    #     return row["date"], row["path"]

    def write_file(self):
        """Replace the current savegame with the selected one."""
        # identifier = self.get_identifier()
        selection = self.get_selected()
        if len(selection) != 1:
            messagebox.showerror(title="Multiple Entries are selected",
                                 message="You cannot restore "
                                 "multiple file versions!")
            return
        row = self.data[selection[0]]
        path = pathlib.Path(row["path"])
        confirmed = messagebox.askokcancel(
            title="Confirmation", message="Really overwrite file {} ?"
            "".format(path.parts[-1]))
        print(confirmed)
        if not confirmed:
            return
        cursor = self.parent.cursor
        # print((identifier))
        sql = ("select path, savegame from savegame_history "
               "where date = ? and path = ?")
        cursor.execute(sql, (row["date"], row["path"]))
        data = cursor.fetchall()
        if len(data) > 1:
            messagebox.showerror(
                title="Database Inconsistency!",
                message="Double entries in savegame_history table!")
            return
        row = data[0]
        try:
            with open(row["path"], "wb") as file:
                file.write(row["savegame"])
        except OSError:
            messagebox.showwarning(
                title="File locked!",
                message=("The file is currently locked and cannot be written "
                         "to. Maybe the game is currently saving?"))


class App(tk.Frame):  # pylint: disable=R0901
    """Generates the main GUI window."""

    def __init__(self, parent, connection, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # self.parent = parent  # Not needed?
        connection.row_factory = database.sqlite3.Row
        self.connection = connection
        # self.cursor = self.connection.cursor()
        # self.gamebox = None
        # self.make_gamebox()
        #
        # self.savegame_box = None
        # self.make_savegame_box()
        #
        # self.savegame_states_box = None
        # self.make_savegame_states_box()
        self.games = GameSelect(self)
        self.savegames = SavegameSelect(self)
        self.savegame_states = SavegameStateSelect(self)

        self.games.grid(row=0, column=0, sticky="NEWS")
        self.savegames.grid(row=0, column=1, sticky="NEWS")
        self.savegame_states.grid(row=0, column=2, sticky="NEWS")
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=1)
        tk.Grid.columnconfigure(self, 2, weight=1)
        tk.Grid.columnconfigure(self, 4, weight=0)
        tk.Grid.rowconfigure(self, 0, weight=1)
        # tk.Grid.rowconfigure(self.games, 0, weight=1)
        # tk.Grid.columnconfigure(self.games, 0, weight=1)
        # tk.Grid.rowconfigure(self.savegames, 0, weight=1)
        # tk.Grid.columnconfigure(self.savegames, 0, weight=1)
        # tk.Grid.rowconfigure(self.savegame_states, 0, weight=1)
        # tk.Grid.columnconfigure(self.savegame_states, 0, weight=1)

        # self.update_games()
        # self.update_savegame_list()
        # self.update_savegame_states_box()
        self.trigger_update(2)

        def restore_function():
            """Functionality when restore button is pressed."""
            selection = self.savegame_states.get_selected()
            if selection == tuple():
                print("No game state selected!")
                return
            self.savegame_states.write_file()
        buttonframe = tk.Frame(self)
        buttonframe.grid(row=0, column=4)
        button = tk.Button(buttonframe, text="Restore", command=restore_function)
        button.grid(row=0, column=0, sticky="EW")
        button = tk.Button(self, text="Vacuum",
                           command=lambda: Vacuum(self))
        button.grid(row=0, column=4, sticky="SEW")

        check_for_updates()

    @staticmethod
    def popup(savegame_box, event):
        """Put a popup."""
        try:
            savegame_box.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            savegame_box.popup_menu.grab_release()

    @property
    def cursor(self):
        """Get a cursor from the App connection."""
        return self.connection.cursor()

    def trigger_update(self, level=2):
        """Refresh the gui."""
        if level >= 2:
            self.games.update_content()
        if level >= 1:
            self.savegames.update_content()
        if level >= 0:
            self.savegame_states.update_content()


class Vacuum(tk.Toplevel):
    """Window to select and Path to analyze and start generation."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.transient(parent)
        self.finished = False
        self.title("Vacuuming")
        progress = Progressbar(self, orient=tk.HORIZONTAL, mode='indeterminate')
        self.progress = progress
        text = tk.Label(self, text="Vacuuming in progress. Please wait...")
        text.grid(row=0, column=0)
        self.progress.grid(row=1, sticky="ews")
        self.update()
        center(self)

        thread = threading.Thread(target=vacuum)
        thread.daemon = True
        thread.start()
        while thread.is_alive():
            self.progress.step(amount=1)
            self.progress.update()
            self.update()
            time.sleep(0.01)
        self.progress.grid_forget()
        self.finished = True
        self.destroy()


def vacuum():
    """Vacuum the database. New connection for separate thread."""
    connection = database.get_connect()
    connection.execute("VACUUM")


def delete(cursor, mode, key=None, path=None):
    """Delete entry from the database."""
    statements = {
        "data": "delete from savegame_history where path = ? and date = ?",
        "savegame": "delete from games where path = ?",
        "game": "delte from games where game = ?"
    }
    sql = statements[mode]
    # TODO: Checker in thread locks database
    if mode == "data":
        assert path is not None
        assert key is not None
        print(type(path), path)
        print(type(key), key)
        cursor.execute(sql, (path, key))


def check_for_updates():
    """Look for updates, reload gui if required."""
    thread = threading.Thread(target=watch_files_caller,
                              name="UpdateSeeker",
                              daemon=True)
    thread.start()
    # watch_files_caller(self.trigger_update)


def watch_files_caller():
    """schedule!"""
    connection = database.get_connect()
    check_watched_files(connection)
    finished = time.time()
    while not STOP_EVENT.is_set():
        if time.time() >= finished + 5:
            check_watched_files(connection)
            connection.commit()
            # if changed:
            #     callback_function()
            finished = time.time()
        else:
            time.sleep(1)
    connection.close()
    # schedule = sched.scheduler()
    # schedule.enter(4, 5, watch_files_caller, argument=(connection,))


def check_watched_files(connection):
    """Search at savegame paths and make a backup."""
    cursor = connection.cursor()
    updated = []
    for path in get_paths(cursor):
        if not os.path.exists(path):
            continue
        updated.append(save_new_game(path, connection))
        connection.commit()
    return any(updated)


def main():
    """main func"""
    # connection = sqlite3.connect("Testdb.db")
    connection = database.get_connect()
    check_db(connection)
    check_watched_files(connection)
    connection.close()
    master = tk.Tk()
    master.title("Savegame Manager")
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(size=16)
    master.option_add("*Font", default_font)
    app = App(master, database.get_connect())
    app.grid(row=0, column=0, sticky="NEWS")
    tk.Grid.rowconfigure(master, 0, weight=1)
    tk.Grid.columnconfigure(master, 0, weight=1)
    tk.Grid.rowconfigure(app, 0, weight=1)
    tk.Grid.columnconfigure(app, 0, weight=1)
    # app.append_games(["Ich", "bin", "eine", "Liste"])
    master.mainloop()
    # print(connection)


if __name__ == '__main__':
    main()
