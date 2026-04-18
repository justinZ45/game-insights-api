import argparse
from importlib.metadata import version
from db import Database


def reset_schema():
    db = Database()
    print("resetting all tables (schema)...")
    db.delete_schema()
    db.create_schema()
    print("all tables have been dropped/created again!")


def db_utils(args):
    reset_type = args.reset.strip()
    table_name = args.name
    if reset_type == "schema":
        if table_name:
            print("[--reset schema] does not take any arguments!")
        else:
            reset_schema()
    elif reset_type == "table":
        if not table_name:
            print(
                "--reset table [name] requires a specific table name or '.'(all tables)!"
            )
        elif table_name.strip() == ".":
            print("truncating all tables!")
        else:
            print("deleting specific table!")


def main():

    __version__ = version("game-insights-api")

    parser = argparse.ArgumentParser(
        prog="gia",
        description="List the content of a directory",
        epilog="Thanks for using %(prog)s (game-insights-api)!",
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers(
        title="subcommands", help="subcommands", dest="subcommands"
    )
    db_parser = subparsers.add_parser("db", help="database utilities")
    db_parser.add_argument(
        "-r", "--reset", help="reset schema or table", choices=["schema", "table"]
    )
    db_parser.add_argument(
        "name",
        metavar="table_name",
        nargs="?",
        help="applies ONLY to --reset table. Enter [.] to truncate all tables",
    )
    db_parser.set_defaults(func=db_utils)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
