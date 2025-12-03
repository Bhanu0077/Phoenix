from app import app, init_db, get_db

def run_flow_tests():
    with app.app_context():
        init_db()
        conn = get_db()
        conn.execute("DELETE FROM codes")
        conn.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    client = app.test_client()

    # Signup
    resp = client.post(
        "/signup",
        data={"email": "test@example.com", "password": "Secret123!"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email=?", ("test@example.com",)
        ).fetchone()
        assert user is not None
        code_row = conn.execute(
            """
            SELECT * FROM codes
            WHERE user_id = ? AND purpose = 'signup'
            ORDER BY id DESC LIMIT 1
            """,
            (user["id"],),
        ).fetchone()
        code = code_row["code"]

    # Verify signup
    resp = client.post(
        "/verify-signup", data={"code": code}, follow_redirects=True
    )
    assert resp.status_code == 200

    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email=?", ("test@example.com",)
        ).fetchone()
        assert user["is_verified"] == 1

    # Login
    resp = client.post(
        "/login",
        data={"email": "test@example.com", "password": "Secret123!"},
        follow_redirects=True,
    )

    print(resp.data)
    assert b"PHOENIX" in resp.data   # corrected assertion

    # Dashboard access
    resp = client.get("/dashboard")
    assert resp.status_code == 200

    # Forgot password
    resp = client.post(
        "/forgot-password",
        data={"email": "test@example.com"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with get_db() as conn:
        reset_code = conn.execute(
            """
            SELECT code FROM codes
            WHERE user_id = ? AND purpose = 'reset'
            ORDER BY id DESC LIMIT 1
            """,
            (user["id"],),
        ).fetchone()["code"]

    # Reset password
    resp = client.post(
        "/reset-password",
        data={"code": reset_code, "password": "NewSecret123!"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    # Login with new password
    client.get("/logout")
    resp = client.post(
        "/login",
        data={"email": "test@example.com", "password": "NewSecret123!"},
        follow_redirects=True,
    )
    assert b"PHOENIX" in resp.data

    print("All auth flow tests passed.")

if __name__ == "__main__":
    run_flow_tests()
