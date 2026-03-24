import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Workflows API
export const workflowsApi = {
  list: () => client.get('/workflows'),
  get: (id: string) => client.get(`/workflows/${id}`),
  create: (data: any) => client.post('/workflows', data),
  update: (id: string, data: any) => client.put(`/workflows/${id}`, data),
  delete: (id: string) => client.delete(`/workflows/${id}`),
}

// Executions API
export const executionsApi = {
  list: () => client.get('/executions'),
  get: (id: string) => client.get(`/executions/${id}`),
  start: (workflowId: string, inputs: Record<string, any>) =>
    client.post('/executions/start', { workflow_id: workflowId, inputs }),
  control: (executionId: string, action: 'pause' | 'resume' | 'terminate') =>
    client.post(`/executions/${executionId}/${action}`),
}

// Planner API
export const plannerApi = {
  plan: (data: { goal: string; context: Record<string, any> }) =>
    client.post('/planner/plan', data),
  confirm: (draftId: string) => client.post(`/planner/confirm/${draftId}`),
}

// Scheduler API
export const schedulerApi = {
  list: () => client.get('/scheduler/tasks'),
  create: (data: any) => client.post('/scheduler/tasks', data),
  update: (id: string, data: any) => client.patch(`/scheduler/tasks/${id}`, data),
  delete: (id: string) => client.delete(`/scheduler/tasks/${id}`),
}

// Assets API
export const assetsApi = {
  list: () => client.get('/assets'),
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/assets', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  get: (id: string) => client.get(`/assets/${id}`),
  delete: (id: string) => client.delete(`/assets/${id}`),
  share: (id: string, targetProjectId: string) =>
    client.post(`/assets/${id}/share`, { target_project_id: targetProjectId }),
  getVersions: (id: string) => client.get(`/assets/${id}/versions`),
  createVersion: (id: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post(`/assets/${id}/versions`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export default client
