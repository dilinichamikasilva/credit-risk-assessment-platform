import { NavLink } from "react-router-dom";

const PRIMARY_LINKS = [
  { to: "/", label: "Home", end: true },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/history", label: "History" },
];

const ADVANCED_LINKS = [
  { to: "/default-risk", label: "Default Risk" },
  { to: "/loan-approval", label: "Loan Approval" },
  { to: "/recommended-amount", label: "Recommended Amount" },
  { to: "/model-info", label: "Model Info" },
];

function tabClass({ isActive }) {
  return `nav-tab${isActive ? " active" : ""}`;
}

function ctaClass({ isActive }) {
  return `nav-cta${isActive ? " active" : ""}`;
}

function segmentClass({ isActive }) {
  return `nav-segment${isActive ? " active" : ""}`;
}

export default function Navbar() {
  return (
    <header className="app-header">
      <div className="navbar">
        <NavLink to="/" className="brand">
          <span className="brand-mark" aria-hidden="true">🛡️</span>
          <span className="brand-text">Credit Risk Platform</span>
        </NavLink>

        <nav className="primary-nav" aria-label="Primary">
          {PRIMARY_LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end} className={tabClass}>
              {link.label}
            </NavLink>
          ))}
          <NavLink to="/assessment" className={ctaClass}>
            New Assessment
          </NavLink>
        </nav>
      </div>

      <div className="subnav">
        <div className="subnav-inner">
          <span className="subnav-label">Advanced</span>
          <nav className="nav-segments" aria-label="Advanced assessment tools">
            {ADVANCED_LINKS.map((link) => (
              <NavLink key={link.to} to={link.to} className={segmentClass}>
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
