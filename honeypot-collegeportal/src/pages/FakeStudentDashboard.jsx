import { useState } from "react";
import "./FakeDashboard.css";

const STUDENT = {
  name: "Rahul Verma",
  roll: "22BCS1047",
  program: "B.Tech Computer Science",
  semester: "4th Semester",
  section: "CS-B",
  email: "rahul.verma@christuniversity.in",
  phone: "+91 98765 43210",
  advisor: "Dr. Priya Nair",
};

const ATTENDANCE = [
  { subject: "Data Structures & Algorithms", code: "CSC401", attended: 38, total: 42, pct: 90 },
  { subject: "Operating Systems", code: "CSC403", attended: 29, total: 40, pct: 72 },
  { subject: "Database Management Systems", code: "CSC405", attended: 35, total: 38, pct: 92 },
  { subject: "Computer Networks", code: "CSC407", attended: 22, total: 36, pct: 61 },
  { subject: "Software Engineering", code: "CSC409", attended: 31, total: 34, pct: 91 },
];

const GRADES = [
  { subject: "Mathematics III", code: "MAT301", credits: 4, grade: "A", points: 9 },
  { subject: "Digital Logic Design", code: "CSC301", credits: 3, grade: "A+", points: 10 },
  { subject: "Object Oriented Programming", code: "CSC303", credits: 4, grade: "B+", points: 8 },
  { subject: "Discrete Mathematics", code: "MAT303", credits: 3, grade: "A", points: 9 },
  { subject: "Microprocessors", code: "CSC305", credits: 3, grade: "B", points: 7 },
];

const TIMETABLE = [
  { day: "Monday", slots: ["DSA (9:00)", "OS Lab (11:00)", "DBMS (2:00)", "—", "CN (4:00)"] },
  { day: "Tuesday", slots: ["CN (9:00)", "DSA (10:00)", "—", "SE (2:00)", "DBMS (3:00)"] },
  { day: "Wednesday", slots: ["OS (9:00)", "—", "DSA Lab (11:00)", "CN (2:00)", "SE (3:00)"] },
  { day: "Thursday", slots: ["DBMS (9:00)", "SE (10:00)", "—", "OS (2:00)", "—"] },
  { day: "Friday", slots: ["CN (9:00)", "OS (10:00)", "DBMS Lab (11:00)", "SE (2:00)", "DSA (4:00)"] },
];

