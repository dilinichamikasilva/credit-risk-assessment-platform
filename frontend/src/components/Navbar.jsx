import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="navbar">
      <NavLink to="/" className="brand">
        <span className="brand-mark">🛡️</span>
        Credit Risk Platform
      </NavLink>
      <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
        Home
      </NavLink>
      <NavLink to="/default-risk" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
        Default Risk
      </NavLink>
      <span className="nav-link disabled">Loan Approval</span>
      <span className="nav-link disabled">Recommended Amount</span>
      {/* Loan Approval (Model B), Recommended Amount (Model C), and the
          Full Assessment dashboard become real links here as their owners land them. */}
    </nav>
  );
}
