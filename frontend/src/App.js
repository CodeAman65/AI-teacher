// import logo from './logo.svg';
// import './App.css';

// function App() {
//   return (
//     <div className="App">
//       <header className="App-header">
//         <img src={logo} className="App-logo" alt="logo" />
//         <p>
//           Edit <code>src/App.js</code> and save to reload.
//         </p>
//         <a
//           className="App-link"
//           href="https://reactjs.org"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           Learn React
//         </a>
//       </header>
//     </div>
//   );
// }

// export default App;

import { useState, useEffect, useRef, useCallback } from "react";
import LiveSessionState from "./LiveSessionState";

// ─── CONSTANTS ────────────────────────────────────────────────────────────────

const CHAPTERS = {
  Physics: ["Light — Reflection & Refraction", "Electricity", "Magnetic Effects of Current"],
  Chemistry: ["Chemical Reactions & Equations", "Acids, Bases & Salts", "Metals & Non-Metals"],
  Biology: ["Life Processes", "Control & Coordination", "Reproduction"],
};

const LOADING_STEPS = [
  { icon: "📚", text: "NCERT books search ho rahi hain...", detail: "Pinecone vector database query" },
  { icon: "🧠", text: "Concept samjha ja raha hai...", detail: "AI processing your question" },
  { icon: "✍️", text: "Priya ma'am script likh rahi hain...", detail: "Generating Hinglish explanation" },
  { icon: "🎙️", text: "Awaaz record ho rahi hai...", detail: "Sarvam AI voice synthesis" },
  { icon: "🎬", text: "Video ban raha hai...", detail: "D-ID avatar generation" },
  { icon: "✨", text: "Almost ready! Bas ek second...", detail: "Finalizing your lesson" },
];

const SUBJECT_COLORS = {
  Physics: { primary: "#3b82f6", light: "#60a5fa", glow: "rgba(59,130,246,0.3)" },
  Chemistry: { primary: "#10b981", light: "#34d399", glow: "rgba(16,185,129,0.3)" },
  Biology: { primary: "#f59e0b", light: "#fbbf24", glow: "rgba(245,158,11,0.3)" },
};

// ─── PARTICLE FIELD ───────────────────────────────────────────────────────────

