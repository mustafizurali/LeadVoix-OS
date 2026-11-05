"use client";

import type {
  CreateStagePayload,
  PipelineStageType,
  UpdateStagePayload,
} from "../types/pipeline.types";
import { FormField } from "@/components/crm";

const STAGE_TYPES: PipelineStageType[] = ["NORMAL", "OPEN", "WON", "LOST"];

interface PipelineStageFormProps {
  form: CreateStagePayload | UpdateStagePayload;
  onChange: (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => void;
  onToggleActive?: (checked: boolean) => void;
  error?: string;
}

export default function PipelineStageForm({
  form,
  onChange,
  onToggleActive,
  error,
}: PipelineStageFormProps) {
  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-400">
          {error}
        </div>
      )}

      <FormField
        label="Stage Name"
        name="name"
        value={form.name ?? ""}
        onChange={onChange}
        placeholder="e.g. Discovery Call Scheduled"
        required
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField
          label="Position Index"
          name="position"
          type="number"
          min={0}
          step={1}
          value={form.position ?? 0}
          onChange={onChange}
          helperText="Determines column/order sequence in pipeline"
        />

        <FormField
          label="Stage Type"
          name="stage_type"
          as="select"
          value={form.stage_type ?? "NORMAL"}
          onChange={onChange}
          options={STAGE_TYPES.map((t) => ({ value: t, label: t }))}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField
          label="Win Probability (%)"
          name="probability"
          type="number"
          min={0}
          max={100}
          step={1}
          value={form.probability ?? 0}
          onChange={onChange}
        />

        <FormField
          label="SLA Target (Days)"
          name="sla_days"
          type="number"
          min={0}
          step={1}
          value={form.sla_days ?? 0}
          onChange={onChange}
          helperText="Target resolution timeframe"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:items-center">
        <div>
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
            Stage Color
          </label>
          <div className="flex items-center gap-3 rounded-lg border border-[#273449] bg-[#0E1528] p-2">
            <input
              type="color"
              name="color"
              value={form.color ?? "#64748b"}
              onChange={onChange}
              className="h-8 w-12 cursor-pointer rounded border border-[#273449] bg-transparent"
            />
            <span className="font-mono text-sm text-[#F5F7FC]">
              {form.color ?? "#64748b"}
            </span>
          </div>
        </div>

        {typeof onToggleActive === "function" && (
          <div className="pt-4 sm:pt-6">
            <label className="flex cursor-pointer items-center gap-2.5 text-sm font-medium text-[#F5F7FC]">
              <input
                type="checkbox"
                name="is_active"
                checked={Boolean(form.is_active ?? true)}
                onChange={(event) => onToggleActive(event.target.checked)}
                className="h-4 w-4 rounded border-[#273449] bg-[#0E1528] text-[#7657F6] focus:ring-[#7657F6]/30 focus:ring-offset-0"
              />
              Active Stage
            </label>
          </div>
        )}
      </div>
    </div>
  );
}
