// app/students/page.js
"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import StudentsIndex from "./components/StudentsIndex";
import StudentDetail from "./components/StudentDetail";

function StudentsPageContent() {
  const sp = useSearchParams();
  const studentId = sp.get("student_id");

  if (!studentId) return <StudentsIndex />;
  return <StudentDetail studentId={studentId} />;
}

export default function StudentsPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading…</div>}>
      <StudentsPageContent />
    </Suspense>
  );
}
