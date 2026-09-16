import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import DefaultRiskPage from "./pages/DefaultRiskPage";
import "./App.css";

export default function App() {
  return (
    <div>
      <Navbar />
      <main style={{ padding: "0 1.5rem 3rem" }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/default-risk" element={<DefaultRiskPage />} />
          {/* /loan-approval, /recommended-amount, /assessment routes are
              added here by their respective owners. */}
        </Routes>
      </main>
    </div>
  );
}
