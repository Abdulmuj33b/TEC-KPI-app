import getpass

import psycopg
from pwdlib import PasswordHash
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"


def main():
    email = input("Administrator email: ").strip().lower()
    password = getpass.getpass("New password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm new password: ")

    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    hashed = PasswordHash.recommended().hash(password)

    with psycopg.connect(Settings().database_url) as conn:
        result = conn.execute(
            """
            UPDATE users
            SET password_hash = %s, updated_at = NOW()
            WHERE lower(email) = lower(%s)
              AND role = 'administrator'
              AND is_active = TRUE
            RETURNING id
            """,
            (hashed, email),
        ).fetchone()

        if result is None:
            raise SystemExit(
                "No active administrator found for that email."
            )

    print("Administrator password reset successfully.")


if __name__ == "__main__":
    main()
