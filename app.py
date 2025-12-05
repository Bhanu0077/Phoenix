import os
import sqlite3
import smtplib
import ssl
import random
import socket
import requests
import urllib3
from datetime import datetime, timedelta
from email.message import EmailMessage
from functools import wraps
from openai import OpenAI

from voice_engine import parse_command

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    render_template_string,
    jsonify,
)
from werkzeug.security import generate_password_hash, check_password_hash


PHOENIX_SECRET_KEY = "5fd611b3f3b7faea028d6250b3662f061e628edc3f52868b0e9ad38a7969e184"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # SSL port
SMTP_USER = "phoenix.v.1.00.00@gmail.com"
SMTP_PASS = "vpzivevrqfthzbfn"  # app password, NOT your main password

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "phoenix.db")

app = Flask(__name__, template_folder="Templates")
app.secret_key = PHOENIX_SECRET_KEY
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)


def get_db():
    """Create a new SQLite connection per call."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Ensure the SQLite schema exists before handling requests."""
    conn = get_db()
    cur = conn.cursor()

    # Create users table (only if not exists)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_verified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Add username column if missing
    try:
        cur.execute("ALTER TABLE users ADD COLUMN username TEXT;")
    except:
        pass  # already exists

    # Add is_admin column if missing
    try:
        cur.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0;")
    except:
        pass  # already exists

    # Create codes table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            purpose TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            is_used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )

    conn.commit()
    conn.close()

   

# ---------- EMAIL / CODES ----------

def generate_code(length: int = 6) -> str:
    """Generate a numeric code of given length."""
    return "".join(str(random.randint(0, 9)) for _ in range(length))
# Hello Sushath

def build_verification_email(to_email: str, subject: str, code: str) -> EmailMessage:
    """
    Build a dark, neon 'Phoenix' style HTML email with a verification code.
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    # Plain text fallback
    text_body = f"""Your Project Phoenix verification code

Use this code to continue:

{code}

