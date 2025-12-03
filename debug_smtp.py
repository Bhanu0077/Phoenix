import smtplib
import ssl

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "phoenix.v.1.00.00@gmail.com"

PASSWORDS = [
    "vpzivevrqfthzbfn", # From app.py
    "jssxptcgqhzbykdt"  # From test_mail.py
]

def test_login(password):
    print(f"Testing password: {password[:4]}...{password[-4:]}")
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, password)
            print("  [SUCCESS] Login successful!")
            return True
    except Exception as e:
        print(f"  [FAILED] Login failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting SMTP Credential Test...")
    for pwd in PASSWORDS:
        if test_login(pwd):
            print(f"\nFOUND VALID PASSWORD: {pwd}")
            break
    else:
        print("\nALL PASSWORDS FAILED.")
