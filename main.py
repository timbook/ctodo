#!/usr/bin/env python3

import os
import sys
import json
import time
import click
import curses
import curses.textpad

file = os.path.expandvars('$HOME/.lister/test.json')

class Task:
    def __init__(self, done, text):
        self.done = done
        self.text = text

    def to_str(self):
        sym = 'X' if self.done else ' '
        return f"[{sym}] {self.text}"

    def toggle(self):
        self.done = not self.done

def write_tasks(tasks, file, echo=True):
    tasks_list = [[t.done, t.text] for t in tasks]
    with open(file, 'w') as f:
        json.dump(tasks_list, f)

def read_tasks(file):
    dir_path = os.path.expandvars('$HOME/.lister')
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    # Create empty file
    if not os.path.exists(file):
        write_tasks([], file)


    with open(file, 'r') as f:
        task_list = json.load(f)
        return [Task(done, text) for done, text in task_list]

def add_task(i, tasks, stdscr):
    stdscr.clear()
    stdscr.addstr(0, 1, "Add a new TODO item (Ctrl-G to finish):")

    # (nlines, ncols, beginy, beginx)
    win = curses.newwin(1, 43, 2, 2)
    box = curses.textpad.Textbox(win)

    # (win, uly, ulx, lry, lrx)
    curses.textpad.rectangle(stdscr, 1, 1, 3, 42)

    stdscr.refresh()
    text = box.edit()

    tasks.insert(i, Task(False, text))

def delete_task(i, tasks, stdscr):
    undo_cache = tasks.copy()
    del tasks[i]
    return undo_cache

def curses_app(stdscr, tasks, file):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)

    row = 0
    last_time = 0
    undo_cache = []
    key = None

    while True:
        stdscr.clear()
        stdscr.addstr(0, 1, "TODO LIST: (q to quit)")

        if not tasks:
            stdscr.addstr(1, 1, "Press o to creat your first task!")

        for i, task in enumerate(tasks):
            if i == row:
                stdscr.addstr(i + 1, 0, "> " + task.to_str(), curses.color_pair(1))
            else:
                stdscr.addstr(i + 1, 0, "  " + task.to_str())

        key = stdscr.getch()

        if key == ord('j'):
            row = min(row + 1, len(tasks) - 1)
        elif key == ord('k'):
            row = max(0, row - 1)
        elif key == ord(' '):
            tasks[row].toggle()
        elif key == ord('O'):
            add_task(row, tasks, stdscr)
        elif key == ord('o'):
            add_task(row + 1, tasks, stdscr)
            row = min(row + 1, len(tasks) - 1)
        elif key == ord('d'):
            now = time.time()
            if now - last_time < 0.5:
                undo_cache = delete_task(row, tasks, stdscr)
            last_time = now
        elif key == ord('u'):
            if undo_cache:
                tasks = undo_cache.copy()
                undo_cache.clear()
        elif key == ord('g'):
            row = 0
        elif key == ord('G'):
            row = len(tasks) - 1
        elif key == ord('q'):
            break

        write_tasks(tasks, file)

@click.command()
@click.option('-d', '--delete', is_flag=True, help='Delete file')
@click.option('-l', '--list', 'list_', is_flag=True, help='List possible files')
@click.argument('file', required=False)
def main(delete, list_, file):
    has_file = file
    file = os.path.expandvars(f"$HOME/.lister/{file}.json")

    if delete:
        if not has_file:
            print(f"Please provide a list to delete!")
            sys.exit(1)

        if not os.path.exists(file):
            print(f"{file} does not exist!")
            sys.exit(1)
        else:
            os.remove(file)
            print(f"{file} deleted!")
    elif list_:
        files = os.listdir(os.path.expandvars('$HOME/.lister'))
        print()
        print(f"Available lists:")
        print('='*16)
        for f in files:
            print(f"  - {f.replace('.json', '')}")
        print()
    else:
        if not has_file:
            print(f"Please provide a list to edit!")
            sys.exit(1)

        tasks = read_tasks(file)

        curses.wrapper(curses_app, tasks, file)
        write_tasks(tasks, file)

if __name__ == '__main__':
    main()
    sys.exit(0)

# TODO:
# - Package into a command line library
# - "help" screen with --help or -h
# - Can only undo last step. Recursive logic?
