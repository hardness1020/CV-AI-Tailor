import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Card } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import type { EvidenceLink } from '@/types'
import { apiClient } from '@/services/apiClient'

interface EvidenceLinkManagerProps {
  artifactId: number
  links: EvidenceLink[]
  onUpdate: () => void
}

interface LinkFormData {
  url: string
  link_type: string
  description: string
}

const LINK_TYPES = [
  { value: 'github', label: 'GitHub Repository' },
  { value: 'live_app', label: 'Live Application' },
  { value: 'document', label: 'Document/PDF' },
  { value: 'website', label: 'Website' },
  { value: 'portfolio', label: 'Portfolio' },
  { value: 'other', label: 'Other' }
]

const getLinkIcon = (linkType: string) => {
  switch (linkType) {
    case 'github':
      return '🔗'
    case 'live_app':
      return '🌐'
    case 'document':
      return '📄'
    case 'website':
      return '🌍'
    case 'portfolio':
      return '💼'
    default:
      return '🔗'
  }
}

const EvidenceLinkItem: React.FC<{
  link: EvidenceLink
  onEdit: () => void
  onDelete: () => void
}> = ({ link, onEdit, onDelete }) => {
  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this evidence link?')) {
      onDelete()
    }
  }

  const getLinkTypeLabel = (type: string) => {
    const linkType = LINK_TYPES.find(t => t.value === type)
    return linkType ? linkType.label : type
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-lg">{getLinkIcon(link.link_type)}</span>
            <span className="font-medium text-gray-900">{getLinkTypeLabel(link.link_type)}</span>
          </div>

          <a
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 underline block truncate"
          >
            {link.url}
          </a>

          {link.description && (
            <p className="text-gray-600 mt-1 text-sm">{link.description}</p>
          )}

          <div className="flex items-center space-x-4 mt-2">
            <div className="flex items-center space-x-1">
              {link.is_accessible ? (
                <>
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-sm text-green-600">Accessible</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                  <span className="text-sm text-red-600">Not accessible</span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2 ml-4">
          <Button
            size="sm"
            variant="secondary"
            onClick={onEdit}
          >
            Edit
          </Button>
          <Button
            size="sm"
            variant="danger"
            onClick={handleDelete}
          >
            Delete
          </Button>
        </div>
      </div>
    </div>
  )
}

const AddEvidenceLinkForm: React.FC<{
  onSave: (data: LinkFormData) => Promise<void>
  onCancel: () => void
}> = ({ onSave, onCancel }) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<LinkFormData>({
    defaultValues: {
      url: '',
      link_type: 'website',
      description: ''
    }
  })

  const onSubmit = async (data: LinkFormData) => {
    await onSave(data)
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
      <h4 className="font-medium text-gray-900 mb-4">Add Evidence Link</h4>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Input
            label="URL"
            placeholder="https://..."
            error={errors.url?.message}
            required
            {...register('url', {
              required: 'URL is required',
              pattern: {
                value: /^https?:\/\/.+/,
                message: 'Please enter a valid URL starting with http:// or https://'
              }
            })}
          />
        </div>

        <div>
          <Select
            label="Link Type"
            options={LINK_TYPES}
            error={errors.link_type?.message}
            {...register('link_type', { required: 'Link type is required' })}
          />
        </div>

        <div>
          <Input
            label="Description (optional)"
            placeholder="Brief description of this link"
            error={errors.description?.message}
            {...register('description', {
              maxLength: { value: 255, message: 'Description must be less than 255 characters' }
            })}
          />
        </div>

        <div className="flex items-center justify-end space-x-3">
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            loading={isSubmitting}
            disabled={isSubmitting}
          >
            Add Link
          </Button>
        </div>
      </form>
    </div>
  )
}

const EditEvidenceLinkModal: React.FC<{
  link: EvidenceLink
  isOpen: boolean
  onClose: () => void
  onSave: (linkId: number, data: Partial<LinkFormData>) => Promise<void>
}> = ({ link, isOpen, onClose, onSave }) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<LinkFormData>({
    defaultValues: {
      url: link.url,
      link_type: link.link_type,
      description: link.description || ''
    }
  })

  const onSubmit = async (data: LinkFormData) => {
    await onSave(link.id, data)
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Evidence Link">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Input
            label="URL"
            placeholder="https://..."
            error={errors.url?.message}
            required
            {...register('url', {
              required: 'URL is required',
              pattern: {
                value: /^https?:\/\/.+/,
                message: 'Please enter a valid URL starting with http:// or https://'
              }
            })}
          />
        </div>

        <div>
          <Select
            label="Link Type"
            options={LINK_TYPES}
            error={errors.link_type?.message}
            {...register('link_type', { required: 'Link type is required' })}
          />
        </div>

        <div>
          <Input
            label="Description (optional)"
            placeholder="Brief description of this link"
            error={errors.description?.message}
            {...register('description', {
              maxLength: { value: 255, message: 'Description must be less than 255 characters' }
            })}
          />
        </div>

        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            loading={isSubmitting}
            disabled={isSubmitting}
          >
            Save Changes
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export const EvidenceLinkManager: React.FC<EvidenceLinkManagerProps> = ({
  artifactId,
  links,
  onUpdate
}) => {
  const [isAdding, setIsAdding] = useState(false)
  const [editingLink, setEditingLink] = useState<EvidenceLink | null>(null)

  const handleAddLink = async (linkData: LinkFormData) => {
    try {
      await apiClient.addEvidenceLink(artifactId, linkData)
      onUpdate()
      setIsAdding(false)
      toast.success('Evidence link added successfully')
    } catch (error) {
      console.error('Failed to add evidence link:', error)
      toast.error('Failed to add evidence link')
      throw error
    }
  }

  const handleEditLink = async (linkId: number, linkData: Partial<LinkFormData>) => {
    try {
      await apiClient.updateEvidenceLink(linkId, linkData)
      onUpdate()
      toast.success('Evidence link updated successfully')
    } catch (error) {
      console.error('Failed to update evidence link:', error)
      toast.error('Failed to update evidence link')
      throw error
    }
  }

  const handleDeleteLink = async (linkId: number) => {
    try {
      await apiClient.deleteEvidenceLink(linkId)
      onUpdate()
      toast.success('Evidence link deleted successfully')
    } catch (error) {
      console.error('Failed to delete evidence link:', error)
      toast.error('Failed to delete evidence link')
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Evidence Links</h3>
          <p className="text-gray-600 text-sm">
            Add links to repositories, live applications, and supporting documents
          </p>
        </div>

        {!isAdding && (
          <Button
            onClick={() => setIsAdding(true)}
            size="sm"
          >
            + Add Evidence Link
          </Button>
        )}
      </div>

      <div className="space-y-4">
        {links.map(link => (
          <EvidenceLinkItem
            key={link.id}
            link={link}
            onEdit={() => setEditingLink(link)}
            onDelete={() => handleDeleteLink(link.id)}
          />
        ))}

        {links.length === 0 && !isAdding && (
          <div className="text-center py-8 text-gray-500">
            <p>No evidence links added yet</p>
            <p className="text-sm">Add links to showcase your work</p>
          </div>
        )}

        {isAdding && (
          <AddEvidenceLinkForm
            onSave={handleAddLink}
            onCancel={() => setIsAdding(false)}
          />
        )}
      </div>

      {editingLink && (
        <EditEvidenceLinkModal
          link={editingLink}
          isOpen={!!editingLink}
          onClose={() => setEditingLink(null)}
          onSave={handleEditLink}
        />
      )}
    </Card>
  )
}