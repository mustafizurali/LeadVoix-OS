"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, CheckCircle2, Loader2, Lock, Mail } from "lucide-react";

import { loginSchema, LoginFormData } from "../schemas/login.schema";
import { useLogin } from "../hooks/useLogin";
import { useAuthStore } from "../store/authStore";
import { getSafeRedirectUrl } from "@/lib/api/tokenStorage";
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

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isRegistered = searchParams?.get("registered") === "true";
  const redirectParam = searchParams?.get("redirect");

  const { isAuthenticated, isHydrated } = useAuthStore();
  const loginMutation = useLogin();

  // Redirect authenticated users safely once store hydration completes
  useEffect(() => {
    if (isHydrated && isAuthenticated) {
      const target = getSafeRedirectUrl(redirectParam, "/dashboard");
      router.replace(target);
    }
  }, [isHydrated, isAuthenticated, router, redirectParam]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = (data: LoginFormData) => {
    if (loginMutation.isPending) return;
    loginMutation.mutate(data);
  };

  return (
    <Card className="w-full max-w-md border border-slate-800/80 bg-[#151D32]/95 text-[#F5F7FC] shadow-2xl shadow-black/60 backdrop-blur-md font-sans">
      <CardHeader className="space-y-1.5 pb-6">
        <CardTitle className="text-2xl font-bold tracking-tight text-[#F5F7FC] font-sans">
          Welcome Back
        </CardTitle>
        <CardDescription className="text-sm text-[#AAB4CC]">
          Sign in to your LeadVoix OS account to manage AI voice agents and CRM workflows.
        </CardDescription>
      </CardHeader>

      <CardContent>
        {/* Success Banner from Signup */}
        {isRegistered && (
          <div
            role="status"
            className="mb-5 flex items-start gap-3 rounded-xl border border-[#35D6C1]/30 bg-[#35D6C1]/10 p-3.5 text-sm text-[#35D6C1]"
          >
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#35D6C1]" />
            <div>
              <p className="font-semibold text-[#35D6C1]">Account created successfully!</p>
              <p className="text-xs text-[#35D6C1]/90">Please sign in with your email and password.</p>
            </div>
          </div>
        )}

        {/* Backend Error Banner */}
        {loginMutation.isError && (
          <div
            role="alert"
            className="mb-5 flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-3.5 text-sm text-red-300"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
            <span className="text-xs leading-relaxed text-red-200">
              {getErrorMessage(loginMutation.error)}
            </span>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label
              htmlFor="email"
              className="text-xs font-semibold uppercase tracking-wider text-[#AAB4CC]"
            >
              Email Address
            </Label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6F7D9E]" />
              <Input
                id="email"
                type="email"
                placeholder="name@company.com"
                disabled={loginMutation.isPending}
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
            <div className="flex items-center justify-between">
              <Label
                htmlFor="password"
                className="text-xs font-semibold uppercase tracking-wider text-[#AAB4CC]"
              >
                Password
              </Label>
            </div>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6F7D9E]" />
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                disabled={loginMutation.isPending}
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

          <Button
            type="submit"
            disabled={loginMutation.isPending}
            className="w-full h-10 rounded-lg bg-[#7657F6] text-white font-medium shadow-lg shadow-violet-950/40 transition-all hover:bg-[#6846ed] focus-visible:ring-2 focus-visible:ring-[#24C8D8] disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
          >
            {loginMutation.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-white" />
                Signing in...
              </span>
            ) : (
              "Sign In"
            )}
          </Button>

          <p className="pt-2 text-center text-xs text-[#AAB4CC]">
            Don&apos;t have an account?{" "}
            <Link
              href="/signup"
              className="font-medium text-[#24C8D8] transition-colors hover:underline hover:text-[#53d9e6]"
            >
              Sign up
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
