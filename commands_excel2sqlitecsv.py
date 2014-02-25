#!/usr/bin/env python

"""Takes Copy&Paste data from Excel and 
exports a tab file for .import into SQLite"""

from events import DataLoader

def export_sqlite_csv(p, events):
    for ev in events:
        print "%d\t%s" %(p, ev.tab())


if __name__== "__main__":
    participants = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    # participants = [2]

    for p in participants:
        export_sqlite_csv(p, DataLoader.load_commands(p))
