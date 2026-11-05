"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { createPipeline } from "../api/pipelineApi";
import type { CreatePipelinePayload } from "../types/pipeline.types";
import PipelineForm from "./PipelineForm";
import { Modal, PrimaryButton, SecondaryButton } from "@/components/crm";
import { getErrorMessage } from "@/lib/api/errors";

interface CreatePipelineModalProps {
  open: boolean;
  onClose: () => void;
}

const emptyForm: CreatePipelinePayload = {
  name: "",
  description: "",
  color: "#7657F6",
  is_default: false,
  is_active: true,
};

export default function CreatePipelineModal({
  open,
  onClose,
}: CreatePipelineModalProps) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<CreatePipelinePayload>(emptyForm);

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = event.target;
    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleClose = () => {
    setError(null);
    setForm(emptyForm);
    onClose();
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      setError("Pipeline name is required");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await createPipeline({
        name: form.name.trim(),
        description: form.description?.trim() || undefined,
        color: form.color || undefined,
        is_default: Boolean(form.is_default),
        is_active: Boolean(form.is_active ?? true),
      });

      await queryClient.invalidateQueries({ queryKey: ["pipelines"] });
      handleClose();
    } catch (err: unknown) {
      console.error(err);
      setError(
        getErrorMessage(err, "Failed to create pipeline. Please try again.")
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={open}
      onClose={handleClose}
      title="Create New Pipeline"
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
          <SecondaryButton onClick={handleClose} disabled={loading}>
            Cancel
          </SecondaryButton>
          <PrimaryButton onClick={handleSubmit} loading={loading}>
            Create Pipeline
          </PrimaryButton>
        </div>
      </div>
    </Modal>
  );
}
