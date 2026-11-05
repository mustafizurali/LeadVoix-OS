"use client";

import React, { useState } from "react";
import { Edit, Trash2, Mail, Phone, Building2, Users, AlertCircle } from "lucide-react";

import { useContacts } from "../hooks/useContacts";
import { Contact } from "../types/contact.types";
import { DataTable, StatusBadge, TableSkeleton, EmptyState } from "@/components/crm";

interface ContactTableProps {
  search: string;
  onEditContact: (contact: Contact) => void;
  onDeleteContact: (contact: Contact) => void;
  onCreateContact?: () => void;
}

export default function ContactTable({
  search,
  onEditContact,
  onDeleteContact,
  onCreateContact,
}: ContactTableProps) {
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useContacts({
    search,
    page,
    limit: 10,
    sort_by: "created_at",
    order: "desc",
  });

  const contacts = data?.items ?? [];

  if (isLoading) {
    return <TableSkeleton rows={6} columns={5} />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
        <AlertCircle className="h-8 w-8 text-red-400 mb-2" />
        <p className="text-sm font-semibold text-red-200">Failed to load contacts</p>
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

  if (contacts.length === 0) {
    return (
      <EmptyState
        icon={Users}
        title={search ? "No matching contacts found" : "No contacts in your CRM"}
        description={
          search
            ? `No records matched your search query "${search}". Try clearing your filters.`
            : "Keep track of individual accounts, representatives, and business connections."
        }
        action={
          onCreateContact ? (
            <button
              type="button"
              onClick={onCreateContact}
              className="rounded-lg bg-[#7657F6] px-4 py-2 text-xs font-semibold text-white shadow hover:bg-[#6846ed] transition-colors"
            >
              + Create Contact
            </button>
          ) : undefined
        }
      />
    );
  }

  return (
    <DataTable
      title="All Contacts"
      countLabel={`${contacts.length} records shown`}
      total={data?.total}
      page={data?.page}
      totalPages={data?.total_pages}
      onPageChange={setPage}
    >
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-[#273449] bg-[#0E1528] text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
            <th className="px-6 py-3.5">Contact Name</th>
            <th className="px-4 py-3.5">Company</th>
            <th className="px-4 py-3.5">Status</th>
            <th className="px-4 py-3.5">Added</th>
            <th className="px-6 py-3.5 text-right">Actions</th>
          </tr>
        </thead>

        <tbody className="divide-y divide-[#273449]">
          {contacts.map((contact) => {
            const fullName = [contact.first_name, contact.last_name].filter(Boolean).join(" ") || "Contact";
            const initials = fullName
              .split(" ")
              .map((n) => n[0])
              .slice(0, 2)
              .join("")
              .toUpperCase() || "C";

            return (
              <tr
                key={contact.id}
                className="group transition-colors hover:bg-slate-800/40"
              >
                {/* Contact Name & Details */}
                <td className="px-6 py-3.5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-tr from-[#24C8D8]/30 to-[#7657F6]/40 font-bold text-white border border-[#273449]">
                      {initials}
                    </div>
                    <div className="min-w-0">
                      <p className="font-semibold text-[#F5F7FC] truncate group-hover:text-[#24C8D8] transition-colors">
                        {fullName}
                      </p>
                      <div className="flex items-center gap-2 text-[11px] text-[#94A3B8]">
                        {contact.email && (
                          <span className="flex items-center gap-1 truncate max-w-[150px]">
                            <Mail className="h-3 w-3 shrink-0" />
                            {contact.email}
                          </span>
                        )}
                        {contact.phone && !contact.email && (
                          <span className="flex items-center gap-1 truncate">
                            <Phone className="h-3 w-3 shrink-0" />
                            {contact.phone}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </td>

                {/* Company */}
                <td className="px-4 py-3.5 text-[#F5F7FC]">
                  {contact.company ? (
                    <div className="flex items-center gap-1.5">
                      <Building2 className="h-3.5 w-3.5 text-[#94A3B8]" />
                      <span className="truncate max-w-[140px]">{contact.company}</span>
                    </div>
                  ) : (
                    <span className="text-[#94A3B8]/50">—</span>
                  )}
                </td>

                {/* Status */}
                <td className="px-4 py-3.5">
                  <StatusBadge status={contact.status} type="lead" />
                </td>

                {/* Created */}
                <td className="px-4 py-3.5 text-[#94A3B8]">
                  {contact.created_at ? new Date(contact.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—"}
                </td>

                {/* Actions */}
                <td className="px-6 py-3.5 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => onEditContact(contact)}
                      className="rounded-lg p-1.5 text-[#94A3B8] transition-colors hover:bg-slate-800 hover:text-[#24C8D8]"
                      title="Edit Contact"
                    >
                      <Edit className="h-3.5 w-3.5" />
                    </button>

                    <button
                      type="button"
                      onClick={() => onDeleteContact(contact)}
                      className="rounded-lg p-1.5 text-[#94A3B8] transition-colors hover:bg-red-500/15 hover:text-red-400"
                      title="Delete Contact"
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
