"use client";

import { useEffect, useState } from "react";
import { Bot, Mic, Globe, Sparkles, Plus, Edit2, Trash2, CheckCircle2, AlertCircle } from "lucide-react";
import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import api from "@/lib/api/axios";
import {
  PageContainer,
  PageHeader,
  PrimaryButton,
  SecondaryButton,
  DangerButton,
  StatusBadge,
  FormField,
  ConfirmationDialog,
} from "@/components/crm";

type Agent = {
  id: number;
  name: string;
  description: string | null;
  voice: string | null;
  language: string;
  system_prompt: string | null;
  greeting_message: string | null;
  is_active: boolean;
  organization_id: number;
};

type AgentForm = {
  name: string;
  description: string;
  voice: string;
  language: string;
  system_prompt: string;
  greeting_message: string;
  is_active: boolean;
};

const emptyForm: AgentForm = {
  name: "",
  description: "",
  voice: "alloy",
  language: "en",
  system_prompt: "",
  greeting_message: "",
  is_active: true,
};

const VOICE_OPTIONS = [
  { value: "alloy", label: "Alloy (Neutral, Balanced)" },
  { value: "echo", label: "Echo (Warm, Crisp)" },
  { value: "fable", label: "Fable (British, Expressive)" },
  { value: "onyx", label: "Onyx (Deep, Authoritative)" },
  { value: "nova", label: "Nova (Energetic, Friendly)" },
  { value: "shimmer", label: "Shimmer (Clear, High-pitch)" },
];

