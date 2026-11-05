"use client";

import React from "react";
import { UserPlus } from "lucide-react";
import { SearchInput, PrimaryButton } from "@/components/crm";

interface LeadToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  onCreateLead: () => void;
}

export default function LeadToolbar({
  search,
  onSearchChange,
  onCreateLead,
}: LeadToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
      <SearchInput
        value={search}
        onChange={onSearchChange}
        placeholder="Search leads by name, email, company..."
        className="w-full sm:max-w-md"
      />

      <PrimaryButton onClick={onCreateLead} icon={UserPlus}>
        + New Lead
      </PrimaryButton>
    </div>
  );
}
