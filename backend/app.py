from datetime import datetime, timedelta
import json
import sqlite3
import os
from pathlib import Path
from typing import Any, Dict, Optional, Set

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from flask import Flask, request, render_template, redirect, url_for, g, jsonify
from flask_cors import CORS

from attack_classifier import classify_attack


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "honeypot.db"


def get_db() -> Any:
    if "db" not in g:
        db_url = os.environ.get("DATABASE_URL")
        if db_url and HAS_PSYCOPG2:
            conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.DictCursor)
            g.db = conn
            g.is_postgres = True
        else:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            g.db = conn
            g.is_postgres = False
    return g.db


def init_db() -> None:
    db_url = os.environ.get("DATABASE_URL")
    if db_url and HAS_PSYCOPG2:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
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
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ip TEXT NOT NULL,
                webrtc_ips TEXT,
                fingerprint TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS login_attempts (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                ip TEXT NOT NULL,
                login_id TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        conn.commit()
        cur.close()
        conn.close()
    else:
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
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ip TEXT NOT NULL,
                webrtc_ips TEXT,
                fingerprint TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                ip TEXT NOT NULL,
                login_id TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()


def execute_query(db, query, args=(), fetchall=False) -> Any:
    is_postgres = getattr(g, 'is_postgres', False)
    if is_postgres:
        query = query.replace("?", "%s")
        cur = db.cursor()
        cur.execute(query, args)
        if fetchall:
            res = cur.fetchall()
            cur.close()
            return res
        db.commit()
        cur.close()
        return None
    else:
        if fetchall:
            return db.execute(query, args).fetchall()
        db.execute(query, args)
        db.commit()
        return None


def log_request(extra_payload: Optional[Dict[str, Any]] = None, extra_labels: Optional[Set[str]] = None) -> None:
    """
    Log the current request with basic classification.
    """
    db = get_db()

    ip = request.remote_addr or "unknown"
    method = request.method
    path = request.path
    user_agent = request.headers.get("User-Agent", "")

    proxy_headers = {
        "X-Forwarded-For": request.headers.get("X-Forwarded-For", ""),
        "X-Real-IP": request.headers.get("X-Real-IP", ""),
        "True-Client-IP": request.headers.get("True-Client-IP", ""),
        "Via": request.headers.get("Via", "")
    }

    # Combine query string, form data and any extra payload into one blob
    payload_data: Dict[str, Any] = {
        "args": request.args.to_dict(flat=False),
        "form": request.form.to_dict(flat=False),
        "json": request.get_json(silent=True),
        "proxy_headers": proxy_headers,
    }
    if extra_payload:
        payload_data["extra"] = extra_payload

    payload_str = json.dumps(payload_data, default=str)
    labels = classify_attack(payload_str, user_agent)
    if extra_labels:
        labels.update(extra_labels)

    timestamp = datetime.utcnow().isoformat()

    execute_query(db,
        """
        INSERT INTO logs (timestamp, ip, method, path, user_agent, payload, attack_types)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (timestamp, ip, method, path, user_agent, payload_str, ",".join(sorted(labels))),
    )


def check_and_record_attempt(session_id: str, ip: str, login_id: str) -> Optional[str]:
    """
    Returns 'PasswordSpray', 'BruteForce', or None based on attempt history.
    """
    db = get_db()
    timestamp = datetime.utcnow().isoformat()
    window_start = (datetime.utcnow() - timedelta(minutes=10)).isoformat()

    # 1. Record this attempt
    execute_query(db,
        """
        INSERT INTO login_attempts (session_id, ip, login_id, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, ip, login_id, timestamp),
    )

    # 2. Check thresholds within the rolling window (group by session_id; fall back to IP)
    if session_id and session_id != "unknown":
        query_total = "SELECT COUNT(*) as cnt FROM login_attempts WHERE session_id = ? AND timestamp > ?"
        query_unique = "SELECT COUNT(DISTINCT login_id) as cnt FROM login_attempts WHERE session_id = ? AND timestamp > ?"
        param = (session_id, window_start)
    else:
        query_total = "SELECT COUNT(*) as cnt FROM login_attempts WHERE ip = ? AND timestamp > ?"
        query_unique = "SELECT COUNT(DISTINCT login_id) as cnt FROM login_attempts WHERE ip = ? AND timestamp > ?"
        param = (ip, window_start)

    res_total = execute_query(db, query_total, param, fetchall=True)
    res_unique = execute_query(db, query_unique, param, fetchall=True)

    total_count = res_total[0]["cnt"] if res_total else 0
    unique_count = res_unique[0]["cnt"] if res_unique else 0

    if unique_count > 5:
        return "PasswordSpray"
    if total_count > 5:
        return "BruteForce"
    return None


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
        ip = request.remote_addr or "unknown"
        attack_tag = check_and_record_attempt("unknown", ip, username)
        extra_labels = {attack_tag} if attack_tag else None
        
        log_request({"username": username, "password": password}, extra_labels=extra_labels)
        # Always fail with realistic message
        return render_template(
            "fake_error.html",
            message="Invalid username or password. Account locked after multiple failed attempts.",
        )

    @app.route("/login/student", methods=["POST"])
    def fake_student_login():
        roll = request.form.get("roll", "")
        password = request.form.get("password", "")
        ip = request.remote_addr or "unknown"
        attack_tag = check_and_record_attempt("unknown", ip, roll)
        extra_labels = {attack_tag} if attack_tag else None
        
        log_request({"roll": roll, "password": password}, extra_labels=extra_labels)
        return render_template(
            "fake_error.html",
            message="Login failed. Your account is under review by the administrator.",
        )

    @app.route("/login/faculty", methods=["POST"])
    def fake_faculty_login():
        faculty_id = request.form.get("faculty_id", "")
        password = request.form.get("password", "")
        ip = request.remote_addr or "unknown"
        attack_tag = check_and_record_attempt("unknown", ip, faculty_id)
        extra_labels = {attack_tag} if attack_tag else None
        
        log_request({"faculty_id": faculty_id, "password": password}, extra_labels=extra_labels)
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
        session_id = data.get("sessionId", "")
        ip = request.remote_addr or "unknown"

        # Classify attack based on submitted credentials
        probe = json.dumps({"roll": roll, "password": password})
        user_agent = request.headers.get("User-Agent", "")
        attack_labels = classify_attack(probe, user_agent)

        attack_tag = check_and_record_attempt(session_id, ip, roll)
        extra_labels = {attack_tag} if attack_tag else None

        # Always log and flag every attempt
        log_request({"roll": roll, "password": password, "session_id": session_id}, extra_labels=extra_labels)

        # If an injection/traversal attack is detected → let them "in" to fake dashboard
        if attack_labels & {"SQLi", "XSS", "LFI"}:
            return jsonify({
                "status": "trapped",
                "redirect": "/dashboard/student"
            }), 200

        # Bait credentials — attacker must actually "find" this to enter the fake dashboard
        # student 1 - quick entry
        if roll == "12345" and password == "password123":
            return jsonify({
                "status": "trapped",
                "redirect": "/dashboard/student"
            }), 200

        # student 2 - brute force demo
        if roll == "123456" and password == "15":
            return jsonify({
                "status": "trapped",
                "redirect": "/dashboard/student"
            }), 200

        return jsonify({
            "error": "Login failed. Invalid roll number or password.",
            "status": "failed"
        }), 401


    @app.route("/api/login/faculty", methods=["POST"])
    def api_faculty_login():
        data = request.get_json() or {}
        faculty_id = data.get("facultyId", "")
        password = data.get("password", "")
        session_id = data.get("sessionId", "")
        ip = request.remote_addr or "unknown"

        # Classify attack based on submitted credentials
        probe = json.dumps({"facultyId": faculty_id, "password": password})
        user_agent = request.headers.get("User-Agent", "")
        attack_labels = classify_attack(probe, user_agent)

        attack_tag = check_and_record_attempt(session_id, ip, faculty_id)
        extra_labels = {attack_tag} if attack_tag else None

        # Always log and flag every attempt
        log_request({"faculty_id": faculty_id, "password": password, "session_id": session_id}, extra_labels=extra_labels)

        # If an injection/traversal attack is detected → let them "in" to fake dashboard
        if attack_labels & {"SQLi", "XSS", "LFI"}:
            return jsonify({
                "status": "trapped",
                "redirect": "/dashboard/faculty"
            }), 200

        # Bait credentials — attacker must actually "find" this to enter the fake dashboard
        # faculty 1 - quick entry
        if faculty_id == "123" and password == "password123":
            return jsonify({
                "status": "trapped",
                "redirect": "/dashboard/faculty"
            }), 200

        # faculty 2 - brute force demo
        if faculty_id == "1234" and password == "15":
            return jsonify({
                "status": "trapped",
                "redirect": "/dashboard/faculty"
            }), 200

        return jsonify({
            "error": "Authentication failed. Invalid employee ID or password.",
            "status": "failed"
        }), 401

    @app.route("/api/login/admin", methods=["POST"])
    def api_admin_login():
        data = request.get_json() or {}
        username = data.get("username", "")
        password = data.get("password", "")
        session_id = data.get("sessionId", "")
        ip = request.remote_addr or "unknown"
        
        attack_tag = check_and_record_attempt(session_id, ip, username)
        extra_labels = {attack_tag} if attack_tag else None
        
        log_request({"username": username, "password": password, "session_id": session_id}, extra_labels=extra_labels)
        
        if attack_tag:
            return jsonify({
                "error": "Account lock triggered. Redirecting...",
                "status": "locked",
                "redirect": "/backup" 
            }), 403
            
        return jsonify({
            "error": "Invalid username or password.",
            "status": "failed"
        }), 401
    
    @app.route("/api/telemetry", methods=["POST"])
    def api_telemetry():
        data = request.get_json() or {}
        session_id = data.get("sessionId", "unknown")
        webrtc_ips = json.dumps(data.get("webrtcIps", []))
        fingerprint = json.dumps(data.get("fingerprint", {}))
        
        ip = request.remote_addr or "unknown"
        timestamp = datetime.utcnow().isoformat()
        
        db = get_db()
        execute_query(db,
            """
            INSERT INTO telemetry (session_id, timestamp, ip, webrtc_ips, fingerprint)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, timestamp, ip, webrtc_ips, fingerprint),
        )
        return jsonify({"status": "ok"}), 200

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

    DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "honeypot-admin")

    @app.route("/api/logs/recent")
    def api_recent_logs():
        token = request.args.get("token", "")
        if token != DASHBOARD_TOKEN:
            return jsonify({"error": "Unauthorized"}), 403
            
        db = get_db()
        recent_logs = execute_query(db,
            """
            SELECT timestamp, ip, path, payload, attack_types
            FROM logs
            ORDER BY id DESC
            LIMIT 50
            """, fetchall=True)
            
        return jsonify([dict(row) for row in recent_logs])

    @app.route("/dashboard")
    def dashboard():
        token = request.args.get("token", "")
        if token != DASHBOARD_TOKEN:
            return render_template("fake_403.html"), 403
        # Do NOT log dashboard visits — avoids polluting attack data with admin traffic
        db = get_db()

        # Total hits per day
        hits_per_day = execute_query(db,
            """
            SELECT substr(timestamp, 1, 10) as day, COUNT(*) as count
            FROM logs
            GROUP BY day
            ORDER BY day DESC
            LIMIT 30
            """, fetchall=True)

        # Top attacking IPs
        top_ips = execute_query(db,
            """
            SELECT ip, COUNT(*) as count
            FROM logs
            GROUP BY ip
            ORDER BY count DESC
            LIMIT 10
            """, fetchall=True)

        # Most targeted endpoints
        top_paths = execute_query(db,
            """
            SELECT path, COUNT(*) as count
            FROM logs
            GROUP BY path
            ORDER BY count DESC
            LIMIT 10
            """, fetchall=True)

        # Attack type breakdown
        attack_rows = execute_query(db,
            """
            SELECT attack_types
            FROM logs
            WHERE attack_types IS NOT NULL AND attack_types <> ''
            """, fetchall=True)

        attack_counts: Dict[str, int] = {}
        for row in attack_rows:
            types = (row["attack_types"] or "").split(",")
            for t in types:
                if not t:
                    continue
                attack_counts[t] = attack_counts.get(t, 0) + 1

        # Very simple "country" approximation placeholder (all unknown)
        country_counts: Dict[str, int] = {"Unknown": 0}
        all_logs = execute_query(db, "SELECT ip FROM logs", fetchall=True)
        country_counts["Unknown"] = len(all_logs)

        # Recent 50 attacks
        recent_logs = execute_query(db,
            """
            SELECT timestamp, ip, path, payload, attack_types
            FROM logs
            ORDER BY id DESC
            LIMIT 50
            """, fetchall=True)

        return render_template(
            "dashboard.html",
            hits_per_day=hits_per_day,
            top_ips=top_ips,
            top_paths=top_paths,
            attack_counts=attack_counts,
            country_counts=country_counts,
            recent_logs=recent_logs,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    # Banner to mimic a production-like server
    app.config["SERVER_NAME"] = None
    app.run(host="0.0.0.0", port=5000, debug=False)

