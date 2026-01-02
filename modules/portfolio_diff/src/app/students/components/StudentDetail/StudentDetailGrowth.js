"use client";

import { useMemo, useCallback, useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { Loader2 } from "lucide-react";

import { useLOConnectionDataManager } from "lo_event/lo_event/lo_assess/components/components.jsx";
import { MetricsPanel } from "@/app/components/MetricsPanel";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

const DEBUG = false;

/* ---------------------- stable stringify ---------------------- */
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

/* ---------------------- Metric normalization ---------------------- */
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

/* ---------------------- Coverage helpers ---------------------- */
function coveragePercentFromDoc(doc, metricId) {
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

    const s = Math.max(0, Math.min(L, start));
    const e = Math.max(0, Math.min(L, start + len));
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

/* ---------------------- LO Runner ---------------------- */
function LORunner({ wsUrl, dataScope, scopeKey, onData, onErrors }) {
  const { data, errors } = useLOConnectionDataManager({
    url: wsUrl,
    dataScope,
  });

  useEffect(() => onData?.(data), [data, onData]);
  useEffect(() => onErrors?.(errors), [errors, onErrors]);

  useEffect(() => {
    if (!DEBUG) return;
    console.log("[LORunner] mounted scopeKey:", scopeKey);
    return () => console.log("[LORunner] unmounted scopeKey:", scopeKey);
  }, [scopeKey]);

  return null;
}

/* ---------------------- ECharts option builder ---------------------- */
function buildEChartOption({ metricId, points }) {
  const labels = points.map((p) => p.label);

  const barData = points.map((p) => ({
    value: p.barValue,
    docId: p.docId,
    label: p.label,
    raw: p.raw,
  }));

  const lineData = points.map((p) => ({
    value: p.value,
    docId: p.docId,
    label: p.label,
    raw: p.raw,
  }));

  return {
    animation: false,
    grid: { top: 20, right: 20, bottom: 40, left: 60 },

    tooltip: {
      trigger: "axis",
      confine: true,
      axisPointer: {
        type: "line",
        shadowStyle: { opacity: 0 },
        lineStyle: { color: "rgba(107,114,128,0.55)", width: 1 },
      },
      formatter: (params) => {
        const primary = Array.isArray(params) ? params[0] : params;
        const d = primary?.data || {};
        const pct = Number.isFinite(Number(d.raw)) ? Number(d.raw).toFixed(1) : "0.0";
        const docId = d.docId || "—";
        const label = d.label || primary?.axisValue || "";

        return `
          <div style="font-size:12px;">
            <div style="font-weight:600; margin-bottom:2px;">${metricId}</div>
            <div style="color:#6b7280; margin-bottom:6px;">${label}</div>
            <div>Coverage: <b>${pct}%</b></div>
            <div style="color:#6b7280; margin-top:4px;">Document: <span style="font-family:monospace;">${docId}</span></div>
          </div>
        `;
      },
    },

    xAxis: {
      type: "category",
      data: labels,
      axisLabel: { fontSize: 11, interval: "auto" },
      axisPointer: {
        show: true,
        type: "line",
        shadowStyle: { opacity: 0 },
        lineStyle: { color: "rgba(107,114,128,0.55)", width: 1 },
      },
    },

    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      axisLabel: { formatter: "{value}%" },
    },
    series: [
      {
        name: "Coverage (bar)",
        type: "bar",
        data: barData,
        barMaxWidth: 28,
        emphasis: { focus: "none" },
        select: { disabled: true },
        blur: { itemStyle: { opacity: 1 } },
      },
      {
        name: "Coverage (line)",
        type: "line",
        data: lineData,
        smooth: true,
        symbol: "circle",
        symbolSize: 8,
        emphasis: { focus: "none" },
        select: { disabled: true },
        blur: { lineStyle: { opacity: 1 }, itemStyle: { opacity: 1 } },
      },
    ],
  };
}

export default function StudentDetailGrowth({
  metrics,
  setMetrics,

  studentID,
  courseId = "12345678901",
  wsUrl = "ws://localhost:8888/wsapi/communication_protocol",

  essaysInRangeAsc = [],
}) {
  const selectedMetrics = useMemo(() => normalizeSelectedMetrics(metrics), [metrics]);

  const docIdsAsc = useMemo(() => {
    return (Array.isArray(essaysInRangeAsc) ? essaysInRangeAsc : [])
      .map((e) => (e?.id || "").toString().trim())
      .filter(Boolean);
  }, [essaysInRangeAsc]);

  const enabled = !!studentID && docIdsAsc.length > 0 && selectedMetrics.length > 0;

  const dataScope = useMemo(() => {
    if (!enabled) {
      return { wo: { execution_dag: "writing_observer", target_exports: [], kwargs: {} } };
    }

    return {
      wo: {
        execution_dag: "writing_observer",
        target_exports: ["single_student_docs_with_nlp_annotations"],
        kwargs: {
          course_id: courseId,
          student_id: docIdsAsc.map(() => ({ user_id: studentID })),
          document: docIdsAsc.map((doc_id) => ({ doc_id })),
          nlp_options: selectedMetrics,
        },
      },
    };
  }, [enabled, courseId, studentID, docIdsAsc, selectedMetrics]);

  const scopeKey = useMemo(() => {
    const signature = { enabled, studentID, courseId, docIdsAsc, selectedMetrics };
    return stableStringify(signature);
  }, [enabled, studentID, courseId, docIdsAsc, selectedMetrics]);

  const [loData, setLoData] = useState(null);
  const [loErrors, setLoErrors] = useState(null);
  const [isFetching, setIsFetching] = useState(false);
  const prevScopeKeyRef = useRef(scopeKey);

  useEffect(() => {
    if (!enabled) {
      setIsFetching(false);
      return;
    }
    if (prevScopeKeyRef.current !== scopeKey) {
      prevScopeKeyRef.current = scopeKey;
      setIsFetching(true);
      setLoErrors(null);
    }
  }, [enabled, scopeKey]);

  useEffect(() => {
    if (!enabled) return;

    const hasErrors =
      loErrors &&
      ((Array.isArray(loErrors) && loErrors.length > 0) ||
        (typeof loErrors === "object" && Object.keys(loErrors).length > 0));

    if (hasErrors) {
      setIsFetching(false);
      return;
    }
    if (loData) setIsFetching(false);
  }, [enabled, loData, loErrors]);

  const docsObj = loData?.students?.[studentID]?.documents || {};

  const isMetricReady = useCallback(
    (metricId) => {
      if (!metricId) return false;
      for (const d of docIdsAsc) {
        const doc = docsObj?.[d];
        const offsets = doc?.[metricId]?.offsets;
        if (Array.isArray(offsets) && offsets.length > 0) return true;
      }
      return false;
    },
    [docsObj, docIdsAsc]
  );

  const seriesByMetric = useMemo(() => {
    const out = {};
    if (!enabled || !loData) return out;

    for (const metricId of selectedMetrics) {
      // keep per-metric loader behavior for newly added metrics
      if (isFetching && !isMetricReady(metricId)) {
        out[metricId] = null;
        continue;
      }

      const points = [];
      for (let i = 0; i < docIdsAsc.length; i++) {
        const docId = docIdsAsc[i];
        const doc = docsObj?.[docId];

        const essay = essaysInRangeAsc[i] || {};
        const label =
          (essay?.date && String(essay.date)) ||
          (essay?.title && String(essay.title)) ||
          `Essay ${i + 1}`;

        const raw = coveragePercentFromDoc(doc, metricId);

        points.push({
          idx: i,
          label,
          docId,
          raw,
          value: raw,
          barValue: raw,
          metricLabel: metricId,
        });
      }

      out[metricId] = points;
    }

    return out;
  }, [enabled, loData, selectedMetrics, docIdsAsc, docsObj, essaysInRangeAsc, isFetching, isMetricReady]);

  // lock tooltip per metric
  const [lockedIndexByMetric, setLockedIndexByMetric] = useState({});
  const chartRefs = useRef({});

  const showEmpty = selectedMetrics.length === 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
      {enabled ? (
        <LORunner
          key={scopeKey}
          scopeKey={scopeKey}
          wsUrl={wsUrl}
          dataScope={dataScope}
          onData={(d) => setLoData(d)}
          onErrors={(e) => setLoErrors(e)}
        />
      ) : null}

      <MetricsPanel metrics={metrics} setMetrics={setMetrics} title="Metrics" stickyTopClassName="top-24" />

      <section className="col-span-12 md:col-span-8 xl:col-span-9">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="text-xs text-gray-500">
            Showing <span className="font-medium text-gray-700">{docIdsAsc.length}</span> docs
          </div>

          {enabled && isFetching ? (
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-900">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Updating…
            </div>
          ) : null}
        </div>

        {showEmpty ? (
          <div className="bg-white rounded-2xl border border-dashed border-gray-300 p-10 text-center text-gray-500 shadow-sm">
            Select one or more metrics from the left to view trends over time.
          </div>
        ) : !loData ? (
          <div className="bg-white rounded-2xl border border-gray-200 p-6 text-gray-700 shadow-sm flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading documents…
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {selectedMetrics.map((metricId) => {
              const points = seriesByMetric?.[metricId];

              if (enabled && isFetching && points === null) {
                return (
                  <div key={metricId} className="bg-white rounded-2xl border border-gray-200 p-4 shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-gray-900">{metricId}</h4>
                      <div className="text-xs text-gray-600 inline-flex items-center gap-2">
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        Fetching…
                      </div>
                    </div>

                    <div className="h-64 rounded-xl border border-gray-200 bg-gray-50 flex items-center justify-center">
                      <div className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-semibold text-gray-700 shadow-sm">
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        Computing new metric…
                      </div>
                    </div>
                  </div>
                );
              }

              const data = Array.isArray(points) ? points : [];
              const lockedIndex = lockedIndexByMetric?.[metricId];

              const option = buildEChartOption({ metricId, points: data });

              const onEvents = {
                click: (params) => {
                  const idx = params?.dataIndex;
                  if (typeof idx !== "number") return;

                  setLockedIndexByMetric((prev) => {
                    const cur = prev?.[metricId];
                    if (typeof cur === "number" && cur === idx) {
                      const next = { ...prev };
                      delete next[metricId];
                      return next;
                    }
                    return { ...prev, [metricId]: idx };
                  });

                  const inst = chartRefs.current?.[metricId];
                  if (inst) {
                    // lock tooltip without any highlight/selection
                    inst.dispatchAction({ type: "showTip", seriesIndex: 0, dataIndex: idx });
                  }
                },
              };

              return (
                <div key={metricId} className="bg-white rounded-2xl border border-gray-200 p-4 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900">{metricId}</h4>

                    <div className="flex items-center gap-3 text-xs text-gray-600">
                      <span>{data.length} points</span>

                      {typeof lockedIndex === "number" ? (
                        <button
                          type="button"
                          className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 font-semibold text-emerald-900"
                          onClick={() => {
                            setLockedIndexByMetric((prev) => {
                              const next = { ...prev };
                              delete next[metricId];
                              return next;
                            });

                            const inst = chartRefs.current?.[metricId];
                            if (inst) inst.dispatchAction({ type: "hideTip" });
                          }}
                        >
                          <span className="text-[10px] uppercase tracking-wide">Locked</span>
                          <span className="text-[11px]">Clear</span>
                        </button>
                      ) : null}
                    </div>
                  </div>

                  <div className="relative h-64">
                    <ReactECharts
                      option={option}
                      style={{ height: "100%", width: "100%" }}
                      notMerge={true}
                      lazyUpdate={true}
                      onEvents={onEvents}
                      ref={(ref) => {
                        const inst = ref?.getEchartsInstance?.();
                        if (inst) chartRefs.current[metricId] = inst;
                      }}
                    />

                    {enabled && isFetching ? (
                      <div className="absolute inset-0 bg-white/30 flex items-center justify-center rounded-xl pointer-events-none">
                        <div className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-semibold text-gray-700 shadow-sm">
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          Fetching updated metrics…
                        </div>
                      </div>
                    ) : null}
                  </div>

                  <p className="mt-1 text-xs text-gray-500">
                    Hover to show more information.
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
