#!/usr/bin/env python3
"""Script to create admin user credentials for .env file."""

import getpass
import secrets

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    print("=" * 60)
    print("SLURM Usage History - Admin User Creation")
    print("=" * 60)
    print()

    username = input("Enter admin username: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        return

    password = getpass.getpass("Enter admin password: ")
    if not password:
        print("Error: Password cannot be empty")
        return

    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("Error: Passwords do not match")
        return

    # Hash the password
    password_hash = pwd_context.hash(password)

    # Generate a secret key for JWT
    secret_key = secrets.token_urlsafe(32)

    print()
    print("=" * 60)
    print("Admin User Created Successfully!")
    print("=" * 60)
    print()
    print("Add the following to your backend/.env file:")
    print()
    print(f"ADMIN_USERS={username}:{password_hash}")
    print(f"ADMIN_SECRET_KEY={secret_key}")
    print()
    print("IMPORTANT:")
    print("  - Keep these credentials secure")
    print("  - The password hash cannot be reversed")
    print("  - Store the original password in a secure location")
    print("  - To add more admins, use comma-separated format:")
    print(f"    ADMIN_USERS={username}:{password_hash},admin2:hash2")
    print()


if __name__ == "__main__":
    main()
