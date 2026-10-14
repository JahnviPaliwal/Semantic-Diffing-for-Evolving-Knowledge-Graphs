import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { projectsApi, versionsApi, diffApi } from '../api/client';
import { Project, Version, TemporalGraphResponse } from '../api/types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { TimelineVisualizer } from '../components/TimelineVisualizer';
import { JobProgressBar } from '../components/JobProgressBar';
import { 
  ArrowLeft, 
  UploadCloud, 
  GitCompare, 
  Calendar, 
  Layers, 
  FileText, 
  FileUp, 
  AlertCircle,
  ChevronRight,
  TrendingUp,
  Activity,
  Key
} from 'lucide-react';
import { useApiKey } from '../context/ApiKeyContext';

export const ProjectDetailPage: React.FC = () => {
  const { apiKey, hasApiKey } = useApiKey();
  const { projectId } = useParams<{ projectId: string }>();
  const numProjectId = parseInt(projectId || '0', 10);
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [timeline, setTimeline] = useState<TemporalGraphResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  // Diff computation state
  const [computingDiff, setComputingDiff] = useState(false);
  const [diffError, setDiffError] = useState<string | null>(null);

  const fetchProjectData = async () => {
    if (!numProjectId) return;
    try {
      setIsLoading(true);
      const [projData, timelineData] = await Promise.all([
        projectsApi.get(numProjectId),
        projectsApi.getTimeline(numProjectId).catch(() => null),
      ]);
      setProject(projData);
      setTimeline(timelineData);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || 'Failed to fetch project');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectData();
  }, [numProjectId]);

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!numProjectId || !uploadFile) return;

    try {
      setIsUploading(true);
      setError(null);

      const jobResponse = await versionsApi.upload(numProjectId, uploadFile);
      setActiveJobId(jobResponse.job_id);
      setUploadFile(null);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || 'Upload failed');
      setIsUploading(false);
    }
  };

  const handleJobCompleted = () => {
    setActiveJobId(null);
    setIsUploading(false);
    fetchProjectData();
  };

  const handleComputeDiff = async (v1Id: string, v2Id: string) => {
    if (!numProjectId) return;
    try {
      setComputingDiff(true);
      setDiffError(null);

      const res = await diffApi.compute(
        numProjectId,
        parseInt(v1Id, 10),
        parseInt(v2Id, 10)
      );

      navigate(`/projects/${numProjectId}/diff/${res.id}`);
    } catch (err: any) {
      setDiffError(err.response?.data?.error?.message || err.message || 'Failed to compute diff');
    } finally {
      setComputingDiff(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading project details..." />;
  }

  if (!project) {
    return (
      <div className="p-8 text-center text-slate-400">
        <AlertCircle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
        Project not found. <Link to="/" className="text-indigo-400 underline">Back to projects</Link>
      </div>
    );
  }

  const versions = project.versions || [];

  return (
    <div className="space-y-8">
      {/* Back button & Header */}
      <div>
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-indigo-400 mb-3 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Projects
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-2xl font-bold text-slate-100">{project.name}</h1>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              {project.description || 'No description provided.'}
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Calendar className="w-3.5 h-3.5" />
            Created {new Date(project.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>

      {/* Global Error Banner */}
      {(error || diffError) && (
        <div className="p-3 bg-rose-950/40 border border-rose-800 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error || diffError}</span>
        </div>
      )}

      {/* Computing Diff Spinner */}
      {computingDiff && (
        <div className="p-4 bg-indigo-950/40 border border-indigo-800 rounded-lg flex items-center gap-3 text-indigo-300 text-xs">
          <Activity className="w-4 h-4 animate-spin text-indigo-400" />
          <span>Computing semantic differential, running hybrid resolution, and categorizing domain severity...</span>
        </div>
      )}

      {/* Active background job progress */}
      {activeJobId && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Document Ingestion Pipeline</h3>
          <JobProgressBar
            jobId={activeJobId}
            onCompleted={handleJobCompleted}
            onError={(msg) => {
              setError(`Ingestion failed: ${msg}`);
              setActiveJobId(null);
              setIsUploading(false);
            }}
          />
        </div>
      )}

      {/* Evolution Timeline Visualizer */}
      {versions.length > 0 && (
        <TimelineVisualizer
          versions={versions}
          onDiffSelect={handleComputeDiff}
        />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Versions List & Upload Form */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
            <h3 className="text-base font-semibold text-slate-100 flex items-center justify-between mb-4">
              <span className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                Uploaded Versions ({versions.length})
              </span>
            </h3>

            {versions.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-xs">
                No versions uploaded yet. Upload a document below to extract its knowledge graph.
              </div>
            ) : (
              <div className="divide-y divide-slate-800">
                {versions.map((ver) => (
                  <div key={ver.id} className="py-3 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="px-2 py-1 text-xs font-bold rounded bg-indigo-950 text-indigo-300 border border-indigo-800 shrink-0">
                        v{ver.version_num}
                      </span>
                      <div className="min-w-0">
                        <div className="text-sm font-medium text-slate-200 truncate flex items-center gap-2">
                          <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          <span className="truncate">{ver.filename}</span>
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-3">
                          <span>{ver.node_count} entities</span>
                          <span>•</span>
                          <span>{ver.edge_count} relations</span>
                          <span>•</span>
                          <span>{new Date(ver.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                        {ver.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Upload New Version Form */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2 mb-3">
              <FileUp className="w-4 h-4 text-indigo-400" />
              Upload New Document Version
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Supported formats: <code className="text-indigo-300 bg-slate-950 px-1 py-0.5 rounded">.txt</code>,{' '}
              <code className="text-indigo-300 bg-slate-950 px-1 py-0.5 rounded">.pdf</code>,{' '}
              <code className="text-indigo-300 bg-slate-950 px-1 py-0.5 rounded">.docx</code>. Documents are parsed, chunked with character offsets, and extracted via the LangGraph 6-node state graph.
            </p>

            <div className="mb-4 p-2.5 rounded-lg border text-xs flex items-center justify-between bg-slate-950/60 border-slate-800">
              <div className="flex items-center gap-2">
                <Key className={`w-3.5 h-3.5 ${hasApiKey ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span className="text-slate-300">
                  LLM Extraction Engine:
                </span>
                {hasApiKey ? (
                  <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Groq LLM Active (Volatile Session)
                  </span>
                ) : (
                  <span className="text-slate-400">
                    Offline Heuristic & Template Mode (No key provided)
                  </span>
                )}
              </div>
              <span className="text-[11px] text-slate-400">
                {hasApiKey ? 'Wiped on refresh' : 'Set key via top navbar'}
              </span>
            </div>

            <form onSubmit={handleFileUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Document File
                </label>
                <div className="relative border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-lg p-4 text-center cursor-pointer transition-colors bg-slate-950">
                  <input
                    type="file"
                    accept=".txt,.pdf,.docx"
                    required
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <div className="flex items-center justify-center gap-2 text-xs text-slate-300">
                    <UploadCloud className="w-5 h-5 text-indigo-400" />
                    <span>{uploadFile ? uploadFile.name : 'Select or drag document here (.txt, .pdf, .docx)'}</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={isUploading || !uploadFile}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-2"
                >
                  {isUploading ? 'Uploading & Enqueuing...' : 'Ingest & Extract Graph'}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Right Column: Temporal Timeline Events */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
            <h3 className="text-base font-semibold text-slate-100 flex items-center justify-between mb-4">
              <span className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-indigo-400" />
                Ontological Change Events
              </span>
            </h3>

            {(!timeline?.timeline || timeline.timeline.length === 0) ? (
              <div className="text-center py-8 text-slate-400 text-xs">
                Upload at least two versions to observe temporal transitions and persistence intervals across versions.
              </div>
            ) : (
              <div className="space-y-3">
                {timeline.timeline.map((evt, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-200">{evt.event_type}</span>
                      <span className="text-[10px] text-slate-500">{evt.version_id}</span>
                    </div>
                    <p className="text-xs text-slate-400">{evt.description}</p>
                    <div className="flex items-center gap-3 text-[11px] text-slate-500 pt-1 border-t border-slate-800/60">
                      <span>+{evt.entities_added.length} added</span>
                      <span>-{evt.entities_removed.length} removed</span>
                      <span>~{evt.entities_renamed.length} renamed</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
