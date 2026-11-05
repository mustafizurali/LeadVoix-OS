"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, Loader2, Lock, Mail, User as UserIcon } from "lucide-react";

import { signupSchema, SignupFormData } from "../schemas/signup.schema";
import { useSignup } from "../hooks/useSignup";
import { useAuthStore } from "../store/authStore";
import { getErrorMessage } from "@/lib/api/errors";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function SignupForm() {
  const router = useRouter();
  const { isAuthenticated, isHydrated } = useAuthStore();
  const signupMutation = useSignup();

  // Redirect authenticated users once store hydration completes
  useEffect(() => {
    if (isHydrated && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isHydrated, isAuthenticated, router]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
  });

  const onSubmit = (data: SignupFormData) => {
    if (signupMutation.isPending) return;
    signupMutation.mutate({
      name: data.name,
      email: data.email,
      password: data.password,
    });
  };

  return (
    <Card className="w-full max-w-md border border-slate-800/80 bg-[#151D32]/95 text-[#F5F7FC] shadow-2xl shadow-black/60 backdrop-blur-md font-sans">
      <CardHeader className="space-y-1.5 pb-6">
        <CardTitle className="text-2xl font-bold tracking-tight text-[#F5F7FC] font-sans">
          Create Account
        </CardTitle>
        <CardDescription className="text-sm text-[#AAB4CC]">
          Start your free trial with LeadVoix AI Voice Agents and CRM Automation.
        </CardDescription>
      </CardHeader>

      <CardContent>
        {/* Dynamic Backend Error Banner */}
        {signupMutation.isError && (
          <div
            role="alert"
            className="mb-5 flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-3.5 text-sm text-red-300"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
            <span className="text-xs leading-relaxed text-red-200">
              {getErrorMessage(signupMutation.error)}
            </span>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label
              htmlFor="name"
              className="text-xs font-semibold uppercase tracking-wider text-[#AAB4CC]"
            >
              Full Name
            </Label>
            <div className="relative">
              <UserIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6F7D9E]" />
              <Input
                id="name"
                placeholder="Alex Morgan"
                disabled={signupMutation.isPending}
                {...register("name")}
                className="h-10 rounded-lg border-slate-700/80 bg-[#0E1528] pl-9 text-[#F5F7FC] placeholder:text-[#6F7D9E] transition-colors focus-visible:border-[#7657F6] focus-visible:ring-1 focus-visible:ring-[#7657F6]"
              />
            </div>
            {errors.name && (
              <p className="text-xs font-medium text-red-400">
                {errors.name.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label
              htmlFor="email"
              className="text-xs font-semibold uppercase tracking-wider text-[#AAB4CC]"
            >
              Work Email
            </Label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6F7D9E]" />
              <Input
                id="email"
                type="email"
                placeholder="alex@company.com"
                disabled={signupMutation.isPending}
                {...register("email")}
                className="h-10 rounded-lg border-slate-700/80 bg-[#0E1528] pl-9 text-[#F5F7FC] placeholder:text-[#6F7D9E] transition-colors focus-visible:border-[#7657F6] focus-visible:ring-1 focus-visible:ring-[#7657F6]"
              />
            </div>
            {errors.email && (
              <p className="text-xs font-medium text-red-400">
                {errors.email.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label
              htmlFor="password"
              className="text-xs font-semibold uppercase tracking-wider text-[#AAB4CC]"
            >
              Password
            </Label>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6F7D9E]" />
              <Input
                id="password"
                type="password"
                placeholder="At least 8 characters"
                disabled={signupMutation.isPending}
                {...register("password")}
                className="h-10 rounded-lg border-slate-700/80 bg-[#0E1528] pl-9 text-[#F5F7FC] placeholder:text-[#6F7D9E] transition-colors focus-visible:border-[#7657F6] focus-visible:ring-1 focus-visible:ring-[#7657F6]"
              />
            </div>
            {errors.password && (
              <p className="text-xs font-medium text-red-400">
                {errors.password.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label
              htmlFor="confirmPassword"
              className="text-xs font-semibold uppercase tracking-wider text-[#AAB4CC]"
            >
              Confirm Password
            </Label>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6F7D9E]" />
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Re-enter password"
                disabled={signupMutation.isPending}
                {...register("confirmPassword")}
                className="h-10 rounded-lg border-slate-700/80 bg-[#0E1528] pl-9 text-[#F5F7FC] placeholder:text-[#6F7D9E] transition-colors focus-visible:border-[#7657F6] focus-visible:ring-1 focus-visible:ring-[#7657F6]"
              />
            </div>
            {errors.confirmPassword && (
              <p className="text-xs font-medium text-red-400">
                {errors.confirmPassword.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5 pt-1">
            <label className="flex items-start gap-2.5 text-xs text-[#AAB4CC] cursor-pointer select-none">
              <input
                type="checkbox"
                disabled={signupMutation.isPending}
                {...register("terms")}
                className="mt-0.5 h-4 w-4 rounded border-slate-700 bg-[#0E1528] text-[#7657F6] accent-[#7657F6] focus:ring-1 focus:ring-[#7657F6]"
              />
              <span className="leading-tight">
                I agree to the{" "}
                <Link
                  href="/terms"
                  className="text-[#24C8D8] hover:underline hover:text-[#53d9e6]"
                  target="_blank"
                >
                  Terms of Service
                </Link>{" "}
                and{" "}
                <Link
                  href="/privacy"
                  className="text-[#24C8D8] hover:underline hover:text-[#53d9e6]"
                  target="_blank"
                >
                  Privacy Policy
                </Link>
                .
              </span>
            </label>
            {errors.terms && (
              <p className="text-xs font-medium text-red-400">
                {errors.terms.message}
              </p>
            )}
          </div>

          <Button
            type="submit"
            disabled={signupMutation.isPending}
            className="w-full h-10 rounded-lg bg-[#7657F6] text-white font-medium shadow-lg shadow-violet-950/40 transition-all hover:bg-[#6846ed] focus-visible:ring-2 focus-visible:ring-[#24C8D8] disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
          >
            {signupMutation.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-white" />
                Creating Account...
              </span>
            ) : (
              "Create Account"
            )}
          </Button>

          <p className="pt-2 text-center text-xs text-[#AAB4CC]">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-[#24C8D8] transition-colors hover:underline hover:text-[#53d9e6]"
            >
              Sign in
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
