import MockInterviewClient from "./MockInterviewClient";

interface MockInterviewPageProps {
  searchParams: Promise<{
    analysis_id?: string;
  }>;
}

export default async function MockInterviewPage({
  searchParams,
}: MockInterviewPageProps) {
  const params = await searchParams;
  const analysisId = params.analysis_id ?? null;

  return <MockInterviewClient analysisId={analysisId} />;
}