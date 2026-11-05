"use client";

import { FormEvent, useEffect, useState } from "react";

import { useCreateTask, useUpdateTask } from "../hooks/useTasks";
import type { Task, TaskPayload } from "../types/task.types";

import { useLeads } from "@/modules/leads/hooks/useLeads";
import { useContacts } from "@/modules/contacts/hooks/useContacts";
import { useCompanies } from "@/modules/companies/hooks/useCompanies";
import { useDeals } from "@/modules/deals/hooks/useDeals";
import { FormField, PrimaryButton, SecondaryButton } from "@/components/crm";

interface TaskFormProps {
  task?: Task | null;
  onSuccess: () => void;
  onCancel?: () => void;
}

export default function TaskForm({
  task,
  onSuccess,
  onCancel,
}: TaskFormProps) {
  const isEditMode = Boolean(task);

  const createMutation = useCreateTask();
  const updateMutation = useUpdateTask();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("MEDIUM");
  const [status, setStatus] = useState("TODO");
  const [dueDate, setDueDate] = useState("");

  const [dealId, setDealId] = useState("");
  const [leadId, setLeadId] = useState("");
  const [contactId, setContactId] = useState("");
  const [companyId, setCompanyId] = useState("");
  const [assignedTo, setAssignedTo] = useState("");

  const [errorMessage, setErrorMessage] = useState("");

  const { data: leadsData } = useLeads({ page: 1, limit: 100 });
  const { data: contactsData } = useContacts({ page: 1, limit: 100 });
  const { data: companiesData } = useCompanies({ page: 1, limit: 100 });
  const { data: dealsData } = useDeals({ page: 1, limit: 100 });

  useEffect(() => {
    if (task) {
      setTitle(task.title ?? "");
      setDescription(task.description ?? "");
      setPriority(task.priority ?? "MEDIUM");
      setStatus(task.status ?? "TODO");
      setDueDate(task.due_date ?? "");
      setDealId(task.deal_id !== null ? String(task.deal_id) : "");
      setLeadId(task.lead_id !== null ? String(task.lead_id) : "");
      setContactId(task.contact_id !== null ? String(task.contact_id) : "");
      setCompanyId(task.company_id !== null ? String(task.company_id) : "");
      setAssignedTo(task.assigned_to !== null ? String(task.assigned_to) : "");
    } else {
      setTitle("");
      setDescription("");
      setPriority("MEDIUM");
      setStatus("TODO");
      setDueDate("");
      setDealId("");
      setLeadId("");
      setContactId("");
      setCompanyId("");
      setAssignedTo("");
    }
    setErrorMessage("");
  }, [task]);

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage("");

    if (!title.trim()) {
      setErrorMessage("Task title is required.");
      return;
    }

    const payload: TaskPayload = {
      title: title.trim(),
      description: description.trim() || undefined,
      priority,
      status,
      due_date: dueDate || undefined,
      deal_id: dealId ? Number(dealId) : undefined,
      lead_id: leadId ? Number(leadId) : undefined,
      contact_id: contactId ? Number(contactId) : undefined,
      company_id: companyId ? Number(companyId) : undefined,
      assigned_to: assignedTo ? Number(assignedTo) : undefined,
    };

    try {
      if (task) {
        await updateMutation.mutateAsync({
          id: task.id,
          data: payload,
        });
      } else {
        await createMutation.mutateAsync(payload);
      }
      onSuccess();
    } catch (error) {
      console.error("Failed to save task:", error);
      setErrorMessage(
        "Failed to save task. Please check the selected records and try again."
      );
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {errorMessage && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-400">
          {errorMessage}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <FormField
            label="Task Title"
            name="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Follow up on proposal feedback"
            required
          />
        </div>

        <FormField
          label="Priority"
          name="priority"
          as="select"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          options={[
            { value: "LOW", label: "Low Priority" },
            { value: "MEDIUM", label: "Medium Priority" },
            { value: "HIGH", label: "High Priority" },
          ]}
        />

        <FormField
          label="Status"
          name="status"
          as="select"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          options={[
            { value: "TODO", label: "To Do" },
            { value: "IN_PROGRESS", label: "In Progress" },
            { value: "DONE", label: "Done" },
          ]}
        />

        <FormField
          label="Due Date"
          name="dueDate"
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
        />

        <FormField
          label="Assigned User ID"
          name="assignedTo"
          type="number"
          min="1"
          value={assignedTo}
          onChange={(e) => setAssignedTo(e.target.value)}
          placeholder="User ID (optional)"
          helperText="Leave empty if unassigned"
        />

        <FormField
          label="Related Deal"
          name="dealId"
          as="select"
          value={dealId}
          onChange={(e) => setDealId(e.target.value)}
          options={[
            { value: "", label: "No Deal" },
            ...(dealsData?.items?.map((d) => ({
              value: String(d.id),
              label: d.title,
            })) ?? []),
          ]}
        />

        <FormField
          label="Related Lead"
          name="leadId"
          as="select"
          value={leadId}
          onChange={(e) => setLeadId(e.target.value)}
          options={[
            { value: "", label: "No Lead" },
            ...(leadsData?.items?.map((l) => ({
              value: String(l.id),
              label: `${l.first_name} ${l.last_name ?? ""}`.trim(),
            })) ?? []),
          ]}
        />

        <FormField
          label="Related Contact"
          name="contactId"
          as="select"
          value={contactId}
          onChange={(e) => setContactId(e.target.value)}
          options={[
            { value: "", label: "No Contact" },
            ...(contactsData?.items?.map((c) => ({
              value: String(c.id),
              label: `${c.first_name} ${c.last_name ?? ""}`.trim(),
            })) ?? []),
          ]}
        />

        <FormField
          label="Related Company"
          name="companyId"
          as="select"
          value={companyId}
          onChange={(e) => setCompanyId(e.target.value)}
          options={[
            { value: "", label: "No Company" },
            ...(companiesData?.items?.map((c) => ({
              value: String(c.id),
              label: c.name,
            })) ?? []),
          ]}
        />
      </div>

      <FormField
        label="Description / Checklist"
        name="description"
        as="textarea"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Additional context, action items, or notes..."
        rows={3}
      />

      <div className="flex items-center justify-end gap-3 border-t border-[#273449] pt-4">
        {onCancel && (
          <SecondaryButton type="button" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </SecondaryButton>
        )}
        <PrimaryButton type="submit" loading={isSubmitting}>
          {isEditMode ? "Update Task" : "Create Task"}
        </PrimaryButton>
      </div>
    </form>
  );
}
