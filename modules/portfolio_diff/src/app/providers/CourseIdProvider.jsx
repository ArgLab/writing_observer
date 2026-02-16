"use client";

import React, { createContext, useContext } from "react";
import { useCourseId } from "@/app/hooks/useCourseId";

/**
 * React context for sharing the current course ID state
 * across the component tree without prop drilling.
 */
const CourseIdContext = createContext(null);

/**
 * Provides the course ID context to all descendant components.
 *
 * Internally calls `useCourseId()` and exposes its return value
 * via React Context.
 *
 * Must wrap any component that calls `useCourseIdContext()`.
 */
export function CourseIdProvider({ children }) {
  const value = useCourseId();
  return <CourseIdContext.Provider value={value}>{children}</CourseIdContext.Provider>;
}

/**
 * Custom hook to access the course ID context.
 *
 * Throws an error if used outside of `CourseIdProvider`
 * to prevent silent failures and undefined access.
 */
export function useCourseIdContext() {
  const ctx = useContext(CourseIdContext);
  if (!ctx) throw new Error("useCourseIdContext must be used within CourseIdProvider");
  return ctx;
}
