"use client";

import React from "react";
import { FormField } from "@/components/crm";
import { CreateLeadPayload, UpdateLeadPayload } from "../types/lead.types";

interface LeadFormProps {
  form: Partial<CreateLeadPayload & UpdateLeadPayload>;
  onChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => void;
}

export default function LeadForm({ form, onChange }: LeadFormProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <FormField
        label="First Name"
        name="first_name"
        required
        placeholder="e.g. Alex"
        value={form.first_name ?? ""}
        onChange={onChange}
      />

      <FormField
        label="Last Name"
        name="last_name"
        placeholder="e.g. Morgan"
        value={form.last_name ?? ""}
        onChange={onChange}
      />

      <FormField
        label="Email Address"
        name="email"
        type="email"
        placeholder="alex@company.com"
        value={form.email ?? ""}
        onChange={onChange}
      />

      <FormField
        label="Phone Number"
        name="phone"
        placeholder="+1 (555) 000-0000"
        value={form.phone ?? ""}
        onChange={onChange}
      />

      <FormField
        label="Company"
        name="company"
        placeholder="Acme Inc."
        value={form.company ?? ""}
        onChange={onChange}
      />

      <FormField
        label="Lead Source"
        name="source"
        placeholder="Website, Referral, AI Inbound..."
        value={form.source ?? ""}
        onChange={onChange}
      />

      <div className="col-span-1 sm:col-span-2">
        <FormField
          as="textarea"
          label="Notes / Background"
          name="notes"
          rows={3}
          placeholder="Add any context, lead qualification details, or requirements..."
          value={form.notes ?? ""}
          onChange={onChange}
        />
      </div>
    </div>
  );
}
