"use client";

import React from "react";
import { Users } from "lucide-react";
import { SearchInput, PrimaryButton } from "@/components/crm";

interface ContactToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  onCreateContact: () => void;
}

export default function ContactToolbar({
  search,
  onSearchChange,
  onCreateContact,
}: ContactToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
      <SearchInput
        value={search}
        onChange={onSearchChange}
        placeholder="Search contacts by name, email, company..."
        className="w-full sm:max-w-md"
      />

      <PrimaryButton onClick={onCreateContact} icon={Users}>
        + New Contact
      </PrimaryButton>
    </div>
  );
}
