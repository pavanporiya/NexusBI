"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Hexagon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/stores/auth-store";
import { useRedirectIfAuthenticated } from "@/hooks/use-auth";
import { apiClient, ApiClientError } from "@/lib/api-client";
import type { TokenResponse, User } from "@/types/api";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const { isLoading: authLoading } = useRedirectIfAuthenticated();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null);
    try {
      const tokens = await apiClient.post<TokenResponse>("/auth/login", data);
      const user = await apiClient.get<User>("/auth/me", {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      });
      setAuth(tokens, user);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiClientError) {
        setServerError(err.detail || "Invalid credentials");
      } else {
        setServerError("An unexpected error occurred");
      }
    }
  };

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-primary" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        {/* Brand */}
        <div className="mb-8 flex flex-col items-center gap-3">
          <Hexagon className="h-8 w-8 text-primary" />
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Sign in to NexusBI
          </h1>
          <p className="text-sm text-muted-foreground">
            Enterprise AI Analytics Platform
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {serverError && (
            <div className="rounded-md border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {serverError}
            </div>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@company.com"
              autoComplete="email"
              error={errors.email?.message}
              {...register("email")}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
              error={errors.password?.message}
              {...register("password")}
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            loading={isSubmitting}
          >
            Sign in
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="font-medium text-primary hover:text-primary/80 transition-colors"
          >
            Create account
          </Link>
        </p>
      </div>
    </div>
  );
}
