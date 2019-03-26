#!/usr/bin/env python3

import gnupg
from utils.encrypt import GNUPG_HOME, KEY_FILE, KEY_PASSPHRASE
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", dest="gpg_user", help="gnupg user used to create key", default=None)
    args = parser.parse_args()

    # generate key
    gpg = gnupg.GPG(gnupghome=GNUPG_HOME)
    input_data = gpg.gen_key_input(name_email=args.gpg_user, passphrase=KEY_PASSPHRASE, key_type="RSA", key_length=2048)
    key = gpg.gen_key(input_data)

    # export key
    ascii_armored_public_keys = gpg.export_keys(key.fingerprint, False)
    ascii_armored_private_keys = gpg.export_keys(key.fingerprint, True, passphrase=KEY_PASSPHRASE)
    with open(KEY_FILE, 'w') as f:
        f.write(ascii_armored_public_keys)
        f.write(ascii_armored_private_keys)