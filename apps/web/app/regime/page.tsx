"use client";

import { FormEvent, useState } from "react";

type Match = {
  session_date: string;
  distance: number;
  outcome_summary: {
    analogue_bull_rate?: number;
    return_30m_mean?: number;
    return_60m_mean?: number;
    open_close_mean?: number;
    onh_first_rate?: number;
    onl_first_rate?: number;
    trend_day_rate?: number;
    sample_size?: number;
    return_30m_min?: number;
    return_30m_max?: number;
    return_60m_min?: number;
    return_60m_max?: number;
    open_close_min?: number;
    open_close_max?: number;
  };
};

type Result = { session_date: string; matches: Match[] };

const featureNames = [
  ["overnight_return", "Overnight return"],
  ["overnight_range", "Overnight range"],
  ["gap_pct", "Gap percent"],
  ["atr_14", "ATR 14"],
  ["prior_day_high_distance", "Distance from PDH"],
  ["prior_day_low_distance", "Distance from PDL"],
] as const;

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

function percent(value?: number) {
  return value == null ? "—" : `${value >= 0 ? "+" : ""}${(value * 100).toFixed(2)}%`;
}

function OutcomeChart({ summary }: { summary: Match["outcome_summary"] }) {
  const measures = [
    ["30m", summary.return_30m_min, summary.return_30m_max, summary.return_30m_mean],
    ["60m", summary.return_60m_min, summary.return_60m_max, summary.return_60m_mean],
    ["Open → close", summary.open_close_min, summary.open_close_max, summary.open_close_mean],
  ] as const;
  return <div className="outcome-chart" aria-label="Historical analogue possible move ranges">
    {measures.map(([label, min, max, average]) => {
      const low = min ?? average ?? 0;
      const high = max ?? average ?? 0;
      const scale = Math.max(Math.abs(low), Math.abs(high), 0.0001);
      return <div className="move-row" key={label}><div className="move-label"><span>{label}</span><strong>{percent(average)}</strong></div><div className="move-track"><span className="move-negative" style={{ width: `${Math.min(50, Math.abs(Math.min(0, low)) / scale * 50)}%` }} /><span className="move-positive" style={{ width: `${Math.min(50, Math.max(0, high) / scale * 50)}%` }} /></div><div className="move-range">{percent(min)} to {percent(max)}</div></div>;
    })}
  </div>;
}

