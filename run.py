from rnb_to_osm import app
import argparse
from rnb_to_osm.matching import match_function


# Placeholder functions
def compute(code_insee):
    print(f"Computing for {code_insee}")


def compute_all():
    print("Computing for all")


def print_match_sql(code_insee):
    print(match_function(code_insee))


def run():
    app.run(debug=True)


def main():
    parser = argparse.ArgumentParser(
        description="Run the web app or perform computations."
    )
    subparsers = parser.add_subparsers(dest="command")

    # Subparser for the 'run' command
    subparsers.add_parser("run", help="Run the web app")

    # Subparser for the 'compute' command
    compute_parser = subparsers.add_parser(
        "compute", help="Compute for a specific code_insee"
    )
    compute_parser.add_argument(
        "code_insee", type=str, help="The code_insee to compute"
    )

    # Subparser for the 'compute_all' command
    subparsers.add_parser("compute_all", help="Compute for all")

    # Subparser for the 'print_match_sql' command
    print_match_sql_parser = subparsers.add_parser(
        "print_match_sql", help="Print match SQL for a specific code_insee"
    )
    print_match_sql_parser.add_argument(
        "code_insee", type=str, help="The code_insee to print match SQL for"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "run":
        run()
    elif args.command == "compute":
        compute(args.code_insee)
    elif args.command == "compute_all":
        compute_all()
    elif args.command == "print_match_sql":
        print_match_sql(args.code_insee)


if __name__ == "__main__":
    main()
