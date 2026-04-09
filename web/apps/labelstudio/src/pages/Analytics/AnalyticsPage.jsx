import { useCallback, useContext, useEffect, useState } from "react";
import { Button } from "@humansignal/ui";
import { useUpdatePageTitle } from "@humansignal/core";
import { ApiContext } from "../../providers/ApiProvider";
import { cn } from "../../utils/bem";

const rootClass = cn("analytics-page");

const formatTime = (seconds) => {
  if (!seconds && seconds !== 0) return "-";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
};

export const AnalyticsPage = () => {
  const api = useContext(ApiContext);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  useUpdatePageTitle("Analytics");

  const fetchData = useCallback(async () => {
    setLoading(true);
    const params = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;

    try {
      const resp = await fetch(
        `/api/analytics/dashboard/?${new URLSearchParams(params)}`,
        {
          headers: {
            Authorization: `Token ${window.APP_SETTINGS?.token || ""}`,
          },
        },
      );
      if (resp.ok) {
        setData(await resp.json());
      }
    } catch (e) {
      console.error("Failed to fetch analytics", e);
    }
    setLoading(false);
  }, [dateFrom, dateTo]);

  useEffect(() => {
    fetchData();
  }, []);

  const exportCSV = () => {
    const params = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    window.open(
      `/api/analytics/export/?${new URLSearchParams(params)}`,
      "_blank",
    );
  };

  const summary = data?.summary || {};
  const perUser = data?.per_user || [];
  const perDay = data?.per_day || [];

  const cardStyle = {
    background: "#fff",
    borderRadius: 8,
    padding: "20px 24px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
    minWidth: 180,
    textAlign: "center",
  };
  const cardValue = {
    fontSize: 28,
    fontWeight: 700,
    color: "#1a1a1a",
    margin: "8px 0 4px",
  };
  const cardLabel = {
    fontSize: 13,
    color: "#666",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  };

  return (
    <div style={{ padding: "24px 32px", maxWidth: 1100, margin: "0 auto" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <h1 style={{ margin: 0, fontSize: 24 }}>Productivity Dashboard</h1>
        <Button onClick={exportCSV} size="small">
          Export CSV
        </Button>
      </div>

      <div
        style={{
          display: "flex",
          gap: 12,
          marginBottom: 24,
          alignItems: "center",
        }}
      >
        <label>
          From:{" "}
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            style={{ padding: "4px 8px" }}
          />
        </label>
        <label>
          To:{" "}
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            style={{ padding: "4px 8px" }}
          />
        </label>
        <Button onClick={fetchData} size="small">
          Filter
        </Button>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          <div
            style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 32 }}
          >
            <div style={cardStyle}>
              <div style={cardLabel}>Total Transcribed</div>
              <div style={cardValue}>{summary.total_annotations ?? 0}</div>
            </div>
            <div style={cardStyle}>
              <div style={cardLabel}>Avg Time / Chunk</div>
              <div style={cardValue}>
                {formatTime(summary.avg_lead_time)}
              </div>
            </div>
            <div style={cardStyle}>
              <div style={cardLabel}>Accepted</div>
              <div style={{ ...cardValue, color: "#22c55e" }}>
                {summary.total_accepted ?? 0}
              </div>
            </div>
            <div style={cardStyle}>
              <div style={cardLabel}>Rejected</div>
              <div style={{ ...cardValue, color: "#ef4444" }}>
                {summary.total_rejected ?? 0}
              </div>
            </div>
            <div style={cardStyle}>
              <div style={cardLabel}>Pending Review</div>
              <div style={{ ...cardValue, color: "#f59e0b" }}>
                {summary.total_submitted ?? 0}
              </div>
            </div>
          </div>

          <h2 style={{ fontSize: 18, marginBottom: 12 }}>Per-User Breakdown</h2>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              marginBottom: 32,
              background: "#fff",
              borderRadius: 8,
              overflow: "hidden",
              boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
            }}
          >
            <thead>
              <tr
                style={{
                  background: "#f5f5f5",
                  textAlign: "left",
                  fontSize: 13,
                  textTransform: "uppercase",
                  color: "#666",
                }}
              >
                <th style={{ padding: "10px 16px" }}>Email</th>
                <th style={{ padding: "10px 16px" }}>Name</th>
                <th style={{ padding: "10px 16px" }}>Total</th>
                <th style={{ padding: "10px 16px" }}>Avg Time</th>
                <th style={{ padding: "10px 16px" }}>Accepted</th>
                <th style={{ padding: "10px 16px" }}>Rejected</th>
              </tr>
            </thead>
            <tbody>
              {perUser.map((row, i) => (
                <tr
                  key={i}
                  style={{
                    borderTop: "1px solid #eee",
                  }}
                >
                  <td style={{ padding: "10px 16px" }}>
                    {row.completed_by__email}
                  </td>
                  <td style={{ padding: "10px 16px" }}>
                    {`${row.completed_by__first_name || ""} ${row.completed_by__last_name || ""}`.trim()}
                  </td>
                  <td style={{ padding: "10px 16px" }}>{row.count}</td>
                  <td style={{ padding: "10px 16px" }}>
                    {formatTime(row.avg_time)}
                  </td>
                  <td style={{ padding: "10px 16px" }}>{row.accepted}</td>
                  <td style={{ padding: "10px 16px" }}>{row.rejected}</td>
                </tr>
              ))}
              {perUser.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    style={{ padding: "20px 16px", textAlign: "center", color: "#999" }}
                  >
                    No data for the selected period.
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {perDay.length > 0 && (
            <>
              <h2 style={{ fontSize: 18, marginBottom: 12 }}>
                Daily Activity
              </h2>
              <div
                style={{
                  display: "flex",
                  gap: 2,
                  alignItems: "flex-end",
                  height: 120,
                  background: "#fff",
                  borderRadius: 8,
                  padding: "16px",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
                  overflow: "auto",
                }}
              >
                {perDay.map((d, i) => {
                  const max = Math.max(...perDay.map((x) => x.count));
                  const height = max > 0 ? (d.count / max) * 88 : 0;
                  return (
                    <div
                      key={i}
                      title={`${d.day}: ${d.count} annotations`}
                      style={{
                        flex: "1 0 8px",
                        maxWidth: 24,
                        height: Math.max(height, 2),
                        background: "#3b82f6",
                        borderRadius: "2px 2px 0 0",
                      }}
                    />
                  );
                })}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

AnalyticsPage.title = "Analytics";
AnalyticsPage.path = "/analytics";
AnalyticsPage.exact = true;
