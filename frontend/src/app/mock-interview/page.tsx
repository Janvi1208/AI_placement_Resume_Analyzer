import { Suspense } from "react";
import MockInterviewClient from "./MockInterviewClient";

export default function MockInterviewPage() {
  return (
    <Suspense
      fallback={
        <main className="p-10 text-center text-gray-500">
          Loading interview...
        </main>
      }
    >
      <MockInterviewClient />
    </Suspense>
  );
}