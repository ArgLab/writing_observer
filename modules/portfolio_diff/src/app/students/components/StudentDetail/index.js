"use client";

import { Calendar, FileText, GitCompareArrows, TrendingUp, Users } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useLOConnectionDataManager } from "lo_event/lo_event/lo_assess/components/components.jsx";

import StudentDetailCompare from "./StudentDetailCompare";
import StudentDetailGrowth from "./StudentDetailGrowth";

/* =============================================================
   CONSTANTS
   ============================================================= */

const MODES = { COMPARE: "compare", GROWTH: "growth" };

const STUDENTS_BREADCRUMB_HREF =
  "http://localhost:8888/wo_portfolio_diff/portfolio_diff/students";

const monthsShort = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const monthsLong = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const CATEGORY_KEYS = {
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

const iconForCategoryKey = (catKey) => {
  switch (catKey) {
    case "tone":
      return TrendingUp;
    case "dialogue":
      return Users;
    case "details":
      return FileText;
    default:
      return FileText;
  }
};

const METRIC_DEFS_RAW = [
  // language
  { id: "academic_language", title: "Academic Language", categoryKey: "language", function: "percent", desc: "Percent of tokens flagged academic" },
  { id: "informal_language", title: "Informal Language", categoryKey: "language", function: "percent", desc: "Percent of tokens flagged informal" },
  { id: "latinate_words", title: "Latinate Words", categoryKey: "language", function: "percent", desc: "Percent of tokens flagged latinate" },
  { id: "opinion_words", title: "Opinion Words", categoryKey: "language", function: "total", desc: "Total opinion-word signals" },
  { id: "emotion_words", title: "Emotion Words", categoryKey: "language", function: "percent", desc: "Percent emotion words" },

  // argumentation
  { id: "argument_words", title: "Argument Words", categoryKey: "argumentation", function: "percent", desc: "Percent argument words" },
  { id: "explicit_argument", title: "Explicit argument", categoryKey: "argumentation", function: "percent", desc: "Percent explicit argument markers" },

  // statements
  { id: "statements_of_opinion", title: "Statements of Opinion", categoryKey: "statements", function: "percent", desc: "Percent of sentences classified as opinion" },
  { id: "statements_of_fact", title: "Statements of Fact", categoryKey: "statements", function: "percent", desc: "Percent of sentences classified as fact" },

  // transitions
  { id: "transition_words", title: "Transition Words", categoryKey: "transitions", function: "counts", desc: "Transition counts (by type)" },
  { id: "positive_transition_words", title: "Positive Transition Words", categoryKey: "transitions", function: "total", desc: "Total positive transitions" },
  { id: "conditional_transition_words", title: "Conditional Transition Words", categoryKey: "transitions", function: "total", desc: "Total conditional transitions" },
  { id: "consequential_transition_words", title: "Consequential Transition Words", categoryKey: "transitions", function: "total", desc: "Total consequential transitions" },
  { id: "contrastive_transition_words", title: "Contrastive Transition Words", categoryKey: "transitions", function: "total", desc: "Total contrastive transitions" },
  { id: "counterpoint_transition_words", title: "Counterpoint Transition Words", categoryKey: "transitions", function: "total", desc: "Total counterpoint transitions" },
  { id: "comparative_transition_words", title: "Comparative Transition Words", categoryKey: "transitions", function: "total", desc: "Total comparative transitions" },
  { id: "cross_referential_transition_words", title: "Cross Referential Transition Words", categoryKey: "transitions", function: "total", desc: "Total cross-referential transitions" },
  { id: "illustrative_transition_words", title: "Illustrative Transition Words", categoryKey: "transitions", function: "total", desc: "Total illustrative transitions" },
  { id: "negative_transition_words", title: "Negative Transition Words", categoryKey: "transitions", function: "total", desc: "Total negative transitions" },
  { id: "emphatic_transition_words", title: "Emphatic Transition Words", categoryKey: "transitions", function: "total", desc: "Total emphatic transitions" },
  { id: "evenidentiary_transition_words", title: "Evenidentiary Transition Words", categoryKey: "transitions", function: "total", desc: "Total evidentiary transitions" },
  { id: "general_transition_words", title: "General Transition Words", categoryKey: "transitions", function: "total", desc: "Total general transitions" },
  { id: "ordinal_transition_words", title: "Ordinal Transition Words", categoryKey: "transitions", function: "total", desc: "Total ordinal transitions" },
  { id: "purposive_transition_words", title: "Purposive Transition Words", categoryKey: "transitions", function: "total", desc: "Total purposive transitions" },
  { id: "periphrastic_transition_words", title: "Periphrastic Transition Words", categoryKey: "transitions", function: "total", desc: "Total periphrastic transitions" },
  { id: "hypothetical_transition_words", title: "Hypothetical Transition Words", categoryKey: "transitions", function: "total", desc: "Total hypothetical transitions" },
  { id: "summative_transition_words", title: "Summative Transition Words", categoryKey: "transitions", function: "total", desc: "Total summative transitions" },
  { id: "introductory_transition_words", title: "Introductory Transition Words", categoryKey: "transitions", function: "total", desc: "Total introductory transitions" },

  // parts of speech
  { id: "adjectives", title: "Adjectives", categoryKey: "pos", function: "total", desc: "Total adjectives" },
  { id: "adverbs", title: "Adverbs", categoryKey: "pos", function: "total", desc: "Total adverbs" },
  { id: "nouns", title: "Nouns", categoryKey: "pos", function: "total", desc: "Total nouns" },
  { id: "proper_nouns", title: "Proper Nouns", categoryKey: "pos", function: "total", desc: "Total proper nouns" },
  { id: "verbs", title: "Verbs", categoryKey: "pos", function: "total", desc: "Total verbs" },
  { id: "numbers", title: "Numbers", categoryKey: "pos", function: "total", desc: "Total numbers" },
  { id: "prepositions", title: "Prepositions", categoryKey: "pos", function: "total", desc: "Total prepositions" },
  { id: "coordinating_conjunction", title: "Coordinating Conjunction", categoryKey: "pos", function: "total", desc: "Total coordinating conjunctions" },
  { id: "subordinating_conjunction", title: "Subordinating Conjunction", categoryKey: "pos", function: "total", desc: "Total subordinating conjunctions" },
  { id: "auxiliary_verb", title: "Auxiliary Verb", categoryKey: "pos", function: "total", desc: "Total auxiliary verbs" },
  { id: "pronoun", title: "Pronoun", categoryKey: "pos", function: "total", desc: "Total pronouns" },

  // sentence types
  { id: "simple_sentences", title: "Simple Sentences", categoryKey: "sentence_type", function: "total", desc: "Total simple sentences" },
  { id: "simple_with_complex_predicates", title: "Simple with Complex Predicates", categoryKey: "sentence_type", function: "total", desc: "Total simple (complex predicates)" },
  { id: "simple_with_compound_predicates", title: "Simple with Compound Predicates", categoryKey: "sentence_type", function: "total", desc: "Total simple (compound predicates)" },
  { id: "simple_with_compound_complex_predicates", title: "Simple with Compound Complex Predicates", categoryKey: "sentence_type", function: "total", desc: "Total simple (compound complex predicates)" },
  { id: "compound_sentences", title: "Compound Sentences", categoryKey: "sentence_type", function: "total", desc: "Total compound sentences" },
  { id: "complex_sentences", title: "Complex Sentences", categoryKey: "sentence_type", function: "total", desc: "Total complex sentences" },
  { id: "compound_complex_sentences", title: "Compound Complex Sentences", categoryKey: "sentence_type", function: "total", desc: "Total compound-complex sentences" },

  // source info
  { id: "information_sources", title: "Information Sources", categoryKey: "source_information", function: "percent", desc: "Percent source references" },
  { id: "attributions", title: "Attributions", categoryKey: "source_information", function: "percent", desc: "Percent attributions" },
  { id: "citations", title: "Citations", categoryKey: "source_information", function: "percent", desc: "Percent citations" },
  { id: "quoted_words", title: "Quoted Words", categoryKey: "source_information", function: "percent", desc: "Percent quoted words" },

  // dialogue
  { id: "direct_speech_verbs", title: "Direct Speech Verbs", categoryKey: "dialogue", function: "percent", desc: "Percent direct speech verbs" },
  { id: "indirect_speech", title: "Indirect Speech", categoryKey: "dialogue", function: "percent", desc: "Percent indirect speech" },

  // tone
  { id: "positive_tone", title: "Positive Tone", categoryKey: "tone", function: "percent", desc: "Percent positive tone" },
  { id: "negative_tone", title: "Negative Tone", categoryKey: "tone", function: "percent", desc: "Percent negative tone" },

  // details
  { id: "concrete_details", title: "Concrete Details", categoryKey: "details", function: "percent", desc: "Percent concrete details" },
  { id: "main_idea_sentences", title: "Main Idea Sentences", categoryKey: "details", function: "total", desc: "Total main idea sentences" },
  { id: "supporting_idea_sentences", title: "Supporting Idea Sentences", categoryKey: "details", function: "total", desc: "Total supporting idea sentences" },
  { id: "supporting_detail_sentences", title: "Supporting Detail Sentences", categoryKey: "details", function: "total", desc: "Total supporting detail sentences" },

  // other
  { id: "polysyllabic_words", title: "Polysyllabic Words", categoryKey: "other", function: "percent", desc: "Percent polysyllabic tokens" },
  { id: "low_frequency_words", title: "Low Frequency Words", categoryKey: "other", function: "percent", desc: "Percent low-frequency tokens" },
  { id: "sentences", title: "Sentences", categoryKey: "other", function: "total", desc: "Total sentences" },
  { id: "paragraphs", title: "Paragraphs", categoryKey: "other", function: "total", desc: "Total paragraphs" },
  { id: "character_trait_words", title: "Character Trait Words", categoryKey: "other", function: "percent", desc: "Percent character trait tokens" },
  { id: "in_past_tense", title: "In Past Tense", categoryKey: "other", function: "percent", desc: "Percent past tense scope" },
  { id: "explicit_claims", title: "Explicit Claims", categoryKey: "other", function: "percent", desc: "Percent explicit claims" },
  { id: "social_awareness", title: "Social Awareness", categoryKey: "other", function: "percent", desc: "Percent social awareness" },
];

const METRIC_BY_ID = Object.fromEntries(METRIC_DEFS_RAW.map((m) => [m.id, m]));

const DEFAULT_METRICS = [
  "academic_language",
  "informal_language",
  "latinate_words",
  "transition_words",
  "citations",
  "sentences",
  "paragraphs",
];

const GENRE_COLORS = { Document: "hsl(160 70% 40%)" };

/* =============================================================
   HELPERS
   ============================================================= */

const getStudentById = (id) => {
  const init = (id || "ST").slice(0, 2).toUpperCase();
  return {
    id,
    name: id ? String(id).replace(/[-_]/g, " ") : "Student",
    initials: init,
    avatarColor: "bg-gray-100",
    textColor: "text-gray-700",
    gradeLevel: "—",
    section: "—",
  };
};

const median = (arr) => {
  if (!arr.length) return 0;
  const a = [...arr].sort((x, y) => x - y);
  const mid = Math.floor(a.length / 2);
  return a.length % 2 ? a[mid] : (a[mid - 1] + a[mid]) / 2;
};
const mean = (a) => a.reduce((s, x) => s + x, 0) / Math.max(1, a.length);
const std = (a) => {
  if (a.length < 2) return 0;
  const m = mean(a);
  return Math.sqrt(mean(a.map((v) => (v - m) * (v - m))));
};
const slopePerIndex = (series) => {
  if (series.length < 2) return 0;
  const xs = series.map((p) => p.idx);
  const ys = series.map((p) => p.value);
  const xbar = mean(xs);
  const ybar = mean(ys);
  const num = xs.reduce((s, x, i) => s + (x - xbar) * (ys[i] - ybar), 0);
  const den = xs.reduce((s, x) => s + (x - xbar) * (x - xbar), 0) || 1;
  return num / den;
};

const safeNum = (v, fallback = 0) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
};

