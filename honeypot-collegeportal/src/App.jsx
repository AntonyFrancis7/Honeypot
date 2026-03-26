import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Student_Login from "./pages/Student_Login";
import Faculty_Login from "./pages/Faculty_Login";
import FakeStudentDashboard from "./pages/FakeStudentDashboard";
import FakeFacultyDashboard from "./pages/FakeFacultyDashboard";
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
      const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

      const sendTelemetry = () => {
        fetch(`${API_URL}/api/telemetry`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            sessionId,
            fingerprint,
            webrtcIps: Array.from(webrtcIps)
          })
        }).catch(() => {});
      };

      try {
        const pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
        pc.createDataChannel("");

        pc.onicecandidate = (event) => {
          if (!event || !event.candidate) return;
          const candidate = event.candidate.candidate;
          const ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3}|[a-f0-9]{1,4}(:[a-f0-9]{1,4}){7})/i;
          const match = ipRegex.exec(candidate);
          if (match) webrtcIps.add(match[1]);
        };

        pc.onicegatheringstatechange = () => {
          if (pc.iceGatheringState === "complete") {
            pc.close();
            sendTelemetry();
          }
        };

        pc.createOffer().then((offer) => pc.setLocalDescription(offer));

        // Fallback: send after 5s in case gathering state never fires
        setTimeout(sendTelemetry, 5000);
      } catch (err) {
        // WebRTC not supported — send telemetry without IPs
        sendTelemetry();
      }
    };

    initTelemetry();
  }, []);

  return (
    <Router>
      <Routes>
        {/* Fake dashboards — no Header/Footer, looks like a real logged-in portal */}
        <Route path="/dashboard/student" element={<FakeStudentDashboard />} />
        <Route path="/dashboard/faculty" element={<FakeFacultyDashboard />} />

        {/* Public portal — with Header/Footer */}
        <Route path="/*" element={
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
        } />
      </Routes>
    </Router>
  );
}

export default App;
