"use client";

import { useEffect, useMemo, useState } from "react";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
type Bar = { timestamp: string; open: number; high: number; low: number; close: number };
type DashboardData = {
  session: { session_date: string; nq_open: number; nq_high: number; nq_low: number; nq_close: number; overnight_return: number | null; overnight_range: number; atr_14: number | null; contract: { raw_contract_symbol: string } };
  levels: { pdh: number | null; pdl: number | null; onh: number; onl: number; overnight_midpoint: number };
  bars: Bar[];
  bars15: Bar[];
  bars4h: Bar[];
  bars1d: Bar[];
  vwap: number | null;
  bias: { direction: string; confidence: number; recommendation: string; catalyst_risk: string | null; evidence?: string[] } | null;
  news: Array<{ headline?: string; title?: string; source?: string; published_at?: string; nq_relevance?: number }>;
  pb: { status: string; direction: string | null; inversionTimeframe: string | null; entry: number | null; stop: number | null; targets: number[]; riskRewards: number[]; missing: string[]; liquidityEvent?: { sweptLevel: string; price: number; sweptAt: string } | null; inversions?: Array<{ timeframe: string; direction: string; lower: number; upper: number; confirmedAt: string }> } | null;
};

function number(value: number | null | undefined) { return value == null ? "—" : value.toLocaleString(undefined, { maximumFractionDigits: 2 }); }
function percent(value: number | null | undefined) { return value == null ? "—" : `${value >= 0 ? "+" : ""}${(value * 100).toFixed(2)}%`; }
function move(bars: Bar[]) { const first = bars[0]?.close; const last = bars.at(-1)?.close; return first && last ? last / first - 1 : null; }
function followingDate(date: string) { const next = new Date(`${date}T12:00:00Z`); next.setUTCDate(next.getUTCDate() + 1); return next.toISOString().slice(0, 10); }

function CandleChart({ bars, levels, vwap }: { bars: Bar[]; levels: DashboardData["levels"]; vwap: number | null }) {
  const sample = bars.filter((_, index) => index % Math.max(1, Math.floor(bars.length / 80)) === 0).slice(-80);
  const values = sample.flatMap((bar) => [bar.high, bar.low]);
  const high = Math.max(...values, levels.pdh ?? -Infinity, levels.onh);
  const low = Math.min(...values, levels.pdl ?? Infinity, levels.onl);
  const y = (value: number) => 210 - ((value - low) / Math.max(high - low, 1)) * 190;
  const x = (index: number) => 10 + (index / Math.max(sample.length - 1, 1)) * 780;
  return <div className="candle-chart" role="img" aria-label="Five minute NQ candles with previous day, overnight, and VWAP levels"><svg viewBox="0 0 800 230" preserveAspectRatio="none"><line className="chart-axis" x1="0" y1="215" x2="800" y2="215" />{sample.map((bar, index) => { const rising = bar.close >= bar.open; const cx = x(index); return <g key={bar.timestamp}><line className={rising ? "candle-up" : "candle-down"} x1={cx} x2={cx} y1={y(bar.high)} y2={y(bar.low)} /><rect className={rising ? "candle-up" : "candle-down"} x={cx - 2.5} y={Math.min(y(bar.open), y(bar.close))} width="5" height={Math.max(2, Math.abs(y(bar.open) - y(bar.close)))} /></g>; })}{levels.pdh != null && <line className="level-pdh" x1="0" x2="800" y1={y(levels.pdh)} y2={y(levels.pdh)} />}{levels.pdl != null && <line className="level-pdl" x1="0" x2="800" y1={y(levels.pdl)} y2={y(levels.pdl)} />}{<line className="level-onh" x1="0" x2="800" y1={y(levels.onh)} y2={y(levels.onh)} />}{<line className="level-onl" x1="0" x2="800" y1={y(levels.onl)} y2={y(levels.onl)} />}{<line className="level-midpoint" x1="0" x2="800" y1={y(levels.overnight_midpoint)} y2={y(levels.overnight_midpoint)} />}{vwap != null && <line className="level-vwap" x1="0" x2="800" y1={y(vwap)} y2={y(vwap)} />}</svg><div className="chart-legend"><span><i className="legend-up" /> Up</span><span><i className="legend-down" /> Down</span><span>PDH / PDL</span><span>ONH / ONL</span><span>VWAP</span></div></div>;
}

