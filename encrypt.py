#!/usr/bin/env python3

"""
file: encrypt.py

Utility to encrypt your password using gnupg.
"""

import gnupg
from getpass import getpass
import os
import json
import argparse

def get_gnupg_home():
    """
    :return: home directory of gpg
    """
    if "GNUPGHOME" in os.environ and len(os.environ["GNUPGHOME"]) > 0:
        return os.environ["GNUPGHOME"]
    else:
        if "HOME" in os.environ:
            return f"{os.environ['HOME']}/.gnupg"
        else:
            raise ValueError("Could not find home directory of user.")


CONFIGURATION_FILE = "configuration.json"
GNUPG_HOME = get_gnupg_home()
KEY_FILE = os.path.join(GNUPG_HOME, 'ccli_gpg_key.asc')

# because GnuPG >= 2.1 needs a passphrase for secret keys
# yes I know it kind of defeats the purpose, but the best they can do is have a bogus password for a key they can't
# access in a case in which I would have otherwise put no password anyway, for an account for which they can make their
# own free version if they care so much about getting your CCLI password.
# PSA: Don't make passwords like this, and don't push it to git either.
KEY_PASSPHRASE = "passphrase"  # gg


if __name__ == '__main__':
    # if user wants, can enter in a different username as used to generate the key rather than the email address
    # used for the ccli password
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", dest="gpg_user", help="gnupg user used to create key", default=None)
    args = parser.parse_args()

    if args.gpg_user is not None:
        use_different_user = True
        email_address = args.gpg_user
    else:
        use_different_user = False

    # load configuration.json file
    if os.path.exists(CONFIGURATION_FILE):
        with open(CONFIGURATION_FILE, "r") as f_r:
            config = json.load(f_r)
    else:
        config = {}

    # encrypt password
    gnupg_home_directory = get_gnupg_home()
    gpg = gnupg.GPG(gnupghome=gnupg_home_directory)

    # load key
    key_data = open(KEY_FILE).read()
    import_result = gpg.import_keys(key_data)

    if not use_different_user:
        if "ccli_email_address" in config:
            email_address = config["ccli_email_address"]
        else:
            email_address = input("User email: ")
    password = getpass(prompt="Password to encrypt: ")
    encrypted_data = gpg.encrypt(password, email_address)
    encrypted_string = str(encrypted_data)

    # save encrypted password
    if encrypted_data.ok:
        if not use_different_user:
            config["ccli_email_address"] = email_address
        config["ccli_password_encrypted"] = encrypted_string
        with open(CONFIGURATION_FILE, "w") as f_wr:
            json.dump(config, f_wr, indent=2)
        print(f"Success! User email and encrypted password saved to {CONFIGURATION_FILE}")
    else:  # error in encryption process
        print("------------")
        print('ok: ', encrypted_data.ok)
        print('status: ', encrypted_data.status)
        print('stderr: ', encrypted_data.stderr)
        print('encrypted_string: ', encrypted_string)
