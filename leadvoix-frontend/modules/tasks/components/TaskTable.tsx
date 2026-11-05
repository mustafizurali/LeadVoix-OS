"use client";

import { CheckSquare, Edit2, Trash2, Calendar, User as UserIcon } from "lucide-react";
import type { Task } from "../types/task.types";
import {
  SecondaryButton,
  DangerButton,
  StatusBadge,
  TableSkeleton,
  EmptyState,
} from "@/components/crm";

interface TaskTableProps {
  tasks: Task[];
  isLoading: boolean;
  isError: boolean;
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
}

export default function TaskTable({
  tasks,
  isLoading,
  isError,
  onEdit,
  onDelete,
}: TaskTableProps) {
  if (isLoading) {
    return <TableSkeleton rows={5} cols={6} />;
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-6 text-sm text-rose-400">
        Failed to load tasks. Please refresh the page.
      </div>
    );
  }

  if (!tasks || tasks.length === 0) {
    return (
      <EmptyState
        title="No tasks found"
        description="All action items and follow-ups are up to date. Create a new task to stay organized."
        icon={CheckSquare}
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-[#273449] bg-[#151D32] shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-[#273449] text-left text-sm">
          <thead className="bg-[#0E1528] text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
            <tr>
              <th className="px-6 py-3.5">Task Title</th>
              <th className="px-6 py-3.5">Priority</th>
              <th className="px-6 py-3.5">Status</th>
              <th className="px-6 py-3.5">Due Date</th>
              <th className="px-6 py-3.5">Assignee</th>
              <th className="px-6 py-3.5 text-right">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-[#273449]">
            {tasks.map((task) => (
              <tr
                key={task.id}
                className="transition hover:bg-[#1E293B]/40"
              >
                <td className="px-6 py-4">
                  <div className="font-medium text-[#F5F7FC]">
                    {task.title}
                  </div>
                  {task.description && (
                    <div className="mt-0.5 max-w-sm truncate text-xs text-[#94A3B8]">
                      {task.description}
                    </div>
                  )}
                </td>

                <td className="px-6 py-4">
                  <StatusBadge status={task.priority} />
                </td>

                <td className="px-6 py-4">
                  <StatusBadge status={task.status} />
                </td>

                <td className="px-6 py-4">
                  {task.due_date ? (
                    <span className="inline-flex items-center gap-1.5 font-mono text-xs text-[#94A3B8]">
                      <Calendar className="h-3 w-3 text-[#94A3B8]" />
                      {task.due_date}
                    </span>
                  ) : (
                    <span className="text-xs text-[#94A3B8]">—</span>
                  )}
                </td>

                <td className="px-6 py-4">
                  {task.assigned_to ? (
                    <span className="inline-flex items-center gap-1.5 text-xs text-[#F5F7FC]">
                      <UserIcon className="h-3 w-3 text-[#7657F6]" />
                      User #{task.assigned_to}
                    </span>
                  ) : (
                    <span className="text-xs text-[#94A3B8]">Unassigned</span>
                  )}
                </td>

                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <SecondaryButton
                      size="sm"
                      onClick={() => onEdit(task)}
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                      Edit
                    </SecondaryButton>

                    <DangerButton
                      size="sm"
                      onClick={() => onDelete(task)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Delete
                    </DangerButton>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
