"use client";

import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Modal, PrimaryButton, SecondaryButton } from "@/components/crm";
import { createCompany } from "../api/companyApi";
import { CreateCompanyPayload } from "../types/company.types";
import CompanyForm from "./CompanyForm";

interface CreateCompanyModalProps {
  open: boolean;
  onClose: () => void;
}

export default function CreateCompanyModal({
  open,
  onClose,
}: CreateCompanyModalProps) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<CreateCompanyPayload>({
    name: "",
    domain: "",
    industry: "",
    company_size: "",
    website: "",
    notes: "",
  });

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const resetForm = () => {
    setForm({
      name: "",
      domain: "",
      industry: "",
      company_size: "",
      website: "",
      notes: "",
    });
    setError(null);
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      setError("Company Name is required");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const payload = {
        name: form.name.trim(),
        domain: form.domain?.trim() || undefined,
        industry: form.industry?.trim() || undefined,
        company_size: form.company_size?.trim() || undefined,
        website: form.website?.trim() || undefined,
        notes: form.notes?.trim() || undefined,
      };

      await createCompany(payload);

      await queryClient.invalidateQueries({
        queryKey: ["companies"],
      });

      resetForm();
      onClose();
    } catch (err: unknown) {
      console.error(err);
      setError("Failed to create company. Please verify the information and try again.");
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
      title="Create New Company"
      subtitle="Register a new business account or organization."
      maxWidth="2xl"
    >
      <div className="space-y-5">
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/15 p-3 text-xs text-red-300">
            {error}
          </div>
        )}

        <CompanyForm form={form} onChange={handleChange} />

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
            Create Company
          </PrimaryButton>
        </div>
      </div>
    </Modal>
  );
}
