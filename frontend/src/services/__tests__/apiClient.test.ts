import { describe, it, expect, beforeEach, vi } from 'vitest'
import { apiClient } from '../apiClient'

// Mock auth store
vi.mock('@/stores/authStore', () => ({
  useAuthStore: {
    getState: () => ({
      accessToken: 'test-token',
      refreshToken: 'test-refresh-token',
      setTokens: vi.fn(),
      clearAuth: vi.fn(),
    }),
  },
}))

describe('ApiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should have correct base configuration', () => {
    expect(apiClient).toBeDefined()
  })

  describe('Authentication methods', () => {
    it('should have login method', () => {
      expect(typeof apiClient.login).toBe('function')
    })

    it('should have register method', () => {
      expect(typeof apiClient.register).toBe('function')
    })

    it('should have logout method', () => {
      expect(typeof apiClient.logout).toBe('function')
    })

    it('should have getCurrentUser method', () => {
      expect(typeof apiClient.getCurrentUser).toBe('function')
    })
  })

  describe('Artifact methods', () => {
    it('should have getArtifacts method', () => {
      expect(typeof apiClient.getArtifacts).toBe('function')
    })

    it('should have createArtifact method', () => {
      expect(typeof apiClient.createArtifact).toBe('function')
    })

    it('should have updateArtifact method', () => {
      expect(typeof apiClient.updateArtifact).toBe('function')
    })

    it('should have deleteArtifact method', () => {
      expect(typeof apiClient.deleteArtifact).toBe('function')
    })

    it('should have getArtifact method', () => {
      expect(typeof apiClient.getArtifact).toBe('function')
    })

    it('should have uploadArtifactFiles method', () => {
      expect(typeof apiClient.uploadArtifactFiles).toBe('function')
    })
  })

  describe('Generation methods', () => {
    it('should have generateCV method', () => {
      expect(typeof apiClient.generateCV).toBe('function')
    })

    it('should have getGeneration method', () => {
      expect(typeof apiClient.getGeneration).toBe('function')
    })

    it('should have generateCoverLetter method', () => {
      expect(typeof apiClient.generateCoverLetter).toBe('function')
    })

    it('should have getUserGenerations method', () => {
      expect(typeof apiClient.getUserGenerations).toBe('function')
    })

    it('should have rateGeneration method', () => {
      expect(typeof apiClient.rateGeneration).toBe('function')
    })

    it('should have getCVTemplates method', () => {
      expect(typeof apiClient.getCVTemplates).toBe('function')
    })
  })

  describe('Export methods', () => {
    it('should have exportDocument method', () => {
      expect(typeof apiClient.exportDocument).toBe('function')
    })

    it('should have getExportStatus method', () => {
      expect(typeof apiClient.getExportStatus).toBe('function')
    })

    it('should have downloadExport method', () => {
      expect(typeof apiClient.downloadExport).toBe('function')
    })

    it('should have getUserExports method', () => {
      expect(typeof apiClient.getUserExports).toBe('function')
    })

    it('should have getExportTemplates method', () => {
      expect(typeof apiClient.getExportTemplates).toBe('function')
    })
  })

  describe('Labels and metadata methods', () => {
    it('should have getLabels method', () => {
      expect(typeof apiClient.getLabels).toBe('function')
    })

    it('should have createLabel method', () => {
      expect(typeof apiClient.createLabel).toBe('function')
    })

    it('should have suggestSkills method', () => {
      expect(typeof apiClient.suggestSkills).toBe('function')
    })
  })
})