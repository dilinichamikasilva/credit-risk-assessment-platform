import { Link } from "react-router-dom";

const TOOLS = [
  {
    icon: "📉",
    title: "Default Risk",
    desc: "Estimate an applicant's probability of serious default within 2 years.",
    to: "/default-risk",
    ready: true,
  },
  {
    icon: "✅",
    title: "Loan Approval",
    desc: "Predict whether a loan application would be approved or rejected.",
    ready: false,
  },
  {
    icon: "💰",
    title: "Recommended Amount",
    desc: "Suggest a safe loan amount based on the applicant's profile.",
    ready: false,
  },
];

export default function Home() {
  return (
    <div>
      <div className="hero">
        <h1>
          Smarter lending decisions, <span className="accent">one click away</span>
        </h1>
        <p>
          Three ML-powered tools to assess default risk, loan approval, and
          recommended loan amounts &mdash; built on one shared feature pipeline.
        </p>
      </div>

      <div className="feature-grid">
        {TOOLS.map((tool) =>
          tool.ready ? (
            <Link key={tool.title} to={tool.to} className="feature-card active">
              <span className="feature-icon">{tool.icon}</span>
              <h3>{tool.title}</h3>
              <p>{tool.desc}</p>
              <span className="pill ready">Try it &rarr;</span>
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
