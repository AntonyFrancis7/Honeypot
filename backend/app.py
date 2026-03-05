from datetime import datetime
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, request, render_template, redirect, url_for, g, jsonify
from flask_cors import CORS

from attack_classifier import classify_attack


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "honeypot.db"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ip TEXT NOT NULL,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            user_agent TEXT,
            payload TEXT,
            attack_types TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def log_request(extra_payload: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the current request with basic classification.
    """
    db = get_db()

    ip = request.remote_addr or "unknown"
    method = request.method
    path = request.path
    user_agent = request.headers.get("User-Agent", "")

    # Combine query string, form data and any extra payload into one blob
    payload_data: Dict[str, Any] = {
        "args": request.args.to_dict(flat=False),
        "form": request.form.to_dict(flat=False),
        "json": request.get_json(silent=True),
    }
    if extra_payload:
        payload_data["extra"] = extra_payload

    payload_str = json.dumps(payload_data, default=str)
    labels = classify_attack(payload_str, user_agent)

    timestamp = datetime.utcnow().isoformat()

    db.execute(
        """
        INSERT INTO logs (timestamp, ip, method, path, user_agent, payload, attack_types)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (timestamp, ip, method, path, user_agent, payload_str, ",".join(sorted(labels))),
    )
    db.commit()


def create_app() -> Flask:
    init_db()
    app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.teardown_appcontext
    def close_db(exception: Optional[BaseException]) -> None:  # type: ignore[override]
        db = g.pop("db", None)
        if db is not None:
            db.close()

    # -------------------------
    # Deceptive surface routes
    # -------------------------

    @app.route("/")
    def index():
        log_request()
        return redirect(url_for("student_login"))

    @app.route("/admin")
    def admin():
        log_request()
        return render_template("admin_login.html")

    @app.route("/wp-admin")
    def wp_admin():
        log_request()
        return render_template("admin_login.html", wp_style=True)

    @app.route("/phpmyadmin")
    def phpmyadmin():
        log_request()
        # Reuse same template with different label
        return render_template("admin_login.html", phpmyadmin=True)

    @app.route("/login/student")
    def student_login():
        log_request()
        return render_template("student_login.html")

    @app.route("/login/faculty")
    def faculty_login():
        log_request()
        return render_template("faculty_login.html")

    # Juicy-looking fake directories
    @app.route("/backup")
    @app.route("/old_admin")
    @app.route("/db_export")
    def fake_dirs():
        log_request()
        return render_template("fake_403.html"), 403

    # -------------------------
    # Emulated login handlers
    # -------------------------

    @app.route("/admin/login", methods=["POST"])
    def fake_admin_login():
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        log_request({"username": username, "password": password})
        # Always fail with realistic message
        return render_template(
            "fake_error.html",
            message="Invalid username or password. Account locked after multiple failed attempts.",
        )

    @app.route("/login/student", methods=["POST"])
    def fake_student_login():
        roll = request.form.get("roll", "")
        password = request.form.get("password", "")
        log_request({"roll": roll, "password": password})
        return render_template(
            "fake_error.html",
            message="Login failed. Your account is under review by the administrator.",
        )

    @app.route("/login/faculty", methods=["POST"])
    def fake_faculty_login():
        faculty_id = request.form.get("faculty_id", "")
        password = request.form.get("password", "")
        log_request({"faculty_id": faculty_id, "password": password})
        return render_template(
            "fake_error.html",
            message="Authentication failed. Please contact IT support.",
        )

    # -------------------------
    # API endpoints for frontend
    # -------------------------

    @app.route("/api/login/student", methods=["POST"])
    def api_student_login():
        data = request.get_json() or {}
        roll = data.get("roll", "")
        password = data.get("password", "")
        log_request({"roll": roll, "password": password})
        return jsonify({
            "error": "Login failed. Your account is under review by the administrator.",
            "status": "locked"
        }), 401

    @app.route("/api/login/faculty", methods=["POST"])
    def api_faculty_login():
        data = request.get_json() or {}
        faculty_id = data.get("facultyId", "")
        password = data.get("password", "")
        log_request({"faculty_id": faculty_id, "password": password})
        return jsonify({
            "error": "Authentication failed. Please contact IT support.",
            "status": "failed"
        }), 401

    @app.route("/api/login/admin", methods=["POST"])
    def api_admin_login():
        data = request.get_json() or {}
        username = data.get("username", "")
        password = data.get("password", "")
        log_request({"username": username, "password": password})
        return jsonify({
            "error": "Invalid username or password. Account locked after multiple failed attempts.",
            "status": "locked"
        }), 401

    # -------------------------
    # Error handlers
    # -------------------------

    @app.errorhandler(404)
    def not_found(e):
        log_request()
        return render_template("fake_404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        log_request()
        return render_template("fake_500.html"), 500

    # -------------------------
    # Dashboard & reporting
    # -------------------------

    @app.route("/dashboard")
    def dashboard():
        log_request()
        db = get_db()

        # Total hits per day
        hits_per_day = db.execute(
            """
            SELECT substr(timestamp, 1, 10) as day, COUNT(*) as count
            FROM logs
            GROUP BY day
            ORDER BY day DESC
            LIMIT 30
            """
        ).fetchall()

        # Top attacking IPs
        top_ips = db.execute(
            """
            SELECT ip, COUNT(*) as count
            FROM logs
            GROUP BY ip
            ORDER BY count DESC
            LIMIT 10
            """
        ).fetchall()

        # Most targeted endpoints
        top_paths = db.execute(
            """
            SELECT path, COUNT(*) as count
            FROM logs
            GROUP BY path
            ORDER BY count DESC
            LIMIT 10
            """
        ).fetchall()

        # Attack type breakdown
        attack_rows = db.execute(
            """
            SELECT attack_types
            FROM logs
            WHERE attack_types IS NOT NULL AND attack_types <> ''
            """
        ).fetchall()

        attack_counts: Dict[str, int] = {}
        for row in attack_rows:
            types = (row["attack_types"] or "").split(",")
            for t in types:
                if not t:
                    continue
                attack_counts[t] = attack_counts.get(t, 0) + 1

        # Very simple "country" approximation placeholder (all unknown)
        country_counts: Dict[str, int] = {"Unknown": 0}
        all_logs = db.execute("SELECT ip FROM logs").fetchall()
        country_counts["Unknown"] = len(all_logs)

        return render_template(
            "dashboard.html",
            hits_per_day=hits_per_day,
            top_ips=top_ips,
            top_paths=top_paths,
            attack_counts=attack_counts,
            country_counts=country_counts,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    # Banner to mimic a production-like server
    app.config["SERVER_NAME"] = None
    app.run(host="0.0.0.0", port=5000, debug=False)

