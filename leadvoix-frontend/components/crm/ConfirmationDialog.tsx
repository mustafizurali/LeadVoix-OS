"use client";

import React from "react";
import { AlertTriangle } from "lucide-react";
import { Modal } from "./Modal";
import { DangerButton, SecondaryButton, PrimaryButton } from "./Buttons";

interface ConfirmationDialogProps {
  open?: boolean;
  isOpen?: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  description?: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "primary";
  loading?: boolean;
}

export function ConfirmationDialog({
  open,
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  loading = false,
}: ConfirmationDialogProps) {
  const isDialogOpen = Boolean(open ?? isOpen ?? false);
  const resolvedText = description || message || "";

  return (
    <Modal open={isDialogOpen} onClose={onClose} title={title} maxWidth="md">
      <div className="space-y-4">
        <div className="flex items-start gap-3">
          {variant === "danger" && (
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-red-500/30 bg-red-500/15 text-red-400">
              <AlertTriangle className="h-5 w-5" />
            </div>
          )}
          <p className="text-xs sm:text-sm text-[#94A3B8] leading-relaxed">
            {resolvedText}
          </p>
        </div>

        <div className="mt-6 flex justify-end gap-3 pt-3 border-t border-[#273449]">
          <SecondaryButton onClick={onClose} disabled={loading}>
            {cancelLabel}
          </SecondaryButton>
          {variant === "danger" ? (
            <DangerButton onClick={onConfirm} loading={loading}>
              {confirmLabel}
            </DangerButton>
          ) : (
            <PrimaryButton onClick={onConfirm} loading={loading}>
              {confirmLabel}
            </PrimaryButton>
          )}
        </div>
      </div>
    </Modal>
  );
}
