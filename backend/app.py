import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Set

from flask import Flask, request, render_template, redirect, url_for, g, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
try:
    from backend.attack_classifier import classify_attack
except ImportError:
    from attack_classifier import classify_attack

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "honeypot.db"

# Basic Logging setup to capture internal errors without exposing them
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_real_ip() -> str:
    """
    Safely extract the real client IP, even through multiple layer proxies like Cloudflare -> Render.
    """
    # If Cloudflare is fronting the app, this gives the real client
    true_client = request.headers.get("True-Client-IP")
    if true_client:
        return true_client.strip()
        
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
        
    # X-Forwarded-For looks like: 120.61.x.x, 172.69.x.x, 10.x.x.x
    fwded_for = request.headers.get("X-Forwarded-For")
    if fwded_for:
        return fwded_for.split(",")[0].strip()
        
    return request.remote_addr or "unknown"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            g.db = conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    return g.db


def init_db() -> None:
    try:
        # SQLite automatically creates the DB file if it doesn't exist
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
        logger.info("Local SQLite Database initialized successfully.")
    except Exception as e:
        logger.error(f"Critical Error: Failed to initialize SQLite database. App may crash. Details: {e}")


def execute_query(db: sqlite3.Connection, query: str, args=(), fetchall=False) -> Any:
    try:
        if fetchall:
            return db.execute(query, args).fetchall()
        db.execute(query, args)
        db.commit()
        return None
    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}. Query: {query}")
        return [] if fetchall else None


def log_request(extra_payload: Optional[Dict[str, Any]] = None, extra_labels: Optional[Set[str]] = None) -> None:
    """
    Log the current request with basic classification.
    """
    try:
        db = get_db()

        ip = get_real_ip()
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
            "json": request.get_json(silent=True) if request.is_json else None,
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
    except Exception as e:
        # Fails silently to user, logs internally
        logger.error(f"Failed to log incoming request: {e}")


def check_and_record_attempt(session_id: str, ip: str, login_id: str) -> Optional[str]:
    """
    Returns 'PasswordSpray', 'BruteForce', or None based on attempt history.
    """
    try:
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
    except Exception as e:
        logger.error(f"Failed to record/check login attempt thresholds: {e}")

    return None