function ParticleField() {
  const canvasRef = useRef(null);
  const animRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let W = (canvas.width = window.innerWidth);
    let H = (canvas.height = window.innerHeight);

    const particles = Array.from({ length: 60 }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 1.5 + 0.5,
      opacity: Math.random() * 0.4 + 0.1,
    }));

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = W;
        if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H;
        if (p.y > H) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(99, 179, 237, ${p.opacity})`;
        ctx.fill();
      });

      // Draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 100) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(99, 179, 237, ${0.08 * (1 - dist / 100)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    const onResize = () => {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{ position: "fixed", top: 0, left: 0, pointerEvents: "none", zIndex: 0, opacity: 0.6 }}
    />
  );
}

// ─── ANIMATED DOTS ────────────────────────────────────────────────────────────

function PulseDots({ color = "#10b981" }) {
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: color,
            animation: `pulse-dot 1.4s ease-in-out ${i * 0.2}s infinite`,
            boxShadow: `0 0 8px ${color}`,
          }}
        />
      ))}
    </div>
  );
}

// ─── SUBJECT BADGE ────────────────────────────────────────────────────────────

function SubjectBadge({ subject }) {
  const colors = SUBJECT_COLORS[subject] || SUBJECT_COLORS.Physics;
  return (
    <span
      style={{
        background: `linear-gradient(135deg, ${colors.primary}22, ${colors.primary}44)`,
        border: `1px solid ${colors.primary}66`,
        color: colors.light,
        padding: "2px 10px",
        borderRadius: 20,
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
      }}
    >
      {subject}
    </span>
  );
}

// ─── STATE 1: IDLE ────────────────────────────────────────────────────────────

function IdleState({ onStart }) {
  const [selectedSubject, setSelectedSubject] = useState("Physics");
  const [selectedChapter, setSelectedChapter] = useState(CHAPTERS.Physics[0]);
  const [doubt, setDoubt] = useState("");
  const [hovered, setHovered] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);
  const colors = SUBJECT_COLORS[selectedSubject];

  const handleSubjectChange = (subject) => {
    setSelectedSubject(subject);
    setSelectedChapter(CHAPTERS[subject][0]);
  };

  const handleStart = () => {
    onStart({ subject: selectedSubject, chapter: selectedChapter, doubt });
  };

  return (
    <div style={styles.stateContainer}>
      {/* Hero Header */}
      <div style={{ textAlign: "center", marginBottom: 48, position: "relative" }}>
        {/* Glowing avatar circle */}
        <div style={{ position: "relative", display: "inline-block", marginBottom: 24 }}>
          <div
            style={{
              width: 96,
              height: 96,
              borderRadius: "50%",
              background: `linear-gradient(135deg, #1a2744, #0f172a)`,
              border: `2px solid ${colors.primary}66`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 48,
              boxShadow: `0 0 40px ${colors.glow}, 0 0 80px ${colors.glow}`,
              animation: "float 3s ease-in-out infinite",
              margin: "0 auto",
            }}
          >
            👩‍🏫
          </div>
          <div
            style={{
              position: "absolute",
              bottom: 4,
              right: 4,
              width: 20,
              height: 20,
              borderRadius: "50%",
              background: "#10b981",
              border: "2px solid #0f172a",
              boxShadow: "0 0 8px #10b981",
              animation: "pulse-online 2s ease-in-out infinite",
            }}
          />
        </div>

        <h1 style={styles.heroTitle}>
          Priya Ma'am
          <span style={{ display: "block", fontSize: "0.45em", color: colors.light, letterSpacing: "0.15em", fontWeight: 400, marginTop: 4 }}>
            AI SCIENCE TEACHER
          </span>
        </h1>

        <p style={{ color: "#64748b", fontSize: 14, marginTop: 8, letterSpacing: "0.05em" }}>
          Class 10 NCERT • Hinglish Explanations • Instant Video Lessons
        </p>

        {/* Stats row */}
        <div style={{ display: "flex", justifyContent: "center", gap: 24, marginTop: 20 }}>
          {[
            { label: "Topics", value: "9" },
            { label: "Language", value: "Hinglish" },
            { label: "Board", value: "NCERT" },
          ].map((s) => (
            <div key={s.label} style={{ textAlign: "center" }}>
              <div style={{ color: colors.light, fontWeight: 700, fontSize: 16 }}>{s.value}</div>
              <div style={{ color: "#475569", fontSize: 11, letterSpacing: "0.08em" }}>{s.label.toUpperCase()}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Card */}
      <div style={{ ...styles.card, borderColor: `${colors.primary}33` }}>
        {/* Subject Tabs */}
        <div style={{ marginBottom: 24 }}>
          <label style={styles.label}>📖 Subject</label>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            {Object.keys(CHAPTERS).map((subj) => {
              const sc = SUBJECT_COLORS[subj];
              const active = selectedSubject === subj;
              return (
                <button
                  key={subj}
                  onClick={() => handleSubjectChange(subj)}
                  style={{
                    flex: 1,
                    padding: "10px 4px",
                    borderRadius: 10,
                    border: active ? `1.5px solid ${sc.primary}` : "1.5px solid #1e293b",
                    background: active
                      ? `linear-gradient(135deg, ${sc.primary}22, ${sc.primary}11)`
                      : "#0f172a",
                    color: active ? sc.light : "#475569",
                    fontWeight: active ? 700 : 500,
                    fontSize: 13,
                    cursor: "pointer",
                    transition: "all 0.2s",
                    boxShadow: active ? `0 0 16px ${sc.glow}` : "none",
                  }}
                >
                  {subj === "Physics" ? "⚡" : subj === "Chemistry" ? "🧪" : "🌿"} {subj}
                </button>
              );
            })}
          </div>
        </div>

        {/* Chapter Dropdown */}
        <div style={{ marginBottom: 24 }}>
          <label style={styles.label}>📚 Chapter</label>
          <div style={{ position: "relative", marginTop: 8 }}>
            <select
              value={selectedChapter}
              onChange={(e) => setSelectedChapter(e.target.value)}
              style={{
                ...styles.select,
                borderColor: `${colors.primary}44`,
                backgroundImage: `linear-gradient(135deg, #0f172a, #1a2744)`,
              }}
            >
              {CHAPTERS[selectedSubject].map((ch) => (
                <option key={ch} value={ch} style={{ background: "#0f172a" }}>
                  {ch}
                </option>
              ))}
            </select>
            <div
              style={{
                position: "absolute",
                right: 16,
                top: "50%",
                transform: "translateY(-50%)",
                color: colors.primary,
                pointerEvents: "none",
                fontSize: 12,
              }}
            >
              ▼
            </div>
          </div>
        </div>

        {/* Doubt Input */}
        <div style={{ marginBottom: 28 }}>
          <label style={styles.label}>
            💬 Apna Doubt
            <span style={{ color: "#475569", fontWeight: 400, marginLeft: 8, fontSize: 11 }}>
              (optional)
            </span>
          </label>
          <div style={{ position: "relative", marginTop: 8 }}>
            <input
              type="text"
              placeholder="Ya apna doubt type karein... e.g. osmosis kya hota hai?"
              value={doubt}
              onChange={(e) => setDoubt(e.target.value)}
              onFocus={() => setInputFocused(true)}
              onBlur={() => setInputFocused(false)}
              onKeyDown={(e) => e.key === "Enter" && handleStart()}
              style={{
                ...styles.input,
                borderColor: inputFocused ? colors.primary : "#1e293b",
                boxShadow: inputFocused ? `0 0 0 3px ${colors.glow}` : "none",
              }}
            />
            {doubt && (
              <button
                onClick={() => setDoubt("")}
                style={{
                  position: "absolute",
                  right: 12,
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  color: "#475569",
                  cursor: "pointer",
                  fontSize: 16,
                }}
              >
                ×
              </button>
            )}
          </div>
        </div>

        {/* CTA Button */}
        <button
          onClick={handleStart}
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
          style={{
            ...styles.ctaButton,
            background: hovered
              ? `linear-gradient(135deg, #059669, #10b981, #34d399)`
              : `linear-gradient(135deg, #047857, #059669, #10b981)`,
            transform: hovered ? "translateY(-2px) scale(1.01)" : "translateY(0) scale(1)",
            boxShadow: hovered
              ? "0 12px 40px rgba(16,185,129,0.5), 0 0 60px rgba(16,185,129,0.2)"
              : "0 6px 24px rgba(16,185,129,0.35)",
          }}
        >
          <span style={{ fontSize: 20 }}>🎓</span>
          <span>Padhana Shuru Karo</span>
          <span style={{ opacity: 0.8, fontSize: 12 }}>→</span>
        </button>

        {/* Current selection preview */}
        <div
          style={{
            marginTop: 16,
            padding: "10px 14px",
            background: "#0a0f1a",
            borderRadius: 8,
            border: "1px solid #1e293b",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <SubjectBadge subject={selectedSubject} />
          <span style={{ color: "#475569", fontSize: 12 }}>→</span>
          <span style={{ color: "#94a3b8", fontSize: 12, flex: 1 }}>{selectedChapter}</span>
          {doubt && (
            <>
              <span style={{ color: "#475569", fontSize: 12 }}>→</span>
              <span style={{ color: "#64748b", fontSize: 11, maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                "{doubt}"
              </span>
            </>
          )}
        </div>
      </div>

      {/* Features Strip */}
      <div style={{ display: "flex", gap: 12, marginTop: 20, justifyContent: "center", flexWrap: "wrap" }}>
        {[
          { icon: "🧠", text: "RAG-powered NCERT" },
          { icon: "🗣️", text: "Hinglish Voice" },
          { icon: "🎥", text: "AI Avatar Video" },
        ].map((f) => (
          <div
            key={f.text}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "6px 14px",
              background: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: 20,
              color: "#475569",
              fontSize: 12,
            }}
          >
            <span>{f.icon}</span>
            <span>{f.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── STATE 2: LOADING ─────────────────────────────────────────────────────────

function LoadingState({ jobData, onCancel }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef(null);
  const progressRef = useRef(null);
  const elapsedRef = useRef(null);

  useEffect(() => {
    // Step cycling
    intervalRef.current = setInterval(() => {
      setStepIndex((i) => Math.min(i + 1, LOADING_STEPS.length - 1));
    }, 4000);

    // Smooth progress bar — reaches ~90% in 24s
    progressRef.current = setInterval(() => {
      setProgress((p) => {
        if (p >= 90) return p;
        const remaining = 90 - p;
        return p + remaining * 0.015;
      });
    }, 200);

    // Elapsed timer
    elapsedRef.current = setInterval(() => {
      setElapsed((e) => e + 1);
    }, 1000);

    return () => {
      clearInterval(intervalRef.current);
      clearInterval(progressRef.current);
      clearInterval(elapsedRef.current);
    };
  }, []);

  const step = LOADING_STEPS[stepIndex];
  const progressPercent = Math.min(progress, 90);

  return (
    <div style={styles.stateContainer}>
      {/* Teacher Avatar — animated */}
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <div style={{ position: "relative", display: "inline-block" }}>
          {/* Pulsing rings */}
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                width: 96 + i * 28,
                height: 96 + i * 28,
                borderRadius: "50%",
                border: `1px solid rgba(16,185,129,${0.3 / i})`,
                animation: `ripple 2s ease-out ${i * 0.4}s infinite`,
              }}
            />
          ))}

          {/* Teacher Image */}
          <div
            style={{
              width: 96,
              height: 96,
              borderRadius: "50%",
              background: "linear-gradient(135deg, #1a2744, #0f172a)",
              border: "2px solid #10b98166",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 48,
              position: "relative",
              zIndex: 1,
              boxShadow: "0 0 30px rgba(16,185,129,0.4)",
            }}
          >
            👩‍🏫
          </div>
        </div>

        <div style={{ marginTop: 32 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 8 }}>
            <span style={{ fontSize: 22 }}>{step.icon}</span>
            <span
              style={{
                color: "#e2e8f0",
                fontWeight: 600,
                fontSize: 17,
                animation: "fadeSlideIn 0.5s ease",
              }}
            >
              {step.text}
            </span>
          </div>
          <div style={{ color: "#475569", fontSize: 12, letterSpacing: "0.08em" }}>
            {step.detail}
          </div>
        </div>
      </div>

      {/* Progress Section */}
      <div style={styles.card}>
        {/* Progress Bar */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <span style={{ color: "#64748b", fontSize: 12 }}>Progress</span>
            <span style={{ color: "#10b981", fontSize: 12, fontWeight: 600 }}>
              {Math.round(progressPercent)}%
            </span>
          </div>
          <div
            style={{
              width: "100%",
              height: 6,
              background: "#1e293b",
              borderRadius: 3,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${progressPercent}%`,
                background: "linear-gradient(90deg, #059669, #10b981, #34d399)",
                borderRadius: 3,
                transition: "width 0.3s ease",
                boxShadow: "0 0 10px rgba(16,185,129,0.6)",
              }}
            />
          </div>
        </div>

        {/* Step indicators */}
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
          {LOADING_STEPS.map((s, i) => (
            <div
              key={i}
              style={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 13,
                background:
                  i < stepIndex
                    ? "linear-gradient(135deg, #059669, #10b981)"
                    : i === stepIndex
                    ? "#1a2744"
                    : "#0f172a",
                border:
                  i < stepIndex
                    ? "1.5px solid #10b981"
                    : i === stepIndex
                    ? "1.5px solid #10b981"
                    : "1.5px solid #1e293b",
                boxShadow: i === stepIndex ? "0 0 12px rgba(16,185,129,0.5)" : "none",
                transition: "all 0.3s ease",
              }}
            >
              {i < stepIndex ? "✓" : s.icon}
            </div>
          ))}
        </div>

        {/* Current topic & timing */}
        <div
          style={{
            padding: "12px 14px",
            background: "#0a0f1a",
            borderRadius: 8,
            border: "1px solid #1e293b",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <div style={{ color: "#94a3b8", fontSize: 12 }}>{jobData?.chapter}</div>
            {jobData?.doubt && (
              <div style={{ color: "#475569", fontSize: 11, marginTop: 2 }}>"{jobData.doubt}"</div>
            )}
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ color: "#475569", fontSize: 11 }}>Elapsed</div>
            <div style={{ color: "#10b981", fontSize: 13, fontWeight: 600 }}>
              {elapsed}s
            </div>
          </div>
        </div>

        {/* Animated dots */}
        <div style={{ display: "flex", justifyContent: "center", marginTop: 20 }}>
          <PulseDots color="#10b981" />
        </div>
      </div>

      <button
        onClick={onCancel}
        style={{
          marginTop: 16,
          background: "none",
          border: "1px solid #1e293b",
          color: "#475569",
          padding: "8px 20px",
          borderRadius: 8,
          cursor: "pointer",
          fontSize: 13,
          transition: "all 0.2s",
        }}
      >
        ← Wapas Jao
      </button>
    </div>
  );
}

// ─── STATE 3: PLAYING ─────────────────────────────────────────────────────────

function PlayingState({ videoUrl, scriptText, attempt, onRetry, jobData }) {
  const [showScript, setShowScript] = useState(false);
  const [retryHovered, setRetryHovered] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setShowScript(true), 800);
    return () => clearTimeout(t);
  }, []);

  return (
    <div style={styles.stateContainer}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 6 }}>
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "#ef4444",
              boxShadow: "0 0 8px #ef4444",
              animation: "pulse-online 1s ease-in-out infinite",
            }}
          />
          <span style={{ color: "#ef4444", fontSize: 12, fontWeight: 700, letterSpacing: "0.1em" }}>
            LIVE LESSON
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
          <SubjectBadge subject={jobData?.subject || "Physics"} />
          <span style={{ color: "#64748b", fontSize: 13 }}>{jobData?.chapter}</span>
        </div>
        {attempt > 1 && (
          <div
            style={{
              display: "inline-block",
              marginTop: 8,
              padding: "3px 12px",
              background: "rgba(245,158,11,0.15)",
              border: "1px solid rgba(245,158,11,0.3)",
              borderRadius: 20,
              color: "#f59e0b",
              fontSize: 11,
              fontWeight: 600,
            }}
          >
            🔄 Attempt #{attempt} — New Analogy
          </div>
        )}
      </div>

      {/* Audio Player (Podcast Style) */}
      <div
        style={{
          borderRadius: 16,
          overflow: "hidden",
          border: "1px solid #1e293b",
          boxShadow: "0 20px 60px rgba(0,0,0,0.5), 0 0 40px rgba(16,185,129,0.1)",
          marginBottom: 20,
          position: "relative",
          background: "#0a0f1a",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          padding: 40
        }}
      >
        <div style={{ position: "relative", display: "inline-block", marginBottom: 30 }}>
          <div
            style={{
              width: 120,
              height: 120,
              borderRadius: "50%",
              background: `linear-gradient(135deg, #1a2744, #0f172a)`,
              border: `3px solid #10b981`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 60,
              boxShadow: isPlaying ? `0 0 40px rgba(16,185,129,0.4), 0 0 80px rgba(16,185,129,0.2)` : "none",
              animation: isPlaying ? "pulse-dot 2s infinite" : "none",
            }}
          >
            👩‍🏫
          </div>
        </div>
        
        <audio
          key={videoUrl}
          controls
          autoPlay
          style={{ width: "100%", outline: "none" }}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => setIsPlaying(false)}
        >
          <source src={videoUrl} type="video/mp4" />
          <source src={videoUrl} type="audio/wav" />
          Your browser does not support the audio tag.
        </audio>
      </div>

      {/* Script Card */}
      <div
        style={{
          ...styles.card,
          opacity: showScript ? 1 : 0,
          transform: showScript ? "translateY(0)" : "translateY(16px)",
          transition: "all 0.5s ease",
          marginBottom: 20,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 14,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 16 }}>📝</span>
            <span style={{ color: "#94a3b8", fontWeight: 600, fontSize: 14 }}>
              Priya Ma'am ka Script
            </span>
          </div>
          <button
            onClick={() => {
              navigator.clipboard?.writeText(scriptText);
            }}
            style={{
              background: "none",
              border: "1px solid #1e293b",
              color: "#475569",
              padding: "4px 10px",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 11,
            }}
          >
            📋 Copy
          </button>
        </div>

        <p
          style={{
            color: "#94a3b8",
            lineHeight: 1.75,
            fontSize: 14,
            margin: 0,
            fontStyle: "italic",
            borderLeft: "2px solid #10b98144",
            paddingLeft: 14,
          }}
        >
          {scriptText}
        </p>
      </div>

      {/* Retry Button */}
      <button
        onClick={onRetry}
        onMouseEnter={() => setRetryHovered(true)}
        onMouseLeave={() => setRetryHovered(false)}
        style={{
          ...styles.ctaButton,
          background: retryHovered
            ? "linear-gradient(135deg, #d97706, #f59e0b, #fbbf24)"
            : "linear-gradient(135deg, #b45309, #d97706, #f59e0b)",
          boxShadow: retryHovered
            ? "0 12px 40px rgba(245,158,11,0.5)"
            : "0 6px 24px rgba(245,158,11,0.35)",
          transform: retryHovered ? "translateY(-2px)" : "translateY(0)",
          marginBottom: 8,
        }}
      >
        <span style={{ fontSize: 20 }}>🤔</span>
        <span>Samjha Nahi — Dobara Samjhao</span>
      </button>

      <p style={{ textAlign: "center", color: "#334155", fontSize: 12, margin: 0 }}>
        Naya analogy use hoga • Attempt #{attempt + 1} ready hai
      </p>
    </div>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────

export default function App() {
  const [state, setState] = useState("idle"); // idle | loading | playing
  const [jobData, setJobData] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [scriptText, setScriptText] = useState("");
  const [attempt, setAttempt] = useState(1);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  // ── Poll job status ──────────────────────────────────────
  const startPolling = useCallback((id) => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/status/${id}`);
        const data = await res.json();

        if (data.status === "done" || data.video_url) {
          clearInterval(pollRef.current);
          setVideoUrl(data.video_url);
          setScriptText(data.script || "");
          setState("playing");
        } else if (data.status === "error") {
          clearInterval(pollRef.current);
          setError(data.message || "Kuch error ho gaya. Please retry.");
          setState("idle");
        }
      } catch (e) {
        // Keep polling — backend might be processing
      }
    }, 4000);
  }, []);

  // ── Start lesson ─────────────────────────────────────────
  const handleStart = async ({ subject, chapter, doubt }) => {
    setError(null);
    setJobData({ subject, chapter, doubt });
    setState("live"); return; 
    try {
      const res = await fetch("http://localhost:8000/teach", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: chapter,
          student_id: `student_${Date.now()}`,
          doubt: doubt || undefined,
        }),
      });

      const data = await res.json();

      if (data.video_url) {
        // Synchronous response
        setVideoUrl(data.video_url);
        setScriptText(data.script || "");
        setState("playing");
      } else if (data.job_id) {
        // Async — start polling
        setJobId(data.job_id);
        startPolling(data.job_id);
      } else {
        throw new Error("Unexpected response from server");
      }
    } catch (e) {
      setError(`Server se connect nahi ho paya: ${e.message}`);
      setState("idle");
    }
  };

  // ── Retry with new analogy ───────────────────────────────
  const handleRetry = async () => {
    const newAttempt = attempt + 1;
    setAttempt(newAttempt);
    setState("loading");
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/explain-again", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: jobData.chapter,
          attempt: newAttempt,
        }),
      });

      const data = await res.json();

      if (data.video_url) {
        setVideoUrl(data.video_url);
        setScriptText(data.script || "");
        setState("playing");
      } else if (data.job_id) {
        setJobId(data.job_id);
        startPolling(data.job_id);
      }
    } catch (e) {
      setError(`Retry failed: ${e.message}`);
      setState("idle");
    }
  };

  // ── Cancel / back ────────────────────────────────────────
  const handleCancel = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setState("idle");
  };

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  return (
    <>
      {/* Global styles */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          font-family: 'Outfit', sans-serif;
          background: #060c18;
          color: #e2e8f0;
          min-height: 100vh;
          overflow-x: hidden;
        }

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 2px; }

        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-8px); }
        }
        @keyframes pulse-dot {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
        @keyframes pulse-online {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(0.85); }
        }
        @keyframes ripple {
          0% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.6; }
          100% { transform: translate(-50%, -50%) scale(1.4); opacity: 0; }
        }
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes gradientShift {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }

        select option { background: #0f172a; color: #e2e8f0; }
      `}</style>

      {/* Background */}
      <ParticleField />
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: `
            radial-gradient(ellipse 60% 40% at 20% 20%, rgba(16,185,129,0.06) 0%, transparent 60%),
            radial-gradient(ellipse 50% 50% at 80% 80%, rgba(59,130,246,0.06) 0%, transparent 60%),
            radial-gradient(ellipse 70% 60% at 50% 50%, rgba(6,12,24,0.8) 0%, #060c18 100%)
          `,
          zIndex: 0,
        }}
      />

      {/* App Shell */}
      <div
        style={{
          position: "relative",
          zIndex: 1,
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Top Nav */}
        <nav
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "14px 24px",
            borderBottom: "1px solid #0f172a",
            backdropFilter: "blur(12px)",
            background: "rgba(6,12,24,0.7)",
            position: "sticky",
            top: 0,
            zIndex: 100,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 20 }}>⚗️</span>
            <span
              style={{
                fontWeight: 800,
                fontSize: 15,
                background: "linear-gradient(135deg, #10b981, #3b82f6)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                letterSpacing: "0.02em",
              }}
            >
              PriyaTeach
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "4px 12px",
                background: "rgba(16,185,129,0.1)",
                border: "1px solid rgba(16,185,129,0.2)",
                borderRadius: 20,
              }}
            >
              <div
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: "#10b981",
                  animation: "pulse-online 2s infinite",
                }}
              />
              <span style={{ color: "#10b981", fontSize: 11, fontWeight: 600 }}>ONLINE</span>
            </div>
            <span style={{ color: "#1e293b", fontSize: 18 }}>|</span>
            <span style={{ color: "#334155", fontSize: 12 }}>Class 10 Science</span>
          </div>
        </nav>

        {/* Error Banner */}
        {error && (
          <div
            style={{
              margin: "16px 16px 0",
              padding: "12px 16px",
              background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.3)",
              borderRadius: 10,
              color: "#fca5a5",
              fontSize: 13,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>⚠️ {error}</span>
            <button
              onClick={() => setError(null)}
              style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: 16 }}
            >
              ×
            </button>
          </div>
        )}

        {/* Main Content */}
        <main style={{ flex: 1, display: "flex", alignItems: "flex-start", justifyContent: "center", padding: "24px 16px 48px" }}>
          {state === "idle" && <IdleState onStart={handleStart} />}
          {state === "loading" && <LoadingState jobData={jobData} onCancel={handleCancel} />}
          {state === "live" && <LiveSessionState jobData={jobData} onCancel={handleCancel} />}
          {state === "playing" && (
            <PlayingState
              videoUrl={videoUrl}
              scriptText={scriptText}
              attempt={attempt}
              onRetry={handleRetry}
              jobData={jobData}
            />
          )}
        </main>

        {/* Footer */}
        <footer
          style={{
            textAlign: "center",
            padding: "16px",
            borderTop: "1px solid #0f172a",
            color: "#1e293b",
            fontSize: 11,
            letterSpacing: "0.08em",
          }}
        >
          PRIYATEACH • CLASS 10 NCERT • POWERED BY GROQ + SARVAM + D-ID
        </footer>
      </div>
    </>
  );
}

