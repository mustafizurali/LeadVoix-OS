"use client";

import React, { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Modal, PrimaryButton, SecondaryButton } from "@/components/crm";
import { updateContact } from "../api/contactApi";
import { Contact, UpdateContactPayload } from "../types/contact.types";
import ContactForm from "./ContactForm";

interface EditContactModalProps {
  open: boolean;
  onClose: () => void;
  contact: Contact | null;
}

export default function EditContactModal({
  open,
  onClose,
  contact,
}: EditContactModalProps) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<UpdateContactPayload>({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    company: "",
    status: "",
  });

  useEffect(() => {
    if (contact) {
      setForm({
        first_name: contact.first_name,
        last_name: contact.last_name ?? "",
        email: contact.email ?? "",
        phone: contact.phone ?? "",
        company: contact.company ?? "",
        status: contact.status,
      });
      setError(null);
    }
  }, [contact]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async () => {
    if (!contact) return;

    if (!form.first_name?.trim()) {
      setError("First Name is required");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const payload = {
        ...form,
        email: form.email?.trim() || undefined,
        phone: form.phone?.trim() || undefined,
        company: form.company?.trim() || undefined,
        last_name: form.last_name?.trim() || undefined,
      };

      await updateContact(contact.id, payload);

      await queryClient.invalidateQueries({
        queryKey: ["contacts"],
      });

      onClose();
    } catch (err: unknown) {
      console.error(err);
      setError("Failed to update contact. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Edit Contact"
      subtitle={`Updating information for ${contact?.first_name ?? "Contact"} ${contact?.last_name ?? ""}`}
      maxWidth="2xl"
    >
      <div className="space-y-5">
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/15 p-3 text-xs text-red-300">
            {error}
          </div>
        )}

        <ContactForm form={form} onChange={handleChange} />

        <div className="flex justify-end gap-3 pt-4 border-t border-[#273449]">
          <SecondaryButton onClick={onClose} disabled={loading}>
            Cancel
          </SecondaryButton>
          <PrimaryButton onClick={handleSubmit} loading={loading}>
            Save Changes
          </PrimaryButton>
        </div>
      </div>
    </Modal>
  );
}
