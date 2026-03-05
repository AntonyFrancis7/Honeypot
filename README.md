# Honeypot

A honeypot project for security research and testing.

## Project Phases (Medium Interaction Web Honeypot)

This project will follow these phases to build a **medium interaction web honeypot** based on a fake college portal:

### Phase 1 — Design the Deceptive Surface
- Create fake login pages and panels (e.g. `/admin`, `/login/student`, `/login/faculty`, `/wp-admin`, `/phpmyadmin`).
- Simulate realistic responses to all login attempts (e.g. always "Wrong username or password" or "Account locked" without ever granting access).
- Add fake routes and directories that look interesting to scanners (e.g. `/backup`, `/old_admin`, `/db_export`).
- Ensure the UI looks like a real vulnerable web application while remaining fully isolated from any real data.

## Running the Project

To run the project, you have two options:

### Using Scripts (Recommended)

**Windows:**
```cmd
run.bat
```

**Linux/macOS:**
```bash
./run.sh
```

### Manual Startup

**1. Start the Flask Backend:**
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate.bat
# On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python app.py
```
*The backend will run on `http://localhost:5000`*

**2. Start the React Frontend:**
```bash
cd honeypot-collegeportal
npm install
npm run dev
```
*The frontend will run on the Vite default port (usually `http://localhost:5173`)*

### Phase 2 — Build the Emulation Layer
- Implement a backend (e.g. Python/Flask) to handle HTTP methods (`GET`, `POST`, `OPTIONS`) for the fake endpoints.
- Return realistic HTTP headers to mimic common web servers (Apache/Nginx/IIS style headers and version banners).
- Simulate error responses (`404`, `403`, `500`) with believable but fake stack traces and error pages.
- Expose form fields and request parameters that appear vulnerable to SQLi, XSS, and LFI, but never execute the payloads.

### Phase 3 — Logging & Detection Engine
- Log every interaction with:
  - Timestamp
  - Source IP (and later, geolocation)
  - HTTP method and full request path
  - User-Agent
  - Full request payload/body where applicable
- Store logs in a database (e.g. SQLite) for later analysis and reporting.

### Phase 4 — Attack Classification
- Analyze logged requests to classify common attack types using regex/keyword rules, for example:
  - Patterns like `' OR 1=1` → SQL Injection
  - Payloads containing `<script>` → XSS
  - Paths like `../../../etc/passwd` → LFI/Path Traversal
  - User-Agents containing `nmap`, `sqlmap`, `nikto` → Automated scanners
  - Rapid sequential login or request bursts → Brute force / scanning activity
- Tag each log entry with one or more detected attack types.

### Phase 5 — Dashboard & Reporting
- Build an admin dashboard (web UI) to visualize:
  - Total hits per day
  - Top attacking IPs and user agents
  - Most targeted endpoints
  - Attack type breakdown (e.g. bar/pie charts)
  - World map or country list of attacker origins (based on IP geolocation)
- Optionally integrate alerting (e.g. email or Telegram bot) for specific attack patterns or thresholds.

## Login Detection Hazards

### Overview

Login detection in honeypot systems presents several critical challenges and hazards that must be carefully managed to maintain system integrity and research validity.

### Key Hazards

#### 1. **False Positive Detection**

- Legitimate administrative activities may be flagged as attacks
- Scheduled maintenance tasks or automated scripts could trigger false alerts
- System monitoring tools and security scanners may generate excessive noise
- Result: Alert fatigue and missed actual threats

#### 2. **Performance Impact**

- Intensive login monitoring can degrade system performance
- Excessive logging and analysis overhead may make the honeypot noticeably slower than production systems
- Attackers may recognize unnatural response patterns and avoid the honeypot

#### 3. **Detection Evasion**

- Sophisticated attackers use techniques to evade login detection:
  - Distributed attack patterns across time
  - Low-and-slow authentication attempts
  - Encrypted tunneling of login credentials
  - Multi-stage exploitation avoiding obvious login patterns

#### 4. **Data Consistency Issues**

- Incomplete login logs due to system crashes or network interruptions
- Race conditions between login events and log recording
- Timestamps may be unreliable across distributed systems

- Difficult to correlate login attempts with subsequent malicious activity

#### 5. **False Negatives**

- Missed detection of sophisticated login attempts
- Attackers using valid credentials (compromised account hijacking)
- Legitimate multi-failed login attempts due to forgotten passwords
- Account enumeration attacks appearing as normal authentication failures

#### 6. **Privacy and Compliance Concerns**

- Login logs may contain sensitive information (session tokens, encrypted passwords)
- Storage and handling of authentication data must comply with regulations (GDPR, HIPAA, etc.)
- Separate audit trails needed to distinguish honeypot activity from real incidents

#### 7. **System Resource Exhaustion**

- Denial-of-service attacks targeting login services consume resources
- Excessive authentication logging can fill storage systems quickly
- Database operations for login tracking may become bottlenecks

### Best Practices

- **Rate Limiting**: Implement rate limiting on failed login attempts to prevent brute force
- **Selective Logging**: Log only relevant events to reduce noise and storage impact
- **Anomaly Baseline**: Establish normal authentication patterns before deployment
- **Isolation**: Keep honeypots isolated from production systems to prevent cross-contamination
- **Regular Review**: Periodically audit logs for patterns indicating evasion techniques
- **Encrypt Sensitive Data**: Ensure all authentication-related logs are encrypted at rest and in transit
- **Incident Response Plan**: Develop clear procedures for responding to detected attacks
