"use client";

import { useEffect, useState } from "react";
import { Bell, Moon, LogOut, CheckCircle2, User } from "lucide-react";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import { tokenStorage } from "@/lib/api/tokenStorage";
import { useAuthStore } from "@/modules/auth/store/authStore";
import {
  PageContainer,
  PageHeader,
  PrimaryButton,
  DangerButton,
} from "@/components/crm";

const EMAIL_NOTIFICATIONS_KEY = "leadvoix_email_notifications";
const TASK_REMINDERS_KEY = "leadvoix_task_reminders";
const THEME_KEY = "leadvoix_theme";

export default function SettingsPage() {
  const { user, logout } = useAuthStore();
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [taskReminders, setTaskReminders] = useState(true);
  const [theme, setTheme] = useState("dark");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const savedEmailNotifications = localStorage.getItem(EMAIL_NOTIFICATIONS_KEY);
    const savedTaskReminders = localStorage.getItem(TASK_REMINDERS_KEY);
    const savedTheme = localStorage.getItem(THEME_KEY);

    if (savedEmailNotifications !== null) {
      setEmailNotifications(savedEmailNotifications === "true");
    }

    if (savedTaskReminders !== null) {
      setTaskReminders(savedTaskReminders === "true");
    }

    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem(EMAIL_NOTIFICATIONS_KEY, String(emailNotifications));
    localStorage.setItem(TASK_REMINDERS_KEY, String(taskReminders));
    localStorage.setItem(THEME_KEY, theme);

    setSaved(true);
    window.setTimeout(() => {
      setSaved(false);
    }, 2500);
  };

  const handleLogout = () => {
    logout();
    tokenStorage.removeToken();
    window.location.href = "/login";
  };

  return (
    <DashboardLayout>
      <PageContainer>
        <PageHeader
          title="Account Settings & Preferences"
          subtitle="Configure system notifications, workspace preferences, and security access."
          badge="Preferences"
        />

        {saved && (
          <div className="flex items-center gap-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>Preferences updated and saved to local profile.</span>
          </div>
        )}

        <div className="grid gap-8 lg:grid-cols-12">
          {/* Main Preferences */}
          <div className="space-y-6 lg:col-span-8">
            {/* Notifications */}
            <section className="rounded-xl border border-[#273449] bg-[#151D32] p-6 shadow-sm">
              <div className="mb-6 flex items-center gap-2.5 border-b border-[#273449] pb-4">
                <Bell className="h-4 w-4 text-[#7657F6]" />
                <div>
                  <h2 className="text-base font-semibold text-[#F5F7FC]">
                    Notification Dispatch
                  </h2>
                  <p className="text-xs text-[#94A3B8]">
                    Control how LeadVoix OS alerts you of new leads and activities.
                  </p>
                </div>
              </div>

              <div className="space-y-5">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h3 className="text-sm font-medium text-[#F5F7FC]">
                      Email Alerts
                    </h3>
                    <p className="mt-0.5 text-xs text-[#94A3B8]">
                      Receive automated notifications when an AI agent completes a qualified call.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setEmailNotifications((current) => !current)}
                    aria-pressed={emailNotifications}
                    className={`relative h-6 w-11 rounded-full transition ${
                      emailNotifications ? "bg-[#7657F6]" : "bg-[#273449]"
                    }`}
                  >
                    <span
                      className={`absolute top-1 h-4 w-4 rounded-full bg-white transition ${
                        emailNotifications ? "left-6" : "left-1"
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between gap-4 border-t border-[#273449] pt-4">
                  <div>
                    <h3 className="text-sm font-medium text-[#F5F7FC]">
                      Task Reminders
                    </h3>
                    <p className="mt-0.5 text-xs text-[#94A3B8]">
                      Daily summaries of pending follow-ups and SLA milestones.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setTaskReminders((current) => !current)}
                    aria-pressed={taskReminders}
                    className={`relative h-6 w-11 rounded-full transition ${
                      taskReminders ? "bg-[#7657F6]" : "bg-[#273449]"
                    }`}
                  >
                    <span
                      className={`absolute top-1 h-4 w-4 rounded-full bg-white transition ${
                        taskReminders ? "left-6" : "left-1"
                      }`}
                    />
                  </button>
                </div>
              </div>
            </section>

            {/* Appearance */}
            <section className="rounded-xl border border-[#273449] bg-[#151D32] p-6 shadow-sm">
              <div className="mb-6 flex items-center gap-2.5 border-b border-[#273449] pb-4">
                <Moon className="h-4 w-4 text-[#24C8D8]" />
                <div>
                  <h2 className="text-base font-semibold text-[#F5F7FC]">
                    Interface Appearance
                  </h2>
                  <p className="text-xs text-[#94A3B8]">
                    High-contrast dark mode optimized for enterprise CRM dashboards.
                  </p>
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
                  Color Theme
                </label>
                <select
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  className="w-full max-w-xs rounded-lg border border-[#273449] bg-[#0E1528] px-3.5 py-2.5 text-sm text-[#F5F7FC] outline-none transition focus:border-[#7657F6]"
                >
                  <option value="dark">Enterprise Dark (Default)</option>
                  <option value="system">Follow System Preferences</option>
                </select>
              </div>

              <div className="mt-6 flex justify-end">
                <PrimaryButton onClick={handleSave}>
                  Save Preferences
                </PrimaryButton>
              </div>
            </section>
          </div>

          {/* Account Profile Sidebar */}
          <div className="space-y-6 lg:col-span-4">
            <section className="rounded-xl border border-[#273449] bg-[#151D32] p-5 shadow-sm">
              <div className="flex items-center gap-3 border-b border-[#273449] pb-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#7657F6]/10 border border-[#7657F6]/20 text-[#7657F6]">
                  <User className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-[#F5F7FC]">
                    {user?.name || "Operator"}
                  </h3>
                  <p className="font-mono text-xs text-[#94A3B8]">
                    {user?.email || "Authenticated Operator"}
                  </p>
                </div>
              </div>

              <div className="mt-4 space-y-3 text-xs">
                <div className="flex justify-between py-1">
                  <span className="text-[#94A3B8]">Role</span>
                  <span className="font-semibold text-[#F5F7FC]">{user?.role || "Administrator"}</span>
                </div>
                <div className="flex justify-between py-1 border-t border-[#273449]/60">
                  <span className="text-[#94A3B8]">Organization ID</span>
                  <span className="font-mono text-[#24C8D8]">#{user?.organization_id || 1}</span>
                </div>
                <div className="flex justify-between py-1 border-t border-[#273449]/60">
                  <span className="text-[#94A3B8]">Security Level</span>
                  <span className="font-medium text-emerald-400">Enterprise Verified</span>
                </div>
              </div>

              <div className="mt-6 border-t border-[#273449] pt-4">
                <DangerButton
                  onClick={handleLogout}
                  className="w-full justify-center"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out of Session
                </DangerButton>
              </div>
            </section>
          </div>
        </div>
      </PageContainer>
    </DashboardLayout>
  );
}
