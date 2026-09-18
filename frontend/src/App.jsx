import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import DefaultRiskPage from "./pages/DefaultRiskPage";
import RecommendedAmountPage from "./pages/RecommendedAmountPage";
import NewAssessmentPage from "./pages/NewAssessmentPage";
import ApplicationDetailPage from "./pages/ApplicationDetailPage";
import ModelInfoPage from "./pages/ModelInfoPage";
import DashboardPage from "./pages/DashboardPage";
import "./App.css";

export default function App() {
  return (
    <div>
      <Navbar />
      <main style={{ padding: "0 1.5rem 3rem" }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/assessment" element={<NewAssessmentPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/default-risk" element={<DefaultRiskPage />} />
          <Route path="/recommended-amount" element={<RecommendedAmountPage />} />
          <Route path="/applications/:id" element={<ApplicationDetailPage />} />
          <Route path="/model-info" element={<ModelInfoPage />} />
          {/* /loan-approval, /history
              land with their respective owners. */}
        </Routes>
      </main>
    </div>
  );
}
