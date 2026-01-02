"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  X,
  History,
  Sparkles,
  Gauge,
  Layers,
  Activity,
  Loader2,
  AlertTriangle,
  Tag,
  SlidersHorizontal,
  ArrowUpDown,
} from "lucide-react";

import { MetricsPanel } from "@/app/components/MetricsPanel";
import { useLOConnectionDataManager } from "lo_event/lo_event/lo_assess/components/components.jsx";

/* =========================================================
   Helpers
========================================================= */

const DEBUG = true;

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

function mean(arr) {
  if (!arr.length) return 0;
  return arr.reduce((s, x) => s + x, 0) / arr.length;
}

function stableStringify(obj) {
  const seen = new WeakSet();
  const sortObj = (v) => {
    if (v === null || typeof v !== "object") return v;
    if (seen.has(v)) return "[Circular]";
    seen.add(v);
    if (Array.isArray(v)) return v.map(sortObj);
    const keys = Object.keys(v).sort();
    const out = {};
    for (const k of keys) out[k] = sortObj(v[k]);
    return out;
  };
  try {
    return JSON.stringify(sortObj(obj));
  } catch {
    return String(obj);
  }
}

/**
 * Robust normalization to handle whatever MetricsPanel emits.
 */
function normalizeSelectedMetrics(input) {
  if (!input) return [];

  const pickMetricId = (x) => {
    if (!x) return null;
    if (typeof x === "string") return x;

    if (x && typeof x === "object") {
      return (
        x.metricKey ||
        x.metric_key ||
        x.metricId ||
        x.metric_id ||
        x.metric ||
        x.metric_name ||
        x.metricName ||
        x.id ||
        x.key ||
        x.name ||
        x.value ||
        x.label ||
        null
      );
    }
    return null;
  };

  if (Array.isArray(input)) {
    return input
      .map(pickMetricId)
      .filter(Boolean)
      .map((s) => String(s).trim())
      .filter(Boolean);
  }

  if (typeof input === "object") {
    return Object.entries(input)
      .filter(([, v]) => !!v)
      .map(([k]) => String(k).trim())
      .filter(Boolean);
  }

  return [];
}

function metricCoveragePercent(doc, metricId) {
  const text = (doc?.text || "").toString();
  const L = text.length;
  if (!L) return 0;

  const offsets = doc?.[metricId]?.offsets;
  if (!Array.isArray(offsets) || offsets.length === 0) return 0;

  const ranges = [];
  for (const pair of offsets) {
    if (!Array.isArray(pair) || pair.length < 2) continue;
    const start = Number(pair[0]);
    const len = Number(pair[1]);
    if (!Number.isFinite(start) || !Number.isFinite(len) || len <= 0) continue;

    const s = clamp(start, 0, L);
    const e = clamp(start + len, 0, L);
    if (e > s) ranges.push([s, e]);
  }
  if (!ranges.length) return 0;

  ranges.sort((a, b) => a[0] - b[0] || a[1] - b[1]);

  let covered = 0;
  let [curS, curE] = ranges[0];
  for (let i = 1; i < ranges.length; i++) {
    const [s, e] = ranges[i];
    if (s <= curE) curE = Math.max(curE, e);
    else {
      covered += curE - curS;
      curS = s;
      curE = e;
    }
  }
  covered += curE - curS;
  return (covered / L) * 100;
}

function initialsFromStudentKey(studentKey) {
  const s = String(studentKey || "").trim();
  if (!s) return "ST";
  const parts = s.split(/[^a-zA-Z0-9]+/).filter(Boolean);
  const a = (parts[0]?.[0] || "S").toUpperCase();
  const b = (parts[1]?.[0] || "T").toUpperCase();
  return `${a}${b}`.slice(0, 2);
}

/* =========================================================
   Charts (0% to 100%)
========================================================= */

