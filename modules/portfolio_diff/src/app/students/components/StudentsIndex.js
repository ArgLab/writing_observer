"use client";

import {
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Clock,
  Download,
  FileText,
  Search,
  Users,
  AlertTriangle,
  TrendingUp,
  Minus,
  Loader,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import {
  useLOConnectionDataManager,
  LO_CONNECTION_STATUS,
} from "lo_event/lo_event/lo_assess/components/components.jsx";

const SEVEN_DAYS_SECS = 7 * 24 * 60 * 60;

function deepMerge(a, b) {
  const aObj = a && typeof a === "object" && !Array.isArray(a);
  const bObj = b && typeof b === "object" && !Array.isArray(b);
  if (aObj && bObj) {
    const out = { ...a };
    for (const k of Object.keys(b)) out[k] = deepMerge(a[k], b[k]);
    return out;
  }
  return b;
}

function latestLastAccessSec(availableDocuments) {
  if (!availableDocuments) return null;
  const docs = Object.values(availableDocuments);
  if (!docs.length) return null;

  let max = null;
  for (const d of docs) {
    const v = d?.last_access;
    if (v == null) continue;
    const n = Number(v);
    if (Number.isNaN(n)) continue;
    if (max == null || n > max) max = n;
  }
  return max;
}

function formatLastActivity(lastAccessSec) {
  if (!lastAccessSec) return "—";

  const nowSec = Date.now() / 1000;
  const diffSec = Math.max(0, nowSec - Number(lastAccessSec));

  const mins = Math.floor(diffSec / 60);
  const hrs = Math.floor(diffSec / 3600);
  const days = Math.floor(diffSec / 86400);

  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} min ago`;
  if (hrs < 24) return `${hrs} hr${hrs === 1 ? "" : "s"} ago`;
  if (days <= 14) return `${days} day${days === 1 ? "" : "s"} ago`;

  try {
    return new Date(Number(lastAccessSec) * 1000).toLocaleDateString();
  } catch {
    return "—";
  }
}

function riskBadgeClass(risk) {
  if (risk === "At-Risk") return "text-amber-800 bg-amber-100 ring-1 ring-inset ring-amber-200";
  if (risk === "Top Growth") return "text-emerald-800 bg-emerald-100 ring-1 ring-inset ring-emerald-200";
  if (risk === "Under Review") return "text-gray-800 bg-gray-100 ring-1 ring-inset ring-gray-200";
  return "text-gray-700 bg-gray-100 ring-1 ring-inset ring-gray-200";
}

function riskIcon(risk) {
  if (risk === "At-Risk") return <AlertTriangle className="h-3.5 w-3.5" />;
  if (risk === "Top Growth") return <TrendingUp className="h-3.5 w-3.5" />;
  if (risk === "Under Review") return <Loader className="h-3.5 w-3.5" />;
  return <Minus className="h-3.5 w-3.5" />;
}

export default function WritingPortfolioDashboard() {
  // table controls
  const [query, setQuery] = useState("");
  const [focusFilter, setFocusFilter] = useState("All"); // All | At-Risk | Top Growth
  const [pageSize, setPageSize] = useState(10);
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState("id");
  const [sortDir, setSortDir] = useState("asc");
  const [selected, setSelected] = useState(new Set());

  // ------ LO connection setup ------
  const decoded = {};
  decoded.course_id = "12345678901";
  decoded.student_id = [{ user_id: "tc-testcase-Alberta" }];
  decoded.document = [{ doc_id: "fake-google-doc-id-1" }];
  decoded.nlp_options = ["academic_language"];

  const dataScope = {
    wo: {
      execution_dag: "writing_observer",
      target_exports: ["roster", "document_list"],
      kwargs: decoded,
    },
  };

  const { data, errors, connection } = useLOConnectionDataManager({
    url: "ws://localhost:8888/wsapi/communication_protocol",
    dataScope,
  });

  // Merge roster + document_list if they are separate; otherwise use data.students if already merged.
  const studentsMap = useMemo(() => {
    if (!data) return {};

    // In many LO setups, patches are already applied into `data.students`
    const flatStudents = data?.students ?? {};
    if (flatStudents && Object.keys(flatStudents).length) return flatStudents;

    const rosterStudents = data?.wo?.roster?.students ?? {};
    const docsStudents = data?.wo?.document_list?.students ?? {};

    const merged = { ...rosterStudents };
    for (const [k, v] of Object.entries(docsStudents)) {
      merged[k] = deepMerge(merged[k] ?? {}, v ?? {});
    }
    return merged;
  }, [data]);

  // Build rows for the table
  const DATA = useMemo(() => {
    const list = Object.values(studentsMap || {});
    return list.map((s, idx) => {
      const profile = s?.profile ?? {};
      const nameObj = profile?.name ?? {};
      const availableDocuments = s?.availableDocuments ?? {};
      const docCount = Object.keys(availableDocuments).length;

      const lastAccessSec = latestLastAccessSec(availableDocuments);
      const lastActivity = formatLastActivity(lastAccessSec);

      const risk = "Under Review";

      return {
        id: s?.user_id ?? `student-${idx + 1}`,
        firstname: nameObj?.given_name || `Student ${idx + 1}`,
        lastname: nameObj?.family_name || "",
        avatar: "",
        documents: docCount,
        lastAccessSec: lastAccessSec ?? null, // for sorting
        lastActivity,
        risk,
      };
    });
  }, [studentsMap]);

  // Cards metrics
  const metrics = useMemo(() => {
    const totalStudents = DATA.length;

    let totalDocuments = 0;
    let studentsWithDocs = 0;
    let active7d = 0;

    const nowSec = Date.now() / 1000;

    for (const s of DATA) {
      const docs = Number(s.documents) || 0;
      totalDocuments += docs;
      if (docs > 0) studentsWithDocs += 1;

      const last = s.lastAccessSec ? Number(s.lastAccessSec) : null;
      if (last && nowSec - last <= SEVEN_DAYS_SECS) active7d += 1;
    }

    const coverage = totalStudents === 0 ? 0 : Math.round((studentsWithDocs / totalStudents) * 100);

    return { totalStudents, totalDocuments, active7d, coverage };
  }, [DATA]);

  const toggleSort = (key) => {
    if (key === sortKey) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const filtered = useMemo(() => {
    let rows = DATA.slice();

    // search
    if (query.trim()) {
      const q = query.toLowerCase();
      rows = rows.filter((r) => {
        const full = `${r.firstname || ""} ${r.lastname || ""}`.toLowerCase();
        return full.includes(q) || String(r.id).toLowerCase().includes(q);
      });
    }

    // focus tabs now drive the Risk Level column and filtering
    if (focusFilter === "At-Risk") rows = rows.filter((r) => r.risk === "At-Risk");
    if (focusFilter === "Top Growth") rows = rows.filter((r) => r.risk === "Top Growth");

    // sorting
    rows.sort((a, b) => {
      if (sortKey === "lastActivity") {
        const aT = a.lastAccessSec ?? -Infinity;
        const bT = b.lastAccessSec ?? -Infinity;
        if (aT < bT) return sortDir === "asc" ? -1 : 1;
        if (aT > bT) return sortDir === "asc" ? 1 : -1;
        return 0;
      }

      const A = a[sortKey];
      const B = b[sortKey];

      if (A < B) return sortDir === "asc" ? -1 : 1;
      if (A > B) return sortDir === "asc" ? 1 : -1;
      return 0;
    });

    return rows;
  }, [DATA, query, focusFilter, sortKey, sortDir]);

  // pagination
  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(page, totalPages);
  const start = (safePage - 1) * pageSize;
  const rows = filtered.slice(start, start + pageSize);

  const allIdsOnPage = (pageRows) => pageRows.map((s) => s.id);
  const allSelectedOnPage = rows.length > 0 && rows.every((r) => selected.has(r.id));

  // Loading state (improved)
  const isConnecting =
    connection?.status === LO_CONNECTION_STATUS.CONNECTING ||
    connection?.status === LO_CONNECTION_STATUS.RECONNECTING;

  const hasErrors = errors && Object.keys(errors).length > 0;
  const hasStudents = (DATA?.length ?? 0) > 0;

  const showLoading = !hasErrors && !hasStudents;

  console.log(hasErrors, isConnecting, hasStudents, data);
  console.log(DATA);

  const renderLoading = () => (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-3">
        <div className="h-3 w-3 rounded-full bg-emerald-600 animate-pulse" />
        <div className="text-sm text-gray-700">
          {isConnecting ? "Connecting to data source…" : "Loading roster…"}
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-24 rounded-2xl border border-gray-200 bg-gray-50 animate-pulse" />
        ))}
      </div>

      <div className="mt-6 h-10 rounded-md border border-gray-200 bg-gray-50 animate-pulse" />
      <div className="mt-3 space-y-2">
        {[0, 1, 2, 3, 4].map((i) => (
          <div key={i} className="h-12 rounded-md border border-gray-200 bg-gray-50 animate-pulse" />
        ))}
      </div>
    </div>
  );

  const renderError = () => (
    <div className="bg-white rounded-2xl shadow-sm border border-red-200 p-6">
      <div className="text-sm text-red-800 font-semibold">Failed to load dashboard data</div>
      <pre className="mt-2 text-xs text-red-700 whitespace-pre-wrap">{JSON.stringify(errors, null, 2)}</pre>
    </div>
  );

  // Export selected rows as CSV
  const exportSelectedToCsv = () => {
    const esc = (v) => {
      const s = v == null ? "" : String(v);
      const needsQuotes = /[",\n\r]/.test(s);
      const out = s.replace(/"/g, '""');
      return needsQuotes ? `"${out}"` : out;
    };

    const headers = ["ID", "First Name", "Last Name", "Documents", "Last Activity", "Risk Level"];

    const selectedRows = DATA.filter((r) => selected.has(r.id));
    const lines = [
      headers.map(esc).join(","),
      ...selectedRows.map((r) =>
        [r.id, r.firstname, r.lastname, r.documents, r.lastActivity, r.risk].map(esc).join(",")
      ),
    ];

    const csv = lines.join("\r\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `students_export_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();

    URL.revokeObjectURL(url);
  };

  // UPDATED: bulk bar shows ONLY Export (and performs CSV download)
  const renderBulkBar = () => (
    <div className="bg-emerald-50 border-t border-b border-emerald-200 px-4 py-2 flex items-center justify-between">
      <div className="text-sm text-emerald-900">
        <b>{selected.size}</b> selected
      </div>
      <div className="flex gap-2">
        <button
          onClick={exportSelectedToCsv}
          className="inline-flex items-center gap-2 px-3 py-1.5 text-sm rounded-md bg-white border border-gray-300 hover:bg-gray-50"
        >
          <Download className="h-4 w-4" /> Export
        </button>
      </div>
    </div>
  );

  const renderStatsRow = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-4">
      {/* Total Students */}
      <button className="text-left rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow transition relative w-full bg-gradient-to-br from-emerald-500 to-emerald-600">
        <p className="text-sm text-white mb-2 font-semibold">Total Students</p>
        <div className="flex justify-between items-center">
          <p className="text-4xl font-bold text-white">{metrics.totalStudents}</p>
          <div className="p-3 bg-emerald-50 rounded-xl">
            <Users className="h-6 w-6 text-emerald-600" />
          </div>
        </div>
      </button>

      {/* Total Documents */}
      <button className="text-left bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow transition relative w-full">
        <p className="text-sm text-gray-600 mb-2 font-semibold">Total Documents</p>
        <div className="flex justify-between items-center">
          <p className="text-4xl font-bold text-gray-900">{metrics.totalDocuments}</p>
          <div className="p-3 bg-emerald-50 rounded-xl">
            <FileText className="h-6 w-6 text-emerald-600" />
          </div>
        </div>
      </button>

      {/* Active last 7 days */}
      <button className="text-left bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow transition relative w-full">
        <p className="text-sm text-gray-600 mb-2 font-semibold">Active (Last 7 Days)</p>
        <div className="flex justify-between items-center">
          <p className="text-4xl font-bold text-gray-900">{metrics.active7d}</p>
          <div className="p-3 bg-emerald-50 rounded-xl">
            <Clock className="h-6 w-6 text-emerald-600" />
          </div>
        </div>
      </button>

      {/* Roster coverage */}
      <button className="text-left bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow transition relative w-full">
        <p className="text-sm text-gray-600 mb-2 font-semibold">Roster Coverage</p>
        <div className="flex justify-between items-center">
          <p className="text-4xl font-bold text-gray-900">{metrics.coverage}%</p>
          <div className="p-3 bg-emerald-50 rounded-xl">
            <CheckCircle className="h-6 w-6 text-emerald-600" />
          </div>
        </div>
      </button>
    </div>
  );

  const renderHeaderBar = () => (
    <div className="mb-4">
      <div className="flex flex-col gap-3 pt-4 pb-2 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Student Overview & Signals</h1>
          <p className="text-sm text-gray-600">Search for student or use the filter tabs to focus on a subset and review students' writing activities.</p>
        </div>

        {/* Tabs mapped to risk */}
        <div className="inline-flex rounded-full border border-gray-200 bg-white p-1 shadow-sm">
          {["All", "At-Risk", "Top Growth"].map((opt) => (
            <button
              key={opt}
              onClick={() => {
                setFocusFilter(opt);
                setPage(1);
              }}
              className={`px-3 py-1.5 text-sm rounded-full transition ${
                focusFilter === opt ? "bg-emerald-600 text-white" : "text-gray-700 hover:bg-gray-50"
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  const renderTable = () => (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 mb-8">
      <div className="px-6 py-4 border-b border-gray-200 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-gray-900">Students</h2>
          <span className="text-sm text-gray-500">Total: {total.toLocaleString()}</span>
        </div>

        <div className="flex w-full md:w-auto items-center gap-3">
          <div className="relative flex-1 md:flex-none">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              onKeyDown={(e) => e.stopPropagation()}
              onClick={(e) => e.stopPropagation()}
              className="w-full md:w-64 pl-8 pr-3 py-2 text-sm bg-white border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              placeholder="Search name or ID…"
              autoComplete="off"
              autoCorrect="off"
              spellCheck={false}
            />
          </div>
        </div>
      </div>

      {selected.size > 0 && renderBulkBar()}

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left w-[40px]">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 h-5 w-5"
                  checked={allSelectedOnPage}
                  onChange={(e) => {
                    const next = new Set(selected);
                    if (e.target.checked) allIdsOnPage(rows).forEach((id) => next.add(id));
                    else allIdsOnPage(rows).forEach((id) => next.delete(id));
                    setSelected(next);
                  }}
                />
              </th>

              {[
                { key: "id", label: "ID", align: "text-left" },
                { key: "firstname", label: "First Name", align: "text-left" },
                { key: "lastname", label: "Last Name", align: "text-left" },
                { key: "documents", label: "Documents", align: "text-center" },
                { key: "lastActivity", label: "Last Activity", align: "text-left" },
                { key: "risk", label: "Risk Level", align: "text-left" },
              ].map((c) => (
                <th
                  key={c.key}
                  className={`px-6 py-3 ${c.align} text-xs font-semibold text-gray-500 uppercase tracking-wider`}
                >
                  <button
                    onClick={() => toggleSort(c.key)}
                    className="inline-flex items-center gap-1"
                    aria-label={`Sort by ${c.label}`}
                  >
                    <span>{c.label}</span>
                    {sortKey === c.key ? (
                      sortDir === "asc" ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )
                    ) : (
                      <ChevronDown className="h-4 w-4 text-gray-300" />
                    )}
                  </button>
                </th>
              ))}

              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>

          <tbody className="bg-white divide-y divide-gray-200">
            {rows.map((student) => (
              <tr
                key={student.id}
                className="odd:bg-white even:bg-gray-50 hover:bg-emerald-50/40 transition-colors duration-150"
              >
                <td className="px-6 py-4">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 h-5 w-5"
                    checked={selected.has(student.id)}
                    onChange={(e) => {
                      const next = new Set(selected);
                      if (e.target.checked) next.add(student.id);
                      else next.delete(student.id);
                      setSelected(next);
                    }}
                  />
                </td>

                <td className="px-6 py-4">
                  <span className="text-sm text-gray-900">{student.id}</span>
                </td>

                <td className="px-6 py-4">
                  <div className="flex items-center">
                    <div className="h-10 w-10 rounded-full bg-emerald-100 flex items-center justify-center text-sm font-semibold text-emerald-700 mr-3">
                      {student.avatar}
                    </div>
                    <div className="text-sm font-medium text-gray-900">{student.firstname}</div>
                  </div>
                </td>

                <td className="px-6 py-4">
                  <span className="text-sm text-gray-900">{student.lastname}</span>
                </td>

                <td className="px-6 py-4 text-center">
                  <span className="text-sm text-gray-900">{student.documents}</span>
                </td>

                <td className="px-6 py-4">
                  <span className="text-sm text-gray-900">{student.lastActivity}</span>
                </td>

                <td className="px-6 py-4">
                  <span
                    className={`inline-flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-full ${riskBadgeClass(
                      student.risk
                    )}`}
                  >
                    {riskIcon(student.risk)}
                    {student.risk}
                  </span>
                </td>

                <td className="px-6 py-4 text-right">
                  <Link href={`students?student_id=${student.id}`}>
                    <button className="text-emerald-700 hover:text-emerald-900 font-medium text-sm">
                      View Writing Portfolio
                    </button>
                  </Link>
                </td>
              </tr>
            ))}

            {rows.length === 0 && (
              <tr>
                <td colSpan={8} className="px-6 py-10 text-center text-sm text-gray-500">
                  No students match your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="px-6 py-4 border-t border-gray-200">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <span>
              {total === 0 ? "0" : `${start + 1}–${Math.min(start + pageSize, total)} of ${total.toLocaleString()}`}
            </span>
            <span className="text-gray-300">•</span>
            <label className="text-gray-600">Rows per page</label>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="bg-white border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {[10, 25, 50, 100].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <button
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-40"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={safePage <= 1}
            >
              &lt;
            </button>
            <span className="text-sm text-gray-700">
              Page {safePage} of {totalPages}
            </span>
            <button
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-40"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={safePage >= totalPages}
            >
              &gt;
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Welcome header */}
      <div className="p-6 pb-2">
        <div className="rounded-2xl border border-gray-200 bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 shadow-sm">
          <div className="p-6 md:p-8 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-gray-900">
                Welcome back, Ms. Rodriguez! <span className="inline-block">👋</span>
              </h1>
              <p className="mt-2 text-gray-600">A snapshot of your class writing activity and progress.</p>

              <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-gray-500">
                <span className="inline-flex items-center gap-2 rounded-full bg-gray-100 px-3 py-1">📚 English 10A</span>
                <span className="inline-flex items-center gap-2 rounded-full bg-gray-100 px-3 py-1">📅 Fall 2025</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="p-6 space-y-4">
        {hasErrors ? renderError() : showLoading ? renderLoading() : (
          <>
            {renderStatsRow()}
            {renderHeaderBar()}
            {renderTable()}
          </>
        )}
      </div>
    </div>
  );
}
