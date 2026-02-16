"use client";

import { navigateTo } from "@/app/utils/navigation";
import {
  ArrowLeftRight,
  Check,
  ChevronDown,
  Clock,
  Eye,
  FileText,
  Focus,
  Gauge,
  Languages,
  ListCollapse,
  MessageSquareText,
  MessagesSquare,
  Minus,
  Quote,
  RefreshCw,
  Search,
  Speech,
  TrendingDown,
  TrendingUp,
  Users,
  WholeWord,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useLOConnectionDataManager } from "lo_event/lo_event/lo_assess/components/components.jsx";
import dynamic from "next/dynamic";

import { MetricsPanel } from "@/app/components/MetricsPanel";
import { useCourseIdContext } from "@/app/providers/CourseIdProvider";
import { getWsOriginFromWindow } from "@/app/utils/ws";

/* ---------------------- deterministic helpers ---------------------- */
const seedFrom = (s) => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = ((h ^ s.charCodeAt(i)) * 16777619) >>> 0;
  return h >>> 0;
};

/* =============================================================
   OFFSET HIGHLIGHTING HELPERS (multi-metric, overlap-safe)
   ============================================================= */

const HIGHLIGHT_CLASSES = [
  "bg-emerald-200/70",
  "bg-sky-200/70",
  "bg-amber-200/70",
  "bg-rose-200/70",
  "bg-indigo-200/70",
  "bg-lime-200/70",
  "bg-violet-200/60",
  "bg-teal-200/70",
  "bg-fuchsia-200/60",
  "bg-orange-200/70",
];

const highlightClassForMetric = (metricId) => {
  const idx = seedFrom(metricId || "metric") % HIGHLIGHT_CLASSES.length;
  return HIGHLIGHT_CLASSES[idx];
};

function buildSpansFromDoc(doc, metricIds) {
  const text = (doc?.text || "").toString();
  const spans = [];

  for (const metricId of metricIds || []) {
    const m = doc?.[metricId];
    const offsets = m?.offsets;
    if (!Array.isArray(offsets)) continue;

    for (const pair of offsets) {
      if (!Array.isArray(pair) || pair.length < 2) continue;
      const start = Number(pair[0]);
      const len = Number(pair[1]);
      if (!Number.isFinite(start) || !Number.isFinite(len) || len <= 0) continue;

      const end = start + len;

      const s = Math.max(0, Math.min(text.length, start));
      const e = Math.max(0, Math.min(text.length, end));
      if (e > s) spans.push({ start: s, end: e, metricId });
    }
  }

  spans.sort((a, b) => a.start - b.start || b.end - b.start - (a.end - a.start));
  return { text, spans };
}

function segmentTextBySpans(text, spans) {
  const cuts = new Set([0, text.length]);
  for (const s of spans) {
    cuts.add(s.start);
    cuts.add(s.end);
  }
  const points = Array.from(cuts).sort((a, b) => a - b);

  const segs = [];
  for (let i = 0; i < points.length - 1; i++) {
    const a = points[i],
      b = points[i + 1];
    if (b <= a) continue;

    const active = [];
    for (const sp of spans) {
      if (sp.start <= a && sp.end >= b) active.push(sp.metricId);
    }

    segs.push({ start: a, end: b, text: text.slice(a, b), active });
  }
  return segs;
}

/* =============================================================
   METRICS (FULL LIST)
   ============================================================= */

const CATEGORY_LABELS = {
  language: "Language",
  argumentation: "Argumentation",
  statements: "Statements",
  transitions: "Transition Words",
  pos: "Parts of Speech",
  sentence_type: "Sentence Types",
  source_information: "Source Information",
  dialogue: "Dialogue",
  tone: "Tone",
  details: "Details",
  other: "Other",
};

const iconForCategory = (catKey) => {
  switch (catKey) {
    case "language":
      return Languages;
    case "argumentation":
      return MessagesSquare;
    case "statements":
      return MessageSquareText;
    case "transitions":
      return ArrowLeftRight;
    case "pos":
      return Speech;
    case "sentence_type":
      return WholeWord;
    case "source_information":
      return Quote;
    case "dialogue":
      return Users;
    case "tone":
      return Gauge;
    case "details":
      return ListCollapse;
    default:
      return FileText;
  }
};

