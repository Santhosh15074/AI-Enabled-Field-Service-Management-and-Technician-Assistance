"""Create a Sollu operator: a login for the config portal (/config).

This is the only thing configured from the command line, because the config portal needs a
first operator to log in at all. Everything else (shops, owners, technicians, plans, password
resets) is done in the portal.

    python scripts/create_operator.py --name "Santhosh Kumar" --email santhosh@example.com

The password is asked for interactively so it never appears in your shell history.
"""

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.accounts import AccountError, create_operator  # noqa: E402
from app.database import SessionLocal  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True, help="The operator logs in to the config portal with this")
    args = parser.parse_args()

    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Confirm password: "):
        print("The two passwords do not match.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        try:
            operator = create_operator(db, name=args.name, email=args.email, password=password)
        except AccountError as error:
            print(error, file=sys.stderr)
            return 1
    print(f"Created operator {operator.email}. Log in at /config.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
