import { create } from 'zustand'
import toast from 'react-hot-toast'
import { apiClient } from '@/services/apiClient'
import type { Artifact, ArtifactFilters } from '@/types'

interface ArtifactState {
  artifacts: Artifact[]
  selectedArtifacts: number[]
  filters: ArtifactFilters
  isLoading: boolean
  error: string | null

  // Actions
  setArtifacts: (artifacts: Artifact[]) => void
  addArtifact: (artifact: Artifact) => void
  updateArtifact: (id: number, updates: Partial<Artifact>) => void
  deleteArtifact: (id: number) => void
  setFilters: (filters: ArtifactFilters) => void
  toggleSelection: (id: number) => void
  clearSelection: () => void
  selectAll: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  loadArtifacts: (customFilters?: ArtifactFilters) => Promise<void>

  // Editing actions
  bulkUpdateArtifacts: (ids: number[], updates: any) => Promise<void>
}

export const useArtifactStore = create<ArtifactState>((set, get) => ({
  artifacts: [],
  selectedArtifacts: [],
  filters: {},
  isLoading: false,
  error: null,

  setArtifacts: (artifacts: Artifact[]) => {
    set({ artifacts })
  },

  addArtifact: (artifact: Artifact) => {
    set((state) => ({
      artifacts: [artifact, ...state.artifacts]
    }))
  },

  updateArtifact: (id: number, updates: Partial<Artifact>) => {
    set((state) => ({
      artifacts: state.artifacts.map((artifact) =>
        artifact.id === id ? { ...artifact, ...updates } : artifact
      )
    }))
  },

  deleteArtifact: (id: number) => {
    set((state) => ({
      artifacts: state.artifacts.filter((artifact) => artifact.id !== id),
      selectedArtifacts: state.selectedArtifacts.filter((selectedId) => selectedId !== id)
    }))
  },

  setFilters: (filters: ArtifactFilters) => {
    set({ filters })
  },

  toggleSelection: (id: number) => {
    set((state) => {
      const isSelected = state.selectedArtifacts.includes(id)
      return {
        selectedArtifacts: isSelected
          ? state.selectedArtifacts.filter((selectedId) => selectedId !== id)
          : [...state.selectedArtifacts, id]
      }
    })
  },

  clearSelection: () => {
    set({ selectedArtifacts: [] })
  },

  selectAll: () => {
    const { artifacts } = get()
    set({ selectedArtifacts: artifacts.map((artifact) => artifact.id) })
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading })
  },

  setError: (error: string | null) => {
    set({ error })
  },

  loadArtifacts: async (customFilters: ArtifactFilters = {}) => {
    try {
      set({ isLoading: true, error: null })
      const response = await apiClient.getArtifacts(customFilters)
      set({ artifacts: response.results })
    } catch (error) {
      console.error('Failed to load artifacts:', error)
      set({ error: 'Failed to load artifacts' })
      toast.error('Failed to load artifacts')
    } finally {
      set({ isLoading: false })
    }
  },

  bulkUpdateArtifacts: async (ids: number[], updates: any) => {
    try {
      const result = await apiClient.bulkUpdateArtifacts({
        artifact_ids: ids,
        action: updates.action,
        values: updates.values
      })

      // Update local state for successful updates
      const successfulIds = result.results
        .filter(r => r.status === 'success')
        .map(r => r.id)

      if (successfulIds.length > 0) {
        set((state) => ({
          artifacts: state.artifacts.map((artifact) => {
            if (successfulIds.includes(artifact.id)) {
              // Apply the bulk update to the artifact
              const updatedArtifact = { ...artifact }

              switch (updates.action) {
                case 'add_technologies':
                  updatedArtifact.technologies = [
                    ...(artifact.technologies || []),
                    ...updates.values.technologies.filter(
                      (tech: string) => !(artifact.technologies || []).includes(tech)
                    )
                  ]
                  break
                case 'remove_technologies':
                  updatedArtifact.technologies = (artifact.technologies || [])
                    .filter(tech => !updates.values.technologies.includes(tech))
                  break
                case 'update_type':
                  updatedArtifact.artifact_type = updates.values.artifact_type
                  break
                case 'add_collaborators':
                  updatedArtifact.collaborators = [
                    ...(artifact.collaborators || []),
                    ...updates.values.collaborators.filter(
                      (collab: string) => !(artifact.collaborators || []).includes(collab)
                    )
                  ]
                  break
                case 'remove_collaborators':
                  updatedArtifact.collaborators = (artifact.collaborators || [])
                    .filter(collab => !updates.values.collaborators.includes(collab))
                  break
              }

              return updatedArtifact
            }
            return artifact
          })
        }))
      }

      return result
    } catch (error) {
      console.error('Bulk update failed:', error)
      toast.error('Bulk update failed')
      throw error
    }
  },
}))