const METRIC_DEFS = [
  // language
  {
    id: "academic_language",
    title: "Academic Language",
    icon: iconForCategory("language"),
    category: CATEGORY_LABELS.language,
    function: "percent",
    desc: "Percent of tokens flagged academic",
  },
  {
    id: "informal_language",
    title: "Informal Language",
    icon: iconForCategory("language"),
    category: CATEGORY_LABELS.language,
    function: "percent",
    desc: "Percent of tokens flagged informal",
  },
  {
    id: "latinate_words",
    title: "Latinate Words",
    icon: iconForCategory("language"),
    category: CATEGORY_LABELS.language,
    function: "percent",
    desc: "Percent of tokens flagged latinate",
  },
  {
    id: "opinion_words",
    title: "Opinion Words",
    icon: iconForCategory("language"),
    category: CATEGORY_LABELS.language,
    function: "total",
    desc: "Total opinion-word signals",
  },
  {
    id: "emotion_words",
    title: "Emotion Words",
    icon: iconForCategory("language"),
    category: CATEGORY_LABELS.language,
    function: "percent",
    desc: "Percent emotion words",
  },

  // argumentation
  {
    id: "argument_words",
    title: "Argument Words",
    icon: iconForCategory("argumentation"),
    category: CATEGORY_LABELS.argumentation,
    function: "percent",
    desc: "Percent argument words",
  },
  {
    id: "explicit_argument",
    title: "Explicit argument",
    icon: iconForCategory("argumentation"),
    category: CATEGORY_LABELS.argumentation,
    function: "percent",
    desc: "Percent explicit argument markers",
  },

  // statements
  {
    id: "statements_of_opinion",
    title: "Statements of Opinion",
    icon: iconForCategory("statements"),
    category: CATEGORY_LABELS.statements,
    function: "percent",
    desc: "Percent of sentences classified as opinion",
  },
  {
    id: "statements_of_fact",
    title: "Statements of Fact",
    icon: iconForCategory("statements"),
    category: CATEGORY_LABELS.statements,
    function: "percent",
    desc: "Percent of sentences classified as fact",
  },

  // transitions
  {
    id: "transition_words",
    title: "Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "counts",
    desc: "Transition counts (by type)",
  },
  {
    id: "positive_transition_words",
    title: "Positive Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total positive transitions",
  },
  {
    id: "conditional_transition_words",
    title: "Conditional Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total conditional transitions",
  },
  {
    id: "consequential_transition_words",
    title: "Consequential Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total consequential transitions",
  },
  {
    id: "contrastive_transition_words",
    title: "Contrastive Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total contrastive transitions",
  },
  {
    id: "counterpoint_transition_words",
    title: "Counterpoint Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total counterpoint transitions",
  },
  {
    id: "comparative_transition_words",
    title: "Comparative Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total comparative transitions",
  },
  {
    id: "cross_referential_transition_words",
    title: "Cross Referential Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total cross-referential transitions",
  },
  {
    id: "illustrative_transition_words",
    title: "Illustrative Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total illustrative transitions",
  },
  {
    id: "negative_transition_words",
    title: "Negative Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total negative transitions",
  },
  {
    id: "emphatic_transition_words",
    title: "Emphatic Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total emphatic transitions",
  },
  {
    id: "evenidentiary_transition_words",
    title: "Evenidentiary_transition_words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total evidentiary transitions",
  },
  {
    id: "general_transition_words",
    title: "General Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total general transitions",
  },
  {
    id: "ordinal_transition_words",
    title: "Ordinal Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total ordinal transitions",
  },
  {
    id: "purposive_transition_words",
    title: "Purposive Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total purposive transitions",
  },
  {
    id: "periphrastic_transition_words",
    title: "Periphrastic Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total periphrastic transitions",
  },
  {
    id: "hypothetical_transition_words",
    title: "Hypothetical Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total hypothetical transitions",
  },
  {
    id: "summative_transition_words",
    title: "Summative Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total summative transitions",
  },
  {
    id: "introductory_transition_words",
    title: "Introductory Transition Words",
    icon: iconForCategory("transitions"),
    category: CATEGORY_LABELS.transitions,
    function: "total",
    desc: "Total introductory transitions",
  },

  // parts of speech
  {
    id: "adjectives",
    title: "Adjectives",
    icon: iconForCategory("pos"),
    category: CATEGORY_LABELS.pos,
    function: "total",
    desc: "Total adjectives",
  },
  {
    id: "adverbs",
    title: "Adverbs",
    icon: iconForCategory("pos"),
    category: CATEGORY_LABELS.pos,
    function: "total",
    desc: "Total adverbs",
  },
  {
    id: "nouns",
    title: "Nouns",
    icon: iconForCategory("pos"),
    category: CATEGORY_LABELS.pos,
    function: "total",
    desc: "Total nouns",
  },
  {
    id: "proper_nouns",
    title: "Proper Nouns",
    icon: iconForCategory("pos"),
    category: CATEGORY_LABELS.pos,
    function: "total",
    desc: "Total proper nouns",
  },
  {
    id: "verbs",
    title: "Verbs",
    icon: iconForCategory("pos"),
    category: CATEGORY_LABELS.pos,
    function: "total",
    desc: "Total verbs",
  },
  {
    id: "numbers",
    title: "Numbers",
    icon: iconForCategory("pos"),
    category: CATEGORY_LABELS.pos,
    function: "total",
    desc: "Total numbers",
  },
  {
    id: "prepositions",
    title: "Prepositions",
    icon: iconForCategory("pos"),
    category: CATEGORY_LABELS.pos,
    function: "total",
    desc: "Total prepositions",
  },
  {
    id: "coordinating_conjunction",
    title: "Coordinating Conjunction",
    icon: iconForCategory("pos"),
    category: CATEGORY_LABELS.pos,
    function: "total",
    desc: "Total coordinating conjunctions",
  },
  {
    id: "subordinating_conjunction",
    title: "Subordinating Conjunction",
    icon: iconForCategory("pos"),
    category: CATEGORY_LABELS.pos,
    function: "total",
    desc: "Total subordinating conjunctions",
  },
  {
    id: "auxiliary_verb",
    title: "Auxiliary Verb",
    icon: iconForCategory("pos"),
    category: CATEGORY_LABELS.pos,
    function: "total",
    desc: "Total auxiliary verbs",
  },
  {
    id: "pronoun",
    title: "Pronoun",
    icon: iconForCategory("pos"),
    category: CATEGORY_LABELS.pos,
    function: "total",
    desc: "Total pronouns",
  },

  // sentence types
  {
    id: "simple_sentences",
    title: "Simple Sentences",
    icon: iconForCategory("sentence_type"),
    category: CATEGORY_LABELS.sentence_type,
    function: "total",
    desc: "Total simple sentences",
  },
  {
    id: "simple_with_complex_predicates",
    title: "Simple with Complex Predicates",
    icon: iconForCategory("sentence_type"),
    category: CATEGORY_LABELS.sentence_type,
    function: "total",
    desc: "Total simple (complex predicates)",
  },
  {
    id: "simple_with_compound_predicates",
    title: "Simple with Compound Predicates",
    icon: iconForCategory("sentence_type"),
    category: CATEGORY_LABELS.sentence_type,
    function: "total",
    desc: "Total simple (compound predicates)",
  },
  {
    id: "simple_with_compound_complex_predicates",
    title: "Simple with Compound Complex Predicates",
    icon: iconForCategory("sentence_type"),
    category: CATEGORY_LABELS.sentence_type,
    function: "total",
    desc: "Total simple (compound complex predicates)",
  },
  {
    id: "compound_sentences",
    title: "Compound Sentences",
    icon: iconForCategory("sentence_type"),
    category: CATEGORY_LABELS.sentence_type,
    function: "total",
    desc: "Total compound sentences",
  },
  {
    id: "complex_sentences",
    title: "Complex Sentences",
    icon: iconForCategory("sentence_type"),
    category: CATEGORY_LABELS.sentence_type,
    function: "total",
    desc: "Total complex sentences",
  },
  {
    id: "compound_complex_sentences",
    title: "Compound Complex Sentences",
    icon: iconForCategory("sentence_type"),
    category: CATEGORY_LABELS.sentence_type,
    function: "total",
    desc: "Total compound-complex sentences",
  },

  // source info
  {
    id: "information_sources",
    title: "Information Sources",
    icon: iconForCategory("source_information"),
    category: CATEGORY_LABELS.source_information,
    function: "percent",
    desc: "Percent source references",
  },
  {
    id: "attributions",
    title: "Attributions",
    icon: iconForCategory("source_information"),
    category: CATEGORY_LABELS.source_information,
    function: "percent",
    desc: "Percent attributions",
  },
  {
    id: "citations",
    title: "Citations",
    icon: iconForCategory("source_information"),
    category: CATEGORY_LABELS.source_information,
    function: "percent",
    desc: "Percent citations",
  },
  {
    id: "quoted_words",
    title: "Quoted Words",
    icon: iconForCategory("source_information"),
    category: CATEGORY_LABELS.source_information,
    function: "percent",
    desc: "Percent quoted words",
  },

  // dialogue
  {
    id: "direct_speech_verbs",
    title: "Direct Speech Verbs",
    icon: iconForCategory("dialogue"),
    category: CATEGORY_LABELS.dialogue,
    function: "percent",
    desc: "Percent direct speech verbs",
  },
  {
    id: "indirect_speech",
    title: "Indirect Speech",
    icon: iconForCategory("dialogue"),
    category: CATEGORY_LABELS.dialogue,
    function: "percent",
    desc: "Percent indirect speech",
  },

  // tone
  {
    id: "positive_tone",
    title: "Positive Tone",
    icon: iconForCategory("tone"),
    category: CATEGORY_LABELS.tone,
    function: "percent",
    desc: "Percent positive tone",
  },
  {
    id: "negative_tone",
    title: "Negative Tone",
    icon: iconForCategory("tone"),
    category: CATEGORY_LABELS.tone,
    function: "percent",
    desc: "Percent negative tone",
  },

  // details
  {
    id: "concrete_details",
    title: "Concrete Details",
    icon: iconForCategory("details"),
    category: CATEGORY_LABELS.details,
    function: "percent",
    desc: "Percent concrete details",
  },
  {
    id: "main_idea_sentences",
    title: "Main Idea Sentences",
    icon: iconForCategory("details"),
    category: CATEGORY_LABELS.details,
    function: "total",
    desc: "Total main idea sentences",
  },
  {
    id: "supporting_idea_sentences",
    title: "Supporting Idea Sentences",
    icon: iconForCategory("details"),
    category: CATEGORY_LABELS.details,
    function: "total",
    desc: "Total supporting idea sentences",
  },
  {
    id: "supporting_detail_sentences",
    title: "Supporting Detail Sentences",
    icon: iconForCategory("details"),
    category: CATEGORY_LABELS.details,
    function: "total",
    desc: "Total supporting detail sentences",
  },

  // other
  {
    id: "polysyllabic_words",
    title: "Polysyllabic Words",
    icon: iconForCategory("other"),
    category: CATEGORY_LABELS.other,
    function: "percent",
    desc: "Percent polysyllabic tokens",
  },
  {
    id: "low_frequency_words",
    title: "Low Frequency Words",
    icon: iconForCategory("other"),
    category: CATEGORY_LABELS.other,
    function: "percent",
    desc: "Percent low-frequency tokens",
  },
  {
    id: "sentences",
    title: "Sentences",
    icon: iconForCategory("other"),
    category: CATEGORY_LABELS.other,
    function: "total",
    desc: "Total sentences",
  },
  {
    id: "paragraphs",
    title: "Paragraphs",
    icon: iconForCategory("other"),
    category: CATEGORY_LABELS.other,
    function: "total",
    desc: "Total paragraphs",
  },
  {
    id: "character_trait_words",
    title: "Character Trait Words",
    icon: iconForCategory("other"),
    category: CATEGORY_LABELS.other,
    function: "percent",
    desc: "Percent character trait tokens",
  },
  {
    id: "in_past_tense",
    title: "In Past Tense",
    icon: iconForCategory("other"),
    category: CATEGORY_LABELS.other,
    function: "percent",
    desc: "Percent past tense scope",
  },
  {
    id: "explicit_claims",
    title: "Explicit Claims",
    icon: iconForCategory("other"),
    category: CATEGORY_LABELS.other,
    function: "percent",
    desc: "Percent explicit claims",
  },
  {
    id: "social_awareness",
    title: "Social Awareness",
    icon: iconForCategory("other"),
    category: CATEGORY_LABELS.other,
    function: "percent",
    desc: "Percent social awareness",
  },
];

