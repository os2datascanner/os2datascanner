from nacl.secret import SecretBox
from hashlib import pbkdf2_hmac

from os2datascanner.engine2 import settings


def stretch_key(password: str) -> bytes:
    """Stretches the given password into a 32-byte value by way of the PBKDF2
    key derivation function.

    Note that key stretching uses the unique identifier of this OS2datascanner
    instance as a salt. As such, two different instances will produce two
    different values from the same key."""
    if not settings.secret_value:
        raise ValueError(
                "settings.secret_value is missing; can't perform key"
                " stretching")
    return pbkdf2_hmac(
            "sha256",
            password=password.encode(),
            salt=settings.secret_value.encode(),
            iterations=100000)


def make_secret_box(password: str) -> SecretBox:
    """Returns a libsodium SecretBox for symmetric key encryption and
    decryption. The input password can be of any length; it'll be converted
    into a suitable key by the stretch_key function."""
    return SecretBox(stretch_key(password))
