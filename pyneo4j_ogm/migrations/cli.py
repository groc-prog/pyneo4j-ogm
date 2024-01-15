import argparse


def cli():
    parser = argparse.ArgumentParser(prog="my_program")
    parser.add_argument("command", choices=["init"], help="the command to run")

    args = parser.parse_args()

    if args.command == "init":
        print("Initialization has been triggered!")
