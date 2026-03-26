import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Login.css";

function Faculty_Login() {
  const navigate = useNavigate();

  const [facultyId, setFacultyId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
      const response = await fetch(`${API_URL}/api/login/faculty`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ facultyId, password, sessionId: sessionStorage.getItem("honeypot_session") }),
      });

      const data = await response.json();
      if (data.redirect) {
        if (data.redirect.startsWith("http")) {
          window.location.href = data.redirect;
        } else {
          // Relative redirect stays on the same host (frontend), not the backend API
          window.location.href = window.location.origin + data.redirect;
        }
      } else if (!response.ok) {
        setError(data.error || "Authentication failed due to an unknown error.");
      }
    } catch (err) {
      setError("Unable to reach the server. Please try again later.");
    }
  };

  return (
    <div className="container">
      {/* LEFT PANEL */}
      <div className="left-panel">
        <h2>Faculty Login</h2>
        <p className="subtitle">Enter your account details</p>


        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Employee ID"
            value={facultyId}
            onChange={(e) => setFacultyId(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <div className="error-message" style={{ color: "var(--red)", marginTop: "10px", fontSize: "0.9rem" }}>{error}</div>}

          <div className="forgot">Forgot Password?</div>

          <button type="submit">Login</button>
        </form>

        <p className="signup">
          Don’t have an account? <span>Sign up</span>
        </p>
      </div>

      {/* RIGHT PANEL */}
      <div className="right-panel">
        <h1>Welcome to</h1>
        <h1 className="bold">Faculty Portal</h1>
        <p>Login to access your teaching dashboard</p>

        <div className="panel-buttons">
          <button
            className="panel-btn"
            onClick={() => navigate("/login/student")}
          >
            Student Login
          </button>
          <button
            className="panel-btn active"
            onClick={() => navigate("/login/faculty")}
          >
            Faculty Login
          </button>
        </div>

        <button className="back-home-btn" onClick={() => navigate("/")}>
          ← Back to Home
        </button>
      </div>
    </div>
  );
}

export default Faculty_Login;