If you did not request this, you can safely ignore this email.
"""

    # HTML body – dark, neon “Phoenix” style
    html_body = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{subject}</title>
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
                    <span style="background-image:linear-gradient(90deg,#22d3ee,#a855f7);-webkit-background-clip:text;background-clip:text;color:#22d3ee;-webkit-text-fill-color:transparent;">
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

              <!-- Code "pill" with glow -->
              <div style="margin:26px 0 12px;text-align:center;">
                <span style="display:inline-block;padding:14px 28px;border-radius:999px;border:1px solid rgba(56,189,248,0.7);background:radial-gradient(circle at top,#0f172a,#020617);box-shadow:0 0 25px rgba(56,189,248,0.45);font-size:28px;letter-spacing:0.42em;font-weight:700;color:#f9fafb;">
                  {code}
                </span>
              </div>

              <!-- CTA button -->
              <div style="margin:8px 0 24px;text-align:center;">
                <a href="http://127.0.0.1:5000/verify-signup" style="display:inline-block;padding:12px 32px;border-radius:999px;background-image:linear-gradient(90deg,#22d3ee,#a855f7);text-decoration:none;font-size:14px;font-weight:600;color:#020617;box-shadow:0 0 30px rgba(56,189,248,0.7);">
                  Verify email
                </a>
              </div>

              <p style="margin:0 0 10px;font-size:12px;line-height:1.6;color:#9ca3af;text-align:center;">
                This code will expire in <strong>10 minutes</strong>. If you didn&apos;t request this,
                you can safely ignore this email.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:16px 24px 20px;background:linear-gradient(to right,#020617,#030712);font-size:11px;line-height:1.5;color:#6b7280;text-align:center;border-top:1px solid rgba(30,64,175,0.7);">
              © 2025 Project Phoenix · Phoenix AI Experience<br />
              You&apos;re receiving this email because someone attempted to sign in with this address.
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


def send_email(to_email: str, subject: str, code: str) -> bool:
    if not (SMTP_USER and SMTP_PASS):
        print("SMTP credentials missing.")
        return False

    msg = build_verification_email(to_email, subject, code)

    

    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"EMAIL SENT SUCCESSFULLY to {to_email}")
        return True
    except Exception as exc:
        print("SMTP ERROR:", exc)
        return False



# ---------- HELPERS / AUTH ----------

def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "error")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "error")
            return redirect(url_for("login"))
        
        conn = get_db()
        user = conn.execute("SELECT is_admin FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        conn.close()

        if not user or not user["is_admin"]:
            flash("Admin access required.", "error")
            return redirect(url_for("dashboard"))
        
        return view_func(*args, **kwargs)

    return wrapped


def store_code(user_id: int, purpose: str) -> str:
    code = generate_code()
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()

    conn = get_db()
    conn.execute(
        """
        INSERT INTO codes (user_id, code, purpose, expires_at, is_used)
        VALUES (?, ?, ?, ?, 0)
        """,
        (user_id, code, purpose, expires_at),
    )
    conn.commit()
    conn.close()
    return code


def get_user_by_email(email: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def verify_code(user_id: int, code: str, purpose: str):
    """Verify a code and check if it's valid and not expired."""
    conn = get_db()
    row = conn.execute(
        """
        SELECT * FROM codes
        WHERE user_id = ? AND code = ? AND purpose = ? AND is_used = 0
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id, code, purpose),
    ).fetchone()
    conn.close()
    
    if row:
        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at <= datetime.utcnow():
            return None  # Code expired
    
    return row


# ---------- ROUTES ----------

@app.route("/")
def landing():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("signup"))

        existing_user = get_user_by_email(email)
        if existing_user:
            flash("Email already registered. Please login.", "error")
            return redirect(url_for("login"))

        password_hash = generate_password_hash(password)
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (email, password_hash, is_verified) VALUES (?, ?, 0)",
            (email, password_hash),
        )
        user_id = cur.lastrowid
        conn.commit()
        conn.close()

        code = store_code(user_id, "signup")
        sent = send_email(
            email,
            "Project Phoenix - Verify your email",
            code,
        )
        if not sent:
            flash(
                "Could not send verification email. Please check SMTP settings.",
                "warning",
            )

        session["pending_user_id"] = user_id
        flash("Verification code sent to your email.", "success")
        return redirect(url_for("verify_signup"))

    return render_template("register.html")


@app.route("/verify-signup", methods=["GET", "POST"])
def verify_signup():
    pending_user_id = session.get("pending_user_id")
    if not pending_user_id:
        flash("Please signup first.", "error")
        return redirect(url_for("signup"))

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if not code:
            flash("Verification code is required.", "error")
            return redirect(url_for("verify_signup"))

        code_row = verify_code(pending_user_id, code, "signup")
        if not code_row:
            flash("Invalid or expired verification code.", "error")
            return redirect(url_for("verify_signup"))

        conn = get_db()
        conn.execute("UPDATE users SET is_verified = 1 WHERE id = ?", (pending_user_id,))
        conn.execute("UPDATE codes SET is_used = 1 WHERE id = ?", (code_row["id"],))
        conn.commit()
        conn.close()

        session.pop("pending_user_id", None)
        flash("Email verified. You can now login.", "success")
        return redirect(url_for("login"))

    # Get email to display in template
    conn = get_db()
    user = conn.execute("SELECT email FROM users WHERE id = ?", (pending_user_id,)).fetchone()
    conn.close()
    
    email_sent_to = user["email"] if user else "your email"

    return render_template("enter_verification_code.html", email_sent_to=email_sent_to)


@app.route("/resend-verification", methods=["POST"])
def resend_verification():
    """Resend verification code for pending signup."""
    pending_user_id = session.get("pending_user_id")
    if not pending_user_id:
        flash("No pending verification found. Please signup first.", "error")
        return redirect(url_for("signup"))

    conn = get_db()
    user = conn.execute("SELECT email FROM users WHERE id = ?", (pending_user_id,)).fetchone()
    conn.close()

    if not user:
        flash("User not found.", "error")
        session.pop("pending_user_id", None)
        return redirect(url_for("signup"))

    code = store_code(pending_user_id, "signup")
    sent = send_email(
        user["email"],
        "Project Phoenix - Verify your email",
        code,
    )
    
    if sent:
        flash("Verification code resent to your email.", "success")
    else:
        flash(
            "Could not send verification email. Please check SMTP settings or try again later.",
            "warning",
        )

    return redirect(url_for("verify_signup"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        user = get_user_by_email(email)

        # Invalid login
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        # Not verified
        if not user["is_verified"]:
            session["pending_user_id"] = user["id"]
            # Send a new verification code
            code = store_code(user["id"], "signup")
            sent = send_email(
                email,
                "Project Phoenix - Verify your email",
                code,
            )
            if sent:
                flash("Please verify your email before logging in. A new verification code has been sent.", "warning")
            else:
                flash("Please verify your email before logging in. Could not send verification email.", "warning")
            return redirect(url_for("verify_signup"))

        # Login success
        session["user_id"] = user["id"]
        session["email"] = user["email"]

        # 🚀 NEW PART — check if username exists
        if not user["username"]:
            return redirect(url_for("name"))  # redirect to the username page

        flash("Welcome back!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")
@app.route("/name", methods=["GET", "POST"])
@login_required
def name():
    if request.method == "POST":
        username = request.form.get("username").strip()

        conn = get_db()
        conn.execute("UPDATE users SET username = ? WHERE id = ?", (username, session["user_id"]))
        conn.commit()
        conn.close()

        session["username"] = username

        return redirect(url_for("dashboard"))

    return render_template("name.html")
@app.route("/update_username", methods=["POST"])
@login_required
def update_username():
    username = request.form.get("username").strip()

    conn = get_db()
    conn.execute("UPDATE users SET username = ? WHERE id = ?", (username, session["user_id"]))
    conn.commit()
    conn.close()

    session["username"] = username  # update current session

    flash("Username updated successfully!", "success")
    return redirect(url_for("dashboard"))



@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = get_user_by_email(email)

        if not user:
            flash("If this email exists, a reset code has been sent.", "info")
            return redirect(url_for("login"))

        code = store_code(user["id"], "reset")
        sent = send_email(
            email,
            "Project Phoenix - Password reset code",
            code,
        )
        if not sent:
            flash(
                "Could not send reset email. Please check SMTP settings.",
                "warning",
            )
        session["reset_user_id"] = user["id"]
        flash("If this email exists, a reset code has been sent.", "info")
        return redirect(url_for("reset_password"))

    return render_template("forgot-password.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    reset_user_id = session.get("reset_user_id")
    if not reset_user_id:
        flash("Please request a reset code first.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        new_password = request.form.get("password", "").strip()

        if not code or not new_password:
            flash("Code and new password are required.", "error")
            return redirect(url_for("reset_password"))

        code_row = verify_code(reset_user_id, code, "reset")
        if not code_row:
            flash("Invalid or expired code.", "error")
            return redirect(url_for("reset_password"))

        password_hash = generate_password_hash(new_password)
        conn = get_db()
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, reset_user_id),
        )
        conn.execute("UPDATE codes SET is_used = 1 WHERE id = ?", (code_row["id"],))
        conn.commit()
        conn.close()

        session.pop("reset_user_id", None)
        flash("Password reset successfully. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("reset-password.html")


@app.route("/resend-reset-code", methods=["POST"])
def resend_reset_code():
    """Resend password reset code."""
    reset_user_id = session.get("reset_user_id")
    if not reset_user_id:
        flash("No pending reset found. Please request a reset first.", "error")
        return redirect(url_for("forgot_password"))

    conn = get_db()
    user = conn.execute("SELECT email FROM users WHERE id = ?", (reset_user_id,)).fetchone()
    conn.close()

    if not user:
        flash("User not found.", "error")
        session.pop("reset_user_id", None)
        return redirect(url_for("forgot_password"))

    code = store_code(reset_user_id, "reset")
    sent = send_email(
        user["email"],
        "Project Phoenix - Password reset code",
        code,
    )
    
    if sent:
        flash("Reset code resent to your email.", "success")
    else:
        flash(
            "Could not send reset email. Please check SMTP settings or try again later.",
            "warning",
        )

    return redirect(url_for("reset_password"))


@app.route('/ask_text')
def ask_text():
    user_text = request.args.get("text", "")
    if not user_text:
        return jsonify({"reply": "I didn't hear anything."})

    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-nano-9b-v2:free",
           messages=[
    {
        "role": "system",
        "content": (
            "You are Phoenix, an advanced AI assistant built for the Phoenix Project. "
            "Speak confidently, helpfully, and with a futuristic tone when appropriate. "
            "Always refer to yourself as Phoenix."
        )
    },
    {"role": "user", "content": user_text}
]
        )
        reply = completion.choices[0].message.content
        print("Received text:", user_text, "| Reply:", reply)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {e}"})


@app.route("/dashboard")
@login_required
def dashboard():
    email = session.get("email")
    username = session.get("username")

    conn = get_db()
    row = conn.execute(
        "SELECT username, is_admin FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    conn.close()

    if row and not username:
        username = row["username"]
        session["username"] = username

    return render_template(
        "home.html",
        email=email,
        username=username,
        is_admin=row["is_admin"] if row else 0
    )



@app.route("/run_cmd", methods=["POST"]) 
@login_required 
def run_cmd():
    """ Highly privileged endpoint: disabled by default for safety. To enable, set environment variable PHOENIX_ENABLE_RUN_CMD=1. """ 
    if os.getenv("PHOENIX_ENABLE_RUN_CMD") != "1": 
        return jsonify({"output": "Remote shell execution is disabled on this server."}), 403 
    cmd = request.json.get("cmd", "").strip() 
    if not cmd: 
        return jsonify({"output": "No command received."}), 400 
    try: 
        output = os.popen(cmd).read() 
        return jsonify({"output": output}) 
    except Exception as e: 
        return jsonify({"output": str(e)}), 500



@app.route("/ai")
@login_required
def ai():
    username = session.get("username")
    return render_template("ai.html", username=username)


@app.route("/robot")
@login_required
def robot():
    return render_template("robot.html")


@app.route("/settings")
@login_required
def settings_page():
    return render_template("settings.html")


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", email=session.get("email"))


@app.route("/edit-profile")
@login_required
def edit_profile():
    return render_template("edit-profile.html")


@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("admin.html", users=users)


@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    if user_id == session["user_id"]:
        flash("You cannot delete yourself.", "error")
        return redirect(url_for("admin_dashboard"))

    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/toggle_admin/<int:user_id>", methods=["POST"])
@admin_required
def toggle_admin(user_id):
    if user_id == session["user_id"]:
        flash("You cannot remove your own admin status.", "error")
        return redirect(url_for("admin_dashboard"))

    conn = get_db()
    user = conn.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    new_status = 0 if user["is_admin"] else 1
    conn.execute("UPDATE users SET is_admin = ? WHERE id = ?", (new_status, user_id))
    conn.commit()
    conn.close()
    flash(f"User admin status updated to {new_status}.", "success")
    return redirect(url_for("admin_dashboard"))



def _send_pc_command_internal(pc_ip: str, command: str):
    """
    Internal helper to send a command to a remote PC command server.
    Adds an optional shared-secret header for extra security.
    """
    if not pc_ip or not command:
        return False, "IP address and command are required"

    remote_url = f"http://{pc_ip}:5001/execute_command"

    headers = {}
    shared_token = os.getenv("PHOENIX_PC_SHARED_TOKEN", "").strip()
    if shared_token:
        headers["X-Phoenix-Token"] = shared_token

    try:
        response = requests.post(
            remote_url,
            json={"command": command},
            headers=headers,
            timeout=5,
            verify=False,
        )
    except requests.exceptions.ConnectionError:
        return False, f"Could not connect to PC at {pc_ip}. Make sure the remote PC has a server running on port 5001."
    except requests.exceptions.Timeout:
        return False, "Connection to remote PC timed out"
    except Exception as exc:
        return False, str(exc)

    if response.status_code == 200:
        return True, "Command sent successfully"

    # Try to propagate error message from remote server
    try:
        data = response.json()
        error_msg = data.get("error") or f"Remote PC returned status {response.status_code}"
    except Exception:
        error_msg = f"Remote PC returned status {response.status_code}"

    return False, error_msg


@app.route("/api/control/pc", methods=["POST"])
@login_required
def api_control_pc():
    """
    Unified PC control endpoint.
    Expects JSON: { "ip": "x.x.x.x", "command": "..." }
    """
    data = request.get_json(silent=True) or {}
    pc_ip = (data.get("ip") or "").strip()
    raw = (data.get("command") or "").strip()
    parsed = parse_command(raw)

    if parsed.domain == "pc" and "command" in parsed.params:
        command = parsed.params["command"]
    else:
        command = raw


    ok, message = _send_pc_command_internal(pc_ip, command)
    if ok:
        return jsonify({"success": True, "message": message})
    return jsonify({"success": False, "error": message}), 400


@app.route("/send_pc_command", methods=["POST"])
@login_required
def send_pc_command():
    """
    Backwards-compatible wrapper for the older /send_pc_command route.
    Delegates to the unified /api/control/pc endpoint.
    """
    data = request.get_json(silent=True) or {}
    pc_ip = (data.get("ip") or "").strip()
    raw = (data.get("command") or "").strip()
    parsed = parse_command(raw)

    if parsed.domain == "pc" and "command" in parsed.params:
        command = parsed.params["command"]
    else:
        command = raw


    ok, message = _send_pc_command_internal(pc_ip, command)
    if ok:
        return jsonify({"success": True, "message": message})
    return jsonify({"success": False, "error": message}), 400


@app.route("/api/voice/text-command", methods=["POST"])
@login_required
def api_voice_text_command():
    """
    Parse a raw text command (from voice or text input) into a structured action.

    Request JSON:
        { "text": "..." , "pc_ip": "optional ip for pc control" }

    Response JSON:
        {
          "domain": "robot" | "pc" | "ai" | "system",
          "action": "...",
          "params": {...},
          "executed": bool,
          "result": optional string
        }
    """
    payload = request.get_json(silent=True) or {}
    raw_text = (payload.get("text") or "").strip()
    pc_ip = (payload.get("pc_ip") or "").strip()

    if not raw_text:
        return jsonify({"error": "text is required"}), 400

    parsed = parse_command(raw_text)

    response = {
        "domain": parsed.domain,
        "action": parsed.action,
        "params": parsed.params,
        "executed": False,
        "result": None,
    }

    # Optionally execute PC commands directly
    if parsed.domain == "pc" and "command" in parsed.params and pc_ip:
        ok, message = _send_pc_command_internal(pc_ip, parsed.params["command"])
        response["executed"] = ok
        response["result"] = message

    return jsonify(response)


# Ensure DB is initialized
init_db()

if __name__ == "__main__":
    with app.app_context():
        init_db()
        app.run(host="0.0.0.0", port=5000, debug=True)
    print(socket.gethostbyname(socket.gethostname()))