const LANGUAGE_OPTIONS = [
  { value: "en", label: "English (US / Global)" },
  { value: "bn", label: "Bengali (বাংলা)" },
  { value: "hi", label: "Hindi (हिन्दी)" },
  { value: "ar", label: "Arabic (العربية)" },
];

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [form, setForm] = useState<AgentForm>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [agentToDelete, setAgentToDelete] = useState<Agent | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const loadAgents = async () => {
    try {
      setLoading(true);
      setError("");
      const response = await api.get("/agents");
      setAgents(response.data);
    } catch (err) {
      console.error(err);
      setError("Failed to load AI agents from the server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const handleChange = (
    field: keyof AgentForm,
    value: string | boolean
  ) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const payload = {
        name: form.name.trim(),
        description: form.description?.trim() || null,
        voice: form.voice || null,
        language: form.language,
        system_prompt: form.system_prompt?.trim() || null,
        greeting_message: form.greeting_message?.trim() || null,
        is_active: form.is_active,
      };

      if (editingId) {
        await api.put(`/agents/${editingId}`, payload);
        setSuccess("Voice agent updated successfully.");
      } else {
        await api.post("/agents", payload);
        setSuccess("Voice agent created successfully.");
      }

      resetForm();
      await loadAgents();
    } catch (err) {
      console.error(err);
      setError("Failed to save voice agent. Please verify parameters.");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (agent: Agent) => {
    setEditingId(agent.id);
    setForm({
      name: agent.name,
      description: agent.description || "",
      voice: agent.voice || "alloy",
      language: agent.language || "en",
      system_prompt: agent.system_prompt || "",
      greeting_message: agent.greeting_message || "",
      is_active: agent.is_active,
    });
    setSuccess("");
    setError("");
  };

  const handleConfirmDelete = async () => {
    if (!agentToDelete) return;

    try {
      setDeleteLoading(true);
      setError("");
      setSuccess("");
      await api.delete(`/agents/${agentToDelete.id}`);
      setSuccess(`Agent "${agentToDelete.name}" deleted successfully.`);

      if (editingId === agentToDelete.id) {
        resetForm();
      }

      await loadAgents();
      setAgentToDelete(null);
    } catch (err) {
      console.error(err);
      setError("Failed to delete agent.");
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <PageContainer>
        <PageHeader
          title="AI Voice Agents"
          subtitle="Configure conversational telephony agents, personality prompts, and speech synthesis."
          badge="AI Voice Studio"
          action={
            editingId ? (
              <SecondaryButton onClick={resetForm}>
                <Plus className="h-4 w-4" />
                New Agent Studio
              </SecondaryButton>
            ) : undefined
          }
        />

        {error && (
          <div className="flex items-center gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="flex items-center gap-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{success}</span>
          </div>
        )}

        <div className="grid gap-8 lg:grid-cols-12">
          {/* Left Form: Agent Configuration Studio */}
          <div className="rounded-xl border border-[#273449] bg-[#151D32] p-6 shadow-sm lg:col-span-7">
            <div className="mb-6 flex items-center justify-between border-b border-[#273449] pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-[#7657F6]" />
                  <h2 className="text-lg font-semibold text-[#F5F7FC]">
                    {editingId ? "Edit Voice Agent" : "Agent Configuration Studio"}
                  </h2>
                </div>
                <p className="mt-1 text-xs text-[#94A3B8]">
                  Define prompts, voice synthesis parameters, and conversation behavior.
                </p>
              </div>

              {editingId && (
                <span className="rounded bg-[#7657F6]/10 px-2.5 py-1 font-mono text-xs font-semibold text-[#7657F6] border border-[#7657F6]/20">
                  Editing #{editingId}
                </span>
              )}
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <FormField
                label="Agent Name"
                name="name"
                value={form.name}
                onChange={(e) => handleChange("name", e.target.value)}
                placeholder="e.g. Inbound Sales Qualifier"
                required
              />

              <FormField
                label="Role Description"
                name="description"
                value={form.description}
                onChange={(e) => handleChange("description", e.target.value)}
                placeholder="Brief summary of what this agent handles..."
              />

              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  label="Speech Voice Engine"
                  name="voice"
                  as="select"
                  value={form.voice}
                  onChange={(e) => handleChange("voice", e.target.value)}
                  options={VOICE_OPTIONS}
                />

                <FormField
                  label="Primary Language"
                  name="language"
                  as="select"
                  value={form.language}
                  onChange={(e) => handleChange("language", e.target.value)}
                  options={LANGUAGE_OPTIONS}
                />
              </div>

              <FormField
                label="System Prompt (Persona & Instructions)"
                name="system_prompt"
                as="textarea"
                value={form.system_prompt}
                onChange={(e) => handleChange("system_prompt", e.target.value)}
                placeholder="You are LeadVoix Sales Representative. Qualify the prospect based on company size, budget, and implementation timeline..."
                rows={5}
                helperText="Guidance that governs conversation boundaries, tone, and objection handling."
              />

              <FormField
                label="Opening Greeting Phrase"
                name="greeting_message"
                as="textarea"
                value={form.greeting_message}
                onChange={(e) => handleChange("greeting_message", e.target.value)}
                placeholder="Hello, this is Alex from LeadVoix OS. Thanks for requesting a consultation—do you have a quick minute?"
                rows={2}
                helperText="Spoken automatically when the call is answered by the contact."
              />

              <div className="flex items-center gap-3 pt-2">
                <label className="flex cursor-pointer items-center gap-2.5 text-sm font-medium text-[#F5F7FC]">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) => handleChange("is_active", e.target.checked)}
                    className="h-4 w-4 rounded border-[#273449] bg-[#0E1528] text-[#7657F6] focus:ring-[#7657F6]/30 focus:ring-offset-0"
                  />
                  <span>Active Agent (Available for Outbound / Inbound Telephony)</span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 border-t border-[#273449] pt-4">
                {editingId && (
                  <SecondaryButton type="button" onClick={resetForm} disabled={saving}>
                    Cancel Edit
                  </SecondaryButton>
                )}

                <PrimaryButton type="submit" loading={saving}>
                  {editingId ? "Save Agent" : "Create Agent"}
                </PrimaryButton>
              </div>
            </form>
          </div>

          {/* Right Column: Active Agents Roster */}
          <div className="space-y-4 lg:col-span-5">
            <div className="rounded-xl border border-[#273449] bg-[#151D32] p-5 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#273449] pb-3">
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4 text-[#24C8D8]" />
                  <h3 className="text-base font-semibold text-[#F5F7FC]">
                    Configured Agents ({agents.length})
                  </h3>
                </div>
                <span className="font-mono text-xs text-[#94A3B8]">
                  LeadVoix Fleet
                </span>
              </div>

              <div className="mt-4 space-y-3">
                {loading ? (
                  <div className="py-8 text-center text-sm text-[#94A3B8]">
                    Loading voice agents...
                  </div>
                ) : agents.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-[#273449] bg-[#0E1528] p-6 text-center">
                    <Bot className="mx-auto h-8 w-8 text-[#94A3B8]/40" />
                    <p className="mt-2 text-sm text-[#94A3B8]">
                      No voice agents configured yet. Use the studio to launch your first agent.
                    </p>
                  </div>
                ) : (
                  agents.map((agent) => {
                    const isBeingEdited = editingId === agent.id;

                    return (
                      <div
                        key={agent.id}
                        className={`rounded-xl border p-4 transition ${
                          isBeingEdited
                            ? "border-[#7657F6] bg-[#7657F6]/5 ring-1 ring-[#7657F6]/40"
                            : "border-[#273449] bg-[#0E1528] hover:border-[#384964]"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h4 className="font-medium text-[#F5F7FC]">
                              {agent.name}
                            </h4>
                            <p className="mt-0.5 font-mono text-[11px] text-[#94A3B8]">
                              ID: #{agent.id}
                            </p>
                          </div>

                          <StatusBadge
                            status={agent.is_active ? "active" : "inactive"}
                          />
                        </div>

                        {agent.description && (
                          <p className="mt-2 text-xs text-[#94A3B8] line-clamp-2">
                            {agent.description}
                          </p>
                        )}

                        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                          {agent.voice && (
                            <span className="inline-flex items-center gap-1 rounded bg-[#151D32] border border-[#273449] px-2 py-0.5 font-mono text-[11px] text-[#24C8D8]">
                              <Mic className="h-3 w-3" />
                              {agent.voice}
                            </span>
                          )}

                          <span className="inline-flex items-center gap-1 rounded bg-[#151D32] border border-[#273449] px-2 py-0.5 font-mono text-[11px] text-[#94A3B8]">
                            <Globe className="h-3 w-3" />
                            {agent.language.toUpperCase()}
                          </span>
                        </div>

                        <div className="mt-4 flex items-center justify-end gap-2 border-t border-[#273449]/60 pt-3">
                          <SecondaryButton
                            size="sm"
                            onClick={() => handleEdit(agent)}
                          >
                            <Edit2 className="h-3.5 w-3.5" />
                            Edit
                          </SecondaryButton>

                          <DangerButton
                            size="sm"
                            onClick={() => setAgentToDelete(agent)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                            Delete
                          </DangerButton>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>

        <ConfirmationDialog
          isOpen={Boolean(agentToDelete)}
          onClose={() => setAgentToDelete(null)}
          onConfirm={handleConfirmDelete}
          title="Delete AI Agent"
          message={`Are you sure you want to delete "${agentToDelete?.name}"? Telephony routes relying on this agent will be disrupted.`}
          confirmLabel="Delete Agent"
          variant="danger"
          loading={deleteLoading}
        />
      </PageContainer>
    </DashboardLayout>
  );
}