export default function FakeStudentDashboard() {
  const [activeTab, setActiveTab] = useState("overview");

  const cgpa = (
    GRADES.reduce((acc, g) => acc + g.points * g.credits, 0) /
    GRADES.reduce((acc, g) => acc + g.credits, 0)
  ).toFixed(2);

  return (
    <div className="fd-root">
      {/* Sidebar */}
      <aside className="fd-sidebar">
        <div className="fd-logo">
          <div className="fd-logo-icon">CU</div>
          <div>
            <div className="fd-logo-title">Christ University</div>
            <div className="fd-logo-sub">Student Portal</div>
          </div>
        </div>

        <nav className="fd-nav">
          {[
            { id: "overview", icon: "⊞", label: "Overview" },
            { id: "attendance", icon: "📋", label: "Attendance" },
            { id: "grades", icon: "📊", label: "Grades" },
            { id: "timetable", icon: "🗓️", label: "Timetable" },
            { id: "fees", icon: "💳", label: "Fee Status" },
          ].map((item) => (
            <button
              key={item.id}
              className={`fd-nav-item ${activeTab === item.id ? "active" : ""}`}
              onClick={() => setActiveTab(item.id)}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="fd-sidebar-footer">
          <div className="fd-avatar">{STUDENT.name.charAt(0)}</div>
          <div>
            <div className="fd-username">{STUDENT.name}</div>
            <div className="fd-roll">{STUDENT.roll}</div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="fd-main">
        <header className="fd-header">
          <div>
            <h1 className="fd-heading">
              {activeTab === "overview" && "Dashboard Overview"}
              {activeTab === "attendance" && "Attendance Report"}
              {activeTab === "grades" && "Academic Grades"}
              {activeTab === "timetable" && "Class Timetable"}
              {activeTab === "fees" && "Fee Statement"}
            </h1>
            <p className="fd-subheading">
              {STUDENT.program} · {STUDENT.semester}
            </p>
          </div>
          <div className="fd-semester-badge">Sem 4 · 2025–26</div>
        </header>

        {/* OVERVIEW */}
        {activeTab === "overview" && (
          <>
            <div className="fd-cards">
              <div className="fd-card">
                <div className="fd-card-label">CGPA</div>
                <div className="fd-card-value green">{cgpa}</div>
                <div className="fd-card-sub">Out of 10.00</div>
              </div>
              <div className="fd-card">
                <div className="fd-card-label">Avg Attendance</div>
                <div className="fd-card-value yellow">
                  {Math.round(ATTENDANCE.reduce((a, r) => a + r.pct, 0) / ATTENDANCE.length)}%
                </div>
                <div className="fd-card-sub">Minimum required: 75%</div>
              </div>
              <div className="fd-card">
                <div className="fd-card-label">Subjects</div>
                <div className="fd-card-value blue">{ATTENDANCE.length}</div>
                <div className="fd-card-sub">This semester</div>
              </div>
              <div className="fd-card">
                <div className="fd-card-label">Credits Earned</div>
                <div className="fd-card-value purple">72</div>
                <div className="fd-card-sub">Of 160 total</div>
              </div>
            </div>

            <div className="fd-section-title">Profile Details</div>
            <div className="fd-profile-grid">
              {Object.entries({
                "Full Name": STUDENT.name,
                "Roll Number": STUDENT.roll,
                "Program": STUDENT.program,
                "Section": STUDENT.section,
                "Email": STUDENT.email,
                "Phone": STUDENT.phone,
                "Faculty Advisor": STUDENT.advisor,
              }).map(([k, v]) => (
                <div className="fd-profile-item" key={k}>
                  <span className="fd-profile-label">{k}</span>
                  <span className="fd-profile-value">{v}</span>
                </div>
              ))}
            </div>
          </>
        )}

        {/* ATTENDANCE */}
        {activeTab === "attendance" && (
          <div className="fd-table-wrap">
            <table className="fd-table">
              <thead>
                <tr>
                  <th>Subject</th>
                  <th>Code</th>
                  <th>Attended</th>
                  <th>Total</th>
                  <th>Percentage</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {ATTENDANCE.map((row) => (
                  <tr key={row.code}>
                    <td>{row.subject}</td>
                    <td><span className="fd-badge">{row.code}</span></td>
                    <td>{row.attended}</td>
                    <td>{row.total}</td>
                    <td>
                      <div className="fd-bar-wrap">
                        <div className="fd-bar" style={{ width: `${row.pct}%`, background: row.pct < 75 ? "#ef4444" : row.pct < 85 ? "#f59e0b" : "#22c55e" }} />
                        <span>{row.pct}%</span>
                      </div>
                    </td>
                    <td>
                      <span className={`fd-status ${row.pct >= 75 ? "ok" : "low"}`}>
                        {row.pct >= 75 ? "Safe" : "Shortage"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* GRADES */}
        {activeTab === "grades" && (
          <div className="fd-table-wrap">
            <div className="fd-cgpa-banner">Current CGPA: <strong>{cgpa}</strong></div>
            <table className="fd-table">
              <thead>
                <tr>
                  <th>Subject</th>
                  <th>Code</th>
                  <th>Credits</th>
                  <th>Grade</th>
                  <th>Grade Points</th>
                </tr>
              </thead>
              <tbody>
                {GRADES.map((row) => (
                  <tr key={row.code}>
                    <td>{row.subject}</td>
                    <td><span className="fd-badge">{row.code}</span></td>
                    <td>{row.credits}</td>
                    <td><span className={`fd-grade grade-${row.grade.replace("+", "p")}`}>{row.grade}</span></td>
                    <td>{row.points}.0</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* TIMETABLE */}
        {activeTab === "timetable" && (
          <div className="fd-table-wrap">
            <table className="fd-table">
              <thead>
                <tr>
                  <th>Day</th>
                  <th>9:00–10:00</th>
                  <th>10:00–11:00</th>
                  <th>11:00–12:00</th>
                  <th>2:00–3:00</th>
                  <th>3:00–4:00</th>
                </tr>
              </thead>
              <tbody>
                {TIMETABLE.map((row) => (
                  <tr key={row.day}>
                    <td><strong>{row.day}</strong></td>
                    {row.slots.map((s, i) => (
                      <td key={i} className={s === "—" ? "fd-empty" : ""}>{s}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* FEES */}
        {activeTab === "fees" && (
          <div className="fd-table-wrap">
            <div className="fd-cgpa-banner" style={{ background: "rgba(34,197,94,0.12)", borderColor: "#22c55e", color: "#4ade80" }}>
              Fee Status: <strong>Paid ✓</strong>
            </div>
            <table className="fd-table">
              <thead>
                <tr><th>Description</th><th>Amount (₹)</th><th>Due Date</th><th>Status</th></tr>
              </thead>
              <tbody>
                {[
                  { desc: "Tuition Fee — Sem 4", amt: "85,000", due: "15 Jan 2026", status: "Paid" },
                  { desc: "Library Fee", amt: "2,000", due: "15 Jan 2026", status: "Paid" },
                  { desc: "Exam Fee", amt: "3,500", due: "01 Feb 2026", status: "Paid" },
                  { desc: "Development Fee", amt: "5,000", due: "15 Jan 2026", status: "Paid" },
                ].map((r, i) => (
                  <tr key={i}>
                    <td>{r.desc}</td>
                    <td>₹ {r.amt}</td>
                    <td>{r.due}</td>
                    <td><span className="fd-status ok">{r.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
