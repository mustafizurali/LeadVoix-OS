"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface BaseFieldProps {
  label: string;
  error?: string;
  helperText?: string;
  required?: boolean;
  className?: string;
  id?: string;
}

interface InputFieldProps
  extends BaseFieldProps,
    React.InputHTMLAttributes<HTMLInputElement> {
  as?: "input";
}

interface TextAreaFieldProps
  extends BaseFieldProps,
    React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  as: "textarea";
}

interface SelectOption {
  label: string;
  value: string | number;
}

interface SelectFieldProps
  extends BaseFieldProps,
    Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "children"> {
  as: "select";
  children?: React.ReactNode;
  options?: SelectOption[];
}

export type FormFieldProps = InputFieldProps | TextAreaFieldProps | SelectFieldProps;

export function FormField({
  label,
  error,
  helperText,
  required,
  className,
  id,
  as = "input",
  ...props
}: FormFieldProps) {
  const generatedId = id || (props.name ? `field-${props.name}` : undefined);

  return (
    <div className={cn("space-y-1.5", className)}>
      <label
        htmlFor={generatedId}
        className="block text-xs font-semibold uppercase tracking-wider text-[#94A3B8]"
      >
        {label}
        {required && <span className="text-[#24C8D8] ml-1">*</span>}
      </label>

      {as === "textarea" ? (
        <textarea
          id={generatedId}
          className={cn(
            "w-full rounded-lg border border-[#273449] bg-[#0E1528] px-3.5 py-2 text-xs sm:text-sm text-[#F5F7FC] placeholder:text-[#6F7D9E] transition-colors outline-none focus:border-[#7657F6] focus:ring-1 focus:ring-[#7657F6] disabled:opacity-50",
            error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20"
          )}
          {...(props as React.TextareaHTMLAttributes<HTMLTextAreaElement>)}
        />
      ) : as === "select" ? (
        <select
          id={generatedId}
          className={cn(
            "w-full rounded-lg border border-[#273449] bg-[#0E1528] px-3.5 py-2 text-xs sm:text-sm text-[#F5F7FC] transition-colors outline-none focus:border-[#7657F6] focus:ring-1 focus:ring-[#7657F6] disabled:opacity-50",
            error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20"
          )}
          {...(props as React.SelectHTMLAttributes<HTMLSelectElement>)}
        >
          {"options" in props && props.options
            ? props.options.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))
            : "children" in props
            ? props.children
            : null}
        </select>
      ) : (
        <input
          id={generatedId}
          className={cn(
            "w-full rounded-lg border border-[#273449] bg-[#0E1528] px-3.5 py-2 text-xs sm:text-sm text-[#F5F7FC] placeholder:text-[#6F7D9E] transition-colors outline-none focus:border-[#7657F6] focus:ring-1 focus:ring-[#7657F6] disabled:opacity-50",
            error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20"
          )}
          {...(props as React.InputHTMLAttributes<HTMLInputElement>)}
        />
      )}

      {error ? (
        <p className="text-xs text-red-400 mt-1">{error}</p>
      ) : helperText ? (
        <p className="text-[11px] text-[#94A3B8] mt-1">{helperText}</p>
      ) : null}
    </div>
  );
}
