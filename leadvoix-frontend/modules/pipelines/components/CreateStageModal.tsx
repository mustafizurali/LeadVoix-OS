"use client";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { createPipelineStage } from "../api/pipelineApi";
import type {
  CreateStagePayload,
  PipelineStageType,
} from "../types/pipeline.types";
import PipelineStageForm from "./PipelineStageForm";
import { Modal, PrimaryButton, SecondaryButton } from "@/components/crm";
import { getErrorMessage } from "@/lib/api/errors";

interface CreateStageModalProps {
  open: boolean;
  onClose: () => void;
  pipelineId: number;
  defaultPosition?: number;
  existingPositions?: number[];
}

const getEmptyForm = (
  pipelineId: number,
  defaultPosition = 0
): CreateStagePayload => ({
  pipeline_id: pipelineId,
  name: "",
  position: defaultPosition,
  color: "#64748b",
  stage_type: "NORMAL",
  probability: 0,
  sla_days: 0,
  is_active: true,
});

export default function CreateStageModal({
  open,
  onClose,
  pipelineId,
  defaultPosition = 0,
  existingPositions = [],
}: CreateStageModalProps) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<CreateStagePayload>(() =>
    getEmptyForm(pipelineId, defaultPosition)
  );

  useEffect(() => {
    if (open) {
      setForm(getEmptyForm(pipelineId, defaultPosition));
      setError(null);
    }
  }, [open, pipelineId, defaultPosition]);

  const handleChange = (
    event: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value, type } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]:
        type === "number"
          ? Number(value)
          : name === "stage_type"
          ? (value as PipelineStageType)
          : value,
    }));
  };

  const handleToggleActive = (checked: boolean) => {
    setForm((previous) => ({
      ...previous,
      is_active: checked,
    }));
  };

  const handleClose = () => {
    setError(null);
    setForm(getEmptyForm(pipelineId, defaultPosition));
    onClose();
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      setError("Stage name is required");
      return;
    }

    const pos = Number(form.position);
    if (isNaN(pos) || pos < 0) {
      setError("Position index must be a non-negative number");
      return;
    }

    if (existingPositions.includes(pos)) {
      setError(
        `A stage already exists at position ${pos}. Please choose a different position index.`
      );
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await createPipelineStage(pipelineId, {
        pipeline_id: pipelineId,
        name: form.name.trim(),
        position: pos,
        color: form.color || undefined,
        stage_type: form.stage_type,
        probability: Number(form.probability),
        sla_days: Number(form.sla_days),
        is_active: Boolean(form.is_active),
      });

      await queryClient.invalidateQueries({
        queryKey: ["pipeline-stages"],
      });

      handleClose();
    } catch (err: unknown) {
      console.error(err);
      setError(getErrorMessage(err, "Failed to create stage. Please try again."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={open}
      onClose={handleClose}
      title="Create Pipeline Stage"
      maxWidth="max-w-xl"
    >
      <div className="space-y-6">
        <PipelineStageForm
          form={form}
          onChange={handleChange}
          onToggleActive={handleToggleActive}
          error={error || undefined}
        />

        <div className="flex justify-end gap-3 border-t border-[#273449] pt-4">
          <SecondaryButton onClick={handleClose} disabled={loading}>
            Cancel
          </SecondaryButton>
          <PrimaryButton onClick={handleSubmit} loading={loading}>
            Create Stage
          </PrimaryButton>
        </div>
      </div>
    </Modal>
  );
}
