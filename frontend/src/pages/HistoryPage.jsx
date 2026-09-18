import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { formatApiError, formatCurrency, getApplications } from "../api/client";

/** APPLICATION HISTORY */

export default function HistoryPage() {
  const [applications, setApplications] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function loadHistory() {
    setLoading(true);
    setError(null);
    try {
      const data = await getApplications({ limit: 100, offset: 0 });
      // The API may return a plain array or {applications: [...]}.
      setApplications(Array.isArray(data) ? data : (data.applications || []));
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return applications;

    return applications.filter((application) =>
      [
        application.applicant_name,
        application.status,
        application.cibil_score,
        application.id,
      ]
        .filter((value) => value != null)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [applications, search]);

  return (
    <div>
      <div className="page-header">
        <p className="eyebrow">Application records</p>
        <h1>Assessment History</h1>
        <p>
          Review previously saved applicants and open an individual record
          for the complete assessment timeline.
        </p>
      </div>

      <div className="history-toolbar">
        <div className="field history-search">
          <label htmlFor="history-search">Search applications</label>
          <input
            id="history-search"
            type="search"
            value={search}
            placeholder="Search by name, ID, CIBIL, or status"
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <button type="button" className="secondary-btn" onClick={loadHistory} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="result-wrap">
          <div className="result-card error">
            <div className="result-details">
              <h3>Could not load history</h3>
              <p style={{ color: "#991b1b", margin: 0 }}>{error}</p>
            </div>
          </div>
        </div>
      )}

      {!error && (
        <div className="history-card">
          {loading ? (
            <div className="center-pad history-state">
              <span className="spinner dark" />
              Loading saved applications...
            </div>
          ) : filtered.length === 0 ? (
            <div className="history-state">
              <h3>No applications found</h3>
              <p className="muted">
                Run a full assessment or a saved model assessment to create an
                application record.
              </p>
            </div>
          ) : (
            <div className="history-table-wrap">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Applicant</th>
                    <th>CIBIL</th>
                    <th>Loan amount</th>
                    <th>Status</th>
                    <th>Assessments</th>
                    <th>Created</th>
                    <th aria-label="Actions" />
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((application) => (
                    <tr key={application.id}>
                      <td>
                        <strong>{application.applicant_name}</strong>
                        <span className="table-subtext">#{application.id}</span>
                      </td>
                      <td>{application.cibil_score ?? "—"}</td>
                      <td>{formatCurrency(application.loan_amount)}</td>
                      <td>
                        <span className="badge medium">
                          {application.status || "submitted"}
                        </span>
                      </td>
                      <td>{application.assessments?.length ?? 0}</td>
                      <td>
                        {application.created_at
                          ? new Date(application.created_at).toLocaleDateString()
                          : "—"}
                      </td>
                      <td>
                        <Link
                            className="table-action"
                            to={`/applications/${application.id}`}
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
