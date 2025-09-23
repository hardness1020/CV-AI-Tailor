import { create } from 'zustand'
import type { GeneratedDocument } from '@/types'

interface GenerationState {
  activeGenerations: Map<string, GeneratedDocument>
  completedDocuments: GeneratedDocument[]
  isGenerating: boolean

  // Actions
  startGeneration: (id: string, type: 'cv' | 'cover_letter') => void
  updateGeneration: (id: string, document: GeneratedDocument) => void
  completeGeneration: (id: string, document: GeneratedDocument) => void
  removeGeneration: (id: string) => void
  clearCompleted: () => void
}

export const useGenerationStore = create<GenerationState>((set) => ({
  activeGenerations: new Map(),
  completedDocuments: [],
  isGenerating: false,

  startGeneration: (id: string, type: 'cv' | 'cover_letter') => {
    const newGeneration: GeneratedDocument = {
      id,
      type,
      status: 'processing',
      progressPercentage: 0,
      createdAt: new Date().toISOString(),
      jobDescriptionHash: '',
    }

    set((state) => {
      const newActiveGenerations = new Map(state.activeGenerations)
      newActiveGenerations.set(id, newGeneration)
      return {
        activeGenerations: newActiveGenerations,
        isGenerating: true,
      }
    })
  },

  updateGeneration: (id: string, document: GeneratedDocument) => {
    set((state) => {
      const newActiveGenerations = new Map(state.activeGenerations)
      newActiveGenerations.set(id, document)
      return {
        activeGenerations: newActiveGenerations,
      }
    })
  },

  completeGeneration: (id: string, document: GeneratedDocument) => {
    set((state) => {
      const newActiveGenerations = new Map(state.activeGenerations)
      newActiveGenerations.delete(id)

      return {
        activeGenerations: newActiveGenerations,
        completedDocuments: [document, ...state.completedDocuments],
        isGenerating: newActiveGenerations.size > 0,
      }
    })
  },

  removeGeneration: (id: string) => {
    set((state) => {
      const newActiveGenerations = new Map(state.activeGenerations)
      newActiveGenerations.delete(id)

      return {
        activeGenerations: newActiveGenerations,
        isGenerating: newActiveGenerations.size > 0,
      }
    })
  },

  clearCompleted: () => {
    set({ completedDocuments: [] })
  },
}))