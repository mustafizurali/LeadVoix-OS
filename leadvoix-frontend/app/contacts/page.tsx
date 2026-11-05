"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import ContactToolbar from "@/modules/contacts/components/ContactToolbar";
import ContactTable from "@/modules/contacts/components/ContactTable";
import CreateContactModal from "@/modules/contacts/components/CreateContactModal";
import EditContactModal from "@/modules/contacts/components/EditContactModal";
import { PageContainer, PageHeader, ConfirmationDialog } from "@/components/crm";

import { deleteContact } from "@/modules/contacts/api/contactApi";
import { Contact } from "@/modules/contacts/types/contact.types";

export default function ContactsPage() {
  const queryClient = useQueryClient();

  const [openCreate, setOpenCreate] = useState(false);
  const [openEdit, setOpenEdit] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);

  const [deleteConfirmContact, setDeleteConfirmContact] = useState<Contact | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleEditContact = (contact: Contact) => {
    setSelectedContact(contact);
    setOpenEdit(true);
  };

  const handleCloseEdit = () => {
    setOpenEdit(false);
    setSelectedContact(null);
  };

  const handleDeleteContact = (contact: Contact) => {
    setDeleteConfirmContact(contact);
  };

  const confirmDelete = async () => {
    if (!deleteConfirmContact) return;

    try {
      setIsDeleting(true);
      await deleteContact(deleteConfirmContact.id);
      await queryClient.invalidateQueries({
        queryKey: ["contacts"],
      });
      setDeleteConfirmContact(null);
    } catch (error) {
      console.error("Failed to delete contact:", error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <DashboardLayout>
      <PageContainer>
        <PageHeader
          title="Contacts"
          subtitle="Directory of customer stakeholders, accounts, and individual representatives."
          badge={{ label: "Directory", variant: "cyan" }}
        />

        <ContactToolbar
          search={search}
          onSearchChange={setSearch}
          onCreateContact={() => setOpenCreate(true)}
        />

        <ContactTable
          search={search}
          onEditContact={handleEditContact}
          onDeleteContact={handleDeleteContact}
          onCreateContact={() => setOpenCreate(true)}
        />
      </PageContainer>

      <CreateContactModal
        open={openCreate}
        onClose={() => setOpenCreate(false)}
      />

      <EditContactModal
        open={openEdit}
        onClose={handleCloseEdit}
        contact={selectedContact}
      />

      <ConfirmationDialog
        open={!!deleteConfirmContact}
        onClose={() => setDeleteConfirmContact(null)}
        onConfirm={confirmDelete}
        title="Delete Contact Record"
        description={`Are you sure you want to delete "${deleteConfirmContact?.first_name} ${deleteConfirmContact?.last_name || ""}"? This operation cannot be undone.`}
        confirmLabel="Delete Contact"
        loading={isDeleting}
      />
    </DashboardLayout>
  );
}
