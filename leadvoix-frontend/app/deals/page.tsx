"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import DealTable from "@/modules/deals/components/DealTable";
import DealForm from "@/modules/deals/components/DealForm";
import { deleteDeal } from "@/modules/deals/api/dealApi";
import { useDeals } from "@/modules/deals/hooks/useDeals";
import { Deal } from "@/modules/deals/types/deal.types";
import { usePipelines } from "@/modules/pipelines/hooks/usePipelines";
import { usePipelineStages } from "@/modules/pipelines/hooks/usePipelineStages";
import {
  PageContainer,
  PageHeader,
  PrimaryButton,
  SecondaryButton,
  SearchInput,
  FilterDropdown,
  Modal,
  ConfirmationDialog,
} from "@/components/crm";

export default function DealsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
  const [dealToDelete, setDealToDelete] = useState<Deal | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [pipelineId, setPipelineId] = useState("");
  const [page, setPage] = useState(1);

  const { data: pipelinesData } = usePipelines();

  const filters = {
    page,
    limit: 10,
    search,
    status,
    pipeline_id: pipelineId ? Number(pipelineId) : undefined,
  };

  const { data, isLoading, isError } = useDeals(filters);

  const selectedPipelineId = data?.items?.[0]?.pipeline_id ?? 0;
  const { data: stagesData } = usePipelineStages(selectedPipelineId);

  const pipelineNames = Object.fromEntries(
    (pipelinesData?.items ?? []).map((pipeline) => [
      pipeline.id,
      pipeline.name,
    ])
  );

  const stageNames = Object.fromEntries(
    (stagesData ?? []).map((stage) => [
      stage.id,
      stage.name,
    ])
  );

  const handleDealSuccess = () => {
    setShowForm(false);
    setSelectedDeal(null);
    void queryClient.invalidateQueries({ queryKey: ["deals"] });
  };

  const handleEdit = (deal: Deal) => {
    setSelectedDeal(deal);
    setShowForm(true);
  };

  const handleConfirmDelete = async () => {
    if (!dealToDelete) return;

    try {
      setDeleteLoading(true);
      await deleteDeal(dealToDelete.id);
      await queryClient.invalidateQueries({ queryKey: ["deals"] });
      setDealToDelete(null);
    } catch (error) {
      console.error("Failed to delete deal:", error);
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <PageContainer>
        <PageHeader
          title="Deals & Opportunities"
          subtitle="Track revenue opportunities, forecast pipeline velocity, and close deals faster."
          badge="CRM"
          action={
            <PrimaryButton
              onClick={() => {
                setSelectedDeal(null);
                setShowForm(true);
              }}
            >
              <Plus className="h-4 w-4" />
              New Deal
            </PrimaryButton>
          }
        />

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="flex-1">
            <SearchInput
              value={search}
              onChange={(value) => {
                setSearch(value);
                setPage(1);
              }}
              placeholder="Search deals by title or description..."
            />
          </div>

          <FilterDropdown
            label="Status"
            value={status}
            onChange={(val) => {
              setStatus(val);
              setPage(1);
            }}
            options={[
              { label: "All Statuses", value: "" },
              { label: "Open", value: "OPEN" },
              { label: "Won", value: "WON" },
              { label: "Lost", value: "LOST" },
            ]}
          />

          <FilterDropdown
            label="Pipeline"
            value={pipelineId}
            onChange={(val) => {
              setPipelineId(val);
              setPage(1);
            }}
            options={[
              { label: "All Pipelines", value: "" },
              ...(pipelinesData?.items.map((pipeline) => ({
                label: pipeline.name,
                value: String(pipeline.id),
              })) ?? []),
            ]}
          />
        </div>

        <DealTable
          deals={data?.items || []}
          isLoading={isLoading}
          isError={isError}
          onEdit={handleEdit}
          onDelete={(deal) => setDealToDelete(deal)}
          pipelineNames={pipelineNames}
          stageNames={stageNames}
        />

        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between border-t border-[#273449] pt-4 text-xs text-[#94A3B8]">
            <span>
              Page <span className="font-mono text-[#F5F7FC]">{page}</span> of{" "}
              <span className="font-mono text-[#F5F7FC]">{data.total_pages}</span>
            </span>

            <div className="flex items-center gap-2">
              <SecondaryButton
                size="sm"
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={page === 1}
              >
                Previous
              </SecondaryButton>

              <SecondaryButton
                size="sm"
                onClick={() =>
                  setPage((current) => Math.min(data.total_pages, current + 1))
                }
                disabled={page >= data.total_pages}
              >
                Next
              </SecondaryButton>
            </div>
          </div>
        )}

        <Modal
          isOpen={showForm}
          onClose={() => {
            setShowForm(false);
            setSelectedDeal(null);
          }}
          title={selectedDeal ? `Edit Deal: ${selectedDeal.title}` : "Create New Deal"}
          maxWidth="max-w-2xl"
        >
          <DealForm
            key={selectedDeal?.id ?? "create"}
            deal={selectedDeal}
            onSuccess={handleDealSuccess}
            onCancel={() => {
              setShowForm(false);
              setSelectedDeal(null);
            }}
          />
        </Modal>

        <ConfirmationDialog
          isOpen={Boolean(dealToDelete)}
          onClose={() => setDealToDelete(null)}
          onConfirm={handleConfirmDelete}
          title="Delete Deal"
          message={`Are you sure you want to delete deal "${dealToDelete?.title}"? This action cannot be undone.`}
          confirmLabel="Delete Deal"
          variant="danger"
          loading={deleteLoading}
        />
      </PageContainer>
    </DashboardLayout>
  );
}
