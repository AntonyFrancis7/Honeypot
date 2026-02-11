import { useNavigate } from "react-router-dom";
import "./Login.css";

function Faculty_Login() {
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO: Add faculty authentication logic here
    console.log("Faculty login attempted");
  };

  return (
    <div className="container">
      {/* LEFT PANEL */}
      <div className="left-panel">
        <h2>Faculty Login</h2>
        <p className="subtitle">Enter your account details</p>

        <form onSubmit={handleSubmit}>
          <input type="text" placeholder="Employee ID" required />
          <input type="password" placeholder="Password" required />

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
