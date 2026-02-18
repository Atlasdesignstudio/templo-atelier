"use client";

import { useEffect, useState } from "react";
import { fetchProjects, fetchLogs, Project, AgentLog } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Hammer, Activity, DollarSign } from "lucide-react";

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [p, l] = await Promise.all([fetchProjects(), fetchLogs()]);
        setProjects(p);
        setLogs(l);
      } catch (error) {
        console.error("Failed to fetch dashboard data", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
    const interval = setInterval(loadData, 2000); // Poll every 2s
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="p-8 text-white">Connecting to Studio...</div>;

  const totalBudget = projects.reduce((acc, p) => acc + p.budget_cap, 0);
  const totalSpent = projects.reduce((acc, p) => acc + p.budget_spent, 0);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            <Hammer className="text-purple-500" /> Studio Glass House
          </h1>
          <p className="text-slate-400">Autonomous Creative Agency • Mission Control</p>
        </div>
        <div className="flex gap-4">
          <Badge variant="secondary" className="px-4 py-2 text-sm bg-slate-800 text-slate-200 border-slate-700">
            System Status: <span className="text-green-400 ml-2">● Online</span>
          </Badge>
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Total Projects</CardTitle>
            <Hammer className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{projects.length}</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Active Budget</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">${totalBudget.toFixed(2)}</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Burn Rate</CardTitle>
            <Activity className="h-4 w-4 text-red-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">${totalSpent.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">Total utilized across all projects</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Active Projects</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {projects.map((project) => (
                <div key={project.id} className="flex items-center justify-between p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                  <div className="space-y-1">
                    <p className="text-sm font-medium leading-none text-white">{project.name}</p>
                    <p className="text-xs text-muted-foreground">{project.client_brief.substring(0, 50)}...</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm font-medium text-white">${project.budget_spent} / ${project.budget_cap}</p>
                      <p className="text-xs text-slate-400">Budget Usage</p>
                    </div>
                    <Badge className={project.status === "Approved" ? "bg-green-900 text-green-300 hover:bg-green-800" : "bg-yellow-900 text-yellow-300"}>
                      {project.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3 bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Live Agent Feed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 h-[400px] overflow-y-auto pr-2">
              {logs.map((log) => (
                <div key={log.id} className="flex flex-col gap-1 p-3 rounded bg-slate-800/30 border border-slate-700/50">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-purple-400 font-mono">[{log.agent_name}]</span>
                    <span className="text-[10px] text-slate-500">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-sm text-slate-300">{log.message}</p>
                  {log.cost_incurred > 0 && (
                    <div className="self-start mt-1">
                      <Badge variant="outline" className="text-xs border-red-500/30 text-red-400 bg-red-950/20">
                        -${log.cost_incurred.toFixed(2)}
                      </Badge>
                    </div>
                  )}
                  {log.severity !== "INFO" && (
                    <div className="self-start">
                      <span className="text-[10px] text-red-500 font-bold">⚠️ {log.severity}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
