"use client";

import { FormEvent, useState } from "react";

import { createDeal, updateDeal } from "../api/dealApi";
import { Deal, DealPayload } from "../types/deal.types";
import { usePipelineStages } from "../../pipelines/hooks/usePipelineStages";
import { usePipelines } from "../../pipelines/hooks/usePipelines";
import { useLeads } from "../../leads/hooks/useLeads";
import { useContacts } from "../../contacts/hooks/useContacts";
import { useCompanies } from "../../companies/hooks/useCompanies";
import { FormField, PrimaryButton, SecondaryButton } from "@/components/crm";

interface DealFormProps {
  deal?: Deal | null;
  onSuccess?: () => void;
  onCancel?: () => void;
}

type DealFormState = {
  title: string;
  amount: string;
  currency: string;
  status: string;
  expected_close_date: string;
  description: string;
  pipeline_id: string;
  stage_id: string;
  lead_id: string;
  contact_id: string;
  company_id: string;
  owner_id: string;
};

const getInitialForm = (deal?: Deal | null): DealFormState => ({
  title: deal?.title ?? "",
  amount: String(deal?.amount ?? 0),
  currency: deal?.currency ?? "USD",
  status: deal?.status ?? "OPEN",
  expected_close_date: deal?.expected_close_date ?? "",
  description: deal?.description ?? "",
  pipeline_id: String(deal?.pipeline_id ?? ""),
  stage_id: String(deal?.stage_id ?? ""),
  lead_id: String(deal?.lead_id ?? ""),
  contact_id: String(deal?.contact_id ?? ""),
  company_id: String(deal?.company_id ?? ""),
  owner_id: String(deal?.owner_id ?? ""),
});

const optionalNumber = (value: string) => {
  if (!value.trim()) {
    return undefined;
  }
  return Number(value);
};

export default function DealForm({ deal, onSuccess, onCancel }: DealFormProps) {
  const [form, setForm] = useState<DealFormState>(() => getInitialForm(deal));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const { data: pipelinesData } = usePipelines();
  const { data: leadsData } = useLeads({ page: 1, limit: 100 });
  const { data: contactsData } = useContacts({ page: 1, limit: 100 });
  const { data: companiesData } = useCompanies({ page: 1, limit: 100 });
  const { data: stagesData } = usePipelineStages(Number(form.pipeline_id));

  const handleChange = (
    event: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = event.target;
    setForm((current) => ({
      ...current,
      [name]: value,
      ...(name === "pipeline_id" ? { stage_id: "" } : {}),
    }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    if (!form.title.trim()) {
      setError("Deal title is required.");
      return;
    }

    const payload: DealPayload = {
      title: form.title.trim(),
      amount: Number(form.amount) || 0,
      currency: form.currency.trim().toUpperCase(),
      status: form.status,
      expected_close_date: form.expected_close_date || undefined,
      description: form.description.trim() || undefined,
      pipeline_id: optionalNumber(form.pipeline_id),
      stage_id: optionalNumber(form.stage_id),
      lead_id: optionalNumber(form.lead_id),
      contact_id: optionalNumber(form.contact_id),
      company_id: optionalNumber(form.company_id),
      owner_id: optionalNumber(form.owner_id),
    };

    try {
      setIsSubmitting(true);
      if (deal) {
        await updateDeal(deal.id, payload);
      } else {
        await createDeal(payload);
      }

      setForm(getInitialForm());
      onSuccess?.();
    } catch (requestError) {
      console.error(requestError);
      setError(`Failed to ${deal ? "update" : "create"} deal. Please try again.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-400">
          {error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Deal Title"
          name="title"
          value={form.title}
          onChange={handleChange}
          placeholder="e.g. Enterprise Cloud License"
          required
        />

        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Amount"
            name="amount"
            type="number"
            min="0"
            step="0.01"
            value={form.amount}
            onChange={handleChange}
            required
          />

          <FormField
            label="Currency"
            name="currency"
            value={form.currency}
            onChange={handleChange}
            placeholder="USD"
            required
          />
        </div>

        <FormField
          label="Status"
          name="status"
          as="select"
          value={form.status}
          onChange={handleChange}
          options={[
            { value: "OPEN", label: "Open" },
            { value: "WON", label: "Won" },
            { value: "LOST", label: "Lost" },
          ]}
        />

        <FormField
          label="Expected Close Date"
          name="expected_close_date"
          type="date"
          value={form.expected_close_date}
          onChange={handleChange}
        />

        <FormField
          label="Pipeline"
          name="pipeline_id"
          as="select"
          value={form.pipeline_id}
          onChange={handleChange}
          options={[
            { value: "", label: "Select pipeline" },
            ...(pipelinesData?.items.map((pipeline) => ({
              value: String(pipeline.id),
              label: pipeline.name,
            })) ?? []),
          ]}
        />

        <FormField
          label="Stage"
          name="stage_id"
          as="select"
          value={form.stage_id}
          onChange={handleChange}
          disabled={!form.pipeline_id}
          options={[
            { value: "", label: "Select stage" },
            ...(stagesData?.map((stage) => ({
              value: String(stage.id),
              label: stage.name,
            })) ?? []),
          ]}
        />

        <FormField
          label="Associated Lead"
          name="lead_id"
          as="select"
          value={form.lead_id}
          onChange={handleChange}
          options={[
            { value: "", label: "Select lead (optional)" },
            ...(leadsData?.items.map((lead) => ({
              value: String(lead.id),
              label: `${lead.first_name} ${lead.last_name ?? ""}`.trim(),
            })) ?? []),
          ]}
        />

        <FormField
          label="Associated Contact"
          name="contact_id"
          as="select"
          value={form.contact_id}
          onChange={handleChange}
          options={[
            { value: "", label: "Select contact (optional)" },
            ...(contactsData?.items.map((contact) => ({
              value: String(contact.id),
              label: `${contact.first_name} ${contact.last_name ?? ""}`.trim(),
            })) ?? []),
          ]}
        />

        <FormField
          label="Associated Company"
          name="company_id"
          as="select"
          value={form.company_id}
          onChange={handleChange}
          options={[
            { value: "", label: "Select company (optional)" },
            ...(companiesData?.items.map((company) => ({
              value: String(company.id),
              label: company.name,
            })) ?? []),
          ]}
        />

        <FormField
          label="Owner ID"
          name="owner_id"
          type="number"
          min="1"
          value={form.owner_id}
          onChange={handleChange}
          placeholder="User ID"
        />
      </div>

      <FormField
        label="Description / Scope"
        name="description"
        as="textarea"
        value={form.description}
        onChange={handleChange}
        rows={3}
        placeholder="Key terms, requirements, and next steps..."
      />

      <div className="flex items-center justify-end gap-3 border-t border-[#273449] pt-4">
        {onCancel && (
          <SecondaryButton type="button" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </SecondaryButton>
        )}
        <PrimaryButton type="submit" loading={isSubmitting}>
          {deal ? "Update Deal" : "Create Deal"}
        </PrimaryButton>
      </div>
    </form>
  );
}
