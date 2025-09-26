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
  Label,
  BulkUploadResponse,
  ArtifactProcessingStatus,
  LLMModelStats,
  LLMSystemHealth,
  LLMPerformanceMetric,
  LLMCostTracking,
  JobDescriptionEmbedding,
  EnhancedArtifact,
  GenerationAnalytics,
  ExportAnalytics
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

        // Don't automatically show error toasts - let components handle error display

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
      formData.append(`files`, file)
    })

    await this.client.post(`/v1/artifacts/${artifactId}/upload/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  }

  async bulkUploadArtifact(data: {
    files?: File[]
    metadata: {
      title: string
      description: string
      artifact_type?: string
      start_date?: string
      end_date?: string
      technologies?: string[]
      collaborators?: string[]
      evidence_links?: Array<{
        url: string
        link_type: string
        description?: string
      }>
    }
  }): Promise<BulkUploadResponse> {
    const formData = new FormData()

    // Add files if provided
    if (data.files) {
      data.files.forEach(file => {
        formData.append('files', file)
      })
    }

    // Add metadata as JSON string
    formData.append('metadata', JSON.stringify(data.metadata))

    const response = await this.client.post('/v1/artifacts/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async getArtifactProcessingStatus(artifactId: number): Promise<ArtifactProcessingStatus> {
    const response = await this.client.get(`/v1/artifacts/${artifactId}/status/`)
    return response.data
  }

  async getTechnologySuggestions(query?: string): Promise<string[]> {
    const params = new URLSearchParams()
    if (query) params.append('q', query)

    const response = await this.client.get<{ suggestions: string[] }>(
      `/v1/artifacts/suggestions/?${params.toString()}`
    )
    return response.data.suggestions
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
      '/v1/generate/cover-letter/',
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
      `/v1/artifacts/suggestions/?q=${encodeURIComponent(query)}`
    )
    return response.data.suggestions
  }

  // Artifact editing endpoints
  async addEvidenceLink(artifactId: number, linkData: {
    url: string;
    link_type: string;
    description?: string;
  }): Promise<{
    id: number;
    url: string;
    link_type: string;
    description: string;
    created_at: string;
  }> {
    const response = await this.client.post(`/v1/artifacts/${artifactId}/evidence-links/`, linkData)
    return response.data
  }

  async updateEvidenceLink(linkId: number, linkData: {
    url?: string;
    link_type?: string;
    description?: string;
  }): Promise<{
    id: number;
    url: string;
    link_type: string;
    description: string;
    updated_at: string;
  }> {
    const response = await this.client.put(`/v1/artifacts/evidence-links/${linkId}/`, linkData)
    return response.data
  }

  async deleteEvidenceLink(linkId: number): Promise<void> {
    await this.client.delete(`/v1/artifacts/evidence-links/${linkId}/`)
  }

  async deleteArtifactFile(fileId: string): Promise<void> {
    await this.client.delete(`/v1/artifacts/files/${fileId}/`)
  }

  async bulkUpdateArtifacts(data: {
    artifact_ids: number[];
    action: 'add_technologies' | 'remove_technologies' | 'update_type' | 'add_collaborators' | 'remove_collaborators';
    values: {
      technologies?: string[];
      artifact_type?: string;
      collaborators?: string[];
    };
  }): Promise<{
    results: Array<{
      id: number;
      status: 'success' | 'error';
      updated_fields?: string[];
      message?: string;
    }>;
    total_processed: number;
    successful: number;
    failed: number;
  }> {
    const response = await this.client.patch('/v1/artifacts/bulk/', data)
    return response.data
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

  async getExportAnalytics(): Promise<ExportAnalytics> {
    const response = await this.client.get<ExportAnalytics>('/v1/export/analytics/')
    return response.data
  }

  // Analytics endpoints
  async getGenerationAnalytics(): Promise<GenerationAnalytics> {
    const response = await this.client.get<GenerationAnalytics>('/v1/generate/analytics/')
    return response.data
  }

  // LLM Services endpoints
  async getLLMModelStats(): Promise<LLMModelStats[]> {
    const response = await this.client.get<LLMModelStats[]>('/v1/llm/model-stats/')
    return response.data
  }

  async selectLLMModel(modelId: string): Promise<{ message: string; selected_model: string }> {
    const response = await this.client.post<{ message: string; selected_model: string }>('/v1/llm/select-model/', { model_id: modelId })
    return response.data
  }

  async getLLMSystemHealth(): Promise<LLMSystemHealth> {
    const response = await this.client.get<LLMSystemHealth>('/v1/llm/system-health/')
    return response.data
  }

  async getAvailableLLMModels(): Promise<string[]> {
    const response = await this.client.get<{ models: string[] }>('/v1/llm/available-models/')
    return response.data.models
  }

  async getLLMPerformanceMetrics(params?: Record<string, string>): Promise<PaginatedResponse<LLMPerformanceMetric>> {
    const queryString = params ? `?${new URLSearchParams(params).toString()}` : ''
    const response = await this.client.get<PaginatedResponse<LLMPerformanceMetric>>(`/v1/llm/performance-metrics/${queryString}`)
    return response.data
  }

  async getLLMCircuitBreakers(): Promise<any> {
    const response = await this.client.get('/v1/llm/circuit-breakers/')
    return response.data
  }

  async getLLMCostTracking(params?: Record<string, string>): Promise<PaginatedResponse<LLMCostTracking>> {
    const queryString = params ? `?${new URLSearchParams(params).toString()}` : ''
    const response = await this.client.get<PaginatedResponse<LLMCostTracking>>(`/v1/llm/cost-tracking/${queryString}`)
    return response.data
  }

  async getLLMJobEmbeddings(params?: Record<string, string>): Promise<PaginatedResponse<JobDescriptionEmbedding>> {
    const queryString = params ? `?${new URLSearchParams(params).toString()}` : ''
    const response = await this.client.get<PaginatedResponse<JobDescriptionEmbedding>>(`/v1/llm/job-embeddings/${queryString}`)
    return response.data
  }

  async getLLMEnhancedArtifacts(params?: Record<string, string>): Promise<PaginatedResponse<EnhancedArtifact>> {
    const queryString = params ? `?${new URLSearchParams(params).toString()}` : ''
    const response = await this.client.get<PaginatedResponse<EnhancedArtifact>>(`/v1/llm/enhanced-artifacts/${queryString}`)
    return response.data
  }
}

// Create singleton instance
export const apiClient = new ApiClient()
export default apiClient