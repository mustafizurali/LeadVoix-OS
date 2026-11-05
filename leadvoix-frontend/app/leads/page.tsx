"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import LeadToolbar from "@/modules/leads/components/LeadToolbar";
import LeadTable from "@/modules/leads/components/LeadTable";
import CreateLeadModal from "@/modules/leads/components/CreateLeadModal";
import EditLeadModal from "@/modules/leads/components/EditLeadModal";
import { PageContainer, PageHeader, ConfirmationDialog } from "@/components/crm";

import { deleteLead } from "@/modules/leads/api/leadApi";
import { Lead } from "@/modules/leads/types/lead.types";

export default function LeadsPage() {
  const queryClient = useQueryClient();

  const [openCreate, setOpenCreate] = useState(false);
  const [openEdit, setOpenEdit] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  // Confirmation dialog state
  const [deleteConfirmLead, setDeleteConfirmLead] = useState<Lead | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleEditLead = (lead: Lead) => {
    setSelectedLead(lead);
    setOpenEdit(true);
  };

  const handleCloseEdit = () => {
    setOpenEdit(false);
    setSelectedLead(null);
  };

  const handleDeleteLead = (lead: Lead) => {
    setDeleteConfirmLead(lead);
  };

  const confirmDelete = async () => {
    if (!deleteConfirmLead) return;

    try {
      setIsDeleting(true);
      await deleteLead(deleteConfirmLead.id);
      await queryClient.invalidateQueries({
        queryKey: ["leads"],
      });
      setDeleteConfirmLead(null);
    } catch (error) {
      console.error("Failed to delete lead:", error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <DashboardLayout>
      <PageContainer>
        <PageHeader
          title="Leads"
          subtitle="Manage sales pipeline prospects and automated AI inbound contacts."
          badge={{ label: "Sales Pipeline", variant: "cyan" }}
        />

        <LeadToolbar
          onCreateLead={() => setOpenCreate(true)}
          search={search}
          onSearchChange={setSearch}
        />

        <LeadTable
          search={search}
          onEditLead={handleEditLead}
          onDeleteLead={handleDeleteLead}
          onCreateLead={() => setOpenCreate(true)}
        />
      </PageContainer>

      <CreateLeadModal
        open={openCreate}
        onClose={() => setOpenCreate(false)}
      />

      <EditLeadModal
        open={openEdit}
        onClose={handleCloseEdit}
        lead={selectedLead}
      />

      <ConfirmationDialog
        open={!!deleteConfirmLead}
        onClose={() => setDeleteConfirmLead(null)}
        onConfirm={confirmDelete}
        title="Delete Lead Record"
        description={`Are you sure you want to delete "${deleteConfirmLead?.first_name} ${deleteConfirmLead?.last_name || ""}"? This operation cannot be undone.`}
        confirmLabel="Delete Lead"
        loading={isDeleting}
      />
    </DashboardLayout>
  );
}