function BaselineCurrentChart({ baselinePct, currentPct, height = 120 }) {
  const width = 520;
  const padL = 42;
  const padR = 10;
  const padT = 10;
  const padB = 28;

  const b = Number.isFinite(baselinePct) ? Number(baselinePct) : 0;
  const c = Number.isFinite(currentPct) ? Number(currentPct) : 0;

  const yMin = 0;
  const yMax = 100;

  const xBaseline = padL;
  const xCurrent = width - padR;

  const Y = (v) => {
    const t = (v - yMin) / Math.max(1e-6, yMax - yMin);
    return padT + (1 - t) * (height - padT - padB);
  };

  const yBaseline = Y(b);
  const yCurrent = Y(c);
  const tickTargets = [0, 25, 50, 75, 100];

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="w-full h-[120px] bg-white border border-gray-200 rounded-lg"
      role="img"
      aria-label="Baseline vs Current chart"
    >
      {tickTargets.map((t) => {
        const y = Y(t);
        return (
          <g key={t}>
            <line x1={padL} x2={width - padR} y1={y} y2={y} stroke="rgb(226,232,240)" strokeWidth="1" />
            <text x={padL - 8} y={y + 4} textAnchor="end" fontSize="10" fill="rgb(100,116,139)">
              {t}%
            </text>
          </g>
        );
      })}

      <line x1={padL} x2={padL} y1={padT} y2={height - padB} stroke="rgb(148,163,184)" strokeWidth="1" />
      <line
        x1={padL}
        x2={width - padR}
        y1={height - padB}
        y2={height - padB}
        stroke="rgb(148,163,184)"
        strokeWidth="1"
      />

      <text x={xBaseline} y={height - 10} textAnchor="start" fontSize="10" fill="rgb(100,116,139)">
        Baseline
      </text>
      <text x={xCurrent} y={height - 10} textAnchor="end" fontSize="10" fill="rgb(100,116,139)">
        Current
      </text>

      <line x1={xBaseline} x2={xCurrent} y1={yBaseline} y2={yCurrent} stroke="rgb(15,118,110)" strokeWidth="2" />
      <circle cx={xBaseline} cy={yBaseline} r="4" fill="rgb(148,163,184)" />
      <circle cx={xCurrent} cy={yCurrent} r="4.5" fill="rgb(190,24,93)" />

      <text x={xBaseline + 6} y={yBaseline - 6} textAnchor="start" fontSize="10" fill="rgb(71,85,105)">
        {b.toFixed(1)}%
      </text>
      <text x={xCurrent - 6} y={yCurrent - 6} textAnchor="end" fontSize="10" fill="rgb(71,85,105)">
        {c.toFixed(1)}%
      </text>
    </svg>
  );
}

function MetricTile({ metricKey, baseline, currentValue }) {
  return (
    <div className="rounded-2xl border border-gray-200 p-4 bg-white shadow-sm">
      <div className="min-w-0">
        <div className="text-sm font-semibold text-gray-900 truncate">{metricKey}</div>
        <div className="mt-1 text-xs text-gray-500">Baseline (prior essays only) → Current (this essay)</div>
      </div>
      <div className="mt-3">
        <BaselineCurrentChart baselinePct={baseline} currentPct={currentValue} />
      </div>
    </div>
  );
}

/* =========================================================
   Evidence blocks for Actionable Feedback
========================================================= */