export default function RegimePage() {
  const [sessionDate, setSessionDate] = useState("2026-09-03");
  const [predictionTime, setPredictionTime] = useState("2026-09-03T09:30");
  const [features, setFeatures] = useState<Record<string, string>>(
    Object.fromEntries(featureNames.map(([name]) => [name, "0"])),
  );
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [featureStatus, setFeatureStatus] = useState<string | null>(null);

  async function loadStoredFeatures() {
    setError(null);
    setFeatureStatus(null);
    try {
      const response = await fetch(`${apiBase}/market/nq/analogue-features?session_date=${sessionDate}`);
      if (!response.ok) throw new Error(`Could not load session features (${response.status})`);
      const payload = (await response.json()) as { features: Record<string, number> };
      setFeatures(Object.fromEntries(featureNames.map(([name]) => [name, String(payload.features[name] ?? 0)])));
      setFeatureStatus("Stored session features loaded");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load session features");
    }
  }

  async function findAnalogues(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch(`${apiBase}/regimes/similar`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          sessionDate,
          features: Object.fromEntries(Object.entries(features).map(([key, value]) => [key, Number(value)])),
          predictionTime: new Date(predictionTime).toISOString(),
          topK: 20,
          metric: "euclidean",
        }),
      });
      if (!response.ok) throw new Error(`Analogue search failed (${response.status})`);
      setResult((await response.json()) as Result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Analogue search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">NQMATE / RESEARCH</p>
          <h1>Historical regime finder</h1>
          <p className="subtitle">Compare today&apos;s pre-open structure with point-in-time historical sessions.</p>
        </div>
        <a className="quiet-link" href="/">Back to overview</a>
      </header>

      <section className="query-panel" aria-labelledby="query-title">
        <div className="section-heading"><div><p className="eyebrow">QUERY</p><h2 id="query-title">Session context</h2></div><span className="badge">Euclidean / top 20</span></div>
        <form onSubmit={findAnalogues}>
          <div className="form-grid">
            <label>Session date<input type="date" value={sessionDate} onChange={(event) => setSessionDate(event.target.value)} required /></label>
            <label>Prediction time<input type="datetime-local" value={predictionTime} onChange={(event) => setPredictionTime(event.target.value)} required /></label>
            {featureNames.map(([name, label]) => (
              <label key={name}>{label}<input type="number" step="any" value={features[name]} onChange={(event) => setFeatures({ ...features, [name]: event.target.value })} required /></label>
            ))}
          </div>
          <div className="form-actions"><button className="secondary-button" type="button" onClick={loadStoredFeatures}>Load stored features</button><button className="primary-button" type="submit" disabled={loading}>{loading ? "Finding sessions…" : "Find similar sessions"}</button>{featureStatus && <span className="success" role="status">{featureStatus}</span>}</div>
        </form>
      </section>

      {error && <p className="state error" role="alert">{error}. Check that the FastAPI server is running.</p>}
      {!result && !error && <div className="state" role="status"><strong>Ready to compare.</strong><span>Results use only historical rows available by the prediction time.</span></div>}
      {result && (
        <section aria-labelledby="results-title">
          <div className="section-heading results-heading"><div><p className="eyebrow">MATCHES / {result.matches.length}</p><h2 id="results-title">Closest historical sessions</h2></div><span className="result-date">{result.session_date}</span></div>
          {result.matches.length === 0 ? <div className="state"><strong>No eligible sessions found.</strong><span>Try an earlier prediction time or confirm historical vectors are populated.</span></div> : (
            <><div className="insight-grid"><div className="insight-panel"><p className="eyebrow">POSSIBLE MOVES</p><h3>Historical return range</h3><OutcomeChart summary={result.matches[0].outcome_summary} /><p className="footnote">Range shows the lowest to highest observed outcome among the selected analogues. It is historical evidence, not a forecast.</p></div><div className="insight-panel"><p className="eyebrow">READ-THROUGH</p><h3>What the matches suggest</h3><div className="read-through"><div><span>Up at 60m</span><strong>{result.matches[0].outcome_summary.analogue_bull_rate == null ? "—" : `${(result.matches[0].outcome_summary.analogue_bull_rate * 100).toFixed(0)}%`}</strong></div><div><span>ONH first</span><strong>{result.matches[0].outcome_summary.onh_first_rate == null ? "—" : `${(result.matches[0].outcome_summary.onh_first_rate * 100).toFixed(0)}%`}</strong></div><div><span>ONL first</span><strong>{result.matches[0].outcome_summary.onl_first_rate == null ? "—" : `${(result.matches[0].outcome_summary.onl_first_rate * 100).toFixed(0)}%`}</strong></div><div><span>Trend day</span><strong>{result.matches[0].outcome_summary.trend_day_rate == null ? "—" : `${(result.matches[0].outcome_summary.trend_day_rate * 100).toFixed(0)}%`}</strong></div></div><p className="footnote">Strategy-specific performance will appear after the Phase 7 strategy memory system is implemented.</p></div></div><div className="table-wrap"><table><caption className="sr-only">Historical analogue matches and aggregate outcomes</caption><thead><tr><th scope="col">Rank</th><th scope="col">Session</th><th scope="col">Distance</th><th scope="col">Up at 60m</th><th scope="col">30m return</th><th scope="col">60m return</th><th scope="col">Open → close</th><th scope="col">Trend day</th></tr></thead><tbody>
              {result.matches.map((match, index) => <tr key={match.session_date}><td className="muted">{String(index + 1).padStart(2, "0")}</td><td className="session-cell">{match.session_date}</td><td>{match.distance.toFixed(4)}</td><td>{match.outcome_summary.analogue_bull_rate == null ? "—" : `${(match.outcome_summary.analogue_bull_rate * 100).toFixed(0)}%`}</td><td>{percent(match.outcome_summary.return_30m_mean)}</td><td>{percent(match.outcome_summary.return_60m_mean)}</td><td>{percent(match.outcome_summary.open_close_mean)}</td><td>{match.outcome_summary.trend_day_rate == null ? "—" : `${(match.outcome_summary.trend_day_rate * 100).toFixed(0)}%`}</td></tr>)}
            </tbody></table></div></>
          )}
        </section>
      )}
    </main>
  );
}
