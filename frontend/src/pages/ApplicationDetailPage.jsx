import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {formatApiError, formatCurrency, getApplication,} from "../api/client";

/** APPLICATION DETAIL PAGE */
export default function ApplicationDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();

    const [application, setApplication] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function loadApplication() {
            setLoading(true);
            setError(null);

            try {
                const data = await getApplication(id);
                setApplication(data);
            } catch (err) {
                setError(formatApiError(err));
            } finally {
                setLoading(false);
            }
        }

        loadApplication();
    }, [id]);

    if (loading) {
        return (
            <div className="center-pad">
                <span className="spinner dark" />
                Loading application...
            </div>
        );
    }

    if (error) {
        return (
            <div className="result-wrap">
                <div className="result-card error">
                    <div className="result-details">
                        <h3>Could not load application</h3>
                        <p style={{ color: "#991b1b", margin: 0 }}>
                            {error}
                        </p>

                        <button
                            type="button"
                            className="secondary-btn"
                            onClick={() => navigate("/history")}
                            style={{ marginTop: "1rem" }}
                        >
                            Back to History
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (!application) {
        return (
            <div className="history-state">
                <h3>Application not found</h3>
                <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => navigate("/history")}
                >
                    Back to History
                </button>
            </div>
        );
    }

    return (
        <div>
            <div className="page-header">
                <p className="eyebrow">Application #{application.id}</p>

                <h1>
                    {application.applicant_name || "Applicant"}
                </h1>

                <p>
                    Complete application and assessment details.
                </p>
            </div>

            <div className="form-card">

                {/** BASIC APPLICATION DETAILS */}

                <div className="form-section-title">
                    Application Details
                </div>

                <div className="form-grid">
                    <div className="field">
                        <label>Applicant Name</label>
                        <input
                            value={application.applicant_name || ""}
                            readOnly
                        />
                    </div>

                    <div className="field">
                        <label>Status</label>
                        <input
                            value={application.status || "submitted"}
                            readOnly
                        />
                    </div>

                    <div className="field">
                        <label>CIBIL Score</label>
                        <input
                            value={application.cibil_score ?? "—"}
                            readOnly
                        />
                    </div>

                    <div className="field">
                        <label>Loan Amount</label>
                        <input
                            value={formatCurrency(application.loan_amount)}
                            readOnly
                        />
                    </div>

                    <div className="field">
                        <label>Created</label>
                        <input
                            value={
                                application.created_at
                                    ? new Date(
                                        application.created_at
                                    ).toLocaleString()
                                    : "—"
                            }
                            readOnly
                        />
                    </div>
                </div>

                {/** ASSESSMENT INFORMATION */}

                <div
                    className="form-section-title"
                    style={{ marginTop: "2rem" }}
                >
                    Assessment Information
                </div>

                <div className="form-grid">
                    <div className="field">
                        <label>Assessment Count</label>
                        <input
                            value={
                                application.assessment_count ??
                                application.assessments_count ??
                                "—"
                            }
                            readOnly
                        />
                    </div>

                    <div className="field">
                        <label>Loan Amount</label>
                        <input
                            value={formatCurrency(application.loan_amount)}
                            readOnly
                        />
                    </div>
                </div>

                {/** BACK BUTTON */}

                <div
                    className="form-grid"
                    style={{ marginTop: "1.6rem" }}
                >
                    <button
                        type="button"
                        className="secondary-btn"
                        onClick={() => navigate("/history")}
                    >
                        ← Back to History
                    </button>
                </div>
            </div>
        </div>
    );
}