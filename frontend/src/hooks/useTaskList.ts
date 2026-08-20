/**
 * Hook to fetch and manage task list
 */

import { useState, useEffect, useCallback } from 'react';
import { listTasks } from '../api/tasks';
import type { TaskResponse } from '../types/task';

export function useTaskList(autoRefresh: boolean = true, refreshIntervalMs: number = 5000) {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const data = await listTasks(50, 0);
      setTasks(data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch task list:', err);
      setError(err.message || 'Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();

    if (!autoRefresh) return;

    const interval = setInterval(fetchTasks, refreshIntervalMs);
    return () => clearInterval(interval);
  }, [fetchTasks, autoRefresh, refreshIntervalMs]);

  return {
    tasks,
    loading,
    error,
    refresh: fetchTasks,
  };
}