// ─── SHARED STYLES ────────────────────────────────────────────────────────────

const styles = {
  stateContainer: {
    width: "100%",
    maxWidth: 480,
    animation: "fadeSlideIn 0.4s ease",
  },
  heroTitle: {
    fontSize: 32,
    fontWeight: 900,
    background: "linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    letterSpacing: "-0.02em",
    lineHeight: 1.1,
  },
  card: {
    background: "linear-gradient(135deg, #0f172a, #0a1020)",
    border: "1px solid #1e293b",
    borderRadius: 16,
    padding: "24px",
    boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
  },
  label: {
    color: "#64748b",
    fontSize: 12,
    fontWeight: 600,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },
  select: {
    width: "100%",
    padding: "12px 40px 12px 14px",
    background: "#0f172a",
    border: "1px solid #1e293b",
    borderRadius: 10,
    color: "#e2e8f0",
    fontSize: 14,
    outline: "none",
    cursor: "pointer",
    appearance: "none",
    fontFamily: "'Outfit', sans-serif",
    transition: "border-color 0.2s",
  },
  input: {
    width: "100%",
    padding: "12px 40px 12px 14px",
    background: "#0f172a",
    border: "1px solid #1e293b",
    borderRadius: 10,
    color: "#e2e8f0",
    fontSize: 14,
    outline: "none",
    fontFamily: "'Outfit', sans-serif",
    transition: "all 0.2s",
  },
  ctaButton: {
    width: "100%",
    padding: "16px 24px",
    borderRadius: 12,
    border: "none",
    color: "#fff",
    fontWeight: 700,
    fontSize: 16,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    fontFamily: "'Outfit', sans-serif",
    letterSpacing: "0.02em",
    transition: "all 0.2s ease",
  },
};
