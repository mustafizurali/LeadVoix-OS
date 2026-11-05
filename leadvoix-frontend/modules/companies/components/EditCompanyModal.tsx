"use client";

import React, { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Modal, PrimaryButton, SecondaryButton } from "@/components/crm";
import { updateCompany } from "../api/companyApi";
import { Company, UpdateCompanyPayload } from "../types/company.types";
import CompanyForm from "./CompanyForm";

interface EditCompanyModalProps {
  open: boolean;
  onClose: () => void;
  company: Company | null;
}

export default function EditCompanyModal({
  open,
  onClose,
  company,
}: EditCompanyModalProps) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<UpdateCompanyPayload>({
    name: "",
    domain: "",
    industry: "",
    company_size: "",
    website: "",
    status: "",
    notes: "",
  });

  useEffect(() => {
    if (company) {
      setForm({
        name: company.name,
        domain: company.domain ?? "",
        industry: company.industry ?? "",
        company_size: company.company_size ?? "",
        website: company.website ?? "",
        status: company.status,
        notes: company.notes ?? "",
      });
      setError(null);
    }
  }, [company]);

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const handleSubmit = async () => {
    if (!company) return;

    if (!form.name?.trim()) {
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
        status: form.status?.trim() || undefined,
        notes: form.notes?.trim() || undefined,
      };

      await updateCompany(company.id, payload);

      await queryClient.invalidateQueries({
        queryKey: ["companies"],
      });

      onClose();
    } catch (err: unknown) {
      console.error(err);
      setError("Failed to update company. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Edit Company"
      subtitle={`Updating account profile for ${company?.name ?? "Company"}`}
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
