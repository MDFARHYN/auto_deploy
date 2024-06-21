import secrets

def generate_secret_key():
    return secrets.token_hex(32)

secret_key = generate_secret_key()
print("Secret Key:", secret_key)
