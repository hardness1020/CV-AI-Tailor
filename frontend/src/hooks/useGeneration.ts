import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { useGenerationStore } from '@/stores/generationStore'
import { apiClient } from '@/services/apiClient'
import type { CVGenerationRequest } from '@/types'

export function useGeneration() {
  const {
    activeGenerations,
    completedDocuments,
    isGenerating,
    startGeneration,
    updateGeneration,
    completeGeneration,
    removeGeneration,
  } = useGenerationStore()

  const [pollingIntervals, setPollingIntervals] = useState<Record<string, number>>({})

  const generateCV = async (request: CVGenerationRequest) => {
    try {
      const response = await apiClient.generateCV(request)
      const generationId = response.generation_id

      // Start tracking the generation
      startGeneration(generationId, 'cv')

      // Start polling for updates
      startPolling(generationId)

      toast.success('CV generation started!')
      return generationId
    } catch (error) {
      console.error('Failed to start CV generation:', error)
      toast.error('Failed to start CV generation')
      throw error
    }
  }

  const generateCoverLetter = async (request: Omit<CVGenerationRequest, 'templateId'>) => {
    try {
      const response = await apiClient.generateCoverLetter(request)
      const generationId = response.generation_id

      // Start tracking the generation
      startGeneration(generationId, 'cover_letter')

      // Start polling for updates
      startPolling(generationId)

      toast.success('Cover letter generation started!')
      return generationId
    } catch (error) {
      console.error('Failed to start cover letter generation:', error)
      toast.error('Failed to start cover letter generation')
      throw error
    }
  }

  const startPolling = useCallback((generationId: string) => {
    // Clear existing interval if any
    if (pollingIntervals[generationId]) {
      clearInterval(pollingIntervals[generationId])
    }

    const interval = setInterval(async () => {
      try {
        const document = await apiClient.getGeneration(generationId)
        updateGeneration(generationId, document)

        if (document.status === 'completed') {
          completeGeneration(generationId, document)
          clearInterval(interval)
          setPollingIntervals(prev => {
            const newIntervals = { ...prev }
            delete newIntervals[generationId]
            return newIntervals
          })
          toast.success('Generation completed!')
        } else if (document.status === 'failed') {
          removeGeneration(generationId)
          clearInterval(interval)
          setPollingIntervals(prev => {
            const newIntervals = { ...prev }
            delete newIntervals[generationId]
            return newIntervals
          })
          toast.error('Generation failed')
        }
      } catch (error: any) {
        console.error('Failed to poll generation status:', error)
        // Continue polling unless it's a 404 (generation not found)
        if (error.response?.status === 404) {
          removeGeneration(generationId)
          clearInterval(interval)
          setPollingIntervals(prev => {
            const newIntervals = { ...prev }
            delete newIntervals[generationId]
            return newIntervals
          })
        }
      }
    }, 2000) // Poll every 2 seconds

    setPollingIntervals(prev => ({
      ...prev,
      [generationId]: interval
    }))
  }, [updateGeneration, completeGeneration, removeGeneration, pollingIntervals])

  const cancelGeneration = (generationId: string) => {
    // Clear polling
    if (pollingIntervals[generationId]) {
      clearInterval(pollingIntervals[generationId])
      setPollingIntervals(prev => {
        const newIntervals = { ...prev }
        delete newIntervals[generationId]
        return newIntervals
      })
    }

    // Remove from store
    removeGeneration(generationId)
    toast.success('Generation cancelled')
  }

  const rateGeneration = async (generationId: string, rating: number, feedback?: string) => {
    try {
      await apiClient.rateGeneration(generationId, rating, feedback)
      toast.success('Thank you for your feedback!')
    } catch (error) {
      console.error('Failed to rate generation:', error)
      toast.error('Failed to submit rating')
      throw error
    }
  }

  const loadUserGenerations = async () => {
    try {
      const generations = await apiClient.getUserGenerations()
      // Add completed generations to store
      generations.forEach(generation => {
        if (generation.status === 'completed') {
          completeGeneration(generation.id, generation)
        }
      })
    } catch (error) {
      console.error('Failed to load user generations:', error)
    }
  }

  // Cleanup intervals on unmount
  useEffect(() => {
    return () => {
      Object.values(pollingIntervals).forEach(interval => {
        clearInterval(interval)
      })
    }
  }, [pollingIntervals])

  // Load user generations on mount
  useEffect(() => {
    loadUserGenerations()
  }, [])

  return {
    activeGenerations: Array.from(activeGenerations.values()),
    completedDocuments,
    isGenerating,
    generateCV,
    generateCoverLetter,
    cancelGeneration,
    rateGeneration,
    loadUserGenerations,
  }
}