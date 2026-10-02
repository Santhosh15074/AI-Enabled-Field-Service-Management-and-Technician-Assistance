"""Create an admin or technician account from the command line.

The registration page only creates customers, so the first admin is created here:

    python scripts/create_user.py --role admin --name "Santhosh Kumar" --email admin@example.com
    python scripts/create_user.py --role technician --name "Ravi" --email ravi@example.com --skill-area "Electrical"

The password is asked for interactively so it never appears in your shell history.
"""

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.accounts import AccountError, create_user  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import Role  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--role", required=True, choices=[r.value for r in Role])
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--skill-area", help="Technicians only, e.g. Electrical, HVAC, Plumbing")
    parser.add_argument("--phone", help="Customers only")
    parser.add_argument("--address", help="Customers only")
    args = parser.parse_args()

    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Confirm password: "):
        print("The two passwords do not match.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        try:
            user = create_user(
                db,
                name=args.name,
                email=args.email,
                password=password,
                role=Role(args.role),
                skill_area=args.skill_area,
                phone=args.phone,
                address=args.address,
            )
        except AccountError as error:
            print(error, file=sys.stderr)
            return 1
    print(f"Created {user.role} account for {user.email} (id {user.id}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
