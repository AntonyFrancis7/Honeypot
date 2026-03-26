import { useState } from "react";
import "./FakeDashboard.css";

const FACULTY = {
  name: "Dr. Anita Sharma",
  id: "FAC2019048",
  department: "Department of Computer Science",
  designation: "Associate Professor",
  email: "anita.sharma@christuniversity.in",
  phone: "+91 98801 22345",
  office: "Room 304, Block C",
  specialization: "Machine Learning & Data Mining",
};

const CLASSES = [
  { subject: "Machine Learning", code: "CSC601", section: "CS-A", students: 62, schedule: "Mon/Wed 9:00–10:00" },
  { subject: "Deep Learning", code: "CSC703", section: "CS-A & B", students: 58, schedule: "Tue/Thu 11:00–12:00" },
  { subject: "Data Warehousing", code: "CSC605", section: "CS-B", students: 55, schedule: "Mon/Fri 2:00–3:00" },
  { subject: "Research Methodology", code: "PHD101", section: "PhD Batch", students: 14, schedule: "Sat 10:00–12:00" },
];

const STUDENTS = [
  { roll: "22BCS1001", name: "Aarav Mehta", attendance: 88, grade: "A" },
  { roll: "22BCS1012", name: "Sneha Pillai", attendance: 92, grade: "A+" },
  { roll: "22BCS1023", name: "Rohan Das", attendance: 65, grade: "B" },
  { roll: "22BCS1034", name: "Kavish Joshi", attendance: 74, grade: "B+" },
  { roll: "22BCS1045", name: "Lakshmi Iyer", attendance: 95, grade: "A+" },
  { roll: "22BCS1056", name: "Dev Naik", attendance: 55, grade: "C+" },
  { roll: "22BCS1067", name: "Priya Rajan", attendance: 81, grade: "A" },
  { roll: "22BCS1078", name: "Arjun Bose", attendance: 70, grade: "B+" },
];

const NOTICES = [
  { date: "24 Mar 2026", title: "Mid-Sem Grade Submission Deadline extended to 28 March" },
  { date: "20 Mar 2026", title: "Faculty Development Programme on AI Tools — Registration open" },
  { date: "15 Mar 2026", title: "Examination schedule for Semester 6 published on ERP" },
  { date: "10 Mar 2026", title: "Research funding applications due by 30 March 2026" },
];

