import argparse
from sys import exit, stderr, argv


def commands(controller):
    parser = argparse.ArgumentParser(
        description="Add a description for the programm here"
    )

    subparsers = parser.add_subparsers(
        title="Subcommands", description="Search for help with SUBCOMMAND --help"
    )

    parser_version = subparsers.add_parser(
        "version", help="Prints out the Version of the Programm"
    )
    parser_version.set_defaults(func=controller.command_version)

    # prints help instead an exception when no arguments are given
    if len(argv) == 1:
        parser.print_help(stderr)
        exit(1)

    args = parser.parse_args()

    return args
