"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Plus, Edit2, Layers } from "lucide-react";

import { usePipelineStages } from "../hooks/usePipelineStages";
import type { Pipeline, PipelineStage, PipelineStageType } from "../types/pipeline.types";
import CreateStageModal from "./CreateStageModal";
import EditStageModal from "./EditStageModal";
import { PrimaryButton, SecondaryButton, StatusBadge } from "@/components/crm";

interface PipelineStageListProps {
  pipeline: Pipeline;
}

function getStageTypeBadge(type: PipelineStageType) {
  switch (type) {
    case "WON":
      return (
        <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
          Won
        </span>
      );
    case "LOST":
      return (
        <span className="inline-flex items-center rounded-full bg-rose-500/10 px-2.5 py-0.5 text-xs font-medium text-rose-400 border border-rose-500/20">
          Lost
        </span>
      );
    case "OPEN":
      return (
        <span className="inline-flex items-center rounded-full bg-[#7657F6]/10 px-2.5 py-0.5 text-xs font-medium text-[#7657F6] border border-[#7657F6]/20">
          Open
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center rounded-full bg-cyan-500/10 px-2.5 py-0.5 text-xs font-medium text-cyan-400 border border-cyan-500/20">
          Normal
        </span>
      );
  }
}

export default function PipelineStageList({ pipeline }: PipelineStageListProps) {
  const queryClient = useQueryClient();

  const [openCreate, setOpenCreate] = useState(false);
  const [openEdit, setOpenEdit] = useState(false);
  const [selectedStage, setSelectedStage] = useState<PipelineStage | null>(null);

  const {
    data: allStages = [],
    isLoading,
    error,
  } = usePipelineStages(pipeline.id);

  const stages = useMemo(() => {
    return allStages
      .filter((stage: PipelineStage) => stage.pipeline_id === pipeline.id)
      .sort((a: PipelineStage, b: PipelineStage) => a.position - b.position);
  }, [allStages, pipeline.id]);

  const nextPosition = useMemo(() => {
    if (stages.length === 0) return 0;
    const maxPos = Math.max(...stages.map((s: PipelineStage) => s.position));
    return maxPos + 1;
  }, [stages]);

  const existingPositions = useMemo(() => {
    return stages.map((s: PipelineStage) => s.position);
  }, [stages]);

  const handleOpenEdit = (stage: PipelineStage) => {
    setSelectedStage(stage);
    setOpenEdit(true);
  };

  const refreshStages = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["pipeline-stages"],
    });
  };

  return (
    <div className="rounded-xl border border-[#273449] bg-[#0E1528] p-5 shadow-inner">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-[#7657F6]" />
            <h3 className="text-base font-semibold text-[#F5F7FC]">
              Pipeline Stages ({stages.length})
            </h3>
          </div>
          <p className="mt-0.5 text-xs text-[#94A3B8]">
            Sequential stages that deals flow through in this pipeline.
          </p>
        </div>

        <PrimaryButton
          size="sm"
          onClick={() => setOpenCreate(true)}
        >
          <Plus className="h-3.5 w-3.5" />
          Add Stage
        </PrimaryButton>
      </div>

      {isLoading ? (
        <div className="py-6 text-center text-sm text-[#94A3B8]">
          Loading pipeline stages...
        </div>
      ) : error ? (
        <div className="rounded-lg border border-rose-500/20 bg-rose-500/10 p-3 text-sm text-rose-400">
          Failed to load stages for this pipeline.
        </div>
      ) : stages.length === 0 ? (
        <div className="rounded-lg border border-dashed border-[#273449] bg-[#151D32]/50 p-6 text-center">
          <p className="text-sm text-[#94A3B8]">
            No stages defined for this pipeline yet.
          </p>
          <SecondaryButton
            size="sm"
            onClick={() => setOpenCreate(true)}
            className="mt-3"
          >
            Create First Stage
          </SecondaryButton>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-[#273449] bg-[#151D32]">
          <table className="min-w-full divide-y divide-[#273449] text-left text-sm">
            <thead className="bg-[#0E1528] text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
              <tr>
                <th className="px-4 py-3">Order</th>
                <th className="px-4 py-3">Stage Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Color</th>
                <th className="px-4 py-3">Probability</th>
                <th className="px-4 py-3">SLA Days</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#273449]">
              {stages.map((stage: PipelineStage, index: number) => (
                <tr
                  key={stage.id}
                  className="transition hover:bg-[#1E293B]/40"
                >
                  <td className="px-4 py-3">
                    <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#273449] font-mono text-xs font-semibold text-[#F5F7FC]">
                      {stage.position ?? index + 1}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-[#F5F7FC]">
                    {stage.name}
                  </td>
                  <td className="px-4 py-3">
                    {getStageTypeBadge(stage.stage_type)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span
                        className="h-3.5 w-3.5 rounded-full border border-white/20"
                        style={{ backgroundColor: stage.color ?? "#64748b" }}
                      />
                      <span className="font-mono text-xs text-[#94A3B8]">
                        {stage.color ?? "-"}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-sm text-[#F5F7FC]">
                    {stage.probability}%
                  </td>
                  <td className="px-4 py-3 font-mono text-sm text-[#94A3B8]">
                    {stage.sla_days ? `${stage.sla_days}d` : "None"}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge
                      status={stage.is_active ? "active" : "inactive"}
                    />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <SecondaryButton
                      size="sm"
                      onClick={() => handleOpenEdit(stage)}
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                      Edit
                    </SecondaryButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <CreateStageModal
        open={openCreate}
        onClose={async () => {
          setOpenCreate(false);
          await refreshStages();
        }}
        pipelineId={pipeline.id}
        defaultPosition={nextPosition}
        existingPositions={existingPositions}
      />

      <EditStageModal
        open={openEdit}
        onClose={async () => {
          setOpenEdit(false);
          setSelectedStage(null);
          await refreshStages();
        }}
        stage={selectedStage}
        existingPositions={
          selectedStage
            ? existingPositions.filter((p) => p !== selectedStage.position)
            : existingPositions
        }
      />
    </div>
  );
}
