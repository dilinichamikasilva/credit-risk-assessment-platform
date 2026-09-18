import { Link } from "react-router-dom";

const PRIMARY = [
  {
    icon: "🧾",
    title: "New Assessment",
    desc: "Fill in one form to get default risk, loan approval, and a recommended amount — saved as one report.",
    to: "/assessment",
    ready: true,
    cta: "Start assessment →",
  },
  {
    icon: "📊",
    title: "Dashboard",
    desc: "See how many applications you've assessed and how the risk breaks down.",
    to: "/dashboard",
    ready: true,
    cta: "Open dashboard →",
  },
];

const ADVANCED = [
  {
    icon: "📉",
    title: "Default Risk",
    desc: "Check the chance an applicant fails to repay within the next 2 years.",
    to: "/default-risk",
    ready: true,
  },
  {
    icon: "✅",
    title: "Loan Approval",
    desc: "Check whether a loan application would likely be approved or rejected.",
    to: "/loan-approval",
    ready: true,
  },
  {
    icon: "💰",
    title: "Recommended Amount",
    desc: "Suggest a safe loan amount, automatically capped at the requested amount.",
    to: "/recommended-amount",
    ready: true,
  },
];

export default function Home() {
  return (
    <div>
      <div className="hero">
        <h1>
          See the full risk picture, <span className="accent">in one view</span>
        </h1>
        <p>
          Enter an applicant's details once and instantly see their default risk,
          whether their loan would be approved, and how much they could safely borrow.
        </p>
        <div className="hero-actions">
          <Link to="/assessment" className="hero-cta">
            New assessment
          </Link>
          <Link to="/dashboard" className="hero-cta ghost">
            View dashboard
          </Link>
        </div>
      </div>

      <div className="feature-grid">
        {PRIMARY.map((tool) => (
          <Link key={tool.title} to={tool.to} className="feature-card active featured">
            <span className="feature-icon">{tool.icon}</span>
            <h3>{tool.title}</h3>
            <p>{tool.desc}</p>
            <span className="pill ready">{tool.cta}</span>
          </Link>
        ))}
      </div>

      <h2 className="section-heading">Advanced tools</h2>
      <div className="feature-grid">
        {ADVANCED.map((tool) =>
          tool.ready ? (
            <Link key={tool.title} to={tool.to} className="feature-card active">
              <span className="feature-icon">{tool.icon}</span>
              <h3>{tool.title}</h3>
              <p>{tool.desc}</p>
              <span className="pill ready">Try it →</span>
            </Link>
          ) : (
            <div key={tool.title} className="feature-card disabled">
              <span className="feature-icon">{tool.icon}</span>
              <h3>{tool.title}</h3>
              <p>{tool.desc}</p>
              <span className="pill soon">Coming soon</span>
            </div>
          )
        )}
      </div>
    </div>
  );
}