const METRIC_BY_ID = Object.fromEntries(METRIC_DEFS.map((m) => [m.id, m]));

/* ---------------------- Tooltip values from backend ---------------------- */
const PERCENT_IDS = new Set(METRIC_DEFS.filter((m) => m.function === "percent").map((m) => m.id));

const formatMetricValue = (value, id) => {
  if (value == null) return "—";
  if (PERCENT_IDS.has(id)) return `${Math.round(Number(value))}%`;
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(1);
  const n = Number(value);
  return Number.isNaN(n) ? String(value) : n.toFixed(1);
};

/* =============================================================
   coverage-based metric value from offsets
   ============================================================= */
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

    let s = Math.max(0, Math.min(L, start));
    let e = Math.max(0, Math.min(L, start + len));
    if (e > s) ranges.push([s, e]);
  }
  if (!ranges.length) return 0;

  ranges.sort((a, b) => a[0] - b[0] || a[1] - b[1]);

  let covered = 0;
  let [curS, curE] = ranges[0];

  for (let i = 1; i < ranges.length; i++) {
    const [s, e] = ranges[i];
    if (s <= curE) {
      curE = Math.max(curE, e);
    } else {
      covered += curE - curS;
      curS = s;
      curE = e;
    }
  }
  covered += curE - curS;

  return (covered / L) * 100;
}

/* ---------------------- Tooltip builder for highlights ---------------------- */
function buildHighlightTooltip(doc, metricIds) {
  const uniq = Array.from(new Set(metricIds || []));
  if (uniq.length === 0) return "";

  const lines = [];
  for (const id of uniq) {
    const meta = METRIC_BY_ID[id];
    const label = meta?.title || id;

    const v = doc?.[id]?.metric;
    const hasNum = v != null && !Number.isNaN(Number(v));

    const cov = metricCoveragePercent(doc, id);
    const covStr = `${cov.toFixed(1)}% of text`;

    if (hasNum) {
      lines.push(`${label}: ${formatMetricValue(v, id)} (${covStr})`);
    } else {
      lines.push(`${label}: ${covStr}`);
    }
  }
  return lines.join("\n");
}

/* ---------------------- Floating tooltip (custom, reliable) ---------------------- */
function clamp(n, lo, hi) {
  return Math.max(lo, Math.min(hi, n));
}

function FloatingTooltip({ tooltip }) {
  if (!tooltip?.visible) return null;

  return (
    <div className="fixed z-[9999] pointer-events-none" style={{ left: tooltip.x, top: tooltip.y, maxWidth: 420 }}>
      <div className="bg-gray-900 text-white text-xs rounded-lg shadow-lg px-3 py-2 whitespace-pre-line">
        {tooltip.content}
      </div>
    </div>
  );
}

function HighlightedEssay({
  doc,
  activeMetricIds,
  containerRef,
  onShowTooltip,
  onMoveTooltip,
  onHideTooltip,
}) {
  const { text, spans } = useMemo(() => buildSpansFromDoc(doc, activeMetricIds), [doc, activeMetricIds]);
  const segments = useMemo(() => segmentTextBySpans(text, spans), [text, spans]);

  if (!text.trim()) {
    return (
      <div className="text-gray-600 text-sm leading-relaxed whitespace-pre-line">
        (No text returned for this document.)
      </div>
    );
  }

  return (
    <div ref={containerRef} className="text-gray-800 text-[15px] leading-7 whitespace-pre-line">
      {segments.map((seg, idx) => {
        if (!seg.active.length) return <span key={idx}>{seg.text}</span>;

        const top = seg.active[0];
        const cls = highlightClassForMetric(top);
        const tooltipText = buildHighlightTooltip(doc, seg.active);

        return (
          <mark
            key={idx}
            className={`${cls} rounded px-0.5 cursor-help`}
            data-primary-metric={top}
            data-metrics={seg.active.join(",")}
            onMouseEnter={(e) => onShowTooltip(tooltipText, e)}
            onMouseMove={(e) => onMoveTooltip(e)}
            onMouseLeave={() => onHideTooltip()}
            onPointerEnter={(e) => onShowTooltip(tooltipText, e)}
            onPointerMove={(e) => onMoveTooltip(e)}
            onPointerLeave={() => onHideTooltip()}
          >
            {seg.text}
          </mark>
        );
      })}
    </div>
  );
}

