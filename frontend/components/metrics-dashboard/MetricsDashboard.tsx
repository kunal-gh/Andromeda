"use client";
import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";

interface MetricsData {
  requests_per_minute: { time: string; count: number }[];
  decision_distribution: { decision: string; count: number }[];
  avg_latency: { time: string; latency: number }[];
  token_usage: { time: string; tokens: number }[];
}

export function MetricsDashboard() {
  const { data } = useQuery<MetricsData>({
    queryKey: ["metrics"],
    queryFn: () => fetch("/api/metrics").then(r => r.json()),
    refetchInterval: 30000
  });

  return (
    <div className="grid grid-cols-2 gap-4 p-4">
      <div className="bg-white/5 rounded-lg p-4 border border-white/10">
        <h3 className="text-sm font-medium text-gray-400 mb-4">Requests per Minute</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data?.requests_per_minute}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
            <YAxis stroke="#64748b" fontSize={12} />
            <Tooltip contentStyle={{ backgroundColor: "#0a0a0a", border: "1px solid rgba(255,255,255,0.1)" }} />
            <Line type="monotone" dataKey="count" stroke="#60a5fa" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div className="bg-white/5 rounded-lg p-4 border border-white/10">
        <h3 className="text-sm font-medium text-gray-400 mb-4">Decision Distribution</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data?.decision_distribution}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="decision" stroke="#64748b" fontSize={12} />
            <YAxis stroke="#64748b" fontSize={12} />
            <Tooltip contentStyle={{ backgroundColor: "#0a0a0a", border: "1px solid rgba(255,255,255,0.1)" }} />
            <Bar dataKey="count" fill="#4ade80" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
