import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="navbar">
      <NavLink to="/" className="brand">
        <span className="brand-mark">🛡️</span>
        Credit Risk Platform
      </NavLink>

      <div className="nav-group">
        <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
          Home
        </NavLink>
        <NavLink
          to="/assessment"
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          New Assessment
        </NavLink>
        <NavLink
          to="/dashboard"
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          Dashboard
        </NavLink>
          <NavLink
              to="/history"
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
              History
          </NavLink>
      </div>

      <div className="nav-divider" aria-hidden="true" />

      <div className="nav-group advanced">
        <span className="nav-group-label">Advanced</span>
        <NavLink
          to="/default-risk"
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          Default Risk
        </NavLink>
        <NavLink
           to="/loan-approval"
           className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
           Loan Approval
        </NavLink>
        <NavLink
          to="/recommended-amount"
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          Recommended Amount
        </NavLink>
      </div>
    </nav>
  );
}