/* ---------------------- URL param reader (client-safe) ---------------------- */
function readCompareParamsFromLocation() {
  if (typeof window === "undefined") {
    return { urlReady: false, studentID: "", docIds: [] };
  }

  const sp = new URLSearchParams(window.location.search);
  const studentID = (sp.get("student_id") || "").trim();
  const idsRaw = (sp.get("ids") || "").trim();

  const parts = idsRaw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const seen = new Set();
  const docIds = [];
  for (const p of parts) {
    if (!seen.has(p)) {
      seen.add(p);
      docIds.push(p);
    }
    if (docIds.length === 2) break;
  }

  return { urlReady: true, studentID, docIds };
}

function buildEssayFromDoc({ docId, text, side }) {
  const content = (text || "").trim();
  const words = content ? content.split(/\s+/).filter(Boolean).length : 0;

  return {
    id: docId || `${side}-unknown`,
    title: docId ? `Document: ${docId}` : `Document (${side})`,
    date: "",
    minutes: Math.max(10, Math.round(words / 30)),
    words,
    grade: "—",
    tags: [],
    content: content || "(No text returned for this document.)",
  };
}

/* ---------------------- Metrics comparison UI helpers ---------------------- */
function formatPct(n) {
  const x = Number.isFinite(Number(n)) ? Number(n) : 0;
  return `${x.toFixed(1)}%`;
}
function formatDelta(n) {
  const x = Number.isFinite(Number(n)) ? Number(n) : 0;
  const sign = x > 0 ? "+" : x < 0 ? "−" : "±";
  const abs = Math.abs(x).toFixed(1);
  return `${sign}${abs}%`;
}

/* ---------------------- Evidence extraction (short excerpts) ---------------------- */
function extractMetricExamples(doc, metricId, maxExamples = 2) {
  const text = (doc?.text || "").toString();
  if (!text.trim()) return [];

  const offsets = doc?.[metricId]?.offsets;
  if (!Array.isArray(offsets) || offsets.length === 0) return [];

  const L = text.length;
  const spans = [];
  for (const pair of offsets) {
    if (!Array.isArray(pair) || pair.length < 2) continue;
    const start = Number(pair[0]);
    const len = Number(pair[1]);
    if (!Number.isFinite(start) || !Number.isFinite(len) || len <= 0) continue;
    const s = Math.max(0, Math.min(L, start));
    const e = Math.max(0, Math.min(L, start + len));
    if (e > s) spans.push([s, e]);
  }
  if (!spans.length) return [];

  spans.sort((a, b) => a[0] - b[0] || a[1] - b[1]);

  const seen = new Set();
  const out = [];
  for (const [s, e] of spans) {
    if (out.length >= maxExamples) break;

    const pad = 70;
    const a = Math.max(0, s - pad);
    const b = Math.min(L, e + pad);

    let snippet = text.slice(a, b).replace(/\s+/g, " ").trim();

    if (a > 0) snippet = `…${snippet}`;
    if (b < L) snippet = `${snippet}…`;

    const key = snippet.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);

    out.push(snippet);
  }
  return out;
}

function MetricDeltaIcon({ delta }) {
  const d = Number(delta) || 0;
  if (d > 0.0001) return <TrendingUp className="h-4 w-4 text-emerald-700" />;
  if (d < -0.0001) return <TrendingDown className="h-4 w-4 text-rose-700" />;
  return <Minus className="h-4 w-4 text-gray-500" />;
}

