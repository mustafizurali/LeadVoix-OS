"use client";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { updatePipeline } from "../api/pipelineApi";
import type { Pipeline, UpdatePipelinePayload } from "../types/pipeline.types";
import PipelineForm from "./PipelineForm";
import { Modal, PrimaryButton, SecondaryButton } from "@/components/crm";
import { getErrorMessage } from "@/lib/api/errors";

interface EditPipelineModalProps {
  open: boolean;
  onClose: () => void;
  pipeline: Pipeline | null;
}

const emptyForm: UpdatePipelinePayload = {
  name: "",
  description: "",
  color: "#7657F6",
  is_default: false,
  is_active: true,
};

export default function EditPipelineModal({
  open,
  onClose,
  pipeline,
}: EditPipelineModalProps) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<UpdatePipelinePayload>(emptyForm);

  useEffect(() => {
    if (pipeline) {
      setForm({
        name: pipeline.name,
        description: pipeline.description ?? "",
        color: pipeline.color ?? "#7657F6",
        is_default: pipeline.is_default,
        is_active: pipeline.is_active,
      });
      setError(null);
    }
  }, [pipeline]);

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = event.target;
    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async () => {
    if (!pipeline) return;
    if (!form.name?.trim()) {
      setError("Pipeline name is required");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await updatePipeline(pipeline.id, {
        name: form.name.trim(),
        description: form.description?.trim() || undefined,
        color: form.color || undefined,
        is_default: typeof form.is_default === "boolean" ? form.is_default : undefined,
        is_active: typeof form.is_active === "boolean" ? form.is_active : undefined,
      });

      await queryClient.invalidateQueries({ queryKey: ["pipelines"] });
      onClose();
    } catch (err: unknown) {
      console.error(err);
      setError(
        getErrorMessage(err, "Failed to update pipeline. Please try again.")
      );
    } finally {
      setLoading(false);
    }
  };

  if (!open || !pipeline) return null;

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title={`Edit Pipeline: ${pipeline.name}`}
      maxWidth="max-w-xl"
    >
      <div className="space-y-6">
        <PipelineForm
          form={form}
          onChange={handleChange}
          onToggleDefault={(checked) =>
            setForm((previous) => ({ ...previous, is_default: checked }))
          }
          onToggleActive={(checked) =>
            setForm((previous) => ({ ...previous, is_active: checked }))
          }
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
