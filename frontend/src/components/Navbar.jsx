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
        <span className="nav-link disabled">History</span>
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
        <span className="nav-link disabled">Loan Approval</span>
        <NavLink
          to="/recommended-amount"
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          Recommended Amount
        </NavLink>
        <NavLink
          to="/model-info"
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          Model Info
        </NavLink>
      </div>
    </nav>
  );
}
