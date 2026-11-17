import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

export interface JobStatus {
  job_id: string;
  status: string;
  stage: string | null;
  progress: Record<string, unknown>;
}

interface JobsContextValue {
  jobs: Record<string, JobStatus>;
  startJob: (jobId: string) => void;
  getJob: (jobId: string) => JobStatus | undefined;
  clearJob: (jobId: string) => void;
}

const JobsContext = createContext<JobsContextValue | undefined>(undefined);

export function JobsProvider({ children }: { children: React.ReactNode }) {
  const [jobs, setJobs] = useState<Record<string, JobStatus>>({});
  const pollingRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const pollJob = useCallback((jobId: string) => {
    const fetchJob = async () => {
      try {
        const resp = await fetch(`/api/v1/jobs/${jobId}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data: JobStatus = await resp.json();
        setJobs((prev) => ({ ...prev, [jobId]: data }));

        if (data.status === "completed" || data.status === "failed") {
          delete pollingRef.current[jobId];
          return;
        }
      } catch (e) {
        console.error(`Job ${jobId} polling failed:`, e);
      }
      pollingRef.current[jobId] = setTimeout(fetchJob, 2000);
    };
    fetchJob();
  }, []);

  const startJob = useCallback(
    (jobId: string) => {
      if (!pollingRef.current[jobId]) {
        pollJob(jobId);
      }
    },
    [pollJob],
  );

  const getJob = useCallback((jobId: string) => jobs[jobId], [jobs]);

  const clearJob = useCallback((jobId: string) => {
    if (pollingRef.current[jobId]) {
      clearTimeout(pollingRef.current[jobId]);
      delete pollingRef.current[jobId];
    }
    setJobs((prev) => {
      const next = { ...prev };
      delete next[jobId];
      return next;
    });
  }, []);

  // On mount, restore active jobs from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("aet_active_jobs");
    if (!stored) return;
    try {
      const ids: string[] = JSON.parse(stored);
      for (const id of ids) {
        startJob(id);
      }
    } catch {
      /* ignore */
    }
  }, [startJob]);

  // Persist active job IDs
  useEffect(() => {
    const activeIds = Object.entries(jobs)
      .filter(([, j]) => j.status !== "completed" && j.status !== "failed")
      .map(([id]) => id);
    localStorage.setItem("aet_active_jobs", JSON.stringify(activeIds));
  }, [jobs]);

  return (
    <JobsContext.Provider value={{ jobs, startJob, getJob, clearJob }}>
      {children}
    </JobsContext.Provider>
  );
}

export function useJobs() {
  const ctx = useContext(JobsContext);
  if (!ctx) throw new Error("useJobs must be used within JobsProvider");
  return ctx;
}