import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Edit,
  Trash2,
  FileText,
  Calendar,
  Users,
  ExternalLink,
  Github,
  Globe,
  Paperclip
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { ArtifactEditForm } from '@/components/ArtifactEditForm'
import { EvidenceLinkManager } from '@/components/EvidenceLinkManager'
import { BulkEditDialog } from '@/components/BulkEditDialog'
import { useArtifactStore } from '@/stores/artifactStore'
import { apiClient } from '@/services/apiClient'
import { formatDateRange } from '@/utils/formatters'
import toast from 'react-hot-toast'
import type { Artifact, ArtifactCreateData } from '@/types'

const evidenceTypeIcons = {
  github: Github,
  live_app: Globe,
  document: FileText,
  website: Globe,
  portfolio: Paperclip,
  other: ExternalLink,
}

export default function ArtifactDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { updateArtifact, deleteArtifact } = useArtifactStore()

  const [artifact, setArtifact] = useState<Artifact | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showBulkEdit, setShowBulkEdit] = useState(false)
  const [isEditing, setIsEditing] = useState(false)

  // Load artifact data
  useEffect(() => {
    if (!id) {
      setError('Artifact ID is required')
      setIsLoading(false)
      return
    }

    const loadArtifact = async () => {
      try {
        setIsLoading(true)
        setError(null) // Clear any previous errors
        const artifactData = await apiClient.getArtifact(parseInt(id))
        setArtifact(artifactData)
      } catch (error) {
        console.error('Failed to load artifact:', error)
        setError('Failed to load artifact')
        toast.error('Failed to load artifact')
      } finally {
        setIsLoading(false)
      }
    }

    loadArtifact()
  }, [id])

  const handleEdit = async (updates: Partial<ArtifactCreateData>) => {
    if (!artifact) {
      console.error('No artifact to update')
      return
    }

    try {
      setIsEditing(true)
      console.log('Starting artifact update for ID:', artifact.id, 'with updates:', updates)

      const updatedArtifact = await apiClient.updateArtifact(artifact.id, updates)
      console.log('Received updated artifact:', updatedArtifact)

      // Ensure the updated artifact has all required fields
      if (!updatedArtifact || !updatedArtifact.id) {
        throw new Error('Invalid response from server')
      }

      // Merge updated data with existing artifact to preserve all fields
      const mergedArtifact = { ...artifact, ...updatedArtifact }
      setArtifact(mergedArtifact)

      // Update global store with merged data
      updateArtifact(artifact.id, mergedArtifact)

      // Clear any error state first to ensure clean state
      setError(null)

      // Close modal after successful update
      setShowEditModal(false)

      toast.success('Artifact updated successfully!')
      console.log('Artifact update completed successfully')
    } catch (error) {
      console.error('Failed to update artifact:', error)
      toast.error('Failed to update artifact')
      throw error
    } finally {
      setIsEditing(false)
    }
  }

  const handleDelete = async () => {
    if (!artifact) return

    if (window.confirm('Are you sure you want to delete this artifact? This action cannot be undone.')) {
      try {
        await apiClient.deleteArtifact(artifact.id)
        deleteArtifact(artifact.id)
        toast.success('Artifact deleted successfully')
        navigate('/artifacts')
      } catch (error) {
        console.error('Failed to delete artifact:', error)
        toast.error('Failed to delete artifact')
      }
    }
  }

  const handleEvidenceUpdate = async () => {
    if (!artifact || !id) return

    try {
      const updatedArtifact = await apiClient.getArtifact(parseInt(id))
      setArtifact(updatedArtifact)
    } catch (error) {
      console.error('Failed to refresh artifact:', error)
    }
  }


  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error || !artifact) {
    console.log('Rendering error state:', { error, hasArtifact: !!artifact, artifactId: artifact?.id })
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <Card className="p-6 text-center">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {error || 'Artifact not found'}
          </h3>
          <p className="text-gray-600 mb-4">
            {error ? 'There was an error loading this artifact.' : 'The requested artifact could not be found.'}
          </p>
          <Button onClick={() => navigate('/artifacts')} variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Artifacts
          </Button>
        </Card>
      </div>
    )
  }

  console.log('Rendering artifact detail page for:', artifact.title, 'ID:', artifact.id)

  return (
    <div key={artifact?.id} className="max-w-6xl mx-auto py-8 px-4 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between min-w-0 gap-4">
        <div className="flex items-center space-x-4 flex-1 min-w-0">
          <Button
            variant="outline"
            onClick={() => navigate('/artifacts')}
            className="flex-shrink-0"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-gray-900 break-words">{artifact.title}</h1>
            <p className="text-gray-600">
              {artifact.artifact_type} • {formatDateRange(artifact.start_date, artifact.end_date)}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 flex-shrink-0">
          <Button
            variant="outline"
            onClick={() => setShowEditModal(true)}
          >
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button
            variant="danger"
            onClick={handleDelete}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Description</h2>
            <p className="text-gray-700 whitespace-pre-wrap break-words">{artifact.description}</p>
          </Card>

          {/* Evidence Links Manager */}
          <EvidenceLinkManager
            artifactId={artifact.id}
            links={artifact.evidence_links}
            onUpdate={handleEvidenceUpdate}
          />
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Basic Info */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Details</h3>

            <div className="space-y-4">
              <div>
                <dt className="text-sm font-medium text-gray-500 mb-1">Type</dt>
                <dd className="text-sm text-gray-900 capitalize">
                  {artifact.artifact_type.replace('_', ' ')}
                </dd>
              </div>

              {(artifact.start_date || artifact.end_date) && (
                <div>
                  <dt className="text-sm font-medium text-gray-500 mb-1 flex items-center">
                    <Calendar className="h-4 w-4 mr-1" />
                    Duration
                  </dt>
                  <dd className="text-sm text-gray-900">
                    {formatDateRange(artifact.start_date, artifact.end_date)}
                  </dd>
                </div>
              )}

              {artifact.collaborators.length > 0 && (
                <div>
                  <dt className="text-sm font-medium text-gray-500 mb-1 flex items-center">
                    <Users className="h-4 w-4 mr-1" />
                    Collaborators
                  </dt>
                  <dd className="text-sm text-gray-900 space-y-1">
                    {artifact.collaborators.map((collaborator, index) => (
                      <div key={index}>{collaborator}</div>
                    ))}
                  </dd>
                </div>
              )}

              <div>
                <dt className="text-sm font-medium text-gray-500 mb-1">Created</dt>
                <dd className="text-sm text-gray-900">
                  {new Date(artifact.created_at).toLocaleDateString()}
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 mb-1">Last Updated</dt>
                <dd className="text-sm text-gray-900">
                  {new Date(artifact.updated_at).toLocaleDateString()}
                </dd>
              </div>
            </div>
          </Card>

          {/* Technologies */}
          {artifact.technologies.length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Technologies</h3>
              <div className="flex flex-wrap gap-2">
                {artifact.technologies.map((tech, index) => (
                  <span
                    key={index}
                    className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </Card>
          )}

          {/* Quick Actions */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => setShowBulkEdit(true)}
              >
                <Edit className="h-4 w-4 mr-2" />
                Bulk Edit Multiple
              </Button>
            </div>
          </Card>
        </div>
      </div>

      {/* Edit Modal */}
      {showEditModal && (
        <Modal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          title="Edit Artifact"
          size="xl"
        >
          <ArtifactEditForm
            key={`${artifact.id}-${artifact.updated_at}`}
            artifact={artifact}
            onSave={handleEdit}
            onCancel={() => setShowEditModal(false)}
            isLoading={isEditing}
          />
        </Modal>
      )}

      {/* Bulk Edit Dialog */}
      <BulkEditDialog
        selectedArtifacts={[artifact]}
        isOpen={showBulkEdit}
        onClose={() => setShowBulkEdit(false)}
        onSuccess={() => {
          setShowBulkEdit(false)
          handleEvidenceUpdate()
        }}
      />
    </div>
  )
}