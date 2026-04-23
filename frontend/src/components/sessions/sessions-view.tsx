"use client";

import { useState, useEffect } from "react";
import {
  Network,
  Clock,
  Hash,
  ShieldCheck,
  AlertCircle,
  ChevronRight,
  ChevronDown,
  Box,
  Terminal,
  Ban,
  Eye,
  Download,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  MCPSessionSummary,
  MCPSessionResponse,
} from "@/types/api";
import { apiClient } from "@/lib/api-client";

// Evidence class badge colors
const evidenceColors: Record<string, string> = {
  observed: "bg-emerald-100 text-emerald-800 border-emerald-200",
  asserted: "bg-amber-100 text-amber-800 border-amber-200",
  derived: "bg-blue-100 text-blue-800 border-blue-200",
  policy: "bg-purple-100 text-purple-800 border-purple-200",
};

// Source layer badge colors
const sourceColors: Record<string, string> = {
  proxy: "bg-slate-100 text-slate-800 border-slate-200",
  model: "bg-indigo-100 text-indigo-800 border-indigo-200",
  policy: "bg-rose-100 text-rose-800 border-rose-200",
  human: "bg-cyan-100 text-cyan-800 border-cyan-200",
};

function CapsuleIcon({ type }: { type: string }) {
  if (type.includes("DECISION_POINT"))
    return <Network className="h-4 w-4 text-indigo-600" />;
  if (type.includes("TOOL_CALL"))
    return <Terminal className="h-4 w-4 text-emerald-600" />;
  if (type.includes("REFUSAL"))
    return <Ban className="h-4 w-4 text-rose-600" />;
  if (type.includes("SYSTEM_PROMPT"))
    return <ShieldCheck className="h-4 w-4 text-blue-600" />;
  return <Box className="h-4 w-4 text-slate-600" />;
}

