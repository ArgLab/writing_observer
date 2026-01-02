"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeftRight,
  ChevronDown,
  FileText,
  Gauge,
  Languages,
  ListCollapse,
  MessageSquareText,
  MessagesSquare,
  Quote,
  Speech,
  Trash2,
  Users,
  WholeWord,
} from "lucide-react";

/* ---------------------- deterministic helpers ---------------------- */
const seedFrom = (s) => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = ((h ^ s.charCodeAt(i)) * 16777619) >>> 0;
  return h >>> 0;
};

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

/* =============================================================
   METRICS (FULL LIST) — matches EssayComparison
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

const ALL_KEYS = METRIC_DEFS.map((m) => m.id);
const CATEGORIES = Array.from(new Set(METRIC_DEFS.map((m) => m.category)));

const DEFAULT_PRESETS = {
  "Core (language + structure)": [
    "academic_language",
    "informal_language",
    "latinate_words",
    "transition_words",
    "citations",
    "sentences",
    "paragraphs",
  ],
  "Sources & Evidence": ["information_sources", "attributions", "citations", "quoted_words"],
};

const PRESETS_STORAGE_KEY = "wo_metric_presets_v1";

/* ---------------------- presets helpers ---------------------- */
function safeParseJSON(s) {
  try {
    return JSON.parse(s);
  } catch {
    return null;
  }
}

function normalizePresetMetrics(arr) {
  const uniq = Array.from(new Set((arr || []).filter(Boolean)));
  const known = new Set(ALL_KEYS);
  return uniq.filter((id) => known.has(id));
}

/* =============================================================
   MetricsPanel (updated to match EssayComparison sidebar)
   - Keeps backward compat with your existing call:
     <MetricsPanel metrics={metrics} setMetrics={setMetrics} ... />
   ============================================================= */

export function MetricsPanel({
  // Backward-compatible props
  metrics,
  setMetrics,

  // Optional UI knobs
  stickyTopClassName = "top-24",
  title = "Metrics",
}) {
  const selectedMetrics = Array.isArray(metrics) ? metrics : [];
  const setSelectedMetrics = typeof setMetrics === "function" ? setMetrics : () => {};

  /* ---------------------- Presets (stateful, deletable, creatable) ---------------------- */
  const [presets, setPresets] = useState(DEFAULT_PRESETS);
  const [presetName, setPresetName] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = window.localStorage.getItem(PRESETS_STORAGE_KEY);
    const parsed = raw ? safeParseJSON(raw) : null;

    if (parsed && typeof parsed === "object") {
      const merged = { ...DEFAULT_PRESETS };
      for (const [k, v] of Object.entries(parsed)) {
        if (!k) continue;
        merged[k] = normalizePresetMetrics(v);
      }
      setPresets(merged);
    } else {
      setPresets(DEFAULT_PRESETS);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(PRESETS_STORAGE_KEY, JSON.stringify(presets));
  }, [presets]);

  const createPreset = useCallback(() => {
    const name = (presetName || "").trim();
    if (!name) return;

    const arr = normalizePresetMetrics(selectedMetrics);
    if (!arr.length) return;

    setPresets((prev) => ({
      ...prev,
      [name]: arr,
    }));
    setPresetName("");
  }, [presetName, selectedMetrics]);

  const deletePreset = useCallback((name) => {
    setPresets((prev) => {
      const next = { ...prev };
      delete next[name];
      if (!Object.keys(next).length) return { ...DEFAULT_PRESETS };
      return next;
    });
  }, []);

  const applyPreset = useCallback(
    (name) => {
      const arr = presets?.[name] || [];
      setSelectedMetrics(normalizePresetMetrics(arr));
    },
    [presets, setSelectedMetrics]
  );

  /* ---------------------- Category collapse state ---------------------- */
  const [expanded, setExpanded] = useState(() => {
    const o = {};
    CATEGORIES.forEach((c) => (o[c] = true));
    return o;
  });

  const handleMetricToggle = useCallback(
    (id) => {
      setSelectedMetrics((prev) =>
        (prev || []).includes(id) ? prev.filter((x) => x !== id) : [...(prev || []), id]
      );
    },
    [setSelectedMetrics]
  );

  const selectedCount = selectedMetrics.length;

  return (
    <aside className="col-span-12 md:col-span-4 xl:col-span-3">
      <div
        className={`bg-white rounded-2xl border border-gray-200 p-5 shadow-sm sticky ${stickyTopClassName} h-fit`}
      >
        {/* -------- Presets -------- */}
        <div className="mb-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Presets</h3>
            <span className="text-xs text-gray-500">{Object.keys(presets || {}).length}</span>
          </div>

          <div className="mt-3 flex items-center gap-2">
            <input
              value={presetName}
              onChange={(e) => setPresetName(e.target.value)}
              placeholder="Preset name"
              className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <button
              onClick={createPreset}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-600 text-white text-sm hover:bg-emerald-700"
              title="Create preset from selected metrics"
              type="button"
            >
              + Preset
            </button>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(presets || {}).map(([name]) => (
              <div
                key={name}
                className="inline-flex items-center overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm"
              >
                <button
                  onClick={() => applyPreset(name)}
                  className="px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                  title="Apply preset"
                  type="button"
                >
                  {name}
                </button>
                <button
                  onClick={() => deletePreset(name)}
                  className="px-2 py-1.5 border-l border-gray-200 hover:bg-gray-50"
                  aria-label={`Delete preset ${name}`}
                  title="Delete preset"
                  type="button"
                >
                  <Trash2 className="h-4 w-4 text-gray-500" />
                </button>
              </div>
            ))}
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedMetrics(ALL_KEYS)}
              className="text-xs px-2 py-1 rounded-full border border-gray-200 hover:bg-gray-50"
              type="button"
            >
              Select All
            </button>
            <button
              onClick={() => setSelectedMetrics([])}
              className="text-xs px-2 py-1 rounded-full border border-gray-200 hover:bg-gray-50"
              type="button"
            >
              Deselect All
            </button>
          </div>
        </div>

        {/* -------- Metrics -------- */}
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <span className="text-xs text-gray-500">
            {selectedCount} / {METRIC_DEFS.length}
          </span>
        </div>

        <div className="max-h-[62vh] overflow-y-auto pr-1">
          <div className="space-y-2">
            {CATEGORIES.map((cat) => (
              <div key={cat}>
                <button
                  onClick={() => setExpanded((e) => ({ ...e, [cat]: !e[cat] }))}
                  className="w-full flex items-center justify-between text-left text-sm px-2 py-1.5 hover:bg-gray-50 rounded"
                  type="button"
                >
                  <span className="font-medium text-gray-700">{cat}</span>
                  <ChevronDown
                    className={`h-4 w-4 text-gray-500 transition-transform ${
                      expanded[cat] ? "" : "-rotate-90"
                    }`}
                  />
                </button>

                {expanded[cat] && (
                  <div className="mt-1 pl-2 space-y-1">
                    {METRIC_DEFS.filter((m) => m.category === cat).map((m) => (
                      <label
                        key={m.id}
                        className="flex items-center gap-2 px-2 py-1 text-sm rounded hover:bg-gray-50 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedMetrics.includes(m.id)}
                          onChange={() => handleMetricToggle(m.id)}
                          className="accent-emerald-600"
                        />
                        <m.icon className="h-3.5 w-3.5 text-gray-500" />
                        <span className="text-gray-700">{m.title}</span>
                        <span
                          className={`ml-auto inline-block h-3 w-3 rounded ${highlightClassForMetric(
                            m.id
                          )}`}
                          title="Highlight color"
                        />
                      </label>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
