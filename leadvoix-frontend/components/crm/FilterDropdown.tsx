"use client";

import React from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface FilterOption {
  value: string;
  label: string;
}

interface FilterDropdownProps {
  value: string;
  onChange: (value: string) => void;
  options: FilterOption[];
  label?: string;
  placeholder?: string;
  className?: string;
}

export function FilterDropdown({
  value,
  onChange,
  options,
  label,
  placeholder = "All",
  className,
}: FilterDropdownProps) {
  return (
    <div className={cn("relative inline-flex items-center", className)}>
      {label && (
        <span className="mr-2 text-xs font-medium text-[#94A3B8]">
          {label}:
        </span>
      )}
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="h-9 appearance-none rounded-lg border border-[#273449] bg-[#0E1528] pl-3 pr-8 text-xs font-medium text-[#F5F7FC] transition-colors outline-none hover:border-slate-600 focus:border-[#7657F6] focus:ring-1 focus:ring-[#7657F6] cursor-pointer"
        >
          <option value="" className="bg-[#151D32] text-[#F5F7FC]">
            {placeholder}
          </option>
          {options.map((opt) => (
            <option
              key={opt.value}
              value={opt.value}
              className="bg-[#151D32] text-[#F5F7FC]"
            >
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#6F7D9E]" />
      </div>
    </div>
  );
}
