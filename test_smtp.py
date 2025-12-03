import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "phoenix.v.1.00.00@gmail.com"          # <-- put your Gmail here
SMTP_PASS = "danrjrbbyteymcxv"          # <-- 16-char app password, no spaces

msg = MIMEText("This is a test email from Project Phoenix.")
msg["Subject"] = "SMTP Test"
msg["From"] = SMTP_USER
msg["To"] = SMTP_USER  # send to yourself

try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    print("✅ Email sent successfully")
except Exception as e:
    print("❌ SMTP error:", repr(e))