function MetricDeltaPill({ delta }) {
  const d = Number(delta) || 0;
  const cls =
    d > 0.0001
      ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
      : d < -0.0001
      ? "bg-rose-50 text-rose-700 ring-1 ring-rose-200"
      : "bg-gray-100 text-gray-700";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${cls}`}>
      Δ {formatDelta(d)}
    </span>
  );
}

function StoryCard({ label, metricTitle, category, left, right, delta, tone, isDisabled }) {
  const toneCls =
    tone === "up"
      ? "border-emerald-200 bg-emerald-50/40"
      : tone === "down"
      ? "border-rose-200 bg-rose-50/40"
      : "border-gray-200 bg-gray-50";

  return (
    <div className={`rounded-2xl border p-4 ${toneCls}`}>
      <div className="text-xs text-gray-600">{label}</div>
      <div className="mt-1 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className={`text-sm font-semibold truncate ${isDisabled ? "text-gray-400" : "text-gray-900"}`}>
            {isDisabled ? "—" : metricTitle || "—"}
          </div>
          <div className="mt-0.5 text-xs text-gray-500 truncate">{isDisabled ? "" : category || ""}</div>
        </div>
        <MetricDeltaPill delta={isDisabled ? 0 : delta} />
      </div>

      <div className={`mt-3 flex items-center justify-between text-sm ${isDisabled ? "text-gray-400" : "text-gray-700"}`}>
        <span className={`font-medium ${isDisabled ? "text-gray-400" : "text-gray-900"}`}>{formatPct(left)}</span>
        <span className="text-gray-400">→</span>
        <span className={`font-medium ${isDisabled ? "text-gray-400" : "text-gray-900"}`}>{formatPct(right)}</span>
      </div>
    </div>
  );
}

function MetricRow({ row, isFocused, onFocusToggle, onShow }) {
  const { def, left, right, delta } = row;
  return (
    <div
      className={`rounded-xl border p-3 transition ${
        isFocused ? "border-emerald-300 bg-emerald-50/40" : "border-gray-100 hover:bg-gray-50/40"
      }`}
    >
      <div className="flex items-center gap-3">
        <span className={`inline-block h-3 w-3 rounded ${highlightClassForMetric(def.id)}`} title="Highlight color" />
        <div className="min-w-0">
          <div className="flex items-center gap-2 min-w-0">
            <div className="text-sm font-semibold text-gray-900 truncate">{def.title}</div>
            <span className="text-xs text-gray-500 truncate">· {def.category}</span>
          </div>
          <div className="mt-0.5 text-xs text-gray-500 truncate">{def.desc}</div>
        </div>

        <div className="ml-auto flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 text-sm text-gray-700">
            <span className="font-medium text-gray-900">{formatPct(left)}</span>
            <span className="text-gray-400">→</span>
            <span className="font-medium text-gray-900">{formatPct(right)}</span>
          </div>

          <div className="flex items-center gap-2">
            <MetricDeltaIcon delta={delta} />
            <MetricDeltaPill delta={delta} />
          </div>

          <button
            onClick={onFocusToggle}
            className={`inline-flex items-center gap-2 px-3 py-2 rounded-xl text-sm border transition ${
              isFocused
                ? "bg-emerald-600 text-white border-emerald-600 hover:bg-emerald-700"
                : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
            }`}
            title={isFocused ? "Clear focus" : "Focus this metric"}
          >
            <Focus className="h-4 w-4" />
            {isFocused ? "Focused" : "Focus"}
          </button>

          <button
            onClick={onShow}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-sm border border-gray-200 bg-white hover:bg-gray-50 text-gray-700"
            title="Show in essays"
          >
            <Eye className="h-4 w-4" />
            Show
          </button>
        </div>
      </div>
    </div>
  );
}

export default function EssayComparison() {
  const initial = useMemo(() => readCompareParamsFromLocation(), []);
  const [urlReady, setUrlReady] = useState(initial.urlReady);
  const [studentID, setStudentID] = useState(initial.studentID);
  const [docIds, setDocIds] = useState(initial.docIds);
  const { courseId } = useCourseIdContext();

  useEffect(() => {
    const next = readCompareParamsFromLocation();
    if (!next.urlReady) return;

    const sameStudent = next.studentID === studentID;
    const sameDocs =
      next.docIds.length === docIds.length &&
      next.docIds[0] === docIds[0] &&
      next.docIds[1] === docIds[1];

    if (!sameStudent) setStudentID(next.studentID);
    if (!sameDocs) setDocIds(next.docIds);
    if (!urlReady) setUrlReady(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const leftDocId = docIds[0] || "";
  const rightDocId = docIds[1] || "";

  const enabled = urlReady && !!studentID && docIds.length === 2;
  const missingParams = urlReady && (!studentID || docIds.length !== 2);

  const [selectedMetrics, setSelectedMetrics] = useState([
    "academic_language",
    "informal_language",
    "latinate_words",
    "transition_words",
    "citations",
    "sentences",
    "paragraphs",
  ]);

  /* ---------------------- Available docs list (for replacement selection) ---------------------- */
  const docsListEnabled = urlReady && !!studentID;

  const dataScopeList = useMemo(() => {
    if (!docsListEnabled) {
      return {
        wo: {
          execution_dag: "writing_observer",
          target_exports: [],
          kwargs: {},
        },
      };
    }
    return {
      wo: {
        execution_dag: "writing_observer",
        target_exports: ["student_with_docs"],
        kwargs: {
          course_id: courseId,
          student_id: [{ user_id: studentID }],
        },
      },
    };
  }, [courseId, docsListEnabled, studentID]);

  const origin =
    process.env.NEXT_PUBLIC_LO_WS_ORIGIN?.replace(/\/+$/, "") ||
    getWsOriginFromWindow() ||
    "ws://localhost:8888";

  const { data: loListData } = useLOConnectionDataManager({
    url: `${origin}/wsapi/communication_protocol`,
    dataScope: dataScopeList,
  });

  const availableDocIds = useMemo(() => {
    const docsObj = loListData?.students?.[studentID]?.docs || {};
    const ids = Object.keys(docsObj || {});
    ids.sort();
    return ids;
  }, [loListData, studentID]);

  /* ---------------------- comparison data fetch ---------------------- */
  const dataScope = useMemo(() => {
    if (!enabled) {
      return {
        wo: {
          execution_dag: "writing_observer",
          target_exports: [],
          kwargs: {},
        },
      };
    }

    return {
      wo: {
        execution_dag: "writing_observer",
        target_exports: ["single_student_docs_with_nlp_annotations"],
        kwargs: {
          course_id: courseId,
          student_id: docIds.map(() => ({ user_id: studentID })),
          document: docIds.map((doc_id) => ({ doc_id })),
          nlp_options: selectedMetrics,
        },
      },
    };
  }, [enabled, courseId, docIds, selectedMetrics, studentID]);

  const { data: loData, errors: loErrors, connection: loConnection } = useLOConnectionDataManager({
    url: "ws://localhost:8888/wsapi/communication_protocol",
    dataScope,
  });

  const docsObj = loData?.students?.[studentID]?.documents || {};
  const leftDoc = leftDocId ? docsObj?.[leftDocId] : null;
  const rightDoc = rightDocId ? docsObj?.[rightDocId] : null;

  // ----------------- LOADING GATE (non-empty text) -----------------
  const leftHasTextField = !!(leftDoc && Object.prototype.hasOwnProperty.call(leftDoc, "text"));
  const rightHasTextField = !!(rightDoc && Object.prototype.hasOwnProperty.call(rightDoc, "text"));

  const leftTextNonEmpty = leftHasTextField && typeof leftDoc.text === "string" && leftDoc.text.trim().length > 0;
  const rightTextNonEmpty = rightHasTextField && typeof rightDoc.text === "string" && rightDoc.text.trim().length > 0;

  const docsReady = enabled && leftTextNonEmpty && rightTextNonEmpty;
  const isDocsLoading = enabled && !docsReady;
  // -------------------------------------------------------------------

  const leftText = leftHasTextField ? leftDoc?.text || "" : "";
  const rightText = rightHasTextField ? rightDoc?.text || "" : "";

  const showInlineWarning = enabled && isDocsLoading && !!loErrors;

  const [leftEssay, setLeftEssay] = useState(() => buildEssayFromDoc({ docId: leftDocId, text: "", side: "left" }));
  const [rightEssay, setRightEssay] = useState(() => buildEssayFromDoc({ docId: rightDocId, text: "", side: "right" }));

  useEffect(() => {
    setLeftEssay(buildEssayFromDoc({ docId: leftDocId, text: "", side: "left" }));
    setRightEssay(buildEssayFromDoc({ docId: rightDocId, text: "", side: "right" }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leftDocId, rightDocId]);

  useEffect(() => {
    if (!enabled) return;
    if (leftHasTextField) setLeftEssay(buildEssayFromDoc({ docId: leftDocId, text: leftText, side: "left" }));
    if (rightHasTextField) setRightEssay(buildEssayFromDoc({ docId: rightDocId, text: rightText, side: "right" }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, leftHasTextField, rightHasTextField, leftDocId, rightDocId, leftText, rightText]);

  /* ---------------------- CUSTOM TOOLTIP STATE ---------------------- */
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, content: "" });

  const positionFromMouse = useCallback((e) => {
    const pad = 12;
    const vw = typeof window !== "undefined" ? window.innerWidth : 1200;
    const vh = typeof window !== "undefined" ? window.innerHeight : 800;

    const maxW = 420;
    const maxH = 220;

    const x = clamp(e.clientX + pad, 8, vw - maxW);
    const y = clamp(e.clientY + pad, 8, vh - maxH);
    return { x, y };
  }, []);

  const onShowTooltip = useCallback(
    (content, e) => {
      if (!content) return;
      const { x, y } = positionFromMouse(e);
      setTooltip({ visible: true, x, y, content: content || "" });
    },
    [positionFromMouse]
  );

  const onMoveTooltip = useCallback(
    (e) => {
      setTooltip((t) => {
        if (!t.visible) return t;
        const { x, y } = positionFromMouse(e);
        return { ...t, x, y };
      });
    },
    [positionFromMouse]
  );

  const onHideTooltip = useCallback(() => {
    setTooltip((t) => ({ ...t, visible: false }));
  }, []);

  /* ---------------------- URL update (no navigation, no page shift) ---------------------- */
  const updateUrlIds = useCallback(
    (nextDocIds) => {
      if (typeof window === "undefined") return;
      const sp = new URLSearchParams(window.location.search);
      sp.set("student_id", studentID || "");
      sp.set("ids", nextDocIds.join(","));
      const next = `${window.location.pathname}?${sp.toString()}`;
      window.history.replaceState({}, "", next);
    },
    [studentID]
  );

  const setDocIdForSide = useCallback(
    (side, newId) => {
      const id = (newId || "").trim();
      if (!id) return;

      setDocIds((prev) => {
        const next = [...prev];
        const L = next[0] || "";
        const R = next[1] || "";

        // Prevent selecting the same doc for both sides; if chosen, swap.
        if (side === "left") {
          if (id === R) {
            next[0] = R;
            next[1] = L;
          } else {
            next[0] = id;
            next[1] = R;
          }
        } else {
          if (id === L) {
            next[0] = R;
            next[1] = L;
          } else {
            next[0] = L;
            next[1] = id;
          }
        }

        // Ensure length 2
        if (!next[0]) next[0] = L;
        if (!next[1]) next[1] = R;

        updateUrlIds(next);
        return next;
      });
    },
    [updateUrlIds]
  );

  /* ---------------------- Replace Modal (no shifting, full doc list) ---------------------- */
  const [replaceModal, setReplaceModal] = useState({ open: false, side: "left" });
  const [replaceQuery, setReplaceQuery] = useState("");
  const [replaceActiveIdx, setReplaceActiveIdx] = useState(0);

  const openReplace = (side) => {
    setReplaceQuery("");
    setReplaceActiveIdx(0);
    setReplaceModal({ open: true, side });
    if (typeof document !== "undefined") document.body.style.overflow = "hidden";
  };
  const closeReplace = () => {
    setReplaceModal({ open: false, side: "left" });
    setReplaceQuery("");
    setReplaceActiveIdx(0);
    if (typeof document !== "undefined") document.body.style.overflow = "";
  };

  useEffect(() => {
    return () => {
      if (typeof document !== "undefined") document.body.style.overflow = "";
    };
  }, []);

  const currentIdForSide = replaceModal.side === "left" ? leftDocId : rightDocId;
  const otherIdForSide = replaceModal.side === "left" ? rightDocId : leftDocId;

  const replaceMatches = useMemo(() => {
    const q = replaceQuery.trim().toLowerCase();
    const pool = availableDocIds || [];
    if (!q) return pool;
    return pool.filter((id) => id.toLowerCase().includes(q));
  }, [replaceQuery, availableDocIds]);

  const replacePick = (id) => {
    setDocIdForSide(replaceModal.side, id);
    closeReplace();
  };

  const onReplaceKeyDown = (e) => {
    if (!replaceModal.open) return;

    if (e.key === "Escape") {
      e.preventDefault();
      closeReplace();
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setReplaceActiveIdx((i) => Math.min(replaceMatches.length - 1, i + 1));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setReplaceActiveIdx((i) => Math.max(0, i - 1));
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      const id = replaceMatches[replaceActiveIdx];
      if (id) replacePick(id);
      return;
    }
  };

  // Keep active index in bounds as filter changes
  useEffect(() => {
    if (!replaceModal.open) return;
    setReplaceActiveIdx(0);
  }, [replaceModal.open, replaceQuery]);

  /* =============================================================
     METRICS COMPARISON (Coverage-based)
     ============================================================= */

  const [focusedMetricId, setFocusedMetricId] = useState(null);
  const [showAllMetrics, setShowAllMetrics] = useState(false);

  // If focused metric is removed from selection, clear focus
  useEffect(() => {
    if (focusedMetricId && !selectedMetrics.includes(focusedMetricId)) {
      setFocusedMetricId(null);
    }
  }, [focusedMetricId, selectedMetrics]);

  const activeMetricIds = focusedMetricId ? [focusedMetricId] : selectedMetrics;

  const coverageRows = useMemo(() => {
    if (!selectedMetrics.length) return [];
    const defs = selectedMetrics.map((id) => METRIC_BY_ID[id]).filter(Boolean);

    const rows = defs.map((def) => {
      const a = metricCoveragePercent(leftDoc, def.id);
      const b = metricCoveragePercent(rightDoc, def.id);
      const delta = (Number(b) || 0) - (Number(a) || 0);
      const absDelta = Math.abs(delta);

      return { def, left: Number(a) || 0, right: Number(b) || 0, delta, absDelta };
    });

    rows.sort((x, y) => y.absDelta - x.absDelta || String(x.def.title).localeCompare(String(y.def.title)));
    return rows;
  }, [selectedMetrics, leftDoc, rightDoc]);

  const metricsSummary = useMemo(() => {
    if (!coverageRows.length) {
      return { mostIncreased: null, mostDecreased: null, mostStable: null };
    }

    const byDeltaDesc = [...coverageRows].sort((a, b) => b.delta - a.delta);
    const mostIncreased = byDeltaDesc[0] || null;

    const byStable = [...coverageRows].sort((a, b) => a.absDelta - b.absDelta);
    const mostStable = byStable[0] || null;

    const negatives = coverageRows.filter((r) => r.delta < -0.0001);
    let mostDecreased = null;
    if (negatives.length) {
      negatives.sort((a, b) => a.delta - b.delta);
      mostDecreased = negatives[0];
    }

    return { mostIncreased, mostDecreased, mostStable };
  }, [coverageRows]);

  const topChanges = useMemo(() => coverageRows.slice(0, 8), [coverageRows]);
  const allRemaining = useMemo(() => (coverageRows.length > 8 ? coverageRows.slice(8) : []), [coverageRows]);

  const leftEssayRef = useRef(null);
  const rightEssayRef = useRef(null);

  const scrollToFirstHighlight = useCallback((metricId) => {
    if (!metricId) return;

    const sel = `mark[data-metrics*="${metricId}"], mark[data-primary-metric="${metricId}"]`;

    const leftEl = leftEssayRef.current ? leftEssayRef.current.querySelector(sel) : null;
    const rightEl = rightEssayRef.current ? rightEssayRef.current.querySelector(sel) : null;

    const target = leftEl || rightEl;
    if (target && typeof target.scrollIntoView === "function") {
      target.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
    }
  }, []);

  const focusMetric = useCallback(
    (metricId, shouldScroll = false) => {
      if (!metricId) return;

      setFocusedMetricId((cur) => (cur === metricId ? null : metricId));

      if (shouldScroll) setTimeout(() => scrollToFirstHighlight(metricId), 30);
    },
    [scrollToFirstHighlight]
  );

  const focusedMeta = focusedMetricId ? METRIC_BY_ID[focusedMetricId] : null;

  const focusedExamples = useMemo(() => {
    if (!focusedMetricId) return { left: [], right: [] };
    return {
      left: extractMetricExamples(leftDoc, focusedMetricId, 2),
      right: extractMetricExamples(rightDoc, focusedMetricId, 2),
    };
  }, [focusedMetricId, leftDoc, rightDoc]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <FloatingTooltip tooltip={tooltip} />

      {/* Replace Modal */}
      {replaceModal.open && (
        <div className="fixed inset-0 z-[9998]" onKeyDown={onReplaceKeyDown} tabIndex={-1}>
          <div className="absolute inset-0 bg-black/30" onClick={closeReplace} />
          <div className="absolute inset-0 flex items-start justify-center p-4 pt-16">
            <div className="w-full max-w-2xl rounded-2xl bg-white shadow-2xl border border-gray-200 overflow-hidden">
              <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-gray-900">
                    Replace {replaceModal.side === "left" ? "Left" : "Right"} document
                  </div>
                  <div className="mt-1 text-xs text-gray-500">
                    Student: <span className="font-mono text-gray-700">{studentID}</span>
                    {" • "}
                    Docs: <span className="font-medium text-gray-700">{availableDocIds.length}</span>
                    {" • "}
                    Current: <span className="font-mono text-gray-700">{currentIdForSide || "—"}</span>
                  </div>
                </div>
                <button onClick={closeReplace} className="p-2 rounded-lg hover:bg-gray-50" aria-label="Close">
                  <X className="h-5 w-5 text-gray-500" />
                </button>
              </div>

              <div className="p-4 border-b border-gray-100">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    value={replaceQuery}
                    onChange={(e) => setReplaceQuery(e.target.value)}
                    autoFocus
                    placeholder="Search by document id…"
                    className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div className="mt-2 text-xs text-gray-500">Tip: Use ↑ / ↓ then Enter to select.</div>
              </div>

              <div className="max-h-[55vh] overflow-auto">
                {replaceMatches.length === 0 ? (
                  <div className="p-4 text-sm text-gray-600">No matches.</div>
                ) : (
                  replaceMatches.map((id, idx) => {
                    const isActive = idx === replaceActiveIdx;
                    const isCurrent = id === currentIdForSide;
                    const isOther = id === otherIdForSide;

                    return (
                      <button
                        key={id}
                        onClick={() => replacePick(id)}
                        onMouseEnter={() => setReplaceActiveIdx(idx)}
                        className={`w-full text-left px-4 py-3 flex items-center gap-3 ${isActive ? "bg-emerald-50" : "hover:bg-gray-50"}`}
                      >
                        <span className="font-mono text-xs text-gray-800">{id}</span>

                        <div className="ml-auto flex items-center gap-2">
                          {isCurrent && (
                            <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                              <Check className="h-3 w-3" />
                              Current
                            </span>
                          )}
                          {isOther && !isCurrent && (
                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 ring-1 ring-amber-200">
                              Other side (will swap)
                            </span>
                          )}
                        </div>
                      </button>
                    );
                  })
                )}
              </div>

              <div className="p-4 border-t border-gray-100 flex items-center justify-end gap-2">
                <button onClick={closeReplace} className="px-4 py-2 rounded-xl border border-gray-200 hover:bg-gray-50 text-sm">
                  Cancel
                </button>
                <button onClick={closeReplace} className="px-4 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700 text-sm">
                  Done
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="px-6 pt-6">
        <nav className="text-sm text-gray-500 mb-4" aria-label="Breadcrumb">
          <ol className="inline-flex items-center gap-1 md:gap-2">
            <li className="inline-flex items-center cursor-pointer" onClick={() => navigateTo("students", {})}>
              <span className="inline-flex gap-2 items-center cursor-pointer text-gray-500 hover:text-emerald-600">
                <Users className="h-4 w-4" />
                <span>Students</span>
              </span>
            </li>
            <li className="text-gray-400">›</li>
            <li
              className="text-gray-700 font-medium cursor-pointer hover:text-emerald-600"
              onClick={() => {
                navigateTo("students", { student_id: studentID });
              }}
            >
              {studentID || "—"}
            </li>
            <li className="text-gray-400">›</li>
            <li className="text-gray-900 font-semibold">Essay Comparison</li>
          </ol>
        </nav>

        {missingParams ? (
          <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            Missing URL params. Expected: <span className="font-mono">?student_id=...&ids=docA,docB</span>
          </div>
        ) : null}

        {urlReady ? (
          <div className="mb-4 text-xs text-gray-600">
            ids: <span className="font-mono">{docIds.join(", ")}</span>
            {loConnection?.status ? <span> • ws: {String(loConnection.status)}</span> : null}
            {availableDocIds.length ? <span> • available docs: {availableDocIds.length}</span> : null}
          </div>
        ) : null}
      </div>

      <div className="px-6 pb-6">
        {isDocsLoading ? (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <div className="text-sm text-gray-700 font-medium">Loading documents…</div>
            </div>
            <div className="mt-2 text-xs text-gray-500">
              Waiting until both documents return non-empty <span className="font-mono">text</span>.
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* ✅ Sidebar replaced with MetricsPanel */}
            <div className="lg:col-span-3">
              <MetricsPanel metrics={selectedMetrics} setMetrics={setSelectedMetrics} title="Metrics" stickyTopClassName="top-24" />
            </div>

            <section className="lg:col-span-9">
              {showInlineWarning ? (
                <div className="mb-4 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
                  Some data errors were reported while loading documents.
                </div>
              ) : null}

              {/* Essays */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left */}
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                  <div className="p-6 pb-4 border-b border-gray-100">
                    <div className="flex items-center justify-between gap-3">
                      <h2 className="text-lg font-semibold text-gray-900">{leftEssay.title}</h2>
                      <button
                        onClick={() => openReplace("left")}
                        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 text-sm text-gray-700"
                        title="Replace document"
                      >
                        <RefreshCw className="h-4 w-4" />
                        Replace
                      </button>
                    </div>

                    <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-600">
                      <span className="inline-flex items-center gap-1">
                        <Clock className="h-4 w-4" /> {leftEssay.minutes} min
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <FileText className="h-4 w-4" /> {leftEssay.words.toLocaleString()} words
                      </span>
                    </div>

                    {focusedMetricId ? (
                      <div className="mt-3 flex items-center gap-2 text-xs">
                        <span className="inline-flex items-center gap-2 px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200">
                          <Focus className="h-3.5 w-3.5" />
                          Focus: <span className="font-medium">{focusedMeta?.title || focusedMetricId}</span>
                        </span>
                        <button
                          onClick={() => setFocusedMetricId(null)}
                          className="text-xs px-2 py-1 rounded-full border border-gray-200 hover:bg-gray-50 text-gray-700"
                        >
                          Clear
                        </button>
                      </div>
                    ) : null}
                  </div>

                  <div className="p-6 py-2 bg-white h-[16rem] overflow-y-auto">
                    <div className="text-xs text-gray-500 mb-3">
                      Hover highlights to see metric tooltip.
                      {focusedMetricId ? <span className="ml-2">Showing only the focused metric highlights.</span> : null}
                    </div>
                    <HighlightedEssay
                      doc={leftDoc}
                      activeMetricIds={activeMetricIds}
                      containerRef={leftEssayRef}
                      onShowTooltip={onShowTooltip}
                      onMoveTooltip={onMoveTooltip}
                      onHideTooltip={onHideTooltip}
                    />
                  </div>
                </div>

                {/* Right */}
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                  <div className="p-6 pb-4 border-b border-gray-100">
                    <div className="flex items-center justify-between gap-3">
                      <h2 className="text-lg font-semibold text-gray-900">{rightEssay.title}</h2>
                      <button
                        onClick={() => openReplace("right")}
                        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 text-sm text-gray-700"
                        title="Replace document"
                      >
                        <RefreshCw className="h-4 w-4" />
                        Replace
                      </button>
                    </div>

                    <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-600">
                      <span className="inline-flex items-center gap-1">
                        <Clock className="h-4 w-4" /> {rightEssay.minutes} min
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <FileText className="h-4 w-4" /> {rightEssay.words.toLocaleString()} words
                      </span>
                    </div>

                    {focusedMetricId ? (
                      <div className="mt-3 flex items-center gap-2 text-xs">
                        <span className="inline-flex items-center gap-2 px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200">
                          <Focus className="h-3.5 w-3.5" />
                          Focus: <span className="font-medium">{focusedMeta?.title || focusedMetricId}</span>
                        </span>
                        <button
                          onClick={() => setFocusedMetricId(null)}
                          className="text-xs px-2 py-1 rounded-full border border-gray-200 hover:bg-gray-50 text-gray-700"
                        >
                          Clear
                        </button>
                      </div>
                    ) : null}
                  </div>

                  <div className="p-6 py-2 bg-white h-[16rem] overflow-y-auto">
                    <div className="text-xs text-gray-500 mb-3">
                      Hover highlights to see metric tooltip.
                      {focusedMetricId ? <span className="ml-2">Showing only the focused metric highlights.</span> : null}
                    </div>
                    <HighlightedEssay
                      doc={rightDoc}
                      activeMetricIds={activeMetricIds}
                      containerRef={rightEssayRef}
                      onShowTooltip={onShowTooltip}
                      onMoveTooltip={onMoveTooltip}
                      onHideTooltip={onHideTooltip}
                    />
                  </div>
                </div>
              </div>

              {/* =========================
                  What changed in the writing (Coverage)
                  ========================= */}
              {selectedMetrics.length > 0 && (
                <div className="mt-6 bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900">What is different</h3>
                      <div className="mt-1 text-xs text-gray-500">
                        Coverage = <span className="font-medium text-gray-700">% of essay text highlighted</span> for a signal.
                      </div>
                    </div>

                    {focusedMetricId ? (
                      <button
                        onClick={() => setFocusedMetricId(null)}
                        className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-sm text-gray-700"
                      >
                        <X className="h-4 w-4" />
                        Clear focus
                      </button>
                    ) : null}
                  </div>

                  {/* Story cards (Improved | Consistent | Dropped) */}
                  <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <StoryCard
                      label="Biggest improvement (Left − Right)"
                      metricTitle={metricsSummary.mostIncreased?.def?.title}
                      category={metricsSummary.mostIncreased?.def?.category}
                      left={metricsSummary.mostIncreased?.left ?? 0}
                      right={metricsSummary.mostIncreased?.right ?? 0}
                      delta={metricsSummary.mostIncreased?.delta ?? 0}
                      tone="up"
                      isDisabled={!metricsSummary.mostIncreased}
                    />

                    <StoryCard
                      label="Most consistent (smallest change)"
                      metricTitle={metricsSummary.mostStable?.def?.title}
                      category={metricsSummary.mostStable?.def?.category}
                      left={metricsSummary.mostStable?.left ?? 0}
                      right={metricsSummary.mostStable?.right ?? 0}
                      delta={metricsSummary.mostStable?.delta ?? 0}
                      tone="flat"
                      isDisabled={!metricsSummary.mostStable}
                    />

                    <StoryCard
                      label="Biggest drop (Left − Right)"
                      metricTitle={metricsSummary.mostDecreased?.def?.title}
                      category={metricsSummary.mostDecreased?.def?.category}
                      left={metricsSummary.mostDecreased?.left ?? 0}
                      right={metricsSummary.mostDecreased?.right ?? 0}
                      delta={metricsSummary.mostDecreased?.delta ?? 0}
                      tone="down"
                      isDisabled={!metricsSummary.mostDecreased}
                    />
                  </div>

                  <div className="mt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-semibold text-gray-900">Top changes</div>
                        <div className="mt-0.5 text-xs text-gray-500">
                          Click “Focus” to show only that metric’s highlights in both essays.
                        </div>
                      </div>
                      <div className="text-xs text-gray-500">
                        Showing <span className="font-medium text-gray-700">{Math.min(8, coverageRows.length)}</span> of{" "}
                        <span className="font-medium text-gray-700">{coverageRows.length}</span>
                      </div>
                    </div>

                    <div className="mt-3 space-y-3">
                      {topChanges.length === 0 ? (
                        <div className="text-sm text-gray-600">No metrics selected.</div>
                      ) : (
                        topChanges.map((r) => (
                          <MetricRow
                            key={r.def.id}
                            row={r}
                            isFocused={focusedMetricId === r.def.id}
                            onFocusToggle={() => focusMetric(r.def.id, false)}
                            onShow={() => {
                              setFocusedMetricId(r.def.id);
                              setTimeout(() => scrollToFirstHighlight(r.def.id), 30);
                            }}
                          />
                        ))
                      )}
                    </div>

                    {coverageRows.length > 8 ? (
                      <div className="mt-4">
                        <button
                          onClick={() => setShowAllMetrics((v) => !v)}
                          className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-sm text-gray-700"
                        >
                          <ChevronDown className={`h-4 w-4 transition-transform ${showAllMetrics ? "rotate-180" : ""}`} />
                          {showAllMetrics ? "Hide all metrics" : "Show all metrics"}
                        </button>

                        {showAllMetrics ? (
                          <div className="mt-3 space-y-3">
                            {allRemaining.map((r) => (
                              <MetricRow
                                key={r.def.id}
                                row={r}
                                isFocused={focusedMetricId === r.def.id}
                                onFocusToggle={() => focusMetric(r.def.id, false)}
                                onShow={() => {
                                  setFocusedMetricId(r.def.id);
                                  setTimeout(() => scrollToFirstHighlight(r.def.id), 30);
                                }}
                              />
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
