"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import CreatePipelineModal from "@/modules/pipelines/components/CreatePipelineModal";
import EditPipelineModal from "@/modules/pipelines/components/EditPipelineModal";
import PipelineTable from "@/modules/pipelines/components/PipelineTable";
import PipelineToolbar from "@/modules/pipelines/components/PipelineToolbar";
import { deletePipeline } from "@/modules/pipelines/api/pipelineApi";
import type { Pipeline } from "@/modules/pipelines/types/pipeline.types";
import {
  PageContainer,
  PageHeader,
  PrimaryButton,
  ConfirmationDialog,
} from "@/components/crm";

export default function PipelinesPage() {
  const queryClient = useQueryClient();

  const [openCreate, setOpenCreate] = useState(false);
  const [openEdit, setOpenEdit] = useState(false);
  const [search, setSearch] = useState("");

  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
  const [pipelineToDelete, setPipelineToDelete] = useState<Pipeline | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const handleEditPipeline = (pipeline: Pipeline) => {
    setSelectedPipeline(pipeline);
    setOpenEdit(true);
  };

  const handleCloseEdit = () => {
    setOpenEdit(false);
    setSelectedPipeline(null);
  };

  const handleConfirmDelete = async () => {
    if (!pipelineToDelete) return;

    try {
      setDeleteLoading(true);
      await deletePipeline(pipelineToDelete.id);
      await queryClient.invalidateQueries({
        queryKey: ["pipelines"],
      });
      setPipelineToDelete(null);
    } catch (error) {
      console.error("Failed to delete pipeline:", error);
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <PageContainer>
        <PageHeader
          title="Pipelines"
          subtitle="Manage sales pipelines, deal progression workflows, and qualification stages."
          badge="CRM"
          action={
            <PrimaryButton onClick={() => setOpenCreate(true)}>
              <Plus className="h-4 w-4" />
              New Pipeline
            </PrimaryButton>
          }
        />

        <PipelineToolbar
          search={search}
          onSearchChange={setSearch}
        />

        <PipelineTable
          search={search}
          onEditPipeline={handleEditPipeline}
          onDeletePipeline={(pipeline) => setPipelineToDelete(pipeline)}
        />

        <CreatePipelineModal
          open={openCreate}
          onClose={() => setOpenCreate(false)}
        />

        <EditPipelineModal
          open={openEdit}
          onClose={handleCloseEdit}
          pipeline={selectedPipeline}
        />

        <ConfirmationDialog
          isOpen={Boolean(pipelineToDelete)}
          onClose={() => setPipelineToDelete(null)}
          onConfirm={handleConfirmDelete}
          title="Delete Pipeline"
          message={`Are you sure you want to delete pipeline "${pipelineToDelete?.name}"? All associated stages and configuration will be affected.`}
          confirmLabel="Delete Pipeline"
          variant="danger"
          loading={deleteLoading}
        />
      </PageContainer>
    </DashboardLayout>
  );
}
