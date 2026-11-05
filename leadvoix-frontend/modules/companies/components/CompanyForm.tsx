"use client";

import React from "react";
import { FormField } from "@/components/crm";
import { CreateCompanyPayload, UpdateCompanyPayload } from "../types/company.types";

interface CompanyFormProps {
  form: CreateCompanyPayload | UpdateCompanyPayload;
  onChange: (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => void;
}

export default function CompanyForm({ form, onChange }: CompanyFormProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <FormField
        label="Company Name"
        name="name"
        required
        placeholder="Acme Corporation"
        value={form.name ?? ""}
        onChange={onChange}
      />

      <FormField
        label="Domain"
        name="domain"
        placeholder="acme.com"
        value={form.domain ?? ""}
        onChange={onChange}
      />

      <FormField
        label="Industry"
        name="industry"
        placeholder="Software, Finance, Retail..."
        value={form.industry ?? ""}
        onChange={onChange}
      />

      <FormField
        label="Company Size"
        name="company_size"
        placeholder="1-10, 11-50, 50-200, 200+..."
        value={form.company_size ?? ""}
        onChange={onChange}
      />

      <div className={"status" in form ? "col-span-1" : "col-span-1 sm:col-span-2"}>
        <FormField
          label="Website URL"
          name="website"
          type="url"
          placeholder="https://acme.com"
          value={form.website ?? ""}
          onChange={onChange}
        />
      </div>

      {"status" in form && (
        <FormField
          label="Account Status"
          name="status"
          placeholder="Active, Prospect, Former..."
          value={form.status ?? ""}
          onChange={onChange}
        />
      )}

      <div className="col-span-1 sm:col-span-2">
        <FormField
          as="textarea"
          label="Notes / Account Description"
          name="notes"
          rows={3}
          placeholder="Add background, account relationship notes, or contract details..."
          value={form.notes ?? ""}
          onChange={onChange}
        />
      </div>
    </div>
  );
}
