"use client";

import React, { useState } from "react";
import { Edit, Trash2, Globe, Building2, AlertCircle } from "lucide-react";

import { useCompanies } from "../hooks/useCompanies";
import { Company } from "../types/company.types";
import { DataTable, StatusBadge, TableSkeleton, EmptyState } from "@/components/crm";

interface CompanyTableProps {
  search: string;
  onEditCompany: (company: Company) => void;
  onDeleteCompany: (company: Company) => void;
  onCreateCompany?: () => void;
}

export default function CompanyTable({
  search,
  onEditCompany,
  onDeleteCompany,
  onCreateCompany,
}: CompanyTableProps) {
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useCompanies({
    search,
    page,
    limit: 10,
    sort_by: "created_at",
    order: "desc",
  });

  const companies = data?.items ?? [];

  if (isLoading) {
    return <TableSkeleton rows={6} columns={6} />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
        <AlertCircle className="h-8 w-8 text-red-400 mb-2" />
        <p className="text-sm font-semibold text-red-200">Failed to load companies</p>
        <button
          type="button"
          onClick={() => refetch()}
          className="mt-4 rounded-lg bg-red-500/20 px-3.5 py-1.5 text-xs font-semibold text-red-300 hover:bg-red-500/30 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (companies.length === 0) {
    return (
      <EmptyState
        icon={Building2}
        title={search ? "No matching companies found" : "No companies in your CRM"}
        description={
          search
            ? `No records matched your search query "${search}". Try clearing your filters.`
            : "Organize accounts, business domains, and target organization records."
        }
        action={
          onCreateCompany ? (
            <button
              type="button"
              onClick={onCreateCompany}
              className="rounded-lg bg-[#7657F6] px-4 py-2 text-xs font-semibold text-white shadow hover:bg-[#6846ed] transition-colors"
            >
              + Create Company
            </button>
          ) : undefined
        }
      />
    );
  }

  return (
    <DataTable
      title="All Companies"
      countLabel={`${companies.length} records shown`}
      total={data?.total}
      page={data?.page}
      totalPages={data?.total_pages}
      onPageChange={setPage}
    >
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-[#273449] bg-[#0E1528] text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
            <th className="px-6 py-3.5">Company Account</th>
            <th className="px-4 py-3.5">Domain</th>
            <th className="px-4 py-3.5">Industry</th>
            <th className="px-4 py-3.5">Size</th>
            <th className="px-4 py-3.5">Status</th>
            <th className="px-6 py-3.5 text-right">Actions</th>
          </tr>
        </thead>

        <tbody className="divide-y divide-[#273449]">
          {companies.map((company) => {
            const initials = company.name
              ? company.name
                  .split(" ")
                  .map((n) => n[0])
                  .slice(0, 2)
                  .join("")
                  .toUpperCase()
              : "CO";

            return (
              <tr
                key={company.id}
                className="group transition-colors hover:bg-slate-800/40"
              >
                {/* Company Name */}
                <td className="px-6 py-3.5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-tr from-[#35D6C1]/30 to-[#24C8D8]/40 font-bold text-white border border-[#273449]">
                      {initials}
                    </div>
                    <div>
                      <p className="font-semibold text-[#F5F7FC] truncate group-hover:text-[#24C8D8] transition-colors">
                        {company.name}
                      </p>
                      {company.website && (
                        <a
                          href={company.website.startsWith("http") ? company.website : `https://${company.website}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-[11px] text-[#24C8D8] hover:underline"
                        >
                          <Globe className="h-3 w-3" />
                          <span>{company.website.replace(/^https?:\/\//, "")}</span>
                        </a>
                      )}
                    </div>
                  </div>
                </td>

                {/* Domain */}
                <td className="px-4 py-3.5 text-[#F5F7FC]">
                  {company.domain || "—"}
                </td>

                {/* Industry */}
                <td className="px-4 py-3.5 text-[#94A3B8]">
                  {company.industry || "—"}
                </td>

                {/* Size */}
                <td className="px-4 py-3.5 text-[#94A3B8]">
                  {company.company_size || "—"}
                </td>

                {/* Status */}
                <td className="px-4 py-3.5">
                  <StatusBadge status={company.status} type="lead" />
                </td>

                {/* Actions */}
                <td className="px-6 py-3.5 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => onEditCompany(company)}
                      className="rounded-lg p-1.5 text-[#94A3B8] transition-colors hover:bg-slate-800 hover:text-[#24C8D8]"
                      title="Edit Company"
                    >
                      <Edit className="h-3.5 w-3.5" />
                    </button>

                    <button
                      type="button"
                      onClick={() => onDeleteCompany(company)}
                      className="rounded-lg p-1.5 text-[#94A3B8] transition-colors hover:bg-red-500/15 hover:text-red-400"
                      title="Delete Company"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </DataTable>
  );
}