export default function FakeFacultyDashboard() {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="fd-root">
      {/* Sidebar */}
      <aside className="fd-sidebar">
        <div className="fd-logo">
          <div className="fd-logo-icon">CU</div>
          <div>
            <div className="fd-logo-title">Christ University</div>
            <div className="fd-logo-sub">Faculty Portal</div>
          </div>
        </div>

        <nav className="fd-nav">
          {[
            { id: "overview", icon: "⊞", label: "Overview" },
            { id: "classes", icon: "📚", label: "My Classes" },
            { id: "students", icon: "👥", label: "Student Roster" },
            { id: "notices", icon: "📢", label: "Notices" },
            { id: "payroll", icon: "💳", label: "Payroll" },
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
          <div className="fd-avatar">{FACULTY.name.charAt(0)}</div>
          <div>
            <div className="fd-username">{FACULTY.name}</div>
            <div className="fd-roll">{FACULTY.id}</div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="fd-main">
        <header className="fd-header">
          <div>
            <h1 className="fd-heading">
              {activeTab === "overview" && "Faculty Dashboard"}
              {activeTab === "classes" && "My Classes"}
              {activeTab === "students" && "Student Roster"}
              {activeTab === "notices" && "Notices & Circulars"}
              {activeTab === "payroll" && "Payroll Statement"}
            </h1>
            <p className="fd-subheading">{FACULTY.department}</p>
          </div>
          <div className="fd-semester-badge">Sem 6 · 2025–26</div>
        </header>

        {/* OVERVIEW */}
        {activeTab === "overview" && (
          <>
            <div className="fd-cards">
              <div className="fd-card">
                <div className="fd-card-label">Classes</div>
                <div className="fd-card-value blue">{CLASSES.length}</div>
                <div className="fd-card-sub">This semester</div>
              </div>
              <div className="fd-card">
                <div className="fd-card-label">Total Students</div>
                <div className="fd-card-value green">{CLASSES.reduce((a, c) => a + c.students, 0)}</div>
                <div className="fd-card-sub">Across all sections</div>
              </div>
              <div className="fd-card">
                <div className="fd-card-label">Avg Attendance</div>
                <div className="fd-card-value yellow">
                  {Math.round(STUDENTS.reduce((a, s) => a + s.attendance, 0) / STUDENTS.length)}%
                </div>
                <div className="fd-card-sub">ML class (CS-A)</div>
              </div>
              <div className="fd-card">
                <div className="fd-card-label">At-Risk Students</div>
                <div className="fd-card-value red">{STUDENTS.filter(s => s.attendance < 75).length}</div>
                <div className="fd-card-sub">Below 75% attendance</div>
              </div>
            </div>

            <div className="fd-section-title">Profile Details</div>
            <div className="fd-profile-grid">
              {Object.entries({
                "Full Name": FACULTY.name,
                "Employee ID": FACULTY.id,
                "Designation": FACULTY.designation,
                "Department": FACULTY.department,
                "Specialization": FACULTY.specialization,
                "Email": FACULTY.email,
                "Phone": FACULTY.phone,
                "Office": FACULTY.office,
              }).map(([k, v]) => (
                <div className="fd-profile-item" key={k}>
                  <span className="fd-profile-label">{k}</span>
                  <span className="fd-profile-value">{v}</span>
                </div>
              ))}
            </div>
          </>
        )}

        {/* CLASSES */}
        {activeTab === "classes" && (
          <div className="fd-table-wrap">
            <table className="fd-table">
              <thead>
                <tr><th>Subject</th><th>Code</th><th>Section</th><th>Students</th><th>Schedule</th></tr>
              </thead>
              <tbody>
                {CLASSES.map((c) => (
                  <tr key={c.code}>
                    <td>{c.subject}</td>
                    <td><span className="fd-badge">{c.code}</span></td>
                    <td>{c.section}</td>
                    <td>{c.students}</td>
                    <td>{c.schedule}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* STUDENTS */}
        {activeTab === "students" && (
          <div className="fd-table-wrap">
            <table className="fd-table">
              <thead>
                <tr><th>Roll No.</th><th>Name</th><th>Attendance</th><th>Grade</th><th>Status</th></tr>
              </thead>
              <tbody>
                {STUDENTS.map((s) => (
                  <tr key={s.roll}>
                    <td><span className="fd-badge">{s.roll}</span></td>
                    <td>{s.name}</td>
                    <td>
                      <div className="fd-bar-wrap">
                        <div className="fd-bar" style={{ width: `${s.attendance}%`, background: s.attendance < 75 ? "#ef4444" : s.attendance < 85 ? "#f59e0b" : "#22c55e" }} />
                        <span>{s.attendance}%</span>
                      </div>
                    </td>
                    <td><span className={`fd-grade grade-${s.grade.replace("+", "p")}`}>{s.grade}</span></td>
                    <td><span className={`fd-status ${s.attendance >= 75 ? "ok" : "low"}`}>
                      {s.attendance >= 75 ? "Regular" : "At Risk"}
                    </span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* NOTICES */}
        {activeTab === "notices" && (
          <div className="fd-notices">
            {NOTICES.map((n, i) => (
              <div className="fd-notice-card" key={i}>
                <div className="fd-notice-date">{n.date}</div>
                <div className="fd-notice-title">{n.title}</div>
              </div>
            ))}
          </div>
        )}

        {/* PAYROLL */}
        {activeTab === "payroll" && (
          <div className="fd-table-wrap">
            <div className="fd-cgpa-banner" style={{ background: "rgba(34,197,94,0.12)", borderColor: "#22c55e", color: "#4ade80" }}>
              March 2026 Payslip — <strong>Credited ✓</strong>
            </div>
            <table className="fd-table">
              <thead>
                <tr><th>Component</th><th>Amount (₹)</th></tr>
              </thead>
              <tbody>
                {[
                  ["Basic Salary", "72,000"],
                  ["HRA", "18,000"],
                  ["Transport Allowance", "3,200"],
                  ["Medical Allowance", "1,500"],
                  ["PF Deduction", "− 8,640"],
                  ["TDS Deduction", "− 6,200"],
                  ["Net Pay", "79,860"],
                ].map(([comp, amt], i) => (
                  <tr key={i} className={comp === "Net Pay" ? "fd-row-bold" : ""}>
                    <td>{comp}</td>
                    <td>₹ {amt}</td>
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
