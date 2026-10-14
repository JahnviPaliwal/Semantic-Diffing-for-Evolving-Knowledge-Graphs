import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Job } from '../api/types';
import { jobsApi } from '../api/client';

interface JobProgressBarProps {
  jobId: string;
  onCompleted?: (job: Job) => void;
  onError?: (error: string) => void;
  className?: string;
}

export const JobProgressBar: React.FC<JobProgressBarProps> = ({
  jobId,
  onCompleted,
  onError,
  className = '',
}) => {
  const [job, setJob] = useState<Job | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    let eventSource: EventSource | null = null;
    let pollingInterval: any = null;

    const startPolling = () => {
      pollingInterval = setInterval(async () => {
        try {
          const updated = await jobsApi.get(jobId);
          if (!isMounted) return;
          setJob(updated);
          if (updated.status === 'completed') {
            clearInterval(pollingInterval);
            onCompleted?.(updated);
          } else if (updated.status === 'failed') {
            clearInterval(pollingInterval);
            onError?.(updated.error_message || 'Job failed');
          }
        } catch (err: any) {
          if (!isMounted) return;
          setConnectionError(err.message || 'Error tracking job status');
        }
      }, 1500);
    };

    // Try SSE first
    try {
      const token = localStorage.getItem('access_token');
      const url = `/api/v1/jobs/${jobId}/events${token ? `?token=${encodeURIComponent(token)}` : ''}`;
      eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        if (!isMounted) return;
        try {
          const data: Job = JSON.parse(event.data);
          setJob(data);

          if (data.status === 'completed') {
            eventSource?.close();
            onCompleted?.(data);
          } else if (data.status === 'failed') {
            eventSource?.close();
            onError?.(data.error_message || 'Job failed');
          }
        } catch (e) {
          console.error('Failed to parse SSE payload', e);
        }
      };

      eventSource.onerror = () => {
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
        // Fall back to polling if SSE encounters issues
        if (isMounted) {
          startPolling();
        }
      };
    } catch {
      startPolling();
    }

    return () => {
      isMounted = false;
      if (eventSource) eventSource.close();
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, [jobId]);

  if (!job) {
    return (
      <div className={`p-4 bg-slate-900 border border-slate-800 rounded-lg flex items-center gap-3 ${className}`}>
        <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
        <span className="text-sm text-slate-300">Initializing background job #{jobId.slice(0, 8)}...</span>
      </div>
    );
  }

  const isCompleted = job.status === 'completed';
  const isFailed = job.status === 'failed';
  const progressPercent = Math.min(100, Math.max(0, job.progress || 0));

  return (
    <div className={`p-4 bg-slate-900 border border-slate-800 rounded-lg ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isCompleted ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : isFailed ? (
            <AlertTriangle className="w-5 h-5 text-rose-400" />
          ) : (
            <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
          )}
          <span className="text-sm font-medium text-slate-200">
            {job.stage || (isCompleted ? 'Processing complete' : 'Processing...')}
          </span>
        </div>
        <span className="text-xs font-semibold text-slate-400">
          {isCompleted ? '100%' : `${progressPercent}%`}
        </span>
      </div>

      <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full transition-all duration-300 rounded-full ${
            isCompleted
              ? 'bg-emerald-500'
              : isFailed
              ? 'bg-rose-500'
              : 'bg-indigo-500 animate-pulse'
          }`}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {job.error_message && (
        <p className="mt-2 text-xs text-rose-400 bg-rose-950/30 p-2 rounded border border-rose-900">
          {job.error_message}
        </p>
      )}

      {connectionError && !job.error_message && (
        <p className="mt-2 text-xs text-amber-400">
          Notice: Streaming updates re-established via polling fallback.
        </p>
      )}
    </div>
  );
};