export default function DashboardPage() {
  const [selectedDate, setSelectedDate] = useState("2026-09-02");
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    async function load() {
      const endDate = followingDate(selectedDate);
      setData(null);
      setError(null);
      try {
        const [session, levels, bars, bars15, bars4h, bars1d, features, bias, news, strategies] = await Promise.all([
          fetch(`${apiBase}/market/nq/session/${selectedDate}`).then((r) => r.ok ? r.json() : null),
          fetch(`${apiBase}/market/nq/levels?session_date=${selectedDate}`).then((r) => r.ok ? r.json() : null),
          fetch(`${apiBase}/market/nq/bars?start=${selectedDate}&end=${endDate}&timeframe=5m`).then((r) => r.ok ? r.json() : null),
          fetch(`${apiBase}/market/nq/bars?start=${selectedDate}&end=${endDate}&timeframe=15m`).then((r) => r.ok ? r.json() : null),
          fetch(`${apiBase}/market/nq/bars?start=2026-01-01&end=${endDate}&timeframe=4h`).then((r) => r.ok ? r.json() : null),
          fetch(`${apiBase}/market/nq/bars?start=2026-01-01&end=${endDate}&timeframe=1d`).then((r) => r.ok ? r.json() : null),
          fetch(`${apiBase}/market/nq/features?session_date=${selectedDate}`).then((r) => r.ok ? r.json() : null),
          fetch(`${apiBase}/bias/current`).then((r) => r.ok ? r.json() : null),
          fetch(`${apiBase}/news/high-impact?limit=5`).then((r) => r.ok ? r.json() : null),
          fetch(`${apiBase}/strategies?active=true`).then((r) => r.ok ? r.json() : null),
        ]);
        if (!session || !levels || !bars) throw new Error("Required market data is unavailable");
        const activeStrategy = strategies?.strategies?.[0];
        const pb = activeStrategy ? await fetch(`${apiBase}/strategies/${activeStrategy.id}/assess-session?session_date=${selectedDate}`).then((r) => r.ok ? r.json() : null) : null;
        setData({ session, levels, bars: bars.bars ?? [], bars15: bars15?.bars ?? [], bars4h: bars4h?.bars ?? [], bars1d: bars1d?.bars ?? [], vwap: features?.features?.vwap ?? null, bias, news: news?.events ?? [], pb });
      } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not load dashboard"); }
    }
    void load();
  }, [selectedDate]);
  const latest = useMemo(() => data?.bars.at(-1), [data]);
  return <main className="shell"><header className="page-header"><div><p className="eyebrow">NQMATE / MARKET DESK</p><h1>NQ dashboard</h1><p className="subtitle">Completed-session market context, deterministic levels, and evidence-backed bias.</p></div><div className="header-links"><label className="date-picker">Completed session<input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} /></label><span className="badge">Historical / {selectedDate}</span><a className="quiet-link" href="/">Back to overview</a></div></header>
    {error && <div className="state error" role="alert"><strong>Dashboard data unavailable.</strong><span>{error}. Check that FastAPI is running and the session is populated.</span></div>}
    {!data && !error && <div className="state" role="status" aria-busy="true"><strong>Loading market context…</strong><span>Reading completed-session candles and evidence.</span></div>}
    {data && <>
      <section className="dashboard-top"><div className="bias-card"><p className="eyebrow">DIRECTIONAL BIAS</p><div className="bias-direction">{data.bias?.direction ?? "NO PREDICTION"}</div><p>{data.bias ? `${number(data.bias.confidence * 100)}% confidence · ${data.bias.recommendation}` : "Generate a bias prediction to populate this panel."}</p><span className="badge">No automated execution</span></div><div className="metric-grid dashboard-metrics"><div><span>Last close</span><strong>{number(latest?.close ?? data.session.nq_close)}</strong></div><div><span>Session range</span><strong>{number(data.session.nq_high - data.session.nq_low)}</strong></div><div><span>Overnight return</span><strong>{percent(data.session.overnight_return)}</strong></div><div><span>ATR 14</span><strong>{number(data.session.atr_14)}</strong></div></div></section>
      <section className="query-panel timeframe-panel" aria-labelledby="timeframe-title"><div className="section-heading"><div><p className="eyebrow">MULTI-TIMEFRAME CONTEXT</p><h2 id="timeframe-title">Momentum read-through</h2></div><span className="badge">Stored candles</span></div><div className="timeframe-grid"><div><span>15m session momentum</span><strong>{percent(move(data.bars15))}</strong><small>{data.bars15.length} bars · entry context</small></div><div><span>4H recent momentum</span><strong>{percent(move(data.bars4h.slice(-10)))}</strong><small>{data.bars4h.length} bars · higher-timeframe context</small></div><div><span>Daily recent momentum</span><strong>{percent(move(data.bars1d.slice(-10)))}</strong><small>{data.bars1d.length} bars · directional context</small></div></div></section>
      <section className="query-panel pb-panel" aria-labelledby="pb-title"><div className="section-heading"><div><p className="eyebrow">PB BLAKE / ICT EVALUATION</p><h2 id="pb-title">Historical setup assessment</h2></div><span className="badge">Deterministic · no execution</span></div>{data.pb ? <><div className="pb-summary"><strong>{data.pb.status.replace("_", " ")}</strong><span>{data.pb.direction ?? "No direction"}{data.pb.inversionTimeframe ? ` · ${data.pb.inversionTimeframe} inversion` : ""}</span></div><div className="metric-grid pb-metrics"><div><span>Entry</span><strong>{number(data.pb.entry)}</strong></div><div><span>Stop</span><strong>{number(data.pb.stop)}</strong></div><div><span>Targets</span><strong>{data.pb.targets.length ? data.pb.targets.map(number).join(" / ") : "—"}</strong></div><div><span>R:R</span><strong>{data.pb.riskRewards.length ? data.pb.riskRewards.map((value) => `${value.toFixed(2)}R`).join(" / ") : "—"}</strong></div></div><p className="footnote">Liquidity: {data.pb.liquidityEvent ? `${data.pb.liquidityEvent.sweptLevel} at ${number(data.pb.liquidityEvent.price)}` : "none detected"}. Inversions: {data.pb.inversions?.length ? data.pb.inversions.map((item) => `${item.timeframe} ${item.direction}`).join(", ") : "none detected"}.</p>{data.pb.missing.length > 0 && <p className="footnote">Missing evidence: {data.pb.missing.join("; ")}</p>}</> : <div className="state"><strong>No PB assessment available.</strong><span>Ensure the active strategy and selected completed session are available.</span></div>}</section>
      <div className="dashboard-grid"><section className="query-panel chart-panel" aria-labelledby="chart-title"><div className="section-heading"><div><p className="eyebrow">PRICE ACTION / 5M</p><h2 id="chart-title">NQ completed session</h2></div><span className="result-date">{data.session.contract.raw_contract_symbol}</span></div><CandleChart bars={data.bars} levels={data.levels} vwap={data.vwap} /></section><section className="query-panel" aria-labelledby="levels-title"><p className="eyebrow">LIQUIDITY MAP</p><h2 id="levels-title">Key levels</h2><div className="level-list">{[["PDH", data.levels.pdh], ["PDL", data.levels.pdl], ["ONH", data.levels.onh], ["ONL", data.levels.onl], ["ON midpoint", data.levels.overnight_midpoint], ["VWAP", data.vwap]].map(([label, value]) => <div key={String(label)}><span>{label}</span><strong>{number(value as number | null)}</strong></div>)}</div><p className="footnote">Levels are calculated from stored completed-session bars. They are context, not trade signals.</p></section></div>
      <div className="dashboard-grid"><section className="query-panel" aria-labelledby="evidence-title"><p className="eyebrow">EVIDENCE</p><h2 id="evidence-title">Bias context</h2>{data.bias?.evidence?.length ? <ul className="evidence-list">{data.bias.evidence.map((item) => <li key={item}>{item}</li>)}</ul> : <div className="state"><strong>No bias evidence stored.</strong><span>Use the bias API to create an evidence-backed prediction.</span></div>}</section><section className="query-panel" aria-labelledby="news-title"><p className="eyebrow">CATALYSTS</p><h2 id="news-title">High-impact news</h2>{data.news.length ? <ul className="news-list">{data.news.map((item, index) => <li key={`${item.published_at ?? "news"}-${index}`}><strong>{item.headline ?? item.title ?? "Untitled event"}</strong><small>{item.source ?? "Unknown source"}</small></li>)}</ul> : <div className="state"><strong>No recent high-impact items.</strong><span>News is read from the configured 14-day cache.</span></div>}</section></div>
    </>}
  </main>;
}
