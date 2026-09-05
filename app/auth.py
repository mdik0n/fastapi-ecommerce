from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
        Converts password into hash
    """

    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
        Checks if entered password corresponds to saved hash
    """

    return password_hash.verify(plain_password, hashed_password)
