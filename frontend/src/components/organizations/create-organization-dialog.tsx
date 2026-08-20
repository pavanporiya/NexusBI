"use client";

import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiClient, ApiClientError } from "@/lib/api-client";
import type { Organization } from "@/types/api";

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/[\s_]+/g, "-")
    .replace(/-+/g, "-");
}

const createOrganizationSchema = z.object({
  name: z
    .string()
    .min(1, "Organization name is required")
    .max(256, "Organization name cannot exceed 256 characters"),
  slug: z
    .string()
    .min(1, "Slug identifier is required")
    .max(256, "Slug cannot exceed 256 characters")
    .regex(
      /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
      "Slug must contain only lowercase alphanumeric characters and single hyphens (e.g. acme-corp)"
    ),
  description: z
    .string()
    .max(1000, "Description cannot exceed 1000 characters")
    .optional(),
});

type CreateOrganizationFormValues = z.infer<typeof createOrganizationSchema>;

interface CreateOrganizationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function CreateOrganizationDialog({
  open,
  onOpenChange,
  onSuccess,
}: CreateOrganizationDialogProps) {
  const [isSlugTouched, setIsSlugTouched] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors, isSubmitting, isValid },
  } = useForm<CreateOrganizationFormValues>({
    resolver: zodResolver(createOrganizationSchema),
    defaultValues: {
      name: "",
      slug: "",
      description: "",
    },
    mode: "onChange",
  });

  const nameValue = watch("name");

  // Auto-generate slug from name unless manually modified by user
  useEffect(() => {
    if (!isSlugTouched && nameValue !== undefined) {
      setValue("slug", slugify(nameValue), { shouldValidate: true });
    }
  }, [nameValue, isSlugTouched, setValue]);

  // Reset form and state when dialog opens or closes
  useEffect(() => {
    if (!open) {
      reset();
      setIsSlugTouched(false);
    }
  }, [open, reset]);

  const onSubmit = async (values: CreateOrganizationFormValues) => {
    try {
      const payload = {
        name: values.name.trim(),
        slug: values.slug.trim(),
        ...(values.description && values.description.trim()
          ? { description: values.description.trim() }
          : {}),
      };

      await apiClient.post<Organization>("/organizations", payload);
      toast.success("Organization created successfully");
      onOpenChange(false);
      onSuccess();
    } catch (err: unknown) {
      let errorMessage = "Failed to create organization";
      if (err instanceof ApiClientError) {
        errorMessage = err.detail || err.message;
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      toast.error(errorMessage);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <DialogHeader>
            <DialogTitle>Create Organization</DialogTitle>
            <DialogDescription>
              Add a new tenant organization to the platform.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Name Field */}
            <div className="space-y-1.5">
              <Label htmlFor="org-name" className="text-xs font-medium">
                Organization Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="org-name"
                placeholder="e.g. Acme Enterprise"
                autoFocus
                disabled={isSubmitting}
                aria-invalid={!!errors.name}
                aria-describedby={errors.name ? "org-name-error" : undefined}
                {...register("name")}
              />
              {errors.name && (
                <p id="org-name-error" className="text-xs text-destructive" role="alert">
                  {errors.name.message}
                </p>
              )}
            </div>

            {/* Slug Field */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="org-slug" className="text-xs font-medium">
                  Slug Identifier <span className="text-destructive">*</span>
                </Label>
                <span className="text-2xs text-muted-foreground">
                  Unique URL slug
                </span>
              </div>
              <Input
                id="org-slug"
                placeholder="e.g. acme-enterprise"
                disabled={isSubmitting}
                aria-invalid={!!errors.slug}
                aria-describedby={errors.slug ? "org-slug-error" : undefined}
                {...register("slug", {
                  onChange: () => setIsSlugTouched(true),
                })}
              />
              {errors.slug && (
                <p id="org-slug-error" className="text-xs text-destructive" role="alert">
                  {errors.slug.message}
                </p>
              )}
            </div>

            {/* Description Field */}
            <div className="space-y-1.5">
              <Label htmlFor="org-desc" className="text-xs font-medium">
                Description <span className="text-muted-foreground font-normal">(optional)</span>
              </Label>
              <Textarea
                id="org-desc"
                placeholder="Brief details about the organization..."
                disabled={isSubmitting}
                className="resize-none min-h-[80px]"
                aria-invalid={!!errors.description}
                aria-describedby={errors.description ? "org-desc-error" : undefined}
                {...register("description")}
              />
              {errors.description && (
                <p id="org-desc-error" className="text-xs text-destructive" role="alert">
                  {errors.description.message}
                </p>
              )}
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || !isValid}
              className="gap-2"
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isSubmitting ? "Creating..." : "Create Organization"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
