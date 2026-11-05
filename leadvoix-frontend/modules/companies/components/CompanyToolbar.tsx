"use client";

import React from "react";
import { Building2 } from "lucide-react";
import { SearchInput, PrimaryButton } from "@/components/crm";

interface CompanyToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  onCreateCompany: () => void;
}

export default function CompanyToolbar({
  search,
  onSearchChange,
  onCreateCompany,
}: CompanyToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
      <SearchInput
        value={search}
        onChange={onSearchChange}
        placeholder="Search companies by name, domain, industry..."
        className="w-full sm:max-w-md"
      />

      <PrimaryButton onClick={onCreateCompany} icon={Building2}>
        + New Company
      </PrimaryButton>
    </div>
  );
}
