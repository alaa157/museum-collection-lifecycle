from app.security.passwords import hash_password, verify_password


def test_password_hash_is_not_plaintext():
    password = "MuseumStrongPassword123!"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("WrongPassword123!", password_hash)
