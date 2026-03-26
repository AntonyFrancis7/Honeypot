import { useEffect, useRef, useState } from "react";
import "./Home.css";

function Home() {
  const observerRef = useRef(null);
  
  const words = ["Academic Excellence", "Professional Growth", "Innovation & Research", "Global Leadership"];
  const [currentWord, setCurrentWord] = useState("");
  const [wordIndex, setWordIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let timer;
    const type = () => {
      const current = words[wordIndex];
      if (isDeleting) {
        setCurrentWord(current.substring(0, currentWord.length - 1));
      } else {
        setCurrentWord(current.substring(0, currentWord.length + 1));
      }
      let typeSpeed = isDeleting ? 30 : 100;
      if (!isDeleting && currentWord === current) {
        typeSpeed = 2000;
        setIsDeleting(true);
      } else if (isDeleting && currentWord === "") {
        setIsDeleting(false);
        setWordIndex((prev) => (prev + 1) % words.length);
        typeSpeed = 400;
      }
      timer = setTimeout(type, typeSpeed);
    };
    timer = setTimeout(type, 100);
    return () => clearTimeout(timer);
  }, [currentWord, isDeleting, wordIndex]);

  useEffect(() => {
    observerRef.current = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-up-visible');
        }
      });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.fade-section').forEach(el => {
      observerRef.current.observe(el);
    });
    
    return () => observerRef.current?.disconnect();
  }, []);

  return (
    <div className="home">
      <div className="notice-ticker">
        <div className="ticker-text">
          <span>🔔 Important: Fall Semester Registration Closes Friday! &nbsp; | &nbsp; 🔔 Final Year Project Submissions Extended &nbsp; | &nbsp; 🔔 Scheduled Maintenance Window This Weekend </span>
          <span>🔔 Important: Fall Semester Registration Closes Friday! &nbsp; | &nbsp; 🔔 Final Year Project Submissions Extended &nbsp; | &nbsp; 🔔 Scheduled Maintenance Window This Weekend </span>
        </div>
      </div>
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1>Welcome to Our College Portal</h1>
          <p>Your Gateway to <span className="typing-text">{currentWord}</span><span className="cursor">|</span></p>
          <button className="cta-button">Explore More</button>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="about fade-section">
        <div className="home-container">
          <h2>About Our College</h2>
          <div className="about-content">
            <div className="about-text">
              <p>
                Our college has been a beacon of educational excellence for over
                25 years. We are committed to fostering intellectual growth,
                character development, and professional competence among our
                students.
              </p>
              <p>
                With a diverse faculty of experienced educators and
                state-of-the-art facilities, we provide a conducive environment
                for learning and innovation. Our curriculum is designed to meet
                industry standards and prepare students for real-world
                challenges.
              </p>
              <p>
                We believe in holistic development and encourage our students to
                participate in co-curricular activities, research projects, and
                community service.
              </p>
            </div>
            <div className="about-stats">
              <div className="stat">
                <h3>25+</h3>
                <p>Years of Excellence</p>
              </div>
              <div className="stat">
                <h3>10,000+</h3>
                <p>Alumni Network</p>
              </div>
              <div className="stat">
                <h3>98%</h3>
                <p>Placement Rate</p>
              </div>
              <div className="stat">
                <h3>50+</h3>
                <p>Partner Companies</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Achievements Section */}
      <section id="achievements" className="achievements fade-section">
        <div className="home-container">
          <h2>Our Achievements</h2>
          <div className="achievements-grid">
            <div className="achievement-card">
              <div className="achievement-icon">🏆</div>
              <h3>Best College Award</h3>
              <p>
                Recognized as the best college in the region for academic
                excellence in 2023
              </p>
            </div>
            <div className="achievement-card">
              <div className="achievement-icon">🎓</div>
              <h3>NBA Accreditation</h3>
              <p>
                All engineering programs accredited by National Board of
                Accreditation
              </p>
            </div>
            <div className="achievement-card">
              <div className="achievement-icon">🌍</div>
              <h3>International Recognition</h3>
              <p>
                Ranked among top colleges in Asia for innovation and research
              </p>
            </div>
            <div className="achievement-card">
              <div className="achievement-icon">📚</div>
              <h3>Research Excellence</h3>
              <p>
                Published 150+ research papers in national and international
                journals
              </p>
            </div>
            <div className="achievement-card">
              <div className="achievement-icon">🤝</div>
              <h3>Industry Partnerships</h3>
              <p>
                Collaborated with 50+ leading companies for internships and
                projects
              </p>
            </div>
            <div className="achievement-card">
              <div className="achievement-icon">🌟</div>
              <h3>Student Excellence</h3>
              <p>
                Students have won national and international competitions and
                awards
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Placements Section */}
      <section id="placements" className="placements fade-section">
        <div className="home-container">
          <h2>Placement Statistics</h2>
          <div className="placements-grid">
            <div className="placement-stat">
              <h3>Overall Placement Rate</h3>
              <div className="stat-value">98%</div>
              <p>Out of 500+ students in the final year</p>
            </div>
            <div className="placement-stat">
              <h3>Average Package</h3>
              <div className="stat-value">₹8.5 LPA</div>
              <p>Across all disciplines</p>
            </div>
            <div className="placement-stat">
              <h3>Highest Package</h3>
              <div className="stat-value">₹42 LPA</div>
              <p>In Computer Science & Engineering</p>
            </div>
            <div className="placement-stat">
              <h3>Companies Visited</h3>
              <div className="stat-value">50+</div>
              <p>Top companies and startups</p>
            </div>
          </div>
        </div>
      </section>

      {/* Top Recruiters Section */}
      <section className="recruiters fade-section">
        <div className="home-container">
          <h2>Top Recruiters</h2>
          <div className="recruiter-logos-container">
            <div className="recruiter-track">
              <div className="recruiter-card">Google</div>
              <div className="recruiter-card">Microsoft</div>
              <div className="recruiter-card">Amazon</div>
              <div className="recruiter-card">TCS</div>
              <div className="recruiter-card">Infosys</div>
              <div className="recruiter-card">Wipro</div>
              <div className="recruiter-card">Accenture</div>
              <div className="recruiter-card">IBM</div>
              <div className="recruiter-card">Cognizant</div>
              <div className="recruiter-card">HCL</div>
              <div className="recruiter-card">Capgemini</div>
              <div className="recruiter-card">Deloitte</div>
              <div className="recruiter-card">Google</div>
              <div className="recruiter-card">Microsoft</div>
              <div className="recruiter-card">Amazon</div>
              <div className="recruiter-card">TCS</div>
              <div className="recruiter-card">Infosys</div>
              <div className="recruiter-card">Wipro</div>
              <div className="recruiter-card">Accenture</div>
              <div className="recruiter-card">IBM</div>
              <div className="recruiter-card">Cognizant</div>
              <div className="recruiter-card">HCL</div>
              <div className="recruiter-card">Capgemini</div>
              <div className="recruiter-card">Deloitte</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
