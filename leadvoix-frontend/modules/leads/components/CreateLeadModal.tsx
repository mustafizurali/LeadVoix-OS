"use client";

import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Modal, PrimaryButton, SecondaryButton } from "@/components/crm";
import { createLead } from "../api/leadApi";
import { CreateLeadPayload } from "../types/lead.types";
import LeadForm from "./LeadForm";

interface CreateLeadModalProps {
  open: boolean;
  onClose: () => void;
}

export default function CreateLeadModal({
  open,
  onClose,
}: CreateLeadModalProps) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<CreateLeadPayload>({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    company: "",
    source: "",
    notes: "",
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const resetForm = () => {
    setForm({
      first_name: "",
      last_name: "",
      email: "",
      phone: "",
      company: "",
      source: "",
      notes: "",
    });
    setError(null);
  };

  const handleSubmit = async () => {
    if (!form.first_name.trim()) {
      setError("First Name is required");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const payload = {
        ...form,
        email: form.email?.trim() || undefined,
        phone: form.phone?.trim() || undefined,
        company: form.company?.trim() || undefined,
        source: form.source?.trim() || undefined,
        notes: form.notes?.trim() || undefined,
        last_name: form.last_name?.trim() || undefined,
      };

      await createLead(payload);

      await queryClient.invalidateQueries({
        queryKey: ["leads"],
      });

      resetForm();
      onClose();
    } catch (err: unknown) {
      console.error(err);
      setError("Failed to create lead. Please verify the information and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={() => {
        resetForm();
        onClose();
      }}
      title="Create New Lead"
      subtitle="Register a new prospect into the LeadVoix sales pipeline."
      maxWidth="2xl"
    >
      <div className="space-y-5">
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/15 p-3 text-xs text-red-300">
            {error}
          </div>
        )}

        <LeadForm form={form} onChange={handleChange} />

        <div className="flex justify-end gap-3 pt-4 border-t border-[#273449]">
          <SecondaryButton
            onClick={() => {
              resetForm();
              onClose();
            }}
            disabled={loading}
          >
            Cancel
          </SecondaryButton>
          <PrimaryButton onClick={handleSubmit} loading={loading}>
            Create Lead
          </PrimaryButton>
        </div>
      </div>
    </Modal>
  );
}
