import bcrypt

password = "admin123"
# Generate salt and hash
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(f"Generated hash: {hashed.decode('utf-8')}")
