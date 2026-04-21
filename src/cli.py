import argparse
from importlib.metadata import version
from db import Database
from src.ingest import ingest_data

# single shared db instance
db = Database()


def handle_db_status(args):
    """Handles the db status subcommand. Prints connection status and optional verbose metadata."""
    conn, db_dict = db.get_db_status(args.verbose)

    if conn:
        print(f"Connection to {db.name} is successful!")
        if db_dict:
            print(
                f"database: {db_dict['db_name']}",
                f"version: {db_dict['db_version']}",
                f"database size: {db_dict['db_size']}",
                f"tables: {db_dict['tables']}",
                f"number of connections: {db_dict['db_num_connections']}",
                sep="\n",
            )
    else:
        print("Could not connect to database. Is Docker running?")


def reset_schema():
    """Drops and recreates all tables defined in ORM models."""
    print("resetting all tables (schema)...")
    db.delete_schema()
    db.create_schema()
    print("all tables have been dropped/created again!")


def handle_db_reset(args):
    """Handles the db reset subcommand. Routes to schema or table reset based on target."""
    reset_target = args.target.strip()
    table_name = args.name
    if reset_target == "schema":
        if table_name:
            print("[reset schema] does not take any arguments!")
        else:
            reset_schema()
    elif reset_target == "table":
        if not table_name:
            print(
                "reset table [name] requires a specific table name or '.'(all tables)!"
            )
        elif table_name.strip() == ".":
            db.truncate_all()
        else:
            affected_tables = db.get_dependent_tables(table_name)
            if affected_tables:
                print("The following tables will be cascaded: ", affected_tables)
                cascade_tables = input(
                    "Would you like to proceed? Enter Y or any other key to abort: "
                )
                if cascade_tables.upper() == "Y":
                    db.truncate_table(table_name)
                    print(f"Cascaded tables: {', '.join(affected_tables)}")
                else:
                    print("aborting table reset..")
            else:
                db.truncate_table(table_name)


def handle_query(args):
    """Handles the query subcommand. Allows quick insights into db table rows"""
    if args.count:
        row_cnt = db.get_table_count(args.name)
        print(f"{args.name} has {row_cnt} rows")
    # else:
    #     results = db.get_all_cols(args.name, args.limit)
    #     for row in results:
    #         print(dict(row))


def handle_ingest(args):
    """Handles the ingest subcommand. Source data file specified by input with flag."""
    ingest_data(args.file, db)


def main():
    """Entry point for the gia CLI. Builds the argument parser and routes to the correct handler."""

    __version__ = version("game-insights-api")

    parser = argparse.ArgumentParser(
        prog="gia",
        description="game-insights-api CLI",
        epilog="Thanks for using %(prog)s (game-insights-api)!",
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    # top level subcommands: db, ingest
    gia_subparsers = parser.add_subparsers(title="subcommands", dest="gia_subcommands")

    # --- ingest subcommand ---
    ingest_parser = gia_subparsers.add_parser("ingest", help="loading data to db")

    # file to ingest from
    ingest_parser.add_argument(
        "-f", "--file", help="path to file to ingest to db", action="store"
    )

    # --- db subcommand ---
    db_parser = gia_subparsers.add_parser("db", help="database utilities")
    db_subparsers = db_parser.add_subparsers(title="subcommands", dest="db_subcommands")

    # --- db query ---
    query_parser = db_subparsers.add_parser(
        "query",
        help="query information from specified db table",
        usage="gia query table_name [-c] [-l n]",
    )

    # target (which table to query)
    query_parser.add_argument(
        "name",
        metavar="table_name",
        help="name of table to query",
    )

    # get count of specified table
    query_parser.add_argument(
        "-c", "--count", help="count of table rows", action="store_true"
    )

    # limit query
    query_parser.add_argument(
        "-l", "--limit", type=int, metavar="n", help="limit results"
    )

    # --- db status ---
    status_parser = db_subparsers.add_parser(
        "status", help="get connection status to db"
    )

    # detailed output
    status_parser.add_argument(
        "-v", "--verbose", help="verbose status output", action="store_true"
    )

    # --- db reset subcommand ---
    reset_parser = db_subparsers.add_parser(
        "reset", help="reset (drop & recreate) schema or truncate table"
    )

    # target (what to reset in db)
    reset_parser.add_argument(
        "target", help="target of db reset", choices=["schema", "table"]
    )
    reset_parser.add_argument(
        "name",
        metavar="table_name",
        nargs="?",
        help="applies ONLY to reset table. Enter [.] to truncate all tables",
    )

    query_parser.set_defaults(func=handle_query)
    reset_parser.set_defaults(func=handle_db_reset)
    status_parser.set_defaults(func=handle_db_status)
    ingest_parser.set_defaults(func=handle_ingest)

    args = parser.parse_args()

    # route to the correct handler, or print help if no subcommand given
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("Please enter a valid command prompt! \n")
        parser.print_help()


if __name__ == "__main__":
    main()
