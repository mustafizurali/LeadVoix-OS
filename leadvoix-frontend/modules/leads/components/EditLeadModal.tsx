"use client";

import React, { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Modal, PrimaryButton, SecondaryButton } from "@/components/crm";
import { updateLead } from "../api/leadApi";
import { Lead, UpdateLeadPayload } from "../types/lead.types";
import LeadForm from "./LeadForm";

interface EditLeadModalProps {
  open: boolean;
  onClose: () => void;
  lead: Lead | null;
}

export default function EditLeadModal({
  open,
  onClose,
  lead,
}: EditLeadModalProps) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<UpdateLeadPayload>({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    company: "",
    source: "",
    notes: "",
    status: "",
  });

  useEffect(() => {
    if (lead) {
      setForm({
        first_name: lead.first_name,
        last_name: lead.last_name ?? "",
        email: lead.email ?? "",
        phone: lead.phone ?? "",
        company: lead.company ?? "",
        source: lead.source ?? "",
        notes: lead.notes ?? "",
        status: lead.status ?? "",
      });
      setError(null);
    }
  }, [lead]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async () => {
    if (!lead) return;

    if (!form.first_name?.trim()) {
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

      await updateLead(lead.id, payload);

      await queryClient.invalidateQueries({
        queryKey: ["leads"],
      });

      onClose();
    } catch (err: unknown) {
      console.error(err);
      setError("Failed to update lead. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Edit Lead"
      subtitle={`Updating record for ${lead?.first_name ?? "Lead"} ${lead?.last_name ?? ""}`}
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
