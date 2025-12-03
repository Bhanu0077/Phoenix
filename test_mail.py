import smtplib
import ssl
from email.message import EmailMessage
import random

def generate_code(length=6):
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def build_verification_email(to_email, code):
    msg = EmailMessage()
    msg["Subject"] = "Your MyApp verification code"
    msg["From"] = "MyApp Security <no-reply@yourdomain.com>"
    msg["To"] = to_email

    # Plain text fallback
    text_body = f"""\
Your MyApp verification code

Use this code to verify your email address:

{code}

If you did not request this, you can safely ignore this email.
"""

        # HTML body – dark, neon “Phoenix” style
    html_body = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Your MyApp verification code</title>
</head>
<body style="margin:0;padding:0;background-color:#020617;background-image:radial-gradient(circle at top,#1f2937 0,#020617 55%,#000105 100%);background-repeat:no-repeat;background-size:cover;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:32px 16px 40px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:520px;border-radius:24px;overflow:hidden;background:rgba(15,23,42,0.96);box-shadow:0 0 40px rgba(56,189,248,0.35);">
          <!-- Top bar / logo -->
          <tr>
            <td style="padding:16px 24px 8px;border-bottom:1px solid rgba(148,163,184,0.25);">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td align="left" style="font-size:18px;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;">
                    <span style="background-image:linear-gradient(90deg,#22d3ee,#a855f7);-webkit-background-clip:text;background-clip:text;color:#22d3ee;/* fallback */-webkit-text-fill-color:transparent;">
                      PHOENIX&nbsp;AI
                    </span>
                  </td>
                  <td align="right" style="font-size:11px;color:#9ca3af;">
                    Security&nbsp;Center
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main content -->
          <tr>
            <td style="padding:28px 24px 8px;">
              <p style="margin:0 0 10px;font-size:12px;letter-spacing:0.24em;text-transform:uppercase;color:#38bdf8;text-align:center;">
                Awaken the Phoenix
              </p>
              <h1 style="margin:0 0 12px;font-size:24px;line-height:1.3;text-align:center;background-image:linear-gradient(90deg,#22d3ee,#a855f7);-webkit-background-clip:text;background-clip:text;color:#22d3ee;-webkit-text-fill-color:transparent;">
                Your verification code
              </h1>
              <p style="margin:0 0 18px;font-size:14px;line-height:1.6;color:#e5e7eb;text-align:center;">
                Use the one-time code below to verify your email address and continue
                securely into your Phoenix experience.
              </p>

              <!-- Code “pill” with glow -->
              <div style="margin:26px 0 12px;text-align:center;">
                <span style="display:inline-block;padding:14px 28px;border-radius:999px;border:1px solid rgba(56,189,248,0.7);background:radial-gradient(circle at top,#0f172a,#020617);box-shadow:0 0 25px rgba(56,189,248,0.45);font-size:28px;letter-spacing:0.42em;font-weight:700;color:#f9fafb;">
                  {code}
                </span>
              </div>

              <!-- CTA button -->
              <div style="margin:8px 0 24px;text-align:center;">
                <a href="#" style="display:inline-block;padding:12px 32px;border-radius:999px;background-image:linear-gradient(90deg,#22d3ee,#a855f7);text-decoration:none;font-size:14px;font-weight:600;color:#020617;box-shadow:0 0 30px rgba(56,189,248,0.7);">
                  Verify email
                </a>
              </div>

              <p style="margin:0 0 10px;font-size:12px;line-height:1.6;color:#9ca3af;text-align:center;">
                This code will expire in <strong>10 minutes</strong>. If you didn’t request this,
                you can safely ignore this email.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:16px 24px 20px;background:linear-gradient(to right,#020617,#030712);font-size:11px;line-height:1.5;color:#6b7280;text-align:center;border-top:1px solid rgba(30,64,175,0.7);">
              © {2025} MyApp · Phoenix AI Experience<br />
              You’re receiving this email because someone attempted to sign in with this address.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    return msg

def send_email(msg):
    SMTP_HOST = "smtp.gmail.com"       # or your SMTP server
    SMTP_PORT = 465                    # 465 for SSL, 587 for STARTTLS
    SMTP_USER = "phoenix.v.1.00.00@gmail.com"
    SMTP_PASS = "vpzivevrqfthzbfn"    # Correct app password from app.py

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

if __name__ == "__main__":
    print("--- Email Test Script ---")
    recipient = input("Enter recipient email: ").strip()
    if not recipient:
        print("No email provided. Exiting.")
        exit()
        
    code = generate_code()
    email_msg = build_verification_email(recipient, code)
    try:
        send_email(email_msg)
        print(f"SUCCESS: Sent verification code {code} to {recipient}")
    except Exception as e:
        print(f"ERROR: Failed to send email. {e}")
