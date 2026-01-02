"use client";

import React, { useMemo, useState } from "react";
import {
  X,
  Calendar,
  Search,
  ChevronDown,
  Info,
  Maximize2,
  GitCompareArrows,
} from "lucide-react";

import { SingleEssayModal } from "./SingleEssayModel";

/* =========================================================
   Student Compare (Modal imported)
========================================================= */

export default function StudentDetailCompare({
  groupedEssays,
  studentId,

  selectedEssays,
  setSelectedEssays,
  handleEssaySelect,

  cardsPerRow,
  setCardsPerRow,
  sortBy,
  setSortBy,
  search,
  setSearch,
  filterTags,
  setFilterTags,
  tagOpen,
  setTagOpen,
  tagQuery,
  setTagQuery,
  tagRef,
  baseTags,
  clearFilters,
  isAnyFilter,

  getGridCols,
  getGradeColor,
  strengthAndFocusForEssay,

  loDocData,
  loDocErrors,
  loDocConnection,
  documentIDS,
}) {
  const safeGetGridCols = typeof getGridCols === "function" ? getGridCols : () => "grid-cols-3";
  const safeGetGradeColor =
    typeof getGradeColor === "function"
      ? getGradeColor
      : () => "bg-gray-50 text-gray-700 ring-1 ring-gray-200";
  const safeStrengthAndFocus =
    typeof strengthAndFocusForEssay === "function"
      ? strengthAndFocusForEssay
      : () => ({ strength: null, focus: null });
  const safeHandleEssaySelect = typeof handleEssaySelect === "function" ? handleEssaySelect : () => {};
  const safeSetSelectedEssays = typeof setSelectedEssays === "function" ? setSelectedEssays : () => {};

  // ---- Modal state (inside compare) ----
  const [openEssay, setOpenEssay] = useState(null);

  // ---- LO docs for compare list ----
  const loStudentID = String(studentId);
  const docsObj = loDocData?.students?.[loStudentID]?.documents || {};

  const expectedDocIds = Array.isArray(documentIDS) ? documentIDS : [];
  const receivedDocIds = Object.keys(docsObj || {});
  const hasAllExpectedDocs =
    expectedDocIds.length === 0 || expectedDocIds.every((id) => receivedDocIds.includes(id));

  const isDocsLoading =
    !!(loDocConnection &&
      (loDocConnection.loading || loDocConnection.isLoading || loDocConnection.status === "loading")) ||
    (expectedDocIds.length > 0 && !hasAllExpectedDocs);

  const isDocsEmpty = !isDocsLoading && Object.keys(docsObj || {}).length === 0;

  // ---- Build doc list (used for modal props too) ----
  const docList = useMemo(() => {
    return Object.entries(docsObj || {}).map(([docId, doc], index) => {
      const text = typeof doc?.text === "string" ? doc.text : "";
      const words = text ? text.trim().split(/\s+/).filter(Boolean).length : 0;

      const dateISO =
        doc?.dateISO || doc?.date_iso || doc?.date || doc?.submitted_at || doc?.created_at || "";

      const grade = doc?.grade ?? doc?.score ?? "";
      const tagsFromDoc = Array.isArray(doc?.tags)
        ? doc.tags
        : Array.isArray(doc?.meta?.tags)
          ? doc.meta.tags
          : ["Document"];

      return {
        id: docId,
        title: doc?.title || `Document ${index + 1}`,
        date: dateISO
          ? new Date(dateISO).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
          : "",
        dateISO: dateISO ? new Date(dateISO).toISOString() : "",
        words,
        grade: grade === null || grade === undefined ? "" : String(grade),
        preview: text,
        tags: tagsFromDoc.map(String),
        _raw: doc,
        _index: index + 1,
      };
    });
  }, [docsObj]);

  const allDocIds = useMemo(() => docList.map((d) => d.id).filter(Boolean), [docList]);

  const docMetaById = useMemo(() => {
    const m = new Map();
    for (const d of docList) m.set(String(d.id), d);
    return m;
  }, [docList]);

  // ---- tags base ----
  const safeBaseTags = useMemo(() => {
    if (Array.isArray(baseTags) && baseTags.length) return baseTags;
    const s = new Set();
    for (const d of docList) {
      for (const t of (Array.isArray(d?.tags) ? d.tags : [])) s.add(String(t));
    }
    return Array.from(s).sort((a, b) => a.localeCompare(b));
  }, [baseTags, docList]);

  // ---- filtering + sorting ----
  const filteredDocs = useMemo(() => {
    const q = String(search || "").trim().toLowerCase();
    const activeTags = Array.isArray(filterTags) ? filterTags : [];

    return (docList || [])
      .filter((d) => {
        if (activeTags.length > 0) {
          const dtags = Array.isArray(d?.tags) ? d.tags.map(String) : [];
          if (!activeTags.every((t) => dtags.includes(t))) return false;
        }

        if (q) {
          const hay = [
            d?.title || "",
            d?.preview || "",
            Array.isArray(d?.tags) ? d.tags.join(" ") : "",
            d?.grade || "",
            d?.date || "",
          ]
            .join(" ")
            .toLowerCase();
          if (!hay.includes(q)) return false;
        }
        return true;
      })
      .sort((a, b) => {
        const mode = String(sortBy || "date");
        if (mode === "words") return (Number(b.words) || 0) - (Number(a.words) || 0);
        if (mode === "title") return String(a.title || "").localeCompare(String(b.title || ""));
        if (mode === "grade") return (Number(b.grade) || 0) - (Number(a.grade) || 0);

        const ad = a?.dateISO ? new Date(a.dateISO).getTime() : 0;
        const bd = b?.dateISO ? new Date(b.dateISO).getTime() : 0;
        return bd - ad;
      });
  }, [docList, search, filterTags, sortBy]);

  const groupedDocs = useMemo(() => {
    return filteredDocs.reduce((acc, d) => {
      const key = d.dateISO
        ? new Date(d.dateISO).toLocaleString("en-US", { month: "long", year: "numeric" })
        : "Undated";
      (acc[key] ||= []).push(d);
      return acc;
    }, {});
  }, [filteredDocs]);

  const SkeletonCard = ({ i }) => (
    <div key={i} className="bg-white rounded-2xl border border-gray-200 shadow-sm">
      <div className="p-6 h-84 flex flex-col animate-pulse">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 rounded bg-gray-200" />
            <div className="h-5 w-40 rounded bg-gray-200" />
          </div>
          <div className="h-6 w-6 rounded bg-gray-200" />
        </div>
        <div className="flex-1 space-y-2 mb-3">
          <div className="h-4 w-full rounded bg-gray-200" />
          <div className="h-4 w-11/12 rounded bg-gray-200" />
          <div className="h-4 w-10/12 rounded bg-gray-200" />
        </div>
        <div className="flex flex-wrap gap-2 mt-auto">
          <div className="h-5 w-20 rounded-full bg-gray-200" />
          <div className="h-5 w-16 rounded-full bg-gray-200" />
        </div>
      </div>
    </div>
  );

  return (
    <>
      {isDocsLoading ? (
        <div className="mt-4">
          <div className={`grid ${safeGetGridCols()} gap-4`}>
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} i={i} />
            ))}
          </div>
        </div>
      ) : isDocsEmpty ? (
        <div className="mt-6 p-6 bg-white border border-gray-200 rounded-2xl">
          <div className="text-gray-900 font-semibold">No documents yet</div>
          <div className="text-sm text-gray-600 mt-1">We didn’t find any documents for this student.</div>
        </div>
      ) : (
        <>
          {Object.entries(groupedDocs).map(([category, list], index) => {
            const wordsAvg = Math.round(
              list.reduce((s, e) => s + (Number(e.words) || 0), 0) / Math.max(1, list.length)
            );

            return (
              <div key={category} className="mb-10">
                {index !== 0 && <hr className="border-t border-gray-200 mb-4" />}

                <div className="mb-2">
                  <div className="flex items-baseline justify-between">
                    <h2 className="text-xl font-semibold text-gray-900">{category}</h2>
                    <div className="text-sm text-gray-600">
                      {list.length} essays • Avg {wordsAvg.toLocaleString()} words
                    </div>
                  </div>

                  {index === 0 && (
                    <div className="mt-3 py-3 px-3 bg-white border border-gray-200 rounded-xl">
                      <div className="flex flex-wrap items-center gap-3">
                        <div className="relative" ref={tagRef}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (typeof setTagOpen === "function") setTagOpen((v) => !v);
                            }}
                            className="inline-flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50"
                          >
                            Tags{" "}
                            {Array.isArray(filterTags) && filterTags.length > 0 && (
                              <span className="text-gray-500">({filterTags.length})</span>
                            )}
                            <ChevronDown className="h-4 w-4 text-gray-500" />
                          </button>

                          {tagOpen && (
                            <div className="absolute z-20 mt-2 w-64 rounded-md border border-gray-200 bg-white shadow-lg p-2">
                              <div className="flex items-center gap-2 px-2 py-1 mb-2 rounded bg-gray-50">
                                <Search className="h-4 w-4 text-gray-400" />
                                <input
                                  placeholder="Search tags…"
                                  value={tagQuery || ""}
                                  onChange={(e) => typeof setTagQuery === "function" && setTagQuery(e.target.value)}
                                  className="w-full bg-transparent text-sm outline-none"
                                />
                              </div>
                              <div className="max-h-56 overflow-auto pr-1">
                                {safeBaseTags
                                  .filter((t) => String(t).toLowerCase().includes(String(tagQuery || "").toLowerCase()))
                                  .map((t) => (
                                    <label
                                      key={t}
                                      className="flex items-center gap-2 px-2 py-1 text-sm hover:bg-gray-50 rounded cursor-pointer"
                                    >
                                      <input
                                        type="checkbox"
                                        checked={Array.isArray(filterTags) ? filterTags.includes(t) : false}
                                        onChange={() => {
                                          if (typeof setFilterTags !== "function") return;
                                          setFilterTags((prev) => {
                                            const p = Array.isArray(prev) ? prev : [];
                                            return p.includes(t) ? p.filter((x) => x !== t) : [...p, t];
                                          });
                                        }}
                                        className="accent-emerald-600"
                                      />
                                      {t}
                                    </label>
                                  ))}
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="relative">
                          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                          <input
                            value={search || ""}
                            onChange={(e) => typeof setSearch === "function" && setSearch(e.target.value)}
                            placeholder="Search title, tags, text…"
                            className="pl-8 pr-3 py-2 border border-gray-300 rounded-md text-sm bg-white w-64 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                          />
                        </div>

                        <div className="flex-1" />

                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600">Sort by:</span>
                          <select
                            value={sortBy || "date"}
                            onChange={(e) => typeof setSortBy === "function" && setSortBy(e.target.value)}
                            className="px-3 py-1 border border-gray-300 rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                          >
                            <option value="date">Date</option>
                            <option value="grade">Grade</option>
                            <option value="words">Word Count</option>
                            <option value="title">Title</option>
                          </select>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600">Cards per row</span>
                          <select
                            value={cardsPerRow ?? 3}
                            onChange={(e) =>
                              typeof setCardsPerRow === "function" && setCardsPerRow(Number(e.target.value))
                            }
                            className="px-3 py-1 border border-gray-300 rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                          >
                            {[1, 2, 3, 4, 5, 6].map((n) => (
                              <option key={n} value={n}>
                                {n}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {isAnyFilter && (
                        <div className="flex flex-wrap items-center gap-2 mt-3">
                          {(Array.isArray(filterTags) ? filterTags : []).map((t) => (
                            <span
                              key={`tag-${t}`}
                              className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full"
                            >
                              Tag: {t}
                              <button
                                className="ml-1 rounded hover:bg-gray-200 p-0.5"
                                onClick={() => {
                                  if (typeof setFilterTags !== "function") return;
                                  setFilterTags((prev) => (Array.isArray(prev) ? prev.filter((x) => x !== t) : []));
                                }}
                                aria-label={`Remove ${t}`}
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </span>
                          ))}

                          {String(search || "").trim().length > 0 && (
                            <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">
                              Search: “{search}”
                              <button
                                className="ml-1 rounded hover:bg-gray-200 p-0.5"
                                onClick={() => typeof setSearch === "function" && setSearch("")}
                                aria-label="Clear search"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </span>
                          )}

                          <button
                            onClick={() => typeof clearFilters === "function" && clearFilters()}
                            className="ml-1 text-xs text-gray-600 underline underline-offset-2 hover:text-gray-800"
                          >
                            Clear all
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className={`mt-4 grid ${safeGetGridCols()} gap-4`}>
                  {list.map((essay) => {
                    const essayTags = Array.isArray(essay?.tags) ? essay.tags : [];
                    const isSelected = Array.isArray(selectedEssays) ? selectedEssays.includes(essay.id) : false;
                    const { strength, focus } = safeStrengthAndFocus(essay);

                    return (
                      <div
                        key={essay.id}
                        className={`bg-white rounded-2xl border transition-all cursor-pointer shadow-sm ${
                          isSelected
                            ? "border-emerald-500 ring-2 ring-emerald-200"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                        onClick={() => safeHandleEssaySelect(essay.id)}
                      >
                        <div className="p-6 h-84 flex flex-col">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => safeHandleEssaySelect(essay.id)}
                                className="w-5 h-5 accent-emerald-600"
                                onClick={(e) => e.stopPropagation()}
                                aria-label={`Select ${essay.title}`}
                              />
                              <h3 className="font-bold text-lg text-gray-900 leading-snug">{essay.title}</h3>
                            </div>

                            <button
                              className="p-1 rounded hover:bg-gray-100"
                              aria-label="Expand essay details"
                              onClick={(e) => {
                                e.stopPropagation();
                                const meta = docMetaById.get(String(essay.id));
                                setOpenEssay({
                                  docId: essay.id,
                                  title: meta?.title || essay.title || "Document",
                                  docIndex: meta?._index || null,
                                  grade: meta?.grade || essay.grade || "",
                                  words: Number(meta?.words ?? essay.words ?? 0),
                                  date: meta?.date || essay.date || "",
                                });
                              }}
                            >
                              <Maximize2 className="h-4 w-4 text-gray-500" />
                            </button>
                          </div>

                          <div className="flex items-center justify-between mb-3">
                            <p className="text-sm text-gray-600 flex items-center gap-2">
                              <Calendar className="w-4 h-4" />
                              {essay.date || "Unknown date"}
                            </p>
                            <div className="flex items-center gap-3">
                              <span className="text-sm text-gray-600">
                                {(Number(essay.words) || 0).toLocaleString()} words
                              </span>
                            </div>
                          </div>

                          <div className="flex-1 overflow-hidden mb-3">
                            <p className="text-sm text-gray-700 leading-relaxed line-clamp-5">{essay.preview || ""}</p>
                          </div>

                          <div className="flex flex-wrap gap-2 mb-3">
                            {strength && (
                              <span className="px-2 py-1 bg-emerald-50 text-emerald-800 text-xs rounded-full ring-1 ring-emerald-200">
                                Strength: {String(strength.label || "").split("(")[0].trim()}{" "}
                                {Number(strength.delta) > 0 ? "▲" : ""}
                              </span>
                            )}
                            {focus && (
                              <span className="px-2 py-1 bg-amber-50 text-amber-800 text-xs rounded-full ring-1 ring-amber-200">
                                Focus: {String(focus.label || "").split("(")[0].trim()}{" "}
                                {Number(focus.delta) < 0 ? "▼" : ""}
                              </span>
                            )}
                          </div>

                          <div className="flex flex-wrap gap-1 mt-auto">
                            {essayTags.map((tag, i) => (
                              <span
                                key={`${essay.id}-tag-${tag}-${i}`}
                                className="px-2 py-1 text-xs rounded-full ring-1 bg-green-200 border-green-700"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </>
      )}

      {Array.isArray(selectedEssays) && selectedEssays.length < 2 && (
        <div className="px-6 mx-auto bg-emerald-50 border-t border-emerald-200 py-3">
          <div className="flex items-start gap-3 text-emerald-900 text-sm">
            <Info className="h-4 w-4 mt-0.5" />
            <p>Tip: click cards or use the checkboxes to add essays to the selection tray (max 2).</p>
          </div>
        </div>
      )}

      <div className="sticky bottom-0 inset-x-0 bg-emerald-700 text-white px-6 py-3 shadow-[0_-2px_10px_rgba(0,0,0,0.08)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-32 h-2 bg-white/25 rounded overflow-hidden">
              <div
                className="h-full bg-white"
                style={{
                  width: `${(Math.min(2, Array.isArray(selectedEssays) ? selectedEssays.length : 0) / 2) * 100}%`,
                }}
              />
            </div>

            <span className="text-sm opacity-90">
              Selected {Array.isArray(selectedEssays) ? selectedEssays.length : 0}/2
            </span>

            <div className="flex items-center gap-2">
              {[0, 1].map((i) => {
                const id = Array.isArray(selectedEssays) ? selectedEssays[i] : undefined;
                return (
                  <div
                    key={i}
                    className={`h-8 px-3 rounded-full flex items-center gap-2 ${
                      id ? "bg-white text-emerald-700" : "bg-emerald-600 text-white/90"
                    }`}
                  >
                    <span className="text-xs font-medium">{id ? `#${id}` : "—"}</span>
                    {id && (
                      <button
                        className="p-0.5 rounded hover:bg-emerald-100"
                        onClick={() =>
                          safeSetSelectedEssays((prev) => (Array.isArray(prev) ? prev.filter((x) => x !== id) : []))
                        }
                        aria-label="Remove from selection"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>

            <button
              className="ml-2 text-sm underline decoration-white/50 underline-offset-2 hover:opacity-90"
              onClick={() => safeSetSelectedEssays([])}
            >
              Clear
            </button>
          </div>

          <button
            onClick={() => {
              const ids = Array.isArray(selectedEssays) ? selectedEssays.join(",") : "";
              const targetPath = "students/compare";
              const query = `?ids=${ids}&student_id=${studentId}`;
              window.location.assign(targetPath + query);
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-md font-semibold ${
              Array.isArray(selectedEssays) && selectedEssays.length >= 2
                ? "bg-white text-emerald-700 hover:bg-emerald-50"
                : "bg-white/30 text-white/80 cursor-not-allowed"
            }`}
            disabled={!(Array.isArray(selectedEssays) && selectedEssays.length >= 2)}
          >
            <GitCompareArrows className="h-4 w-4" />
            Compare Essays
          </button>
        </div>
      </div>

      {openEssay?.docId && (
        <SingleEssayModal
          studentKey={loStudentID}
          docId={openEssay.docId}
          docIds={allDocIds}
          docTitle={openEssay.title}
          docIndex={openEssay.docIndex}
          initialWords={openEssay.words}
          subtitleDate={openEssay.date}
          onClose={() => setOpenEssay(null)}
        />
      )}
    </>
  );
}