const sentenceSplit = (text) => {
  const t = (text || "").trim();
  if (!t) return [];
  return t.split(/(?<=[.!?])\s+/).filter(Boolean);
};

const wordSplit = (text) => {
  const t = (text || "").trim();
  if (!t) return [];
  return t
    .split(/\s+/)
    .map((w) => w.replace(/[^\p{L}\p{N}'-]+/gu, "").trim())
    .filter(Boolean);
};

const makePreviewFromText = (text, maxChars = 420) => {
  const t = (text || "").replace(/\s+/g, " ").trim();
  if (!t) return "";
  return t.length > maxChars ? `${t.slice(0, maxChars)}…` : t;
};

const formatDocTitle = (docId, meta) => {
  const fromMeta =
    meta?.title ||
    meta?.name ||
    meta?.doc_title ||
    meta?.document_title ||
    meta?.filename ||
    meta?.file_name;
  if (fromMeta && String(fromMeta).trim()) return String(fromMeta).trim();
  return docId ? String(docId).replace(/[-_]/g, " ") : "Document";
};

const getDocObjFromLO = (data2, studentID, docId) => {
  const s = data2?.students?.[studentID];
  const d1 = s?.documents?.[docId];
  if (d1 && typeof d1 === "object") return d1;
  const d2 = s?.docs?.[docId];
  if (d2 && typeof d2 === "object") return d2;
  const d3 = s?.doc_by_id?.[docId];
  if (d3 && typeof d3 === "object") return d3;
  const d4 = s?.documents?.[docId]?.value;
  if (d4 && typeof d4 === "object") return d4;
  return null;
};

const getDocTextFromLO = (data2, studentID, docId) => {
  const doc = getDocObjFromLO(data2, studentID, docId);
  const t = doc?.text;
  return typeof t === "string" ? t : "";
};

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

const buildEssaysFromDocs = ({ studentID, documentIDS, docsObj, data2 }) => {
  const out = (documentIDS || []).map((docId) => {
    const meta = docsObj?.[docId] || {};
    const lastAccess = meta?.last_access;
    const lastAccessMs =
      typeof lastAccess === "number"
        ? (lastAccess > 1e12 ? lastAccess : lastAccess * 1000)
        : null;

    const dateISO = lastAccessMs ? new Date(lastAccessMs).toISOString() : "";
    const dateObj = lastAccessMs ? new Date(lastAccessMs) : null;

    const dateStr = dateObj
      ? `${monthsShort[dateObj.getMonth()]} ${dateObj.getDate()}, ${dateObj.getFullYear()}`
      : "—";

    const category = dateObj ? `${monthsLong[dateObj.getMonth()]} ${dateObj.getFullYear()}` : "Unknown date";

    const doc = getDocObjFromLO(data2, studentID, docId);
    const text =
      doc?.text && typeof doc.text === "string" ? doc.text : getDocTextFromLO(data2, studentID, docId);

    const wordsArr = wordSplit(text);
    const words = wordsArr.length;

    const lowerWords = wordsArr.map((w) => w.toLowerCase());
    const uniqueWords = new Set(lowerWords).size;
    const lexicalDiversity = words ? Number(((uniqueWords / words) * 100).toFixed(1)) : 0;

    const sents = sentenceSplit(text);
    const sentences = Math.max(1, sents.length || 1);
    const avgSentenceLen = words ? Math.round(words / sentences) : 0;

    return {
      id: docId,
      title: formatDocTitle(docId, meta),
      date: dateStr,
      dateISO: dateISO || new Date(0).toISOString(),
      category,
      words,
      uniqueWords,
      lexicalDiversity,
      avgSentenceLen,
      grade: "—",
      preview: makePreviewFromText(text),
      tags: ["Document"], // ✅ never empty
      _doc: doc || { text },
    };
  });

  return out.sort((a, b) => new Date(b.dateISO) - new Date(a.dateISO));
};

/* =============================================================
   child: fetch docs by id & lift to parent
   ============================================================= */

function StudentDocsByIdFetcher({ studentID, documentIDS, setData2, setErrors2, setConnection2 }) {
  const dataScope2 = useMemo(() => {
    return {
      wo: {
        execution_dag: "writing_observer",
        target_exports: ["single_student_doc_by_id"],
        kwargs: {
          course_id: "12345678901",
          student_id: documentIDS.map(() => ({ user_id: studentID })),
          document: documentIDS.map((doc_id) => ({ doc_id })),
        },
      },
    };
  }, [studentID, documentIDS]);

  const { data, errors, connection } = useLOConnectionDataManager({
    url: "ws://localhost:8888/wsapi/communication_protocol",
    dataScope: dataScope2,
  });

  const prevSigsRef = useRef({ dataSig: "", errSig: "", connSig: "" });

  const dataSig = useMemo(() => {
    const studentsCount =
      data?.students && typeof data.students === "object" ? Object.keys(data.students).length : 0;
    const topKeys = data && typeof data === "object" ? Object.keys(data).length : 0;
    return `top:${topKeys}|students:${studentsCount}`;
  }, [data]);

  const errSig = useMemo(() => {
    if (!errors) return "noerr";
    if (Array.isArray(errors)) return `errarr:${errors.length}`;
    if (typeof errors === "object") return `errobj:${Object.keys(errors).length}`;
    return "err:1";
  }, [errors]);

  const connSig = useMemo(() => {
    if (!connection) return "noconn";
    const s = connection.status ?? connection.readyState ?? "unknown";
    const u = connection.url ?? "";
    return `status:${s}|url:${u}`;
  }, [connection]);

  useEffect(() => {
    const prev = prevSigsRef.current;

    if (prev.dataSig !== dataSig) {
      prev.dataSig = dataSig;
      setData2(data);
    }
    if (prev.errSig !== errSig) {
      prev.errSig = errSig;
      setErrors2(errors);
    }
    if (prev.connSig !== connSig) {
      prev.connSig = connSig;
      setConnection2(connection);
    }
  }, [dataSig, errSig, connSig, data, errors, connection, setData2, setErrors2, setConnection2]);

  return null;
}

/* =============================================================
   component
   ============================================================= */

export default function StudentDetail({ studentId }) {
  console.count("StudentDetail render");
  const router = useRouter();
  const searchParams = useSearchParams();

  const studentID = searchParams.get("student_id") || String(studentId);

  const [mode, setMode] = useState(MODES.COMPARE);
  const [selectedEssays, setSelectedEssays] = useState([]);

  const [cardsPerRow, setCardsPerRow] = useState(3);
  const [sortBy, setSortBy] = useState("date");
  const [search, setSearch] = useState("");

  const [filterTags, setFilterTags] = useState([]);
  const [tagOpen, setTagOpen] = useState(false);
  const [tagQuery, setTagQuery] = useState("");

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [metrics, setMetrics] = useState([...DEFAULT_METRICS]);

  const [openEssay, setOpenEssay] = useState(null);

  // quick range active state (for the pill buttons below)
  const [activeQuickRange, setActiveQuickRange] = useState("all"); // "all" | "3mo" | "6mo" | "9mo"

  // ------ LO connection #1: student_with_docs ------
  const dataScope = useMemo(() => {
    return {
      wo: {
        execution_dag: "writing_observer",
        target_exports: ["student_with_docs"],
        kwargs: {
          course_id: "12345678901",
          student_id: [{ user_id: studentID }],
        },
      },
    };
  }, [studentID]);

  const { data } = useLOConnectionDataManager({
    url: "ws://localhost:8888/wsapi/communication_protocol",
    dataScope,
  });

  const docsObj = data?.students?.[studentID]?.docs || {};

  const documentIDS = useMemo(() => {
    const ids = Object.keys(docsObj || {});
    ids.sort();
    return ids;
  }, [docsObj]);

  // ------ LO connection #2: single_student_doc_by_id (lifted state) ------
  const [data2, setData2] = useState(null);
  const [errors2, setErrors2] = useState(null);
  const [connection2, setConnection2] = useState(null);

  const essays = useMemo(() => {
    return buildEssaysFromDocs({
      studentID,
      documentIDS,
      docsObj,
      data2,
    });
  }, [studentID, documentIDS, docsObj, data2]);

  // Build metricSections INSIDE component (stable, and uses icon components)
  const metricSections = useMemo(() => {
    return Object.entries(CATEGORY_KEYS).map(([categoryKey, title]) => {
      const list = METRIC_DEFS_RAW.filter((m) => m.categoryKey === categoryKey).map((m) => m.id);
      return {
        title,
        icon: iconForCategoryKey(categoryKey),
        metrics: list,
      };
    });
  }, []);

  const metricByKey = useCallback((key) => {
    const raw = METRIC_BY_ID[key];
    if (!raw) return null;

    const get = (essay) => {
      const doc = essay?._doc || {};
      const direct = doc?.[key]?.metric;
      if (direct != null && !Number.isNaN(Number(direct))) return Number(direct);
      return metricCoveragePercent(doc, key);
    };

    return {
      key,
      label: raw.title,
      unit: raw.function === "percent" ? "%" : "",
      get,
      desc: raw.desc,
    };
  }, []);

  const essaysAscAll = useMemo(() => {
    return [...essays].sort((a, b) => new Date(a.dateISO) - new Date(b.dateISO));
  }, [essays]);

  const baselineByMetric = useMemo(() => {
    const out = {};
    for (const k of metrics) {
      const def = metricByKey(k);
      if (!def) continue;
      const vals = essaysAscAll.map((e) => safeNum(def.get(e), 0));
      out[k] = { median: median(vals), sd: std(vals) };
    }
    return out;
  }, [essaysAscAll, metrics, metricByKey]);

  const essaysInRangeAsc = useMemo(() => {
    const inRange = essaysAscAll.filter((e) => {
      const d = new Date(e.dateISO);
      const afterStart = !startDate || d >= new Date(startDate);
      const beforeEnd = !endDate || d <= new Date(endDate);
      return afterStart && beforeEnd;
    });
    return inRange;
  }, [essaysAscAll, startDate, endDate]);

  const getSeriesForMetric = useCallback(
    (key) => {
      const def = metricByKey(key);
      if (!def) return [];
      const base = baselineByMetric[key] || { median: 0, sd: 0 };

      return essaysInRangeAsc.map((e, idx) => {
        const raw = safeNum(def.get(e), 0);
        const delta = raw - base.median;
        const badge =
          base.sd > 0 ? (delta > 0.75 * base.sd ? "▲" : delta < -0.75 * base.sd ? "▼" : "●") : "●";
        return {
          idx,
          label: e.date,
          title: e.title,
          date: e.date,
          genre: e.tags[0],
          raw,
          value: delta,
          delta,
          badge,
          unit: def.unit,
        };
      });
    },
    [metricByKey, baselineByMetric, essaysInRangeAsc]
  );

  const getGenreSegments = () => {
    const segs = [];
    if (!essaysInRangeAsc.length) return segs;
    let start = 0;
    let current = essaysInRangeAsc[0].tags[0];
    for (let i = 1; i < essaysInRangeAsc.length; i++) {
      const g = essaysInRangeAsc[i].tags[0];
      if (g !== current) {
        segs.push({ x1: start, x2: i - 1, genre: current });
        current = g;
        start = i;
      }
    }
    segs.push({ x1: start, x2: essaysInRangeAsc.length - 1, genre: current });
    return segs;
  };
  const genreSegments = useMemo(() => getGenreSegments(), [essaysInRangeAsc]);

  const filteredEssaysCompare = useMemo(() => {
    const byTags = (e) => filterTags.length === 0 || filterTags.some((t) => (e.tags || []).includes(t));
    const bySearch = (e) => {
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      return (
        (e.title || "").toLowerCase().includes(q) ||
        (e.preview || "").toLowerCase().includes(q) ||
        (e.tags || []).some((t) => t.toLowerCase().includes(q))
      );
    };

    const sorted = [...essays].sort((a, b) => {
      if (sortBy === "words") return safeNum(b.words) - safeNum(a.words);
      if (sortBy === "title") return (a.title || "").localeCompare(b.title || "");
      return new Date(a.dateISO) < new Date(b.dateISO) ? 1 : -1;
    });

    return sorted.filter(byTags).filter(bySearch);
  }, [essays, filterTags, sortBy, search]);

  const groupedEssays = useMemo(() => {
    return filteredEssaysCompare.reduce((acc, essay) => {
      if (!acc[essay.category]) acc[essay.category] = [];
      acc[essay.category].push(essay);
      return acc;
    }, {});
  }, [filteredEssaysCompare]);

  const getGridCols = () => {
    switch (cardsPerRow) {
      case 1:
        return "grid-cols-1";
      case 2:
        return "grid-cols-2";
      case 3:
        return "grid-cols-3";
      case 4:
        return "grid-cols-4";
      case 5:
        return "grid-cols-5";
      case 6:
        return "grid-cols-6";
      default:
        return "grid-cols-4";
    }
  };

  const tagRef = useRef(null);
  useEffect(() => {
    const onClick = (e) => {
      if (tagRef.current && !tagRef.current.contains(e.target)) setTagOpen(false);
    };
    window.addEventListener("click", onClick);
    return () => window.removeEventListener("click", onClick);
  }, []);

  // only All time / 3 mo / 6 mo / 9 mo, and show active
  const applyQuickRange = (key) => {
    setActiveQuickRange(key);

    if (key === "all") {
      setStartDate("");
      setEndDate("");
      return;
    }

    if (!essaysAscAll.length) return;

    const last = new Date(essaysAscAll[essaysAscAll.length - 1].dateISO);
    const end = new Date(last);
    const start = new Date(last);

    if (key === "3mo") start.setMonth(start.getMonth() - 3);
    if (key === "6mo") start.setMonth(start.getMonth() - 6);
    if (key === "9mo") start.setMonth(start.getMonth() - 9);

    setStartDate(start.toISOString().slice(0, 10));
    setEndDate(end.toISOString().slice(0, 10));
  };

  // If user manually edits dates, reflect that by clearing the “active” pill highlight
  const onStartDateChange = (v) => {
    setStartDate(v);
    setActiveQuickRange(""); // custom
  };
  const onEndDateChange = (v) => {
    setEndDate(v);
    setActiveQuickRange(""); // custom
  };

  const clearFilters = () => {
    setFilterTags([]);
    setTagQuery("");
    setSearch("");
  };
  const isAnyFilter = filterTags.length > 0 || search.trim().length > 0;

  const handleEssaySelect = (essayId) => {
    if (mode !== MODES.COMPARE) return;
    setSelectedEssays((prev) => {
      if (prev.includes(essayId)) return prev.filter((id) => id !== essayId);
      if (prev.length >= 2) return prev;
      return [...prev, essayId];
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {documentIDS.length > 0 && (
        <StudentDocsByIdFetcher
          studentID={studentID}
          documentIDS={documentIDS}
          setData2={setData2}
          setErrors2={setErrors2}
          setConnection2={setConnection2}
        />
      )}

      <div className="p-6 pb-0 px-6 mx-auto">
        <nav className="text-sm text-gray-500 mb-4" aria-label="Breadcrumb">
          <ol className="inline-flex items-center space-x-1 md:space-x-3">
            <li className="inline-flex items-center">
              <a
                href={STUDENTS_BREADCRUMB_HREF}
                className="inline-flex gap-2 items-center text-gray-500 hover:text-emerald-600"
              >
                <Users className="h-4 w-4" />
                <span className="ms-1">Students</span>
              </a>
            </li>
            <li className="inline-flex items-center text-gray-400">›</li>
            <li className="inline-flex items-center text-gray-700 font-medium">
              <span className="inline-flex items-center gap-2">
                <span
                  className={`inline-flex items-center justify-center h-6 w-6 rounded-full ${
                    getStudentById(studentId).avatarColor
                  } ${getStudentById(studentId).textColor} text-xs font-semibold`}
                >
                  {getStudentById(studentId).initials}
                </span>
                {getStudentById(studentId).name}
              </span>
            </li>
          </ol>
        </nav>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-6">
          <div className="rounded-2xl p-6 py-4 text-white bg-gradient-to-br from-emerald-500 to-emerald-600 shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm/6 font-medium opacity-90">Essays in Portfolio</p>
              <FileText className="h-5 w-5 opacity-90" />
            </div>
            <p className="text-3xl font-extrabold">{documentIDS.length}</p>
            <p className="mt-1 text-xs/6 text-emerald-50">Available documents</p>
          </div>

          <div className="rounded-2xl p-6 py-4 bg-white border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-medium text-gray-600">Most Improved</p>
              <TrendingUp className="h-5 w-5 text-emerald-600" />
            </div>
            <p className="text-xl font-bold text-gray-900">—</p>
            <p className="mt-2 text-xs text-gray-500">Uses selected growth metrics</p>
          </div>

          <div className="rounded-2xl p-6 py-4 bg-white border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-medium text-gray-600">Biggest Decline</p>
              <TrendingUp className="h-5 w-5 text-gray-500" />
            </div>
            <p className="text-xl font-bold text-gray-900">—</p>
            <p className="mt-2 text-xs text-gray-500">Uses selected growth metrics</p>
          </div>

          <div className="rounded-2xl p-6 py-4 bg-white border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-medium text-gray-600">Avg. Time on Task</p>
              <TrendingUp className="h-5 w-5 text-emerald-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">—</p>
            <p className="mt-2 text-xs text-gray-500">(Not available yet)</p>
          </div>

          <div className="rounded-2xl p-6 py-4 bg-white border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-medium text-gray-600">Writing Fluency</p>
              <TrendingUp className="h-5 w-5 text-emerald-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">—</p>
            <p className="mt-2 text-xs text-gray-500">(Not available yet)</p>
          </div>
        </div>

        <div className="mb-4">
          <div className="inline-flex rounded-full border border-gray-200 bg-white p-1 shadow-sm" role="tablist">
            <button
              role="tab"
              aria-selected={mode === MODES.COMPARE}
              onClick={() => setMode(MODES.COMPARE)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm transition ${
                mode === MODES.COMPARE ? "bg-emerald-600 text-white" : "text-gray-700 hover:bg-gray-50"
              }`}
            >
              <GitCompareArrows className="h-4 w-4" /> Compare Essays
            </button>

            <button
              role="tab"
              aria-selected={mode === MODES.GROWTH}
              onClick={() => setMode(MODES.GROWTH)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm transition ${
                mode === MODES.GROWTH ? "bg-emerald-600 text-white" : "text-gray-700 hover:bg-gray-50"
              }`}
            >
              <TrendingUp className="h-4 w-4" /> Growth Over Time
            </button>
          </div>
        </div>

        {mode === MODES.GROWTH && (
          <div className="mb-2">
            <div className="flex flex-wrap items-center gap-3">
              <div className="inline-flex items-center gap-2 bg-white border border-gray-200 rounded-xl shadow-sm px-3 py-2">
                <Calendar className="h-4 w-4 text-gray-500" />
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => onStartDateChange(e.target.value)}
                  className="border-0 text-sm focus:outline-none"
                  aria-label="Start date"
                />
                <span className="text-gray-400">–</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => onEndDateChange(e.target.value)}
                  className="border-0 text-sm focus:outline-none"
                  aria-label="End date"
                />
              </div>

              {/* Apply active styling HERE (this is the date filter you referenced) */}
              <div className="inline-flex bg-white border border-gray-200 rounded-full p-1 shadow-sm">
                <button
                  type="button"
                  onClick={() => applyQuickRange("all")}
                  className={`px-3 py-1 text-sm rounded-full transition ${
                    activeQuickRange === "all" ? "bg-emerald-600 text-white" : "hover:bg-gray-50 text-gray-700"
                  }`}
                  aria-pressed={activeQuickRange === "all"}
                >
                  All time
                </button>

                <button
                  type="button"
                  onClick={() => applyQuickRange("3mo")}
                  className={`px-3 py-1 text-sm rounded-full transition ${
                    activeQuickRange === "3mo" ? "bg-emerald-600 text-white" : "hover:bg-gray-50 text-gray-700"
                  }`}
                  aria-pressed={activeQuickRange === "3mo"}
                >
                  Last 3 months
                </button>

                <button
                  type="button"
                  onClick={() => applyQuickRange("6mo")}
                  className={`px-3 py-1 text-sm rounded-full transition ${
                    activeQuickRange === "6mo" ? "bg-emerald-600 text-white" : "hover:bg-gray-50 text-gray-700"
                  }`}
                  aria-pressed={activeQuickRange === "6mo"}
                >
                  Last 6 months
                </button>

                <button
                  type="button"
                  onClick={() => applyQuickRange("9mo")}
                  className={`px-3 py-1 text-sm rounded-full transition ${
                    activeQuickRange === "9mo" ? "bg-emerald-600 text-white" : "hover:bg-gray-50 text-gray-700"
                  }`}
                  aria-pressed={activeQuickRange === "9mo"}
                >
                  Last 9 months
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="py-6 px-6 mx-auto">
        {mode === MODES.GROWTH ? (
          <StudentDetailGrowth
            studentID={studentID}
            metrics={metrics}
            setMetrics={setMetrics}
            metricSections={metricSections}
            metricByKey={metricByKey}
            getSeriesForMetric={getSeriesForMetric}
            slopePerIndex={slopePerIndex}
            GENRE_COLORS={GENRE_COLORS}
            genreSegments={genreSegments}
            essaysInRangeAsc={essaysInRangeAsc}
            loDocData={data2}
            loDocErrors={errors2}
            loDocConnection={connection2}
          />
        ) : (
          <StudentDetailCompare
            groupedEssays={groupedEssays}
            studentId={studentId}
            selectedEssays={selectedEssays}
            setSelectedEssays={setSelectedEssays}
            handleEssaySelect={handleEssaySelect}
            cardsPerRow={cardsPerRow}
            setCardsPerRow={setCardsPerRow}
            sortBy={sortBy}
            setSortBy={setSortBy}
            search={search}
            setSearch={setSearch}
            filterTags={filterTags}
            setFilterTags={setFilterTags}
            tagOpen={tagOpen}
            setTagOpen={setTagOpen}
            tagQuery={tagQuery}
            setTagQuery={setTagQuery}
            tagRef={tagRef}
            clearFilters={clearFilters}
            isAnyFilter={isAnyFilter}
            getGridCols={getGridCols}
            openEssay={openEssay}
            setOpenEssay={setOpenEssay}
            getStudentById={getStudentById}
            router={router}
            GENRE_COLORS={GENRE_COLORS}
            loDocData={data2}
            loDocErrors={errors2}
            loDocConnection={connection2}
            documentIDS={documentIDS}
          />
        )}
      </div>
    </div>
  );
}
