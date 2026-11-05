"use client";

import type {
  CreatePipelinePayload,
  UpdatePipelinePayload,
} from "../types/pipeline.types";
import { FormField } from "@/components/crm";

interface PipelineFormProps {
  form: CreatePipelinePayload | UpdatePipelinePayload;
  onChange: (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => void;
  onToggleDefault?: (checked: boolean) => void;
  onToggleActive?: (checked: boolean) => void;
  error?: string;
}

export default function PipelineForm({
  form,
  onChange,
  onToggleDefault,
  onToggleActive,
  error,
}: PipelineFormProps) {
  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-400">
          {error}
        </div>
      )}

      <FormField
        label="Pipeline Name"
        name="name"
        value={form.name ?? ""}
        onChange={onChange}
        placeholder="e.g. Inbound Sales Pipeline"
        required
      />

      <FormField
        label="Description"
        name="description"
        as="textarea"
        value={form.description ?? ""}
        onChange={onChange}
        placeholder="Describe the target deals and sales flow..."
        rows={3}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:items-center">
        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
            Color Indicator
          </label>
          <div className="flex items-center gap-3 rounded-lg border border-[#273449] bg-[#0E1528] p-2">
            <input
              type="color"
              name="color"
              value={form.color ?? "#7657F6"}
              onChange={onChange}
              className="h-8 w-12 cursor-pointer rounded border border-[#273449] bg-transparent"
            />
            <span className="font-mono text-sm text-[#F5F7FC]">
              {form.color ?? "#7657F6"}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-4 pt-4 sm:pt-6">
          {typeof onToggleDefault === "function" && (
            <label className="flex cursor-pointer items-center gap-2.5 text-sm font-medium text-[#F5F7FC]">
              <input
                type="checkbox"
                checked={Boolean((form as UpdatePipelinePayload).is_default ?? false)}
                onChange={(event) => onToggleDefault(event.target.checked)}
                className="h-4 w-4 rounded border-[#273449] bg-[#0E1528] text-[#7657F6] focus:ring-[#7657F6]/30 focus:ring-offset-0"
              />
              Default Pipeline
            </label>
          )}

          {typeof onToggleActive === "function" && (
            <label className="flex cursor-pointer items-center gap-2.5 text-sm font-medium text-[#F5F7FC]">
              <input
                type="checkbox"
                checked={Boolean((form as UpdatePipelinePayload).is_active ?? true)}
                onChange={(event) => onToggleActive(event.target.checked)}
                className="h-4 w-4 rounded border-[#273449] bg-[#0E1528] text-[#7657F6] focus:ring-[#7657F6]/30 focus:ring-offset-0"
              />
              Active
            </label>
          )}
        </div>
      </div>
    </div>
  );
}
