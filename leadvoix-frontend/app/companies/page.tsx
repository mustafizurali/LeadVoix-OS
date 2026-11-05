"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import CompanyToolbar from "@/modules/companies/components/CompanyToolbar";
import CompanyTable from "@/modules/companies/components/CompanyTable";
import CreateCompanyModal from "@/modules/companies/components/CreateCompanyModal";
import EditCompanyModal from "@/modules/companies/components/EditCompanyModal";
import { PageContainer, PageHeader, ConfirmationDialog } from "@/components/crm";

import { deleteCompany } from "@/modules/companies/api/companyApi";
import { Company } from "@/modules/companies/types/company.types";

export default function CompaniesPage() {
  const queryClient = useQueryClient();

  const [openCreate, setOpenCreate] = useState(false);
  const [openEdit, setOpenEdit] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);

  const [deleteConfirmCompany, setDeleteConfirmCompany] = useState<Company | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleEditCompany = (company: Company) => {
    setSelectedCompany(company);
    setOpenEdit(true);
  };

  const handleCloseEdit = () => {
    setOpenEdit(false);
    setSelectedCompany(null);
  };

  const handleDeleteCompany = (company: Company) => {
    setDeleteConfirmCompany(company);
  };

  const confirmDelete = async () => {
    if (!deleteConfirmCompany) return;

    try {
      setIsDeleting(true);
      await deleteCompany(deleteConfirmCompany.id);
      await queryClient.invalidateQueries({
        queryKey: ["companies"],
      });
      setDeleteConfirmCompany(null);
    } catch (error) {
      console.error("Failed to delete company:", error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <DashboardLayout>
      <PageContainer>
        <PageHeader
          title="Companies"
          subtitle="Manage corporate accounts, organizational domains, and client profiles."
          badge={{ label: "Accounts", variant: "cyan" }}
        />

        <CompanyToolbar
          search={search}
          onSearchChange={setSearch}
          onCreateCompany={() => setOpenCreate(true)}
        />

        <CompanyTable
          search={search}
          onEditCompany={handleEditCompany}
          onDeleteCompany={handleDeleteCompany}
          onCreateCompany={() => setOpenCreate(true)}
        />
      </PageContainer>

      <CreateCompanyModal
        open={openCreate}
        onClose={() => setOpenCreate(false)}
      />

      <EditCompanyModal
        open={openEdit}
        onClose={handleCloseEdit}
        company={selectedCompany}
      />

      <ConfirmationDialog
        open={!!deleteConfirmCompany}
        onClose={() => setDeleteConfirmCompany(null)}
        onConfirm={confirmDelete}
        title="Delete Company Account"
        description={`Are you sure you want to delete "${deleteConfirmCompany?.name}"? All associated account metadata will be affected.`}
        confirmLabel="Delete Company"
        loading={isDeleting}
      />
    </DashboardLayout>
  );
}