export default function SessionsView() {
  const [sessions, setSessions] = useState<MCPSessionSummary[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<MCPSessionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedCapsules, setExpandedCapsules] = useState<Set<string>>(new Set());

  const fetchSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getMCPSessions();
      setSessions(data.sessions);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || "Failed to load sessions");
    } finally {
      setLoading(false);
    }
  };

  const fetchSession = async (sessionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getMCPSession(sessionId);
      setSessionData(data);
      setSelectedSession(sessionId);
      setExpandedCapsules(new Set());
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || "Failed to load session");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const toggleCapsule = (id: string) => {
    setExpandedCapsules((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Network className="h-6 w-6 text-indigo-600" />
            MCP Session Audit
          </h1>
          <p className="text-muted-foreground mt-1">
            Cryptographically certified agent session graphs from the certifying gateway.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchSessions}
          disabled={loading}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          <span className="ml-2">Refresh</span>
        </Button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-md bg-rose-50 border border-rose-200 px-4 py-3 text-rose-800">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Session list */}
        <Card className="w-80 flex flex-col shrink-0">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Hash className="h-4 w-4" />
              Sessions
              <Badge variant="secondary" className="ml-auto">
                {sessions.length}
              </Badge>
            </CardTitle>
            <CardDescription className="text-xs">
              Click a session to inspect its graph
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 p-0">
            <div className="h-[calc(100%-1rem)] px-4 pb-4 overflow-auto">
              {sessions.length === 0 && !loading && (
                <div className="text-sm text-muted-foreground text-center py-8">
                  No MCP sessions captured yet.
                  <br />
                  Run the certifying gateway to generate sessions.
                </div>
              )}
              <div className="space-y-2">
                {sessions.map((s) => (
                  <button
                    key={s.session_id}
                    onClick={() => fetchSession(s.session_id)}
                    className={`w-full text-left rounded-lg border px-3 py-2.5 transition-all hover:shadow-sm ${
                      selectedSession === s.session_id
                        ? "border-indigo-300 bg-indigo-50/60 ring-1 ring-indigo-200"
                        : "border-border bg-card hover:bg-accent/50"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Network className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      <span className="text-xs font-mono font-medium truncate flex-1">
                        {s.session_id.slice(0, 16)}...
                      </span>
                      <ChevronRight className="h-3 w-3 text-muted-foreground" />
                    </div>
                    <div className="flex items-center gap-1 mt-1 text-[11px] text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {formatTime(s.latest_timestamp)}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Detail pane */}
        <Card className="flex-1 flex flex-col min-w-0">
          {!selectedSession && (
            <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
              <Network className="h-12 w-12 mb-4 opacity-20" />
              <p className="text-sm">Select a session to view its certified graph</p>
            </div>
          )}

          {selectedSession && sessionData && (
            <>
              <CardHeader className="pb-3 shrink-0">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                      <Network className="h-5 w-5 text-indigo-600" />
                      Session Graph
                    </CardTitle>
                    <CardDescription className="text-xs font-mono mt-1">
                      {sessionData.session_id}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {sessionData.capsule_count} capsules
                    </Badge>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      title="Download session JSON"
                      onClick={() => {
                        const blob = new Blob([JSON.stringify(sessionData, null, 2)], {
                          type: "application/json",
                        });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `session-${sessionData.session_id}.json`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Evidence class & source layer badges */}
                <div className="flex flex-wrap gap-2 mt-3">
                  {sessionData.evidence_classes.map((ec) => (
                    <Badge
                      key={ec}
                      variant="outline"
                      className={`text-[10px] capitalize ${evidenceColors[ec] || ""}`}
                    >
                      {ec}
                    </Badge>
                  ))}
                  {sessionData.source_layers.map((sl) => (
                    <Badge
                      key={sl}
                      variant="outline"
                      className={`text-[10px] capitalize ${sourceColors[sl] || ""}`}
                    >
                      {sl}
                    </Badge>
                  ))}
                </div>
              </CardHeader>

              <CardContent className="flex-1 min-h-0 p-0">
                <div className="h-full px-6 pb-6 overflow-auto">
                  <div className="space-y-3">
                    {sessionData.capsules.map((cap, idx) => {
                      const isExpanded = expandedCapsules.has(cap.capsule_id);
                      return (
                        <div
                          key={cap.capsule_id}
                          className="rounded-lg border bg-card hover:border-indigo-200 transition-colors"
                        >
                          {/* Capsule header */}
                          <button
                            onClick={() => toggleCapsule(cap.capsule_id)}
                            className="w-full flex items-center gap-3 px-4 py-3 text-left"
                          >
                            <span className="text-xs text-muted-foreground font-mono w-6 shrink-0">
                              {idx + 1}
                            </span>
                            <CapsuleIcon type={cap.type} />
                            <Badge variant="secondary" className="text-[10px] shrink-0">
                              {cap.type}
                            </Badge>
                            {cap.parent_id && (
                              <Badge variant="outline" className="text-[10px] shrink-0">
                                parent: {cap.parent_id.slice(0, 8)}...
                              </Badge>
                            )}
                            <span className="text-[11px] text-muted-foreground ml-auto shrink-0">
                              {formatTime(cap.timestamp)}
                            </span>
                            {isExpanded ? (
                              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                            ) : (
                              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                            )}
                          </button>

                          {/* Expanded payload */}
                          {isExpanded && (
                            <div className="border-t bg-slate-50/50 px-4 py-3">
                              <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs mb-3">
                                <div>
                                  <span className="text-muted-foreground">Capsule ID:</span>
                                  <span className="font-mono ml-2">{cap.capsule_id}</span>
                                </div>
                                {cap.upstream_server_id && (
                                  <div>
                                    <span className="text-muted-foreground">Upstream:</span>
                                    <span className="font-mono ml-2">{cap.upstream_server_id}</span>
                                  </div>
                                )}
                                {cap.signature_preview && (
                                  <div className="col-span-2 flex items-center gap-2">
                                    <ShieldCheck className="h-3 w-3 text-emerald-600" />
                                    <span className="text-muted-foreground">Signature:</span>
                                    <span className="font-mono">{cap.signature_preview}</span>
                                  </div>
                                )}
                              </div>
                              <pre className="text-[11px] bg-slate-100 rounded-md p-3 overflow-auto max-h-64 font-mono leading-relaxed">
                                {JSON.stringify(cap.payload, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
