"use client";

import React, { useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
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

const editOrganizationSchema = z.object({
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
      "Slug must contain only lowercase alphanumeric characters and single hyphens (e.g. acme-corp)",
    ),
  description: z
    .string()
    .max(1000, "Description cannot exceed 1000 characters")
    .optional(),
  is_active: z.boolean(),
});

type EditOrganizationFormValues = z.infer<typeof editOrganizationSchema>;

interface EditOrganizationDialogProps {
  organization: Organization | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function EditOrganizationDialog({
  organization,
  open,
  onOpenChange,
  onSuccess,
}: EditOrganizationDialogProps) {
  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting, isValid },
  } = useForm<EditOrganizationFormValues>({
    resolver: zodResolver(editOrganizationSchema),
    defaultValues: {
      name: "",
      slug: "",
      description: "",
      is_active: true,
    },
    mode: "onChange",
  });

  // Pre-fill form when selected organization changes or dialog opens
  useEffect(() => {
    if (organization && open) {
      reset({
        name: organization.name || "",
        slug: organization.slug || "",
        description: organization.description || "",
        is_active: organization.is_active ?? true,
      });
    }
  }, [organization, open, reset]);

  const onSubmit = async (values: EditOrganizationFormValues) => {
    if (!organization) return;

    try {
      const payload = {
        name: values.name.trim(),
        slug: values.slug.trim(),
        description: values.description ? values.description.trim() : "",
        is_active: values.is_active,
      };

      await apiClient.patch<Organization>(
        `/organizations/${organization.id}`,
        payload,
      );
      toast.success("Organization updated successfully");
      onOpenChange(false);
      onSuccess();
    } catch (err: unknown) {
      let errorMessage = "Failed to update organization";
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
            <DialogTitle>Edit Organization</DialogTitle>
            <DialogDescription>
              Update enterprise organization details and configuration.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Organization Name Field */}
            <div className="space-y-1.5">
              <Label htmlFor="edit-org-name" className="text-xs font-medium">
                Organization Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="edit-org-name"
                placeholder="e.g. Acme Enterprise"
                autoFocus
                disabled={isSubmitting}
                aria-invalid={!!errors.name}
                aria-describedby={
                  errors.name ? "edit-org-name-error" : undefined
                }
                {...register("name")}
              />
              {errors.name && (
                <p
                  id="edit-org-name-error"
                  className="text-xs text-destructive"
                  role="alert"
                >
                  {errors.name.message}
                </p>
              )}
            </div>

            {/* Slug Field */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="edit-org-slug" className="text-xs font-medium">
                  Slug Identifier <span className="text-destructive">*</span>
                </Label>
                <span className="text-2xs text-muted-foreground">
                  Unique URL slug
                </span>
              </div>
              <Input
                id="edit-org-slug"
                placeholder="e.g. acme-enterprise"
                disabled={isSubmitting}
                aria-invalid={!!errors.slug}
                aria-describedby={
                  errors.slug ? "edit-org-slug-error" : undefined
                }
                {...register("slug")}
              />
              {errors.slug && (
                <p
                  id="edit-org-slug-error"
                  className="text-xs text-destructive"
                  role="alert"
                >
                  {errors.slug.message}
                </p>
              )}
            </div>

            {/* Description Field */}
            <div className="space-y-1.5">
              <Label htmlFor="edit-org-desc" className="text-xs font-medium">
                Description{" "}
                <span className="text-muted-foreground font-normal">
                  (optional)
                </span>
              </Label>
              <Textarea
                id="edit-org-desc"
                placeholder="Brief details about the organization..."
                disabled={isSubmitting}
                className="resize-none min-h-[80px]"
                aria-invalid={!!errors.description}
                aria-describedby={
                  errors.description ? "edit-org-desc-error" : undefined
                }
                {...register("description")}
              />
              {errors.description && (
                <p
                  id="edit-org-desc-error"
                  className="text-xs text-destructive"
                  role="alert"
                >
                  {errors.description.message}
                </p>
              )}
            </div>

            {/* Active Status Switch */}
            <Controller
              control={control}
              name="is_active"
              render={({ field }) => (
                <div className="flex items-center justify-between rounded-lg border border-border p-3 shadow-xs">
                  <div className="space-y-0.5">
                    <Label
                      htmlFor="edit-org-active"
                      className="text-xs font-medium cursor-pointer"
                    >
                      Active Status
                    </Label>
                    <p className="text-2xs text-muted-foreground">
                      Inactive organizations cannot access platform resources.
                    </p>
                  </div>
                  <Switch
                    id="edit-org-active"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    disabled={isSubmitting}
                  />
                </div>
              )}
            />
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
              {isSubmitting ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
