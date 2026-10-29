# This file should be placed in src/azure_web_app, and should be called db.py
"""Database connection helpers."""

# All of the app's SQL lives in the Database class below. The rest of the app
# calls its methods (db.username_exists(...), db.add_user(...)) and never writes
# SQL itself. If you ever need to change a query, this is the only file to look in.
#
# Each request gets at most one Database. Call get_db() to get it: the first call
# during a request opens a connection, and Flask closes it automatically when the
# request ends. You never need to open or close a connection yourself.

import os

import mssql_python
from flask import Flask, g

from ._constants import CONNECTION_STRING_VARIABLE


def get_connection_string() -> str:
    """Read the connection string from the environment."""
    return os.environ[CONNECTION_STRING_VARIABLE]

class Database:
    """One connection to the database, plus a method for every query the app runs."""

    def __init__(self, connection: mssql_python.Connection):
        self.connection = connection

    def close(self) -> None:
        """Close the connection.

        With mssql-python, "closing" actually hands the connection back to the
        driver's built-in connection pool, so the next request can reuse it
        instead of logging in to Azure all over again. Anything that was not
        committed is rolled back.
        """
        self.connection.close()

    # Every method below follows the same pattern:
    #   1. Open a cursor (the object you run queries through). The `with`
    #      block closes it for us when we're done, even if something goes wrong.
    #   2. Run the query, using ? placeholders for every value.
    #   3. If the query changed anything (INSERT, UPDATE, DELETE), commit.
    #      Nothing is saved until you commit!
    #
    # Why ? placeholders? The driver sends the values separately from the SQL,
    # so a username like "x'; DROP TABLE Users; --" is treated as a weird
    # username instead of as SQL. Never build SQL with f-strings.

    def username_exists(self, username: str) -> bool:
        """Return True if a user with this username is already in the database."""
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM Users WHERE username = ?", (username,))
            return cursor.fetchone() is not None

    def add_user(self, username: str, hashed_password: str, display_name: str) -> bool:
        """Add a new user. Return False if the username is already taken."""
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(
                    "INSERT INTO Users (username, password, display_name) VALUES (?, ?, ?)",
                    (username, hashed_password, display_name),
                )
            except mssql_python.IntegrityError:
                # Register already checks username_exists first, so how could we
                # get here? If two people register the same name at the same
                # moment, both can pass that check before either INSERT runs. The
                # UNIQUE constraint on the username column catches the second one.
                self.connection.rollback()
                return False
        self.connection.commit()
        return True
    
    def get_login_info(self, username: str):
        """Return the user's login details, or None if not found."""
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT password, display_name, last_login
                FROM Users
                WHERE username = ?
                """,
                (username,),
            )
            return cursor.fetchone()

def get_db() -> Database:
    """Return this request's Database, connecting on first use."""
    # `g` is Flask's per-request storage (remember it from the API activity?).
    # Anything we put on it disappears when the request ends, so each request
    # gets its own Database, and requests never share one.
    if "db" not in g:
        g.db = Database(mssql_python.connect(get_connection_string()))
    return g.db


def close_db(exception: BaseException | None = None) -> None:
    """Close this request's Database, if the request opened one.

    Flask calls this automatically at the end of every request (see setup_for_app).
    Flask passes in the exception that ended the request (or None), which we
    don't need, but the function still has to accept it.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def setup_for_app(app: Flask) -> None:
    """Hook the database into the app. Call this from create_app()."""
    app.teardown_appcontext(close_db)
