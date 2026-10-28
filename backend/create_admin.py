import getpass
import re

import psycopg
from pwdlib import PasswordHash
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"


def main():
    settings = Settings()
    hasher = PasswordHash.recommended()

    name = input("Administrator full name: ").strip()
    email = input("Administrator email: ").strip().lower()

    if not name or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise SystemExit("A valid name and email are required.")

    password = getpass.getpass("New password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")

    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    encoded_password = hasher.hash(password)

    with psycopg.connect(settings.database_url) as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE lower(email) = %s",
            (email,),
        ).fetchone()

        if existing:
            raise SystemExit("That email already has an account.")

        conn.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, 'administrator')
            """,
            (name, email, encoded_password),
        )

    print("Administrator account created successfully.")


if __name__ == "__main__":
    main()
