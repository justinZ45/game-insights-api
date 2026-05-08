from importlib.metadata import version
from src.db.db import Database
from src.db.ingest import ingest_file_data, seed_from_url
import pprint
import argparse



CORGIS_URL = (
    "https://corgis-edu.github.io/corgis/datasets/json/video_games/video_games.json"
)

def handle_db_status(args, db):
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
        print(
            "Could not connect to database for status. Check your .env configuration and verify Docker is running."
        )


def reset_schema(db):
    """Drops and recreates all tables defined in ORM models."""
    print("resetting all tables (schema)...")
    db.delete_schema()
    db.create_schema()
    print("all tables have been dropped/created again!")


def handle_db_reset(args, db):
    """Handles the db reset subcommand. Routes to schema or table reset based on target."""
    reset_target = args.target.strip()
    table_name = args.name
    if reset_target == "schema":
        if table_name:
            print("[reset schema] does not take any arguments!")
        else:
            reset_schema(db)
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


def handle_query(args, db):
    """Handles the query subcommand. Allows quick insights into db table rows"""
    if args.count:
        row_cnt = db.get_table_count(args.name)
        print(f"{args.name} has {row_cnt} rows")
    else:
        results = db.get_all_cols(args.name, args.limit)  # full table query with limit
        if results is None:
            return
        if len(results) == 0:
            print(f"{args.name} has no data!")
        else:
            for row in results:
                pprint.pp(row)
                print("-" * 40)


def handle_ingest(args, db):
    """
    Handles the ingest subcommand. 
    """
    if args.file:
        print(f"Ingesting from local file: {args.file}...")
        ingest_file_data(args.file, db)
        
    elif args.url:
        print(f"Ingesting from custom URL: {args.url}...")
        seed_from_url(db, args.url)
        
    else:
        print("No source specified. Defaulting to the CORGIS Dataset Project...")
        print(f"Ingesting from URL: {CORGIS_URL}...") # no flags, default to corgis
        seed_from_url(db, CORGIS_URL)


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

    # overrides
    parser.add_argument(
    "-H","--host",
    default=None,
    metavar="hostname",
    help="database host override e.g. 192.168.1.100"
    )

    parser.add_argument(
        "-p","--port",
        type=int,
        default=None,
        metavar="port",
        help="database port override e.g. 5432"
    )

    parser.add_argument("-u", "--user", default=None, help="DB user override")
    parser.add_argument("-db", "--dbname", default=None, help="DB name override")

    gia_subparsers = parser.add_subparsers(title="subcommands", dest="gia_subcommands")

    ingest_parser = gia_subparsers.add_parser("ingest", help="loading data to db")



    ingest_source = ingest_parser.add_mutually_exclusive_group(required=False)

    # Add both options to the group
    ingest_source.add_argument(
        "-f", "--file", 
        metavar="path", 
        help="path to local JSON file to ingest"
    )

    ingest_source.add_argument(
        "-u", "--url",
        metavar="url",
        # We remove the default here so we can tell if the user actually typed -u
        default=None, 
        help="fetch and ingest latest data from specified url."
    )

    db_parser = gia_subparsers.add_parser("db", help="database utilities")
    db_subparsers = db_parser.add_subparsers(title="subcommands", dest="db_subcommands")

    query_parser = db_subparsers.add_parser(
        "query",
        help="query information from specified db table",
        usage="gia query table_name [-c] [-l n]",
    )

    query_parser.add_argument(
        "name",
        metavar="table_name",
        help="name of table to query",
    )

    query_parser.add_argument(
        "-c", "--count", help="count of table rows", action="store_true"
    )

    query_parser.add_argument(
        "-l", "--limit", type=int, metavar="n", help="limit results"
    )

    status_parser = db_subparsers.add_parser(
        "status", help="get connection status to db"
    )

    status_parser.add_argument(
        "-v", "--verbose", help="verbose status output", action="store_true"
    )

    reset_parser = db_subparsers.add_parser(
        "reset", help="reset (drop & recreate) schema or truncate table"
    )

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



    # instantiate db AFTER overrides are applied
    db = Database(host=args.host, port=args.port, user=args.user, db_name=args.dbname)
    

    # route to the correct handler, or print help if no subcommand given
    if hasattr(args, "func"):
        args.func(args, db)
    else:
        print("Please enter a valid command prompt! \n")
        parser.print_help()


if __name__ == "__main__":
    main()