function EvidenceProduct({ cues }) {
  const list = Array.isArray(cues) ? cues : [];
  if (!list.length) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600">
        No product evidence attached yet.
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
      <div className="px-3 py-2 border-b border-gray-200 bg-gray-50 text-[11px] font-semibold text-gray-600">
        Evidence cues (justification signals)
      </div>
      <div className="divide-y divide-gray-200">
        {list.map((c, i) => (
          <div key={i} className="px-3 py-2">
            <div className="text-xs font-semibold text-gray-900">{c.label}</div>
            {c.sub ? <div className="text-[11px] text-gray-600 mt-0.5">{c.sub}</div> : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function EvidenceProcess({ features }) {
  const list = Array.isArray(features) ? features : [];
  if (!list.length) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600">
        No process evidence attached yet.
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
      <div className="px-3 py-2 border-b border-gray-200 bg-gray-50 text-[11px] font-semibold text-gray-600">
        Process signals (keystroke / behavior metrics)
      </div>
      <div className="divide-y divide-gray-200">
        {list.map((f, i) => (
          <div key={i} className="px-3 py-2">
            <div className="text-xs font-semibold text-gray-900">{f.name}</div>
            <div className="text-[11px] text-gray-600 mt-0.5">
              Baseline {Number(f.baseline).toFixed(1)} → Current {Number(f.current).toFixed(1)} (Score{" "}
              {Number(f.score).toFixed(0)}/100)
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* =========================================================
   Feedback Controls (left column in feedback tab)
========================================================= */

function FeedbackControls({
  detailLevel,
  setDetailLevel,
  ordering,
  setOrdering,
  priority,
  setPriority,
  includeEvidence,
  setIncludeEvidence,
  includeProcessSignals,
  setIncludeProcessSignals,
}) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-50 ring-1 ring-emerald-200 text-emerald-900">
            <SlidersHorizontal className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <div className="text-p font-semibold text-gray-900">Feedback Controls</div>
          </div>
        </div>
        <div className="text-sm text-gray-600 mt-1">Choose ordering and how many items to show.</div>
      </div>

      <div className="px-5 py-4 space-y-5">
        <div>
          <div className="text-xs font-medium text-gray-600 mb-2">Detail level</div>
          <div className="grid grid-cols-2 gap-2">
            {["brief", "standard"].map((k) => (
              <button
                key={k}
                onClick={() => setDetailLevel(k)}
                className={`px-3 py-2 rounded-xl text-xs font-semibold border ${
                  detailLevel === k
                    ? "bg-emerald-50 text-emerald-900 border-emerald-200"
                    : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
                }`}
              >
                {k === "brief" ? "Brief" : "Standard"}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-medium text-gray-600">Sequence / ordering</div>
            <span className="inline-flex items-center gap-1 text-[11px] text-gray-500">
              <ArrowUpDown className="h-3.5 w-3.5" />
              Order
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {[
              { key: "highest_impact", label: "Highest impact" },
              { key: "lowest_impact", label: "Lowest impact" },
            ].map((opt) => (
              <button
                key={opt.key}
                onClick={() => setOrdering(opt.key)}
                className={`px-3 py-2 rounded-xl text-xs font-semibold border ${
                  ordering === opt.key
                    ? "bg-emerald-50 text-emerald-900 border-emerald-200"
                    : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="text-xs font-medium text-gray-600 mb-2">Priority</div>
          <div className="grid grid-cols-3 gap-2">
            {[
              { key: "top1", label: "Top 1" },
              { key: "top2", label: "Top 2" },
              { key: "all", label: "All" },
            ].map((opt) => (
              <button
                key={opt.key}
                onClick={() => setPriority(opt.key)}
                className={`px-3 py-2 rounded-xl text-xs font-semibold border ${
                  priority === opt.key
                    ? "bg-emerald-50 text-emerald-900 border-emerald-200"
                    : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white">
          <div className="px-3 py-2 border-b border-gray-200 bg-gray-50 text-[11px] font-semibold text-gray-600">
            Include in feedback
          </div>
          <div className="px-3 py-3 space-y-3">
            <label className="flex items-start gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                className="mt-1"
                checked={includeEvidence}
                onChange={(e) => setIncludeEvidence(e.target.checked)}
              />
              <span>Evidence snippets</span>
            </label>

            <label className="flex items-start gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                className="mt-1"
                checked={includeProcessSignals}
                onChange={(e) => setIncludeProcessSignals(e.target.checked)}
              />
              <span>Process signals</span>
            </label>
          </div>
        </div>

        <div className="text-[11px] text-gray-500">Tip: “Highest impact + Top 1 + Brief” works well for quick LMS comments.</div>
      </div>
    </div>
  );
}

/* =========================================================
   LO runner (hook lives here)
   Remounting this component forces a fresh subscription/request.
========================================================= */

function LORunner({ url, dataScope, onData, onErrors, scopeKey }) {
  const { data, errors } = useLOConnectionDataManager({ url, dataScope });

  useEffect(() => {
    onData?.(data);
  }, [data, onData]);

  useEffect(() => {
    onErrors?.(errors);
  }, [errors, onErrors]);

  useEffect(() => {
    if (!DEBUG) return;
    console.log("[LORunner] mounted scopeKey:", scopeKey);
    return () => console.log("[LORunner] unmounted scopeKey:", scopeKey);
  }, [scopeKey]);

  return null;
}

/* =========================================================
   Exported Modal
========================================================= */

export function SingleEssayModal({
  studentKey,
  docId,
  docIds,
  docTitle,
  docIndex,
  initialWords,
  subtitleDate,
  onClose,
}) {
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev || "";
    };
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose?.();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const avatar = initialsFromStudentKey(studentKey);
  const title = docTitle || (docIndex ? `Document ${docIndex}` : "Document");
  const subtitle = `• Document • ${studentKey || "—"}${subtitleDate ? ` • ${subtitleDate}` : ""}`;

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/40" onClick={() => onClose?.()} />

      <div className="absolute inset-x-0 top-4 bottom-4 mx-auto px-4 w-[96vw] max-w-[1600px]">
        <div
          className="h-full bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="bg-gradient-to-r from-emerald-600 to-emerald-500 text-white px-6 py-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 min-w-0">
                <div className="h-10 w-10 rounded-full bg-white/20 flex items-center justify-center font-bold">
                  {avatar}
                </div>

                <div className="min-w-0">
                  <div className="text-lg font-bold truncate">{title}</div>
                  <div className="text-sm text-white/90 truncate">{subtitle}</div>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => onClose?.()}
                  className="ml-2 inline-flex items-center gap-2 h-9 px-3 rounded-md bg-white/20 hover:bg-white/25 text-sm font-semibold"
                  aria-label="Close"
                >
                  <X className="h-5 w-5" />
                  Close
                </button>
              </div>
            </div>
          </div>

          <div className="flex-1 min-h-0 bg-gray-50">
            <SingleEssayInnerModal studentKey={studentKey} docId={docId} docIds={docIds} />
          </div>
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   Inner modal (Trajectory + Actionable Feedback fully included)
========================================================= */

function SingleEssayInnerModal({ studentKey, docId, docIds }) {
  const [activeTab, setActiveTab] = useState("trajectory");
  const [feedbackMode, setFeedbackMode] = useState("product");
  const [selectedMetrics, setSelectedMetricsState] = useState(["academic_language"]);

  // LO outputs stored in state (decouple UI from hook internals)
  const [loData, setLoData] = useState(null);
  const [loErrors, setLoErrors] = useState(null);

  // feedback controls
  const [detailLevel, setDetailLevel] = useState("standard");
  const [ordering, setOrdering] = useState("highest_impact");
  const [priority, setPriority] = useState("all");
  const [includeEvidence, setIncludeEvidence] = useState(true);
  const [includeProcessSignals, setIncludeProcessSignals] = useState(true);

  const setSelectedMetrics = (next) => {
    setSelectedMetricsState((prev) => {
      const resolved = typeof next === "function" ? next(prev) : next;
      const normalized = normalizeSelectedMetrics(resolved);

      if (DEBUG) {
        console.groupCollapsed("[SingleEssayInnerModal] metrics-change");
        console.log("resolved from panel:", resolved);
        console.log("normalized ids:", normalized);
        console.groupEnd();
      }

      return normalized;
    });
  };

  const exportEnabled =
    activeTab === "trajectory" &&
    !!studentKey &&
    !!docId &&
    Array.isArray(docIds) &&
    docIds.length > 0 &&
    selectedMetrics.length > 0;

  const dataScope = useMemo(() => {
    if (!exportEnabled) return { wo: { execution_dag: "writing_observer", target_exports: [], kwargs: {} } };

    return {
      wo: {
        execution_dag: "writing_observer",
        target_exports: ["single_student_docs_with_nlp_annotations"],
        kwargs: {
          course_id: "12345678901",
          student_id: docIds.map(() => ({ user_id: studentKey })),
          document: docIds.map((d) => ({ doc_id: d })),
          nlp_options: selectedMetrics,
        },
      },
    };
  }, [exportEnabled, studentKey, docIds, selectedMetrics]);

  // The key that forces LORunner (and hook) remount
  const scopeKey = useMemo(() => {
    const signature = {
      exportEnabled,
      studentKey,
      docId,
      docIds,
      selectedMetrics,
      target_exports: dataScope?.wo?.target_exports || [],
    };
    return stableStringify(signature);
  }, [exportEnabled, studentKey, docId, docIds, selectedMetrics, dataScope]);

  useEffect(() => {
    if (!DEBUG) return;
    console.groupCollapsed("[SingleEssayInnerModal] scopeKey changed -> forcing LO remount");
    console.log("scopeKey:", scopeKey);
    console.log("dataScope:", dataScope);
    console.groupEnd();
  }, [scopeKey, dataScope]);

  // reset outputs on a new scope
  useEffect(() => {
    if (!exportEnabled) return;
    setLoData(null);
    setLoErrors(null);
  }, [scopeKey, exportEnabled]);

  const docsObj = useMemo(() => loData?.students?.[studentKey]?.documents || {}, [loData, studentKey]);

  const hasError = useMemo(() => {
    if (!exportEnabled) return false;
    if (!loErrors) return false;
    if (Array.isArray(loErrors)) return loErrors.length > 0;
    if (typeof loErrors === "object") return Object.keys(loErrors).length > 0;
    return true;
  }, [exportEnabled, loErrors]);

  const hasAllDocs = useMemo(() => {
    if (!exportEnabled) return false;
    return docIds.every((id) => {
      const d = docsObj?.[id];
      return d && typeof d.text === "string" && d.text.length > 0;
    });
  }, [exportEnabled, docIds, docsObj]);

  const isLOLoading = useMemo(() => exportEnabled && !hasError && !hasAllDocs, [exportEnabled, hasError, hasAllDocs]);

  const currentDocIndex = useMemo(() => {
    const idx = docIds.findIndex((id) => String(id) === String(docId));
    return Math.max(0, idx);
  }, [docIds, docId]);

  const hasPriorData = currentDocIndex > 0;

  const metricSummaries = useMemo(() => {
    if (!exportEnabled || !hasAllDocs) return [];
    return selectedMetrics.map((metricKey) => {
      const series = docIds.map((id) => metricCoveragePercent(docsObj?.[id], metricKey));
      const current = Number(series[currentDocIndex] ?? 0);
      const prior = series.slice(0, currentDocIndex).map((x) => Number(x) || 0);
      const baseline = prior.length ? mean(prior) : 0;
      return { key: metricKey, baseline, currentValue: current };
    });
  }, [exportEnabled, hasAllDocs, selectedMetrics, docIds, docsObj, currentDocIndex]);

  const currentText = useMemo(() => (docsObj?.[docId]?.text || "").toString(), [docsObj, docId]);

  const wordCount = useMemo(() => {
    const t = (currentText || "").trim();
    if (!t) return 0;
    return t.split(/\s+/).filter(Boolean).length;
  }, [currentText]);

  /* --------------------------
     Actionable feedback content
     (keep these blocks as-is or replace with real output later)
  -------------------------- */

  const feedbackBlocks = useMemo(() => {
    const product = [
      {
        category: "clarity",
        heading: "Clarify the claim early",
        why: "Your central claim becomes clear only midway through the essay.",
        suggestion: "Rewrite the opening as: claim → reason → preview of evidence (2–3 lines).",
        evidence: { cues: [{ label: "Thesis appears late", sub: "Main stance introduced after several sentences." }] },
        impact: 0.9,
      },
      {
        category: "organization",
        heading: "Use a stronger paragraph map",
        why: "Paragraph purposes aren’t clearly signposted.",
        suggestion: "Add a 1-sentence topic line at the start of each paragraph to guide the reader.",
        evidence: { cues: [{ label: "Weak topic sentences", sub: "Paragraph goals inferred rather than stated." }] },
        impact: 0.75,
      },
      {
        category: "evidence",
        heading: "Connect evidence to the claim explicitly",
        why: "Evidence is present, but the link back to the thesis is implicit.",
        suggestion: "After each quote/example, add one sentence: “This shows ___ because ___.”",
        evidence: { cues: [{ label: "Evidence-to-claim bridge", sub: "Explanation is shorter than evidence in places." }] },
        impact: 0.7,
      },
    ];

    const process = [
      {
        category: "overall",
        heading: "Revise globally before polishing",
        why: "Edits appear late and are mostly sentence-level.",
        suggestion: "Next time: draft quickly → structure pass → line edits.",
        evidence: { features: [{ name: "Late revision burst", baseline: 42.1, current: 61.4, score: 68 }] },
        impact: 0.8,
      },
      {
        category: "organization",
        heading: "Pause to outline before drafting",
        why: "Drafting begins immediately without a planning phase.",
        suggestion: "Spend 3–5 minutes outlining: claim → reasons → evidence before writing.",
        evidence: { features: [{ name: "Planning time", baseline: 18.0, current: 6.5, score: 42 }] },
        impact: 0.7,
      },
      {
        category: "focus",
        heading: "Avoid long uninterrupted drafting runs",
        why: "Long runs often reduce clarity and increase later cleanup work.",
        suggestion: "Try a short checkpoint every 5–7 minutes: “Does this paragraph support my claim?”",
        evidence: { features: [{ name: "Longest uninterrupted run (min)", baseline: 9.2, current: 14.8, score: 55 }] },
        impact: 0.6,
      },
    ];

    return { product, process };
  }, []);

  const applyDetailLevel = (b) => {
    if (detailLevel === "brief") {
      return { ...b, why: "" }; // brief removes the “why” sentence
    }
    return b;
  };

  const orderingLabel = useMemo(() => {
    return ordering === "lowest_impact" ? "Lowest impact" : "Highest impact";
  }, [ordering]);

  const sortedAndFilteredFeedbackBlocks = useMemo(() => {
    const base = feedbackMode === "product" ? feedbackBlocks.product : feedbackBlocks.process;
    const blocks = [...base];

    if (ordering === "highest_impact") {
      blocks.sort((a, b) => (Number(b.impact) || 0) - (Number(a.impact) || 0));
    } else {
      blocks.sort((a, b) => (Number(a.impact) || 0) - (Number(b.impact) || 0));
    }

    if (priority === "top1") return blocks.slice(0, 1);
    if (priority === "top2") return blocks.slice(0, 2);
    return blocks;
  }, [feedbackBlocks, feedbackMode, ordering, priority]);

  return (
    <div className="bg-gray-50 h-full flex flex-col min-h-0">
      {/* Hidden runner that forces re-run by remounting on scopeKey changes */}
      {exportEnabled ? (
        <LORunner
          key={scopeKey}
          scopeKey={scopeKey}
          url={"ws://localhost:8888/wsapi/communication_protocol"}
          dataScope={dataScope}
          onData={(d) => setLoData(d)}
          onErrors={(e) => setLoErrors(e)}
        />
      ) : null}

      <div className="sticky top-0 z-20 bg-white border-b border-gray-200">
        <div className="px-6 py-4 flex items-center justify-between gap-3">
          <div className="text-sm text-gray-600">
            Essay: <span className="font-semibold text-gray-900">{docId}</span> •{" "}
            <span className="font-semibold text-gray-900">{wordCount.toLocaleString()}</span> words
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("trajectory")}
              className={`inline-flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-semibold border ${
                activeTab === "trajectory"
                  ? "bg-emerald-50 text-emerald-900 border-emerald-200"
                  : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
              }`}
            >
              <History className="h-4 w-4" />
              Writing Trajectory
            </button>

            <button
              onClick={() => setActiveTab("feedback")}
              className={`inline-flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-semibold border ${
                activeTab === "feedback"
                  ? "bg-emerald-50 text-emerald-900 border-emerald-200"
                  : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
              }`}
            >
              <Sparkles className="h-4 w-4" />
              Actionable Feedback
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-hidden">
        <div className="px-6 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6 h-full min-h-0 items-stretch">
          {/* Left column */}
          <aside className="lg:col-span-3 h-full min-h-0 flex flex-col">
            <div className="flex-1 min-h-0 overflow-auto pr-1 pb-4">
              {activeTab === "trajectory" ? (
                <MetricsPanel metrics={selectedMetrics} setMetrics={setSelectedMetrics} />
              ) : (
                <FeedbackControls
                  detailLevel={detailLevel}
                  setDetailLevel={setDetailLevel}
                  ordering={ordering}
                  setOrdering={setOrdering}
                  priority={priority}
                  setPriority={setPriority}
                  includeEvidence={includeEvidence}
                  setIncludeEvidence={setIncludeEvidence}
                  includeProcessSignals={includeProcessSignals}
                  setIncludeProcessSignals={setIncludeProcessSignals}
                />
              )}
            </div>
          </aside>

          {/* Middle column: essay */}
          <section className="lg:col-span-4 h-full min-h-0 flex flex-col">
            <div className="flex-1 min-h-0 overflow-auto pb-4 pr-1">
              <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-p font-semibold text-gray-900 truncate">Essay</div>
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <span className="inline-flex items-center gap-1 text-xs text-gray-500">
                          <Tag className="h-3.5 w-3.5" />
                          Tags
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-gray-50 text-gray-700 ring-1 ring-gray-200 text-xs">
                          Document
                        </span>
                      </div>
                    </div>

                    <div className="shrink-0">
                      <span className="px-2 py-1 text-xs font-semibold rounded-xl bg-white border border-gray-200">
                        {wordCount.toLocaleString()} words
                      </span>
                    </div>
                  </div>
                </div>

                <div className="px-5 py-4">
                  <div className="prose prose-sm max-w-none text-gray-800">
                    {currentText ? (
                      <p className="text-p">{currentText}</p>
                    ) : (
                      <p className="text-gray-500 text-p">No text available yet.</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Right column */}
          <section className="lg:col-span-5 h-full min-h-0 flex flex-col">
            {activeTab === "trajectory" ? (
              <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden h-full flex flex-col min-h-0">
                <div className="px-5 py-4 border-b border-gray-200 bg-white/70">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-50 ring-1 ring-emerald-200 text-emerald-900">
                          <Gauge className="h-4 w-4" />
                        </span>
                        <h4 className="text-p font-semibold text-gray-900">Writing Trajectory</h4>
                      </div>
                      <div className="mt-1 text-sm text-gray-600">
                        Baseline = average of prior essays only. Current = this essay.
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-5 flex-1 min-h-0 overflow-auto pb-4">
                  {selectedMetrics.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-6 text-center">
                      <div className="mt-1 text-sm font-semibold text-gray-900">
                        Select metrics on the left to view trajectory
                      </div>
                      <div className="mt-1 text-sm text-gray-600">This starts empty by design — pick signals first.</div>
                    </div>
                  ) : isLOLoading ? (
                    <div className="rounded-2xl border border-gray-200 bg-white p-6">
                      <div className="flex items-center gap-2 text-sm font-semibold text-gray-900">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Computing trajectory…
                      </div>
                    </div>
                  ) : hasError ? (
                    <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6">
                      <div className="flex items-center gap-2 text-sm font-semibold text-rose-900">
                        <AlertTriangle className="h-4 w-4" />
                        Couldn’t compute trajectory
                      </div>
                      <pre className="mt-3 text-[11px] leading-4 text-rose-900/80 bg-white/40 border border-rose-200 rounded-xl p-3 overflow-auto max-h-40">
                        {JSON.stringify(loErrors, null, 2)}
                      </pre>
                    </div>
                  ) : !hasPriorData ? (
                    <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-6 text-center">
                      <div className="mt-1 text-sm font-semibold text-gray-900">No prior data to compare with</div>
                      <div className="mt-1 text-sm text-gray-600">
                        This is the student’s first essay in the trajectory sequence, so we can’t compute a baseline yet.
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 gap-3">
                      {metricSummaries.map((m) => (
                        <MetricTile
                          key={m.key}
                          metricKey={m.key}
                          baseline={m.baseline}
                          currentValue={m.currentValue}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden h-full flex flex-col min-h-0">
                <div className="px-5 py-4 border-b border-gray-200 bg-white/70">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-50 ring-1 ring-emerald-200 text-emerald-900">
                          <Sparkles className="h-4 w-4" />
                        </span>
                        <h4 className="text-p font-semibold text-gray-900">Actionable Feedback</h4>
                      </div>
                      <div className="mt-1 text-sm text-gray-600">
                        {orderingLabel} • {priority === "top1" ? "Top 1" : priority === "top2" ? "Top 2" : "All"} •{" "}
                        {detailLevel === "brief" ? "Brief" : "Standard"}
                      </div>
                    </div>

                    <div className="inline-flex rounded-xl border border-gray-200 overflow-hidden bg-white">
                      <button
                        onClick={() => setFeedbackMode("product")}
                        className={`px-3 py-2 text-xs font-semibold inline-flex items-center gap-2 ${
                          feedbackMode === "product"
                            ? "bg-emerald-50 text-emerald-900"
                            : "bg-white text-gray-700 hover:bg-gray-50"
                        }`}
                      >
                        <Layers className="h-3.5 w-3.5" />
                        Product
                      </button>
                      <button
                        onClick={() => setFeedbackMode("process")}
                        className={`px-3 py-2 text-xs font-semibold inline-flex items-center gap-2 border-l border-gray-200 ${
                          feedbackMode === "process"
                            ? "bg-emerald-50 text-emerald-900"
                            : "bg-white text-gray-700 hover:bg-gray-50"
                        }`}
                      >
                        <Activity className="h-3.5 w-3.5" />
                        Process
                      </button>
                    </div>
                  </div>
                </div>

                <div className="p-5 flex-1 min-h-0 overflow-auto pb-4 pr-1 space-y-3">
                  {sortedAndFilteredFeedbackBlocks.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-6 text-center">
                      <div className="mt-1 text-sm font-semibold text-gray-900">No feedback items available</div>
                      <div className="mt-1 text-sm text-gray-600">
                        Try switching Product/Process or set Priority to “All”.
                      </div>
                    </div>
                  ) : (
                    sortedAndFilteredFeedbackBlocks.map((raw, i) => {
                      const b = applyDetailLevel(raw);

                      return (
                        <div key={i} className="rounded-2xl border border-gray-200 p-4 bg-white shadow-sm">
                          <div className="text-sm font-semibold text-gray-900">{b.heading}</div>

                          {b.why ? <div className="mt-1 text-sm text-gray-700">{b.why}</div> : null}

                          <div className="mt-3">
                            <div className="text-xs text-gray-500 font-medium mb-1">Comment</div>
                            <div className="text-sm text-gray-900 font-medium">{b.suggestion}</div>
                          </div>

                          {feedbackMode === "product" ? (
                            includeEvidence ? (
                              <div className="mt-3">
                                <div className="text-xs text-gray-500 font-medium mb-1">
                                  Evidence (justification)
                                </div>
                                <EvidenceProduct cues={b.evidence?.cues} />
                              </div>
                            ) : null
                          ) : includeProcessSignals ? (
                            <div className="mt-3">
                              <div className="text-xs text-gray-500 font-medium mb-1">
                                Evidence (process signals)
                              </div>
                              <EvidenceProcess features={b.evidence?.features} />
                            </div>
                          ) : null}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
