import axios, { AxiosInstance } from 'axios'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/stores/authStore'
import type {
  User,
  AuthResponse,
  RegisterData,
  Artifact,
  ArtifactCreateData,
  ArtifactFilters,
  PaginatedResponse,
  CVGenerationRequest,
  GeneratedDocument,
  ExportRequest,
  ExportJob,
  Label
} from '@/types'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = useAuthStore.getState().accessToken
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const refreshToken = useAuthStore.getState().refreshToken
            if (refreshToken) {
              const response = await this.refreshToken()
              useAuthStore.getState().setTokens(response.access, response.refresh)
              return this.client(originalRequest)
            }
          } catch (refreshError) {
            useAuthStore.getState().clearAuth()
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        }

        // Show error toast for user-facing errors
        if (error.response?.status >= 400 && error.response?.status < 500) {
          const message = error.response?.data?.message || 'An error occurred'
          toast.error(message)
        }

        return Promise.reject(error)
      }
    )
  }

  // Authentication endpoints
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/v1/auth/login/', {
      email,
      password,
    })
    return response.data
  }

  async register(userData: RegisterData): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/v1/auth/register/', userData)
    return response.data
  }

  async refreshToken(): Promise<{ access: string; refresh: string }> {
    const refreshToken = useAuthStore.getState().refreshToken
    const response = await this.client.post<{ access: string; refresh: string }>(
      '/v1/auth/token/refresh/',
      { refresh: refreshToken }
    )
    return response.data
  }

  async logout(): Promise<void> {
    const refreshToken = useAuthStore.getState().refreshToken
    try {
      await this.client.post('/v1/auth/logout/', { refresh: refreshToken })
    } catch (error) {
      // Continue with logout even if server request fails
      console.warn('Logout request failed:', error)
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/v1/auth/profile/')
    return response.data
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await this.client.patch<User>('/v1/auth/profile/', data)
    return response.data
  }

  async changePassword(data: {
    current_password: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<void> {
    await this.client.post('/v1/auth/change-password/', data)
  }

  async requestPasswordReset(email: string): Promise<void> {
    await this.client.post('/v1/auth/password-reset/', { email })
  }

  // Artifact endpoints
  async getArtifacts(filters?: ArtifactFilters): Promise<PaginatedResponse<Artifact>> {
    const params = new URLSearchParams()

    if (filters?.search) params.append('search', filters.search)
    if (filters?.technologies?.length) {
      filters.technologies.forEach(tech => params.append('technologies', tech))
    }
    if (filters?.labelIds?.length) {
      filters.labelIds.forEach(id => params.append('labels', id.toString()))
    }
    if (filters?.status) params.append('status', filters.status)
    if (filters?.dateRange?.start) params.append('start_date', filters.dateRange.start)
    if (filters?.dateRange?.end) params.append('end_date', filters.dateRange.end)

    const response = await this.client.get<PaginatedResponse<Artifact>>(
      `/v1/artifacts/?${params.toString()}`
    )
    return response.data
  }

  async createArtifact(data: ArtifactCreateData): Promise<Artifact> {
    const response = await this.client.post<Artifact>('/v1/artifacts/', data)
    return response.data
  }

  async updateArtifact(id: number, data: Partial<ArtifactCreateData>): Promise<Artifact> {
    const response = await this.client.patch<Artifact>(`/v1/artifacts/${id}/`, data)
    return response.data
  }

  async deleteArtifact(id: number): Promise<void> {
    await this.client.delete(`/v1/artifacts/${id}/`)
  }

  async getArtifact(id: number): Promise<Artifact> {
    const response = await this.client.get<Artifact>(`/v1/artifacts/${id}/`)
    return response.data
  }

  async uploadArtifactFiles(artifactId: number, files: File[]): Promise<void> {
    const formData = new FormData()
    files.forEach((file, index) => {
      formData.append(`file_${index}`, file)
    })

    await this.client.post(`/v1/artifacts/${artifactId}/upload/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  }

  // Generation endpoints
  async generateCV(request: CVGenerationRequest): Promise<{ generation_id: string }> {
    const response = await this.client.post<{ generation_id: string }>(
      '/v1/generate/cv',
      request
    )
    return response.data
  }

  async getGeneration(id: string): Promise<GeneratedDocument> {
    const response = await this.client.get<GeneratedDocument>(`/v1/generate/cv/${id}`)
    return response.data
  }

  async generateCoverLetter(request: Omit<CVGenerationRequest, 'templateId'>): Promise<{ generation_id: string }> {
    const response = await this.client.post<{ generation_id: string }>(
      '/v1/generate/cover-letter',
      request
    )
    return response.data
  }

  // Export endpoints
  async exportDocument(generationId: string, exportRequest: ExportRequest): Promise<{ export_id: string }> {
    const response = await this.client.post<{ export_id: string }>(
      `/v1/export/${generationId}`,
      exportRequest
    )
    return response.data
  }

  async getExportStatus(exportId: string): Promise<ExportJob> {
    const response = await this.client.get<ExportJob>(`/v1/export/${exportId}/status`)
    return response.data
  }

  async downloadExport(exportId: string): Promise<Blob> {
    const response = await this.client.get(`/v1/export/${exportId}/download`, {
      responseType: 'blob',
    })
    return response.data
  }

  // Labels and metadata endpoints
  async getLabels(): Promise<Label[]> {
    const response = await this.client.get<Label[]>('/v1/labels/')
    return response.data
  }

  async createLabel(data: { name: string; color: string; description?: string }): Promise<Label> {
    const response = await this.client.post<Label>('/v1/labels/', data)
    return response.data
  }

  async suggestSkills(query: string): Promise<string[]> {
    const response = await this.client.get<{ suggestions: string[] }>(
      `/v1/skills/suggest/?q=${encodeURIComponent(query)}`
    )
    return response.data.suggestions
  }

  // Additional generation endpoints
  async getUserGenerations(): Promise<GeneratedDocument[]> {
    const response = await this.client.get<PaginatedResponse<GeneratedDocument>>('/v1/generate/')
    return response.data.results
  }

  async rateGeneration(generationId: string, rating: number, feedback?: string): Promise<void> {
    await this.client.post(`/v1/generate/${generationId}/rate/`, {
      rating,
      feedback,
    })
  }

  async getCVTemplates(): Promise<any[]> {
    const response = await this.client.get<any[]>('/v1/generate/templates/')
    return response.data
  }

  // Additional export endpoints
  async getUserExports(): Promise<ExportJob[]> {
    const response = await this.client.get<PaginatedResponse<ExportJob>>('/v1/export/')
    return response.data.results
  }

  async getExportTemplates(): Promise<any[]> {
    const response = await this.client.get<any[]>('/v1/export/templates/')
    return response.data
  }
}

// Create singleton instance
export const apiClient = new ApiClient()
export default apiClient