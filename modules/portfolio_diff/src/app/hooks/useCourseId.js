"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "wo_course_id";

/**
 * Parses hash params like:
 *   "#course_id=12345678901;tool=WritingObserver"
 * Supports separators: ";" or "&"
 */
function parseHashParams(hash) {
  const raw = (hash || "").replace(/^#/, "");
  const out = {};
  if (!raw) return out;

  const parts = raw.split(/[;&]/g).filter(Boolean);
  for (const part of parts) {
    const [k, ...rest] = part.split("=");
    if (!k) continue;
    const v = rest.join("=");
    out[decodeURIComponent(k)] = decodeURIComponent(v ?? "");
  }
  return out;
}

function getCourseIdFromHash() {
  if (typeof window === "undefined") return null;
  const params = parseHashParams(window.location.hash);
  return params.course_id || null;
}

function getCourseIdFromStorage() {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function setCourseIdToStorage(courseId) {
  if (typeof window === "undefined") return;
  try {
    if (courseId) window.localStorage.setItem(STORAGE_KEY, String(courseId));
    else window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore storage failures (private mode, etc.)
  }
}

/**
 * useCourseId
 * - If URL hash has course_id => use it AND persist it.
 * - Else fall back to localStorage.
 * - Listens to hash changes.
 */
export function useCourseId() {
  const [courseId, _setCourseId] = useState(null);

  // initialize + keep in sync with hash changes
  useEffect(() => {
    const sync = () => {
      const fromHash = getCourseIdFromHash();
      if (fromHash) {
        _setCourseId(fromHash);
        setCourseIdToStorage(fromHash);
        return;
      }

      const fromStorage = getCourseIdFromStorage();
      _setCourseId(fromStorage || null);
    };

    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  // allow manual overrides (and persist them)
  const setCourseId = useCallback((next) => {
    const value = next ? String(next) : null;
    _setCourseId(value);
    setCourseIdToStorage(value);
  }, []);

  const ready = useMemo(() => courseId !== undefined, [courseId]);

  console.log("courseId: ", courseId)

  return { courseId, setCourseId, ready };
}
