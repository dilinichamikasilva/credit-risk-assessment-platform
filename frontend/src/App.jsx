import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import DefaultRiskPage from "./pages/DefaultRiskPage";
import RecommendedAmountPage from "./pages/RecommendedAmountPage";
import NewAssessmentPage from "./pages/NewAssessmentPage";
import DashboardPage from "./pages/DashboardPage";
import LoanApprovalPage from "./pages/LoanApprovalPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import ApplicationDetailPage from "./pages/ApplicationDetailPage.jsx";
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
          <Route path="/loan-approval" element={<LoanApprovalPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/applications/:id" element={<ApplicationDetailPage />}/>
          <Route path="/recommended-amount" element={<RecommendedAmountPage />} />
          {/* /loan-approval, /history, /applications/:id, /model-info
              land with their respective owners. */}
        </Routes>
      </main>
    </div>
  );
}
