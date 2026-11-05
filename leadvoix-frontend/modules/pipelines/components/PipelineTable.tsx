"use client";

import { Fragment, useState } from "react";
import { ChevronDown, ChevronRight, Edit2, Trash2, GitFork, Star } from "lucide-react";

import { usePipelines } from "../hooks/usePipelines";
import type { Pipeline } from "../types/pipeline.types";
import PipelineStageList from "./PipelineStageList";
import {
  SecondaryButton,
  DangerButton,
  StatusBadge,
  TableSkeleton,
  EmptyState,
} from "@/components/crm";

interface PipelineTableProps {
  search: string;
  onEditPipeline: (pipeline: Pipeline) => void;
  onDeletePipeline: (pipeline: Pipeline) => void;
}

export default function PipelineTable({
  search,
  onEditPipeline,
  onDeletePipeline,
}: PipelineTableProps) {
  const [expandedPipelineId, setExpandedPipelineId] = useState<number | null>(
    null
  );

  const { data, isLoading, error } = usePipelines();
  const pipelines: Pipeline[] = data?.items ?? [];

  const normalizedSearch = search.trim().toLowerCase();

  const filteredPipelines = pipelines.filter((pipeline) => {
    if (!normalizedSearch) {
      return true;
    }

    return [pipeline.name, pipeline.description, pipeline.color]
      .filter((value): value is string => Boolean(value))
      .some((value) => value.toLowerCase().includes(normalizedSearch));
  });

  const togglePipeline = (pipelineId: number) => {
    setExpandedPipelineId((current) =>
      current === pipelineId ? null : pipelineId
    );
  };

  if (isLoading) {
    return <TableSkeleton rows={4} cols={6} />;
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-6 text-sm text-rose-400">
        Failed to load sales pipelines.
      </div>
    );
  }

  if (filteredPipelines.length === 0) {
    return (
      <EmptyState
        title="No pipelines found"
        description={
          search
            ? "No pipelines match your current search terms."
            : "No sales pipelines configured yet. Create one to organize deal stages."
        }
        icon={GitFork}
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-[#273449] bg-[#151D32] shadow-sm">
      <div className="flex items-center justify-between border-b border-[#273449] px-6 py-4">
        <h2 className="text-base font-semibold text-[#F5F7FC]">
          All Pipelines
        </h2>
        <span className="font-mono text-xs text-[#94A3B8]">
          Showing {filteredPipelines.length} of {pipelines.length}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-[#273449] text-left text-sm">
          <thead className="bg-[#0E1528] text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
            <tr>
              <th className="w-10 px-4 py-3"></th>
              <th className="px-6 py-3">Pipeline Name</th>
              <th className="px-6 py-3">Description</th>
              <th className="px-6 py-3">Color</th>
              <th className="px-6 py-3">Default</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3 text-right">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-[#273449]">
            {filteredPipelines.map((pipeline) => {
              const isExpanded = expandedPipelineId === pipeline.id;

              return (
                <Fragment key={pipeline.id}>
                  <tr
                    className={`transition hover:bg-[#1E293B]/40 ${
                      isExpanded ? "bg-[#1E293B]/20" : ""
                    }`}
                  >
                    <td className="px-4 py-4 text-center">
                      <button
                        type="button"
                        onClick={() => togglePipeline(pipeline.id)}
                        className="rounded p-1 text-[#94A3B8] transition hover:bg-[#273449] hover:text-[#F5F7FC]"
                        title={isExpanded ? "Collapse stages" : "Expand stages"}
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>
                    </td>

                    <td className="px-6 py-4">
                      <button
                        type="button"
                        onClick={() => togglePipeline(pipeline.id)}
                        className="text-left font-medium text-[#F5F7FC] transition hover:text-[#7657F6]"
                      >
                        <div className="flex items-center gap-2">
                          <span>{pipeline.name}</span>
                          {pipeline.is_default && (
                            <span className="inline-flex items-center gap-1 rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-amber-400 border border-amber-500/20">
                              <Star className="h-2.5 w-2.5 fill-current" />
                              Default
                            </span>
                          )}
                        </div>
                      </button>
                    </td>

                    <td className="max-w-xs truncate px-6 py-4 text-sm text-[#94A3B8]">
                      {pipeline.description || "—"}
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span
                          className="h-3.5 w-3.5 rounded-full border border-white/20"
                          style={{
                            backgroundColor: pipeline.color ?? "#7657F6",
                          }}
                        />
                        <span className="font-mono text-xs text-[#94A3B8]">
                          {pipeline.color ?? "-"}
                        </span>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <span className="text-xs font-medium text-[#94A3B8]">
                        {pipeline.is_default ? "Yes" : "No"}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      <StatusBadge
                        status={pipeline.is_active ? "active" : "inactive"}
                      />
                    </td>

                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <SecondaryButton
                          size="sm"
                          onClick={() => onEditPipeline(pipeline)}
                        >
                          <Edit2 className="h-3.5 w-3.5" />
                          Edit
                        </SecondaryButton>

                        <DangerButton
                          size="sm"
                          onClick={() => onDeletePipeline(pipeline)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Delete
                        </DangerButton>
                      </div>
                    </td>
                  </tr>

                  {isExpanded && (
                    <tr>
                      <td colSpan={7} className="bg-[#0B1020]/70 p-4">
                        <PipelineStageList pipeline={pipeline} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-[#273449] bg-[#0E1528] px-6 py-3.5 text-xs text-[#94A3B8]">
        <p>Click on any pipeline to expand and configure its stages.</p>
        <p className="font-mono">Total: {pipelines.length}</p>
      </div>
    </div>
  );
}
