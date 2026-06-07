"use client";
import { motion } from "motion/react";
import { TraceEvent } from "@/lib/api";

interface AgentNode {
  id: string;
  label: string;
  status: "idle" | "active" | "complete" | "error";
  agent: string;
}

export function AgentFlowVisualizer({ events, loading }: { events: TraceEvent[]; loading: boolean }) {
  // Calculate node statuses dynamically based on actual trace events
  const getIntakeStatus = (): "idle" | "active" | "complete" | "error" => {
    if (events.some(e => e.step === "intake")) return "complete";
    if (loading && events.length === 0) return "active";
    return "idle";
  };

  const getSafetyStatus = (): "idle" | "active" | "complete" | "error" => {
    const hasLock = events.some(e => e.step === "guardrail.lock");
    const hasWarning = events.some(e => e.step === "safety.scan" && e.severity === "warning");
    if (hasLock || hasWarning) return "error";
    if (events.some(e => e.step === "safety.scan")) return "complete";
    if (loading && events.some(e => e.step === "intake") && !events.some(e => e.step === "safety.scan")) return "active";
    return "idle";
  };

  const getSupervisorStatus = (): "idle" | "active" | "complete" | "error" => {
    const hasExtract = events.some(e => e.step === "llm.extract");
    const hasTool = events.some(e => e.step.startsWith("tool."));
    if (hasExtract || hasTool) return "complete";
    if (loading && events.some(e => e.step === "safety.scan") && !events.some(e => e.step === "llm.extract")) return "active";
    return "idle";
  };

  const getPolicyStatus = (): "idle" | "active" | "complete" | "error" => {
    if (events.some(e => e.step === "tool.evaluate_refund_policy")) return "complete";
    const hasExtract = events.some(e => e.step === "llm.extract");
    const hasTool = events.some(e => e.step.startsWith("tool."));
    if (loading && (hasExtract || hasTool) && !events.some(e => e.step === "tool.evaluate_refund_policy")) return "active";
    return "idle";
  };

  const getResponseStatus = (): "idle" | "active" | "complete" | "error" => {
    if (events.some(e => e.step === "llm.compose") || events.some(e => e.step === "final")) return "complete";
    if (loading && events.some(e => e.step === "tool.evaluate_refund_policy") && !events.some(e => e.step === "llm.compose")) return "active";
    return "idle";
  };

  const nodes: AgentNode[] = [
    { id: "intake", label: "Intake", status: getIntakeStatus(), agent: "system" },
    { id: "safety", label: "Safety Guard", status: getSafetyStatus(), agent: "system" },
    { id: "supervisor", label: "Supervisor", status: getSupervisorStatus(), agent: "supervisor" },
    { id: "policy", label: "Policy Agent", status: getPolicyStatus(), agent: "policy" },
    { id: "response", label: "Response Composition", status: getResponseStatus(), agent: "system" },
  ];

  return (
    <div 
      className="slim-scroll"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "flex-start",
        gap: 8,
        padding: "16px 20px",
        background: "rgba(255, 255, 255, 0.02)",
        borderRadius: 12,
        border: "1px solid var(--border)",
        width: "100%",
        marginTop: 12,
        marginBottom: 12,
        overflowX: "auto",
      }}
    >
      {nodes.map((node, i) => (
        <div key={node.id} style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
          <motion.div
            style={{
              padding: "10px 18px",
              borderRadius: 20,
              fontSize: 15.5,
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: "1px solid",
              whiteSpace: "nowrap",
              ...(node.status === "active"
                ? { backgroundColor: "rgba(34, 211, 238, 0.12)", color: "#22d3ee", borderColor: "rgba(34, 211, 238, 0.35)" }
                : node.status === "complete"
                ? { backgroundColor: "rgba(74, 222, 128, 0.12)", color: "#4ade80", borderColor: "rgba(74, 222, 128, 0.35)" }
                : node.status === "error"
                ? { backgroundColor: "rgba(248, 113, 113, 0.12)", color: "#f87171", borderColor: "rgba(248, 113, 113, 0.35)" }
                : { backgroundColor: "rgba(255, 255, 255, 0.03)", color: "var(--text-muted)", borderColor: "var(--border)" }),
            }}
            animate={node.status === "active" ? { scale: [1, 1.03, 1], boxShadow: "0 0 10px rgba(34, 211, 238, 0.2)" } : {}}
            transition={{ repeat: Infinity, duration: 1.5 }}
          >
            {node.label}
          </motion.div>
          {i < nodes.length - 1 && (
            <div style={{ height: 1, width: 24, backgroundColor: "var(--border)", opacity: 0.5 }} />
          )}
        </div>
      ))}
    </div>
  );
}
