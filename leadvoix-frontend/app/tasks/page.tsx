"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import TaskTable from "@/modules/tasks/components/TaskTable";
import TaskForm from "@/modules/tasks/components/TaskForm";
import {
  useTasks,
  useDeleteTask,
} from "@/modules/tasks/hooks/useTasks";
import type { Task } from "@/modules/tasks/types/task.types";
import {
  PageContainer,
  PageHeader,
  PrimaryButton,
  SecondaryButton,
  SearchInput,
  FilterDropdown,
  Modal,
  ConfirmationDialog,
} from "@/components/crm";

export default function TasksPage() {
  const queryClient = useQueryClient();

  const [showForm, setShowForm] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [taskToDelete, setTaskToDelete] = useState<Task | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [page, setPage] = useState(1);

  const filters = {
    page,
    limit: 10,
    search,
    status,
    priority,
  };

  const { data, isLoading, isError } = useTasks(filters);
  const deleteMutation = useDeleteTask();

  const handleTaskSuccess = () => {
    setShowForm(false);
    setSelectedTask(null);
    void queryClient.invalidateQueries({
      queryKey: ["tasks"],
    });
  };

  const handleEdit = (task: Task) => {
    setSelectedTask(task);
    setShowForm(true);
  };

  const handleConfirmDelete = async () => {
    if (!taskToDelete) return;

    try {
      setDeleteLoading(true);
      await deleteMutation.mutateAsync(taskToDelete.id);
      await queryClient.invalidateQueries({
        queryKey: ["tasks"],
      });
      setTaskToDelete(null);
    } catch (error) {
      console.error("Failed to delete task:", error);
    } finally {
      setDeleteLoading(false);
    }
  };

  const totalPages = data?.total_pages ?? 1;

  return (
    <DashboardLayout>
      <PageContainer>
        <PageHeader
          title="Tasks & Activities"
          subtitle="Organize team follow-ups, meeting preparations, and deal action items."
          badge="CRM"
          action={
            <PrimaryButton
              onClick={() => {
                setSelectedTask(null);
                setShowForm(true);
              }}
            >
              <Plus className="h-4 w-4" />
              New Task
            </PrimaryButton>
          }
        />

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="flex-1">
            <SearchInput
              value={search}
              onChange={(value) => {
                setSearch(value);
                setPage(1);
              }}
              placeholder="Search tasks by title or details..."
            />
          </div>

          <FilterDropdown
            label="Status"
            value={status}
            onChange={(val) => {
              setStatus(val);
              setPage(1);
            }}
            options={[
              { label: "All Statuses", value: "" },
              { label: "To Do", value: "TODO" },
              { label: "In Progress", value: "IN_PROGRESS" },
              { label: "Done", value: "DONE" },
            ]}
          />

          <FilterDropdown
            label="Priority"
            value={priority}
            onChange={(val) => {
              setPriority(val);
              setPage(1);
            }}
            options={[
              { label: "All Priorities", value: "" },
              { label: "Low", value: "LOW" },
              { label: "Medium", value: "MEDIUM" },
              { label: "High", value: "HIGH" },
            ]}
          />
        </div>

        <TaskTable
          tasks={data?.items ?? []}
          isLoading={isLoading}
          isError={isError}
          onEdit={handleEdit}
          onDelete={(task) => setTaskToDelete(task)}
        />

        {data && totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-[#273449] pt-4 text-xs text-[#94A3B8]">
            <span>
              Page <span className="font-mono text-[#F5F7FC]">{page}</span> of{" "}
              <span className="font-mono text-[#F5F7FC]">{totalPages}</span>
            </span>

            <div className="flex items-center gap-2">
              <SecondaryButton
                size="sm"
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={page === 1}
              >
                Previous
              </SecondaryButton>

              <SecondaryButton
                size="sm"
                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                disabled={page >= totalPages}
              >
                Next
              </SecondaryButton>
            </div>
          </div>
        )}

        <Modal
          isOpen={showForm}
          onClose={() => {
            setShowForm(false);
            setSelectedTask(null);
          }}
          title={selectedTask ? `Edit Task: ${selectedTask.title}` : "Create New Task"}
          maxWidth="max-w-2xl"
        >
          <TaskForm
            key={selectedTask?.id ?? "create"}
            task={selectedTask}
            onSuccess={handleTaskSuccess}
            onCancel={() => {
              setShowForm(false);
              setSelectedTask(null);
            }}
          />
        </Modal>

        <ConfirmationDialog
          isOpen={Boolean(taskToDelete)}
          onClose={() => setTaskToDelete(null)}
          onConfirm={handleConfirmDelete}
          title="Delete Task"
          message={`Are you sure you want to delete task "${taskToDelete?.title}"? This cannot be undone.`}
          confirmLabel="Delete Task"
          variant="danger"
          loading={deleteLoading}
        />
      </PageContainer>
    </DashboardLayout>
  );
}
