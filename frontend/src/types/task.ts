/**
 * TypeScript Type Definitions
 * Strictly aligned with Backend Pydantic Models & API Schemas
 */

export type TaskStatus =
  | 'pending'
  | 'running'
  | 'paused_for_approval'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type WorkflowPhase =
  | 'initialized'
  | 'repository_analysis'
  | 'planning'
  | 'coding'
  | 'testing'
  | 'debugging'
  | 'review'
  | 'commit'
  | 'pull_request'
  | 'finished';

export type ApprovalStatus =
  | 'not_required'
  | 'pending'
  | 'approved'
  | 'rejected';

export type ToolCategory =
  | 'repository'
  | 'editing'
  | 'execution'
  | 'git'
  | 'github';

export interface PlanStep {
  step_id: number;
  title: string;
  description: string;
  target_files: string[];
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | string;
  completed: boolean;
  notes?: string | null;
}

export interface AgentPlan {
  objective: string;
  architecture_overview: string;
  steps: PlanStep[];
  current_step_index: number;
}

export interface ToolExecutionRecord {
  call_id: string;
  tool_name: string;
  input_args: Record<string, any>;
  output?: string | null;
  error?: string | null;
  exit_code?: number | null;
  execution_time_ms: number;
  requires_approval: boolean;
  approval_status: ApprovalStatus;
  timestamp: string;
}

export interface TestExecutionSummary {
  command: string;
  passed: boolean;
  total_tests: number;
  failures: number;
  errors: number;
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_seconds: number;
}

export interface PendingApproval {
  approval_id?: string | null;
  id?: string | null;
  action_type: string;
  tool_name: string;
  action_payload: Record<string, any>;
  payload: Record<string, any>;
  reason: string;
  status: ApprovalStatus;
  reviewer_feedback?: string | null;
  created_at: string;
  requested_at?: string | null;
}

export interface CreateTaskRequest {
  repository_url: string;
  user_instruction: string;
  base_branch?: string;
  working_branch?: string;
  max_retries?: number;
}

export interface TaskResponse {
  id: string;
  repository_url: string;
  user_instruction: string;
  status: TaskStatus;
  current_phase: WorkflowPhase;
  base_branch: string;
  working_branch: string;
  commit_sha?: string | null;
  pull_request_url?: string | null;
  plan?: AgentPlan | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
  error_message?: string | null;
}

export interface TaskDetailResponse extends TaskResponse {
  tool_history: ToolExecutionRecord[];
  modified_files: string[];
  test_results: TestExecutionSummary[];
  pending_approval?: PendingApproval | null;
}

export interface ApprovalDecisionRequest {
  approved: boolean;
  feedback?: string | null;
}

export interface TaskEvent {
  task_id: string;
  event_type: string;
  phase: WorkflowPhase;
  message: string;
  data: Record<string, any>;
  timestamp: string;
}

export interface TaskDiffResponse {
  task_id: string;
  diff: string;
}
