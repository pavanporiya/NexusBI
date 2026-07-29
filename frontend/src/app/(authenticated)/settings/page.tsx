"use client";

import React, { useState } from "react";
import { User, Lock, Key, Bell } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "sonner";

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [email] = useState(user?.email || "admin@nexusbi.io");

  const [savingGeneral, setSavingGeneral] = useState(false);
  const [savingSecurity, setSavingSecurity] = useState(false);

  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    scheduledReports: true,
    securityAudits: true,
  });

  const handleSaveGeneral = (e: React.FormEvent) => {
    e.preventDefault();
    setSavingGeneral(true);
    setTimeout(() => {
      setSavingGeneral(false);
      toast.success("Profile updated successfully");
    }, 600);
  };

  const handleSaveSecurity = (e: React.FormEvent) => {
    e.preventDefault();
    setSavingSecurity(true);
    setTimeout(() => {
      setSavingSecurity(false);
      toast.success("Password updated");
    }, 600);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-foreground">Settings</h1>
        <p className="text-xs text-muted-foreground">Manage user profile, security settings, API tokens, and notification preferences.</p>
      </div>

      <Tabs defaultValue="general">
        <TabsList className="mb-4">
          <TabsTrigger value="general" className="gap-1.5">
            <User className="h-3.5 w-3.5" /> General Profile
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-1.5">
            <Lock className="h-3.5 w-3.5" /> Security
          </TabsTrigger>
          <TabsTrigger value="api" className="gap-1.5">
            <Key className="h-3.5 w-3.5" /> API Keys
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-1.5">
            <Bell className="h-3.5 w-3.5" /> Notifications
          </TabsTrigger>
        </TabsList>

        {/* General Profile */}
        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">User Profile</CardTitle>
              <CardDescription>Update your personal account details</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSaveGeneral} className="space-y-4 max-w-md">
                <div className="space-y-1.5">
                  <Label>Email Address</Label>
                  <Input value={email} disabled className="bg-muted/50" />
                  <p className="text-2xs text-muted-foreground">Email address cannot be changed directly.</p>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="fullname">Full Name</Label>
                  <Input
                    id="fullname"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Jane Doe"
                  />
                </div>

                <Button type="submit" loading={savingGeneral} size="sm">
                  Save Changes
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security */}
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Change Password</CardTitle>
              <CardDescription>Ensure your account is using a strong password</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSaveSecurity} className="space-y-4 max-w-md">
                <div className="space-y-1.5">
                  <Label htmlFor="curr-pass">Current Password</Label>
                  <Input id="curr-pass" type="password" placeholder="••••••••" required />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="new-pass">New Password</Label>
                  <Input id="new-pass" type="password" placeholder="••••••••" required />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="conf-pass">Confirm New Password</Label>
                  <Input id="conf-pass" type="password" placeholder="••••••••" required />
                </div>

                <Button type="submit" loading={savingSecurity} size="sm">
                  Update Password
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Tokens */}
        <TabsContent value="api">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-sm">Personal Access Tokens</CardTitle>
                <CardDescription>API bearer tokens for programmatically querying NexusBI</CardDescription>
              </div>
              <Button size="sm">
                <Key className="mr-1.5 h-3.5 w-3.5" /> Generate Token
              </Button>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border border-border p-3 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-foreground">CLI Developer Token</p>
                  <p className="font-mono text-2xs text-muted-foreground">nbi_pat_7f8a9b0c... Created 3 days ago</p>
                </div>
                <Button variant="outline" size="sm">Revoke</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Notification Preferences</CardTitle>
              <CardDescription>Control email and push alert notifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between rounded-md border border-border p-3">
                <div>
                  <p className="text-xs font-semibold text-foreground">Email System Alerts</p>
                  <p className="text-2xs text-muted-foreground">Receive critical system health degradation updates</p>
                </div>
                <Switch
                  checked={notifications.emailAlerts}
                  onCheckedChange={(c) => setNotifications({ ...notifications, emailAlerts: c })}
                />
              </div>

              <div className="flex items-center justify-between rounded-md border border-border p-3">
                <div>
                  <p className="text-xs font-semibold text-foreground">Scheduled Report Deliveries</p>
                  <p className="text-2xs text-muted-foreground">Email PDFs/CSVs when scheduled cron tasks fire</p>
                </div>
                <Switch
                  checked={notifications.scheduledReports}
                  onCheckedChange={(c) => setNotifications({ ...notifications, scheduledReports: c })}
                />
              </div>

              <div className="flex items-center justify-between rounded-md border border-border p-3">
                <div>
                  <p className="text-xs font-semibold text-foreground">Security Audit Notifications</p>
                  <p className="text-2xs text-muted-foreground">Alert on new login locations and token rotations</p>
                </div>
                <Switch
                  checked={notifications.securityAudits}
                  onCheckedChange={(c) => setNotifications({ ...notifications, securityAudits: c })}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
