import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// API 版本前缀
const API_V1 = '/api/v1'

// Workflows API
export const workflowsApi = {
  list: () => client.get(`${API_V1}/workflows`),
  get: (id: string) => client.get(`${API_V1}/workflows/${id}`),
  create: (data: any) => client.post(`${API_V1}/workflows`, data),
  update: (id: string, data: any) => client.put(`${API_V1}/workflows/${id}`, data),
  delete: (id: string) => client.delete(`${API_V1}/workflows/${id}`),
}

// Executions API
export const executionsApi = {
  list: () => client.get(`${API_V1}/executions`),
  get: (id: string) => client.get(`${API_V1}/executions/${id}`),
  start: (workflowId: string, inputs: Record<string, any>) =>
    client.post(`${API_V1}/executions/start`, { workflow_id: workflowId, inputs }),
  control: (executionId: string, action: 'pause' | 'resume' | 'terminate') =>
    client.post(`${API_V1}/executions/${executionId}/${action}`),
}

// Planner API
export const plannerApi = {
  plan: (data: { goal: string; context: Record<string, any> }) =>
    client.post(`${API_V1}/planner/plan`, data),
  confirm: (draftId: string) => client.post(`${API_V1}/planner/confirm/${draftId}`),
}

// Scheduler API
export const schedulerApi = {
  list: () => client.get(`${API_V1}/scheduler/tasks`),
  create: (data: any) => client.post(`${API_V1}/scheduler/tasks`, data),
  update: (id: string, data: any) => client.patch(`${API_V1}/scheduler/tasks/${id}`, data),
  delete: (id: string) => client.delete(`${API_V1}/scheduler/tasks/${id}`),
}

// Assets API
export const assetsApi = {
  list: () => client.get(`${API_V1}/assets`),
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`${API_V1}/assets`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  get: (id: string) => client.get(`${API_V1}/assets/${id}`),
  delete: (id: string) => client.delete(`${API_V1}/assets/${id}`),
  share: (id: string, targetProjectId: string) =>
    client.post(`${API_V1}/assets/${id}/share`, { target_project_id: targetProjectId }),
  getVersions: (id: string) => client.get(`${API_V1}/assets/${id}/versions`),
  createVersion: (id: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`${API_V1}/assets/${id}/versions`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export default client
