"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface AgentNode {
  id: string;
  label: string;
  status: "idle" | "active" | "complete" | "error";
  agent: string;
}

export function AgentFlowVisualizer({ conversationId }: { conversationId: string }) {
  const [nodes, setNodes] = useState<AgentNode[]>([
    { id: "intake", label: "Intake", status: "complete", agent: "system" },
    { id: "safety", label: "Safety Guard", status: "complete", agent: "system" },
    { id: "supervisor", label: "Supervisor", status: "active", agent: "supervisor" },
    { id: "policy", label: "Policy Agent", status: "idle", agent: "policy" },
    { id: "response", label: "Response", status: "idle", agent: "system" },
  ]);

  return (
    <div className="flex items-center gap-2 p-4 bg-white/5 rounded-lg">
      {nodes.map((node, i) => (
        <div key={node.id} className="flex items-center gap-2">
          <motion.div
            className={`px-3 py-1.5 rounded-full text-xs font-medium ${
              node.status === "active" ? "bg-blue-500/20 text-blue-400 border border-blue-500/30" :
              node.status === "complete" ? "bg-green-500/20 text-green-400 border border-green-500/30" :
              node.status === "error" ? "bg-red-500/20 text-red-400 border border-red-500/30" :
              "bg-white/5 text-gray-400 border border-white/10"
            }`}
            animate={node.status === "active" ? { scale: [1, 1.05, 1] } : {}}
            transition={{ repeat: Infinity, duration: 1.5 }}
          >
            {node.label}
          </motion.div>
          {i < nodes.length - 1 && (
            <div className="w-4 h-px bg-white/10" />
          )}
        </div>
      ))}
    </div>
  );
}
