"use client";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { updatePipelineStage } from "../api/pipelineApi";
import type {
  PipelineStage,
  PipelineStageType,
  UpdateStagePayload,
} from "../types/pipeline.types";
import PipelineStageForm from "./PipelineStageForm";
import { Modal, PrimaryButton, SecondaryButton } from "@/components/crm";
import { getErrorMessage } from "@/lib/api/errors";

interface EditStageModalProps {
  open: boolean;
  onClose: () => void;
  stage: PipelineStage | null;
  existingPositions?: number[];
}

const emptyForm: UpdateStagePayload = {
  name: "",
  position: 0,
  color: "#64748b",
  stage_type: "NORMAL",
  probability: 0,
  sla_days: 0,
  is_active: true,
};

export default function EditStageModal({
  open,
  onClose,
  stage,
  existingPositions = [],
}: EditStageModalProps) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<UpdateStagePayload>(emptyForm);

  useEffect(() => {
    if (stage) {
      setForm({
        name: stage.name,
        position: stage.position,
        color: stage.color ?? "#64748b",
        stage_type: stage.stage_type,
        probability: stage.probability,
        sla_days: stage.sla_days,
        is_active: stage.is_active,
      });
      setError(null);
    }
  }, [stage]);

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

  const handleSubmit = async () => {
    if (!stage) return;
    if (!form.name?.trim()) {
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
      await updatePipelineStage(stage.id, {
        name: form.name.trim(),
        position: pos,
        color: form.color || undefined,
        stage_type: form.stage_type,
        probability:
          typeof form.probability === "number" ? form.probability : undefined,
        sla_days: typeof form.sla_days === "number" ? form.sla_days : undefined,
        is_active:
          typeof form.is_active === "boolean" ? form.is_active : undefined,
      });

      await queryClient.invalidateQueries({ queryKey: ["pipeline-stages"] });
      onClose();
    } catch (err: unknown) {
      console.error(err);
      setError(
        getErrorMessage(err, "Failed to update pipeline stage. Please try again.")
      );
    } finally {
      setLoading(false);
    }
  };

  if (!open || !stage) return null;

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title={`Edit Stage: ${stage.name}`}
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
          <SecondaryButton onClick={onClose} disabled={loading}>
            Cancel
          </SecondaryButton>
          <PrimaryButton onClick={handleSubmit} loading={loading}>
            Save Changes
          </PrimaryButton>
        </div>
      </div>
    </Modal>
  );
}
