/**
 * Task API Service Functions
 */

import { request, API_BASE_URL } from './client';
import type {
  CreateTaskRequest,
  TaskResponse,
  TaskDetailResponse,
  TaskDiffResponse,
  ApprovalDecisionRequest,
  TaskEvent,
} from '../types/task';

export async function createTask(payload: CreateTaskRequest): Promise<TaskResponse> {
  return request<TaskResponse>('/api/v1/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function listTasks(limit: number = 50, offset: number = 0): Promise<TaskResponse[]> {
  return request<TaskResponse[]>(`/api/v1/tasks?limit=${limit}&offset=${offset}`, {
    method: 'GET',
  });
}

export async function getTask(taskId: string): Promise<TaskResponse> {
  return request<TaskResponse>(`/api/v1/tasks/${taskId}`, {
    method: 'GET',
  });
}

export async function getTaskDetail(taskId: string): Promise<TaskDetailResponse> {
  return request<TaskDetailResponse>(`/api/v1/tasks/${taskId}/detail`, {
    method: 'GET',
  });
}

export async function getTaskDiff(taskId: string): Promise<TaskDiffResponse> {
  return request<TaskDiffResponse>(`/api/v1/tasks/${taskId}/diff`, {
    method: 'GET',
  });
}

export async function approveTaskAction(
  taskId: string,
  approvalId: string,
  decision: ApprovalDecisionRequest
): Promise<{ task_id: string; approval_id: string; status: string }> {
  return request<{ task_id: string; approval_id: string; status: string }>(
    `/api/v1/tasks/${taskId}/approve?approval_id=${encodeURIComponent(approvalId)}`,
    {
      method: 'POST',
      body: JSON.stringify(decision),
    }
  );
}

export async function cancelTask(taskId: string): Promise<{ task_id: string; cancelled: boolean }> {
  return request<{ task_id: string; cancelled: boolean }>(`/api/v1/tasks/${taskId}/cancel`, {
    method: 'POST',
  });
}

/**
 * Connect to SSE stream for live task updates
 * Returns cleanup function to close the EventSource
 */
export function subscribeToTaskEvents(
  taskId: string,
  onEvent: (event: TaskEvent) => void,
  onError?: (err: Event) => void
): () => void {
  const url = `${API_BASE_URL}/api/v1/tasks/${taskId}/events`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (e) => {
    try {
      const data: TaskEvent = JSON.parse(e.data);
      onEvent(data);
    } catch (err) {
      console.error('Error parsing SSE message:', err, e.data);
    }
  };

  // Also listen for specific event types if server emits custom named events
  const commonEvents = [
    'task_started',
    'repository_analysis',
    'repository_analysis_completed',
    'planning',
    'planning_completed',
    'coding',
    'tool_execution',
    'testing',
    'testing_completed',
    'debugging',
    'debugging_completed',
    'review',
    'review_completed',
    'commit',
    'commit_completed',
    'pull_request',
    'pull_request_completed',
    'task_completed',
    'task_failed',
    'paused_for_approval',
  ];

  commonEvents.forEach((eventType) => {
    eventSource.addEventListener(eventType, (e: MessageEvent) => {
      try {
        const data: TaskEvent = JSON.parse(e.data);
        onEvent(data);
      } catch (err) {
        console.error(`Error parsing SSE event ${eventType}:`, err);
      }
    });
  });

  eventSource.onerror = (err) => {
    if (onError) {
      onError(err);
    }
  };

  return () => {
    eventSource.close();
  };
}
