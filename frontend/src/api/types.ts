export type SeverityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type ChangeType = 'ADDED' | 'REMOVED' | 'RENAMED' | 'MODIFIED' | 'UNCHANGED';

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface ExtractedEntity {
  name: string;
  type: string;
  source_quote?: string;
  char_offset_start?: number;
  char_offset_end?: number;
  chunk_id?: number;
  confidence?: number;
}

export interface ExtractedRelation {
  subject: string;
  predicate: string;
  object: string;
  source_quote?: string;
  confidence?: number;
}

export interface ExtractionGraph {
  version_id: string;
  doc_hash: string;
  raw_text?: string;
  entities: ExtractedEntity[];
  relations: ExtractedRelation[];
  timestamp?: string;
}

export interface Version {
  id: number;
  project_id: number;
  version_num: number;
  version_label: string;
  filename: string;
  doc_hash: string;
  status: string;
  node_count: number;
  edge_count: number;
  created_at: string;
  extracted_graph?: ExtractionGraph;
}

export interface Project {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  version_count: number;
  created_at: string;
  updated_at: string;
  versions?: Version[];
}

export interface DiffItem {
  element_type: 'node' | 'edge';
  change_type: ChangeType;
  canonical_name: string;
  previous_name?: string;
  source_quote?: string;
  chunk_reference?: string;
  confidence: number;
  severity: SeverityLevel;
  rationale?: string;
}

export interface DiffChanges {
  from_version: string;
  to_version: string;
  added_entities: string[];
  removed_entities: string[];
  renamed_entities: Array<{ from: string; to: string; confidence?: number }>;
  modified_entities: string[];
  unchanged_entities: string[];
  added_relations: string[][];
  removed_relations: string[][];
  modified_relations: Array<{ subject: string; old_predicate: string; new_predicate: string; object: string }>;
  unchanged_relations: string[][];
  items: DiffItem[];
  severity_summary: Record<string, number>;
  narrative?: string;
}

export interface DiffResponse {
  id: number;
  project_id: number;
  from_version_id: number;
  to_version_id: number;
  from_version_label: string;
  to_version_label: string;
  changes: DiffChanges;
  severity_summary: Record<string, number>;
  narrative?: string;
  created_at: string;
}

export interface Job {
  id: string;
  type: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  stage: string;
  result?: Record<string, any>;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface TimelineEvent {
  version_id: string;
  timestamp?: string;
  event_type: string;
  description: string;
  entities_added: string[];
  entities_removed: string[];
  entities_renamed: Array<{ from: string; to: string }>;
  relations_added: number;
  relations_removed: number;
  critical_changes: number;
  high_changes: number;
}

export interface TemporalNode {
  id: string;
  canonical_name: string;
  entity_type: string;
  valid_from: string;
  valid_to?: string;
  versions: string[];
}

export interface TemporalEdge {
  source: string;
  predicate: string;
  target: string;
  valid_from: string;
  valid_to?: string;
  versions: string[];
}

export interface TemporalGraphResponse {
  versions: string[];
  nodes: TemporalNode[];
  edges: TemporalEdge[];
  timeline: TimelineEvent[];
}

export interface EvalBenchmark {
  benchmark_summary: {
    total_pairs_evaluated: number;
    status: string;
    entity_f1_with_resolution: number;
    entity_f1_without_resolution_naive: number;
    false_add_remove_pairs_with_resolution: number;
    false_add_remove_pairs_without_resolution_naive: number;
  };
  pairs: Array<{
    pair_id: string;
    status: string;
    with_resolution: {
      entity_precision: number;
      entity_recall: number;
      entity_f1: number;
      relation_precision: number;
      relation_recall: number;
      relation_f1: number;
      false_add_remove_pairs: number;
    };
    without_resolution_naive: {
      entity_precision: number;
      entity_recall: number;
      entity_f1: number;
      relation_precision: number;
      relation_recall: number;
      relation_f1: number;
      false_add_remove_pairs: number;
    };
  }>;
}
