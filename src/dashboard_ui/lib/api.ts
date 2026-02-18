import axios from "axios";

// Assuming running locally on port 8000
const API_URL = "http://localhost:8000";

export const api = axios.create({
    baseURL: API_URL,
});

export interface Project {
    id: number;
    name: string;
    status: string;
    client_brief: string;
    budget_cap: number;
    budget_spent: number;
    created_at: string;
}

export interface AgentLog {
    id: number;
    project_id: number;
    agent_name: string;
    message: string;
    severity: "INFO" | "WARN" | "ERROR";
    cost_incurred: number;
    timestamp: string;
}

export const fetchProjects = async (): Promise<Project[]> => {
    const res = await api.get("/projects/");
    return res.data;
};

export const fetchLogs = async (): Promise<AgentLog[]> => {
    const res = await api.get("/logs/?limit=100");
    return res.data;
};
