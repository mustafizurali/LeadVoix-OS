"use client";

import { DollarSign, Edit2, Trash2, Calendar, GitFork } from "lucide-react";
import { Deal } from "../types/deal.types";
import {
  SecondaryButton,
  DangerButton,
  StatusBadge,
  TableSkeleton,
  EmptyState,
} from "@/components/crm";

interface DealTableProps {
  deals: Deal[];
  isLoading: boolean;
  isError: boolean;
  onEdit: (deal: Deal) => void;
  onDelete: (deal: Deal) => void;
  pipelineNames?: Record<number, string>;
  stageNames?: Record<number, string>;
}

function formatCurrency(amount: number, currency: string = "USD") {
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency || "USD",
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${Number(amount).toFixed(2)}`;
  }
}

export default function DealTable({
  deals,
  isLoading,
  isError,
  onEdit,
  onDelete,
  pipelineNames = {},
  stageNames = {},
}: DealTableProps) {
  if (isLoading) {
    return <TableSkeleton rows={5} cols={7} />;
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-6 text-sm text-rose-400">
        Failed to load deals. Please refresh or check your connection.
      </div>
    );
  }

  if (!deals || deals.length === 0) {
    return (
      <EmptyState
        title="No deals found"
        description="No sales opportunities match the selected criteria. Create a new deal to track pipeline progress."
        icon={DollarSign}
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-[#273449] bg-[#151D32] shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-[#273449] text-left text-sm">
          <thead className="bg-[#0E1528] text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
            <tr>
              <th className="px-6 py-3.5">Deal Title</th>
              <th className="px-6 py-3.5">Amount</th>
              <th className="px-6 py-3.5">Status</th>
              <th className="px-6 py-3.5">Pipeline</th>
              <th className="px-6 py-3.5">Stage</th>
              <th className="px-6 py-3.5">Expected Close</th>
              <th className="px-6 py-3.5 text-right">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-[#273449]">
            {deals.map((deal) => {
              const pipelineName = deal.pipeline_id
                ? pipelineNames[deal.pipeline_id] ?? `Pipeline #${deal.pipeline_id}`
                : null;
              const stageName = deal.stage_id
                ? stageNames[deal.stage_id] ?? `Stage #${deal.stage_id}`
                : null;

              return (
                <tr
                  key={deal.id}
                  className="transition hover:bg-[#1E293B]/40"
                >
                  <td className="px-6 py-4">
                    <div className="font-medium text-[#F5F7FC]">
                      {deal.title}
                    </div>
                    {deal.description && (
                      <div className="mt-0.5 max-w-xs truncate text-xs text-[#94A3B8]">
                        {deal.description}
                      </div>
                    )}
                  </td>

                  <td className="px-6 py-4 font-mono font-medium text-[#F5F7FC]">
                    {formatCurrency(Number(deal.amount), deal.currency)}
                  </td>

                  <td className="px-6 py-4">
                    <StatusBadge status={deal.status} />
                  </td>

                  <td className="px-6 py-4">
                    {pipelineName ? (
                      <span className="inline-flex items-center gap-1.5 text-xs text-[#F5F7FC]">
                        <GitFork className="h-3 w-3 text-[#7657F6]" />
                        {pipelineName}
                      </span>
                    ) : (
                      <span className="text-xs text-[#94A3B8]">—</span>
                    )}
                  </td>

                  <td className="px-6 py-4">
                    {stageName ? (
                      <span className="inline-flex rounded-full bg-[#0E1528] border border-[#273449] px-2.5 py-0.5 text-xs font-medium text-[#F5F7FC]">
                        {stageName}
                      </span>
                    ) : (
                      <span className="text-xs text-[#94A3B8]">—</span>
                    )}
                  </td>

                  <td className="px-6 py-4">
                    {deal.expected_close_date ? (
                      <span className="inline-flex items-center gap-1.5 font-mono text-xs text-[#94A3B8]">
                        <Calendar className="h-3 w-3 text-[#94A3B8]" />
                        {deal.expected_close_date}
                      </span>
                    ) : (
                      <span className="text-xs text-[#94A3B8]">—</span>
                    )}
                  </td>

                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <SecondaryButton
                        size="sm"
                        onClick={() => onEdit(deal)}
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                        Edit
                      </SecondaryButton>

                      <DangerButton
                        size="sm"
                        onClick={() => onDelete(deal)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        Delete
                      </DangerButton>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
