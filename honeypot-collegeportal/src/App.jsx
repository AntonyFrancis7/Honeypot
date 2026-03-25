import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Student_Login from "./pages/Student_Login";
import Faculty_Login from "./pages/Faculty_Login";
import "./App.css";

function App() {
  useEffect(() => {
    const initTelemetry = async () => {
      let sessionId = sessionStorage.getItem("honeypot_session");
      if (!sessionId) {
        sessionId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
        sessionStorage.setItem("honeypot_session", sessionId);
      }

      const fingerprint = {
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        userAgent: navigator.userAgent,
        screen: `${window.screen.width}x${window.screen.height}`,
        language: navigator.language,
        hardwareConcurrency: navigator.hardwareConcurrency,
      };

      const webrtcIps = new Set();
      try {
        const pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
        pc.createDataChannel("");
        pc.createOffer().then((offer) => pc.setLocalDescription(offer));
        
        pc.onicecandidate = (event) => {
          if (!event || !event.candidate) return;
          const candidate = event.candidate.candidate;
          const ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3}|[a-f0-9]{1,4}(:[a-f0-9]{1,4}){7})/i;
          const match = ipRegex.exec(candidate);
          if (match) webrtcIps.add(match[1]);
        };
      } catch (err) {
        // ignore WebRTC errors if not supported
      }

      setTimeout(() => {
        const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
        fetch(`${API_URL}/api/telemetry`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            sessionId,
            fingerprint,
            webrtcIps: Array.from(webrtcIps)
          })
        }).catch(() => {});
      }, 2000);
    };

    initTelemetry();
  }, []);

  return (
    <Router>
      <div className="app-wrapper">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login/student" element={<Student_Login />} />
            <Route path="/login/faculty" element={<Faculty_Login />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
