"use client";

import React from "react";
import { FormField } from "@/components/crm";
import { CreateContactPayload, UpdateContactPayload } from "../types/contact.types";

interface ContactFormProps {
  form: CreateContactPayload | UpdateContactPayload;
  onChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => void;
}

export default function ContactForm({ form, onChange }: ContactFormProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <FormField
        label="First Name"
        name="first_name"
        required
        placeholder="e.g. Sarah"
        value={form.first_name}
        onChange={onChange}
      />

      <FormField
        label="Last Name"
        name="last_name"
        placeholder="e.g. Connor"
        value={form.last_name ?? ""}
        onChange={onChange}
      />

      <FormField
        label="Email Address"
        name="email"
        type="email"
        placeholder="sarah@organization.com"
        value={form.email ?? ""}
        onChange={onChange}
      />

      <FormField
        label="Phone Number"
        name="phone"
        placeholder="+1 (555) 234-5678"
        value={form.phone ?? ""}
        onChange={onChange}
      />

      <div className="col-span-1 sm:col-span-2">
        <FormField
          label="Company Name"
          name="company"
          placeholder="Cyberdyne Systems"
          value={form.company ?? ""}
          onChange={onChange}
        />
      </div>
    </div>
  );
}