def create_app() -> Flask:
    init_db()
    
    app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
    
    # Trust the reverse proxy (Render) to provide correct IP protocols
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Simple, functional CORS logic for the React Frontend hosted (like Vercel)
    CORS(app, resources={r"/*": {"origins": "*"}})

    @app.teardown_appcontext
    def close_db(exception: Optional[BaseException]) -> None:
        db = g.pop("db", None)
        if db is not None:
            try:
                db.close()
            except Exception as e:
                logger.error(f"Failed cleanly closing db context: {e}")

    # -------------------------
    # Deceptive surface routes
    # -------------------------

    @app.route("/ping")
    def ping():
        # Health check endpoint for UptimeRobot (does NOT log anything)
        return "ok", 200

    @app.route("/")
    def index():
        try:
            log_request()
            return redirect(url_for("student_login"))
        except Exception:
            return render_template("fake_500.html"), 500

    @app.route("/admin")
    def admin():
        try:
            log_request()
            return render_template("admin_login.html")
        except Exception:
            return render_template("fake_500.html"), 500

    @app.route("/wp-admin")
    def wp_admin():
        try:
            log_request()
            return render_template("admin_login.html", wp_style=True)
        except Exception:
            return render_template("fake_500.html"), 500

    @app.route("/phpmyadmin")
    def phpmyadmin():
        try:
            log_request()
            return render_template("admin_login.html", phpmyadmin=True)
        except Exception:
            return render_template("fake_500.html"), 500

    @app.route("/login/student")
    def student_login():
        try:
            log_request()
            return render_template("student_login.html")
        except Exception:
            return render_template("fake_500.html"), 500

    @app.route("/login/faculty")
    def faculty_login():
        try:
            log_request()
            return render_template("faculty_login.html")
        except Exception:
            return render_template("fake_500.html"), 500

    # Juicy-looking fake directories
    @app.route("/backup")
    @app.route("/old_admin")
    @app.route("/db_export")
    def fake_dirs():
        try:
            log_request()
        except Exception:
            pass
        return render_template("fake_403.html"), 403

    # -------------------------
    # Emulated login handlers
    # -------------------------

    @app.route("/admin/login", methods=["POST"])
    def fake_admin_login():
        try:
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            ip = get_real_ip()
            attack_tag = check_and_record_attempt("unknown", ip, username)
            extra_labels = {attack_tag} if attack_tag else None
            
            log_request({"username": username, "password": password}, extra_labels=extra_labels)
        except Exception as e:
            logger.error(f"Error in fake_admin_login: {e}")
            
        # Always fail with realistic message
        return render_template(
            "fake_error.html",
            message="Invalid username or password. Account locked after multiple failed attempts.",
        )

    @app.route("/login/student", methods=["POST"])
    def fake_student_login():
        try:
            roll = request.form.get("roll", "")
            password = request.form.get("password", "")
            ip = get_real_ip()
            attack_tag = check_and_record_attempt("unknown", ip, roll)
            extra_labels = {attack_tag} if attack_tag else None
            
            log_request({"roll": roll, "password": password}, extra_labels=extra_labels)
        except Exception as e:
            logger.error(f"Error in fake_student_login: {e}")

        return render_template(
            "fake_error.html",
            message="Login failed. Your account is under review by the administrator.",
        )

    @app.route("/login/faculty", methods=["POST"])
    def fake_faculty_login():
        try:
            faculty_id = request.form.get("faculty_id", "")
            password = request.form.get("password", "")
            ip = get_real_ip()
            attack_tag = check_and_record_attempt("unknown", ip, faculty_id)
            extra_labels = {attack_tag} if attack_tag else None
            
            log_request({"faculty_id": faculty_id, "password": password}, extra_labels=extra_labels)
        except Exception as e:
            logger.error(f"Error in fake_faculty_login: {e}")

        return render_template(
            "fake_error.html",
            message="Authentication failed. Please contact IT support.",
        )

    # -------------------------
    # API endpoints for frontend
    # -------------------------

    @app.route("/api/login/student", methods=["POST"])
    def api_student_login():
        try:
            data = request.get_json(silent=True) or {}
            roll = data.get("roll", "")
            password = data.get("password", "")
            session_id = data.get("sessionId", "")
            ip = get_real_ip()

            # Classify attack based on submitted credentials
            probe = json.dumps({"roll": roll, "password": password})
            user_agent = request.headers.get("User-Agent", "")
            attack_labels = classify_attack(probe, user_agent)

            attack_tag = check_and_record_attempt(session_id, ip, roll)
            extra_labels = {attack_tag} if attack_tag else None

            # Always log and flag every attempt
            log_request({"roll": roll, "password": password, "session_id": session_id}, extra_labels=extra_labels)

            # Safety check: bypass missing sets
            if attack_labels and attack_labels.intersection({"SQLi", "XSS", "LFI"}):
                return jsonify({
                    "status": "trapped",
                    "redirect": "/dashboard/student"
                }), 200

            if roll == "12345" and password == "password123":
                return jsonify({"status": "trapped", "redirect": "/dashboard/student"}), 200

            if roll == "123456" and password == "15":
                return jsonify({"status": "trapped", "redirect": "/dashboard/student"}), 200

            return jsonify({
                "error": "Login failed. Invalid roll number or password.",
                "status": "failed"
            }), 401

        except Exception as e:
            logger.error(f"API student login unhandled exception: {e}")
            return jsonify({"error": "Failed to process request.", "status": "failed"}), 500


    @app.route("/api/login/faculty", methods=["POST"])
    def api_faculty_login():
        try:
            data = request.get_json(silent=True) or {}
            faculty_id = data.get("facultyId", "")
            password = data.get("password", "")
            session_id = data.get("sessionId", "")
            ip = get_real_ip()

            # Classify attack based on submitted credentials
            probe = json.dumps({"facultyId": faculty_id, "password": password})
            user_agent = request.headers.get("User-Agent", "")
            attack_labels = classify_attack(probe, user_agent)

            attack_tag = check_and_record_attempt(session_id, ip, faculty_id)
            extra_labels = {attack_tag} if attack_tag else None

            # Always log and flag every attempt
            log_request({"faculty_id": faculty_id, "password": password, "session_id": session_id}, extra_labels=extra_labels)

            if attack_labels and attack_labels.intersection({"SQLi", "XSS", "LFI"}):
                return jsonify({
                    "status": "trapped",
                    "redirect": "/dashboard/faculty"
                }), 200

            if faculty_id == "123" and password == "password123":
                return jsonify({"status": "trapped", "redirect": "/dashboard/faculty"}), 200

            if faculty_id == "1234" and password == "15":
                return jsonify({"status": "trapped", "redirect": "/dashboard/faculty"}), 200

            return jsonify({
                "error": "Authentication failed. Invalid employee ID or password.",
                "status": "failed"
            }), 401

        except Exception as e:
            logger.error(f"API faculty login unhandled exception: {e}")
            return jsonify({"error": "Failed to process request.", "status": "failed"}), 500


    @app.route("/api/login/admin", methods=["POST"])
    def api_admin_login():
        try:
            data = request.get_json(silent=True) or {}
            username = data.get("username", "")
            password = data.get("password", "")
            session_id = data.get("sessionId", "")
            ip = get_real_ip()
            
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
            
        except Exception as e:
            logger.error(f"API admin login unhandled exception: {e}")
            return jsonify({"error": "Failed to process request.", "status": "failed"}), 500

    
    @app.route("/api/telemetry", methods=["POST"])
    def api_telemetry():
        try:
            data = request.get_json(silent=True) or {}
            session_id = data.get("sessionId", "unknown")
            webrtc_ips = json.dumps(data.get("webrtcIps", []))
            fingerprint = json.dumps(data.get("fingerprint", {}))
            
            ip = get_real_ip()
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
        except Exception as e:
            logger.error(f"Telemetry API error: {e}")
            return jsonify({"status": "error"}), 500

    # -------------------------
    # Error handlers
    # -------------------------

    @app.errorhandler(404)
    def not_found(e):
        try:
            log_request()
        except:
            pass
        return render_template("fake_404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        try:
            log_request()
        except:
            pass
        return render_template("fake_500.html"), 500

    # -------------------------
    # Dashboard & reporting
    # -------------------------

    DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "honeypot-admin")

    @app.route("/api/logs/recent")
    def api_recent_logs():
        try:
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
                
            # If fetch fails, provide empty array rather than failing silently completely.
            if not recent_logs:
                return jsonify([])

            return jsonify([dict(row) for row in recent_logs])
        except Exception as e:
            logger.error(f"Failed to fetch recent logs: {e}")
            return jsonify({"error": "Internal Server Error"}), 500


    @app.route("/dashboard")
    def dashboard():
        try:
            token = request.args.get("token", "")
            if token != DASHBOARD_TOKEN:
                return render_template("fake_403.html"), 403
                
            db = get_db()

            # Using fallback `or []` in case the execution query fails internally and returns None
            hits_per_day = execute_query(db,
                """
                SELECT substr(timestamp, 1, 10) as day, COUNT(*) as count
                FROM logs
                GROUP BY day
                ORDER BY day DESC
                LIMIT 30
                """, fetchall=True) or []

            top_ips = execute_query(db,
                """
                SELECT ip, COUNT(*) as count
                FROM logs
                GROUP BY ip
                ORDER BY count DESC
                LIMIT 10
                """, fetchall=True) or []

            top_paths = execute_query(db,
                """
                SELECT path, COUNT(*) as count
                FROM logs
                GROUP BY path
                ORDER BY count DESC
                LIMIT 10
                """, fetchall=True) or []

            attack_rows = execute_query(db,
                """
                SELECT attack_types
                FROM logs
                WHERE attack_types IS NOT NULL AND attack_types <> ''
                """, fetchall=True) or []

            attack_counts: Dict[str, int] = {}
            for row in attack_rows:
                types = (row["attack_types"] or "").split(",")
                for t in types:
                    if not t:
                        continue
                    attack_counts[t] = attack_counts.get(t, 0) + 1

            country_counts: Dict[str, int] = {"Unknown": 0}
            all_logs = execute_query(db, "SELECT ip FROM logs", fetchall=True) or []
            country_counts["Unknown"] = len(all_logs)

            recent_logs = execute_query(db,
                """
                SELECT timestamp, ip, path, payload, attack_types
                FROM logs
                ORDER BY id DESC
                LIMIT 50
                """, fetchall=True) or []

            return render_template(
                "dashboard.html",
                hits_per_day=hits_per_day,
                top_ips=top_ips,
                top_paths=top_paths,
                attack_counts=attack_counts,
                country_counts=country_counts,
                recent_logs=recent_logs,
            )
        except Exception as e:
            logger.error(f"Failed to render dashboard: {e}")
            return render_template("fake_500.html"), 500


    return app


# Required for gunicorn (Gunicorn looks for an `app` object in this module level)
app = create_app()


if __name__ == "__main__":
    # Dynamically grab the port (defaulting to 5000) - Useful if run standalone rather than gunicorn.
    port = int(os.environ.get("PORT", 5000))
    app.config["SERVER_NAME"] = None
    app.run(host="0.0.0.0", port=port, debug=False)
