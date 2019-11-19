#!/usr/bin/env python3
import i3ipc
import sys
import pickle
import os
import pwd

# logged_in_user = os.getlogin()  # does not work for non-interactive shells
logged_in_user = pwd.getpwuid(os.geteuid())[0]  # we think this is only one
PATH = "/tmp/.i3_workspace_mapping_{}".format(logged_in_user)


def showHelp():
    print(sys.argv[0] + " [save|restore]")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        showHelp()
        sys.exit(1)

    i3 = i3ipc.Connection()

    if sys.argv[1] == 'save':
        pickle.dump(i3.get_workspaces(), open(PATH, "wb"))
    elif sys.argv[1] == 'restore':
        try:
            workspace_mapping = pickle.load(open(PATH, "rb"))
        except FileNotFoundError:
            print("Can't find existing mappings...")
            sys.exit(1)

        for workspace in workspace_mapping:
            i3.command(f"workspace {workspace.name}")
            i3.command(f"move workspace to output {workspace.output}")
        for workspace in filter(lambda w: w.visible, workspace_mapping):
            i3.command(f"workspace {workspace.name}")
    else:
        showHelp()
        sys.exit(1)
