"use client";

import { SearchInput } from "@/components/crm";

interface PipelineToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
}

export default function PipelineToolbar({
  search,
  onSearchChange,
}: PipelineToolbarProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="w-full sm:max-w-md">
        <SearchInput
          value={search}
          onChange={onSearchChange}
          placeholder="Search pipelines by name, description..."
        />
      </div>
    </div>
  );
}
