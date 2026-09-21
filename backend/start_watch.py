from app.config import get_settings
from app.db import SessionLocal, init_db
from app.models import User
from app.main import get_password_hash


def create_user(
    username: str, email: str, password: str, is_admin: bool = False
) -> None:
    """Create a user via terminal."""
    init_db()
    hashed_password = get_password_hash(password)
    with SessionLocal() as db:
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_admin=is_admin,
        )
        db.add(user)
        db.commit()
        print(f"User {username} created successfully.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create users or start Gmail watch.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create user command
    create_parser = subparsers.add_parser("create-user", help="Create a new user")
    create_parser.add_argument("--username", required=True, help="Username")
    create_parser.add_argument("--email", required=True, help="Email")
    create_parser.add_argument("--password", required=True, help="Password")
    create_parser.add_argument("--admin", action="store_true", help="Create as admin")

    # Start watch command
    args = parser.parse_args()

    if args.command == "create-user":
        create_user(args.username, args.email, args.password, args.admin)
