/**
 * Hook to manage real-time task detail with SSE and polling fallback
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  getTaskDetail,
  getTaskDiff,
  subscribeToTaskEvents,
  approveTaskAction,
  cancelTask,
} from '../api/tasks';
import type { TaskDetailResponse, TaskEvent } from '../types/task';

export function useTaskDetail(taskId: string | null) {
  const [task, setTask] = useState<TaskDetailResponse | null>(null);
  const [diff, setDiff] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [diffLoading, setDiffLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  const isMountedRef = useRef<boolean>(true);
  const isTerminalRef = useRef<boolean>(false);

  // Determine if task is finished
  const isFinished = task
    ? ['completed', 'failed', 'cancelled'].includes(task.status)
    : false;

  isTerminalRef.current = isFinished;

  const fetchDetail = useCallback(async (silent: boolean = false) => {
    if (!taskId) return;
    if (!silent) setLoading(true);

    try {
      const data = await getTaskDetail(taskId);
      if (isMountedRef.current) {
        setTask(data);
        setError(null);
      }
    } catch (err: any) {
      if (isMountedRef.current) {
        console.error('Failed to fetch task detail:', err);
        setError(err.message || 'Failed to load task details');
      }
    } finally {
      if (isMountedRef.current && !silent) {
        setLoading(false);
      }
    }
  }, [taskId]);

  const fetchDiff = useCallback(async () => {
    if (!taskId) return;
    setDiffLoading(true);
    try {
      const data = await getTaskDiff(taskId);
      if (isMountedRef.current) {
        setDiff(data.diff);
      }
    } catch (err) {
      console.warn('Failed to fetch diff:', err);
    } finally {
      if (isMountedRef.current) {
        setDiffLoading(false);
      }
    }
  }, [taskId]);

  // Initial load & Polling fallback for active tasks
  useEffect(() => {
    if (!taskId) return;
    isMountedRef.current = true;

    fetchDetail(false);
    fetchDiff();

    // Polling interval (2.5s for active tasks, disabled once finished)
    const pollInterval = setInterval(() => {
      if (!isTerminalRef.current && isMountedRef.current) {
        fetchDetail(true);
        fetchDiff();
      }
    }, 2500);

    return () => {
      isMountedRef.current = false;
      clearInterval(pollInterval);
    };
  }, [taskId, fetchDetail, fetchDiff]);

  // SSE Real-Time Stream Subscription
  useEffect(() => {
    if (!taskId || isFinished) return;

    const unsubscribe = subscribeToTaskEvents(
      taskId,
      (event: TaskEvent) => {
        if (!isMountedRef.current) return;
        setEvents((prev) => [...prev, event]);

        // Immediate lightweight state update from event
        setTask((prev) => {
          if (!prev) return prev;
          const updated = { ...prev, current_phase: event.phase };
          if (event.event_type === 'task_completed') {
            updated.status = 'completed';
          } else if (event.event_type === 'task_failed') {
            updated.status = 'failed';
            if (event.data?.error) updated.error_message = event.data.error;
          } else if (event.event_type === 'paused_for_approval') {
            updated.status = 'paused_for_approval';
          }
          return updated;
        });

        // Trigger fresh detail fetch on key milestone events
        if (
          [
            'tool_execution',
            'planning_completed',
            'testing_completed',
            'debugging_completed',
            'review_completed',
            'commit_completed',
            'pull_request_completed',
            'task_completed',
            'task_failed',
            'paused_for_approval',
          ].includes(event.event_type)
        ) {
          fetchDetail(true);
          fetchDiff();
        }
      },
      (err) => {
        console.debug('SSE connection closed or reconnecting:', err);
      }
    );

    return () => {
      unsubscribe();
    };
  }, [taskId, isFinished, fetchDetail, fetchDiff]);

  // Human Approval Action
  const submitApproval = async (approvalId: string, approved: boolean, feedback?: string) => {
    if (!taskId) return;
    setActionLoading(true);
    try {
      await approveTaskAction(taskId, approvalId, { approved, feedback });
      await fetchDetail(true);
    } catch (err: any) {
      console.error('Failed to submit approval:', err);
      throw err;
    } finally {
      setActionLoading(false);
    }
  };

  // Cancel Task Action
  const submitCancel = async () => {
    if (!taskId) return;
    setActionLoading(true);
    try {
      await cancelTask(taskId);
      await fetchDetail(true);
    } catch (err: any) {
      console.error('Failed to cancel task:', err);
      throw err;
    } finally {
      setActionLoading(false);
    }
  };

  return {
    task,
    diff,
    loading,
    diffLoading,
    error,
    events,
    actionLoading,
    isFinished,
    refresh: () => {
      fetchDetail(false);
      fetchDiff();
    },
    submitApproval,
    submitCancel,
  };
}
