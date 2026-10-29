# This file should be placed in src/azure_web_app, and should be called _constants.py
# The leading underscore in the file name is a Python convention meaning
# "internal to this package": it's for our own code, not for anyone importing
# our package from outside.
# 
# Other files import what they need, for example:
#
#    from azure_web_app._constants import MAX_USERNAME_LENGTH
"""Constants used throughout the app"""

import re

# ---------------------------------------------------------------------------
# Secrets and configuration
# ---------------------------------------------------------------------------

SECRET_ENV_FILE = ".secret.env"
"""The name of the file that contains secrets (like the database connection string) in development."""

# NOTE: This is NOT the the connection string itself. Rather, it is the name of the environment variable.
CONNECTION_STRING_VARIABLE = "AZURE_SQL_CONNECTIONSTRING"
""" The name of the environment variable that holds the database connection string."""

# ---------------------------------------------------------------------------
# Account rules
# ---------------------------------------------------------------------------

MAX_USERNAME_LENGTH = 20
MIN_PASSWORD_LENGTH = 8

# These match the patterns in auth.js. We check on the server too, because
# anyone can skip our JavaScript and send a request straight to /register
# (try it with Postman!). Client-side validation is a convenience for the user.
# Server-side validation is the one that actually protects you.
USERNAME_PATTERN = re.compile(rf"[A-Za-z0-9]{{1,{MAX_USERNAME_LENGTH}}}")
# \x21-\x7E is the range of printable ASCII characters from ! to ~ (no spaces).
PASSWORD_PATTERN = re.compile(rf"[\x21-\x7E]{{{MIN_PASSWORD_LENGTH},}}")

# Login uses the same message for "no such user" and "wrong password".
BAD_LOGIN_MESSAGE = "Incorrect username or password"