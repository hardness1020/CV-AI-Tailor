import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { TagInput } from '@/components/ui/TagInput'
import { Modal } from '@/components/ui/Modal'
import type { Artifact } from '@/types'
import { apiClient } from '@/services/apiClient'

interface BulkEditDialogProps {
  selectedArtifacts: Artifact[]
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

type BulkAction = 'add_technologies' | 'remove_technologies' | 'update_type' | 'add_collaborators' | 'remove_collaborators'

interface BulkFormData {
  action: BulkAction
  technologies: string[]
  artifact_type: string
  collaborators: string[]
}

const BULK_ACTIONS = [
  { value: 'add_technologies', label: 'Add Technologies' },
  { value: 'remove_technologies', label: 'Remove Technologies' },
  { value: 'update_type', label: 'Update Artifact Type' },
  { value: 'add_collaborators', label: 'Add Collaborators' },
  { value: 'remove_collaborators', label: 'Remove Collaborators' }
]

const ARTIFACT_TYPES = [
  { value: 'project', label: 'Project' },
  { value: 'publication', label: 'Publication' },
  { value: 'presentation', label: 'Presentation' },
  { value: 'certification', label: 'Certification' },
  { value: 'experience', label: 'Work Experience' },
  { value: 'education', label: 'Education' }
]

const BulkPreview: React.FC<{
  artifacts: Artifact[]
  action: BulkAction
  values: Partial<BulkFormData>
}> = ({ artifacts, action, values }) => {
  const getPreviewText = (artifact: Artifact) => {
    switch (action) {
      case 'add_technologies':
        if (values.technologies?.length) {
          const newTechs = values.technologies.filter(tech =>
            !(artifact.technologies || []).includes(tech)
          )
          if (newTechs.length === 0) return 'No new technologies to add'
          return `+${newTechs.join(', ')}`
        }
        return 'Select technologies to add'

      case 'remove_technologies':
        if (values.technologies?.length) {
          const toRemove = values.technologies.filter(tech =>
            (artifact.technologies || []).includes(tech)
          )
          if (toRemove.length === 0) return 'No matching technologies to remove'
          return `-${toRemove.join(', ')}`
        }
        return 'Select technologies to remove'

      case 'update_type':
        if (values.artifact_type) {
          if (artifact.artifact_type === values.artifact_type) {
            return 'No change (already this type)'
          }
          return `${artifact.artifact_type} → ${values.artifact_type}`
        }
        return 'Select new type'

      case 'add_collaborators':
        if (values.collaborators?.length) {
          const newCollabs = values.collaborators.filter(collab =>
            !(artifact.collaborators || []).includes(collab)
          )
          if (newCollabs.length === 0) return 'No new collaborators to add'
          return `+${newCollabs.join(', ')}`
        }
        return 'Select collaborators to add'

      case 'remove_collaborators':
        if (values.collaborators?.length) {
          const toRemove = values.collaborators.filter(collab =>
            (artifact.collaborators || []).includes(collab)
          )
          if (toRemove.length === 0) return 'No matching collaborators to remove'
          return `-${toRemove.join(', ')}`
        }
        return 'Select collaborators to remove'

      default:
        return 'No changes'
    }
  }

  return (
    <div className="mt-6">
      <h4 className="font-medium text-gray-900 mb-3">Preview Changes</h4>
      <div className="max-h-60 overflow-y-auto space-y-2">
        {artifacts.map(artifact => (
          <div
            key={artifact.id}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div className="flex-1 min-w-0">
              <h5 className="font-medium text-gray-900 truncate">{artifact.title}</h5>
            </div>
            <div className="ml-4 text-sm text-gray-600">
              {getPreviewText(artifact)}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export const BulkEditDialog: React.FC<BulkEditDialogProps> = ({
  selectedArtifacts,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [isProcessing, setIsProcessing] = useState(false)
  const [technologySuggestions, setTechnologySuggestions] = useState<string[]>([])

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors }
  } = useForm<BulkFormData>({
    defaultValues: {
      action: 'add_technologies',
      technologies: [],
      artifact_type: 'project',
      collaborators: []
    }
  })

  const selectedAction = watch('action')
  const formValues = watch()

  // Load technology suggestions when dialog opens
  React.useEffect(() => {
    if (isOpen) {
      const loadSuggestions = async () => {
        try {
          const suggestions = await apiClient.getTechnologySuggestions()
          setTechnologySuggestions(suggestions)
        } catch (error) {
          console.error('Failed to load technology suggestions:', error)
        }
      }
      loadSuggestions()
    }
  }, [isOpen])

  // Reset form when dialog closes
  React.useEffect(() => {
    if (!isOpen) {
      reset()
    }
  }, [isOpen, reset])

  const onSubmit = async (data: BulkFormData) => {
    setIsProcessing(true)
    try {
      const bulkData = {
        artifact_ids: selectedArtifacts.map(a => a.id),
        action: data.action,
        values: {} as any
      }

      switch (data.action) {
        case 'add_technologies':
        case 'remove_technologies':
          bulkData.values.technologies = data.technologies
          break
        case 'update_type':
          bulkData.values.artifact_type = data.artifact_type
          break
        case 'add_collaborators':
        case 'remove_collaborators':
          bulkData.values.collaborators = data.collaborators
          break
      }

      const result = await apiClient.bulkUpdateArtifacts(bulkData)

      // Show results
      const successCount = result.successful
      const failCount = result.failed

      if (failCount === 0) {
        toast.success(`Successfully updated ${successCount} artifacts`)
      } else {
        toast.success(`Updated ${successCount} artifacts, ${failCount} failed`)
      }

      // Show detailed results if there are failures
      if (failCount > 0) {
        const failures = result.results.filter(r => r.status === 'error')
        const failedTitles = failures.map(f => {
          const artifact = selectedArtifacts.find(a => a.id === f.id)
          return artifact ? artifact.title : `ID ${f.id}`
        }).join(', ')

        toast.error(`Failed to update: ${failedTitles}`, { duration: 5000 })
      }

      onSuccess()
      onClose()
    } catch (error) {
      console.error('Bulk update failed:', error)
      toast.error('Bulk update operation failed')
    } finally {
      setIsProcessing(false)
    }
  }

  const renderActionFields = () => {
    switch (selectedAction) {
      case 'add_technologies':
      case 'remove_technologies':
        return (
          <div>
            <TagInput
              label={selectedAction === 'add_technologies' ? 'Technologies to Add' : 'Technologies to Remove'}
              placeholder="Enter technology names"
              value={watch('technologies')}
              onChange={(technologies) => setValue('technologies', technologies)}
              suggestions={technologySuggestions}
              error={errors.technologies?.message}
            />
            <p className="text-sm text-gray-500 mt-1">
              {selectedAction === 'add_technologies'
                ? 'These technologies will be added to all selected artifacts'
                : 'These technologies will be removed from selected artifacts (if present)'
              }
            </p>
          </div>
        )

      case 'update_type':
        return (
          <div>
            <Select
              label="New Artifact Type"
              options={ARTIFACT_TYPES}
              error={errors.artifact_type?.message}
              {...register('artifact_type', { required: 'Artifact type is required' })}
            />
            <p className="text-sm text-gray-500 mt-1">
              All selected artifacts will be changed to this type
            </p>
          </div>
        )

      case 'add_collaborators':
      case 'remove_collaborators':
        return (
          <div>
            <TagInput
              label={selectedAction === 'add_collaborators' ? 'Collaborators to Add' : 'Collaborators to Remove'}
              placeholder="Enter email addresses"
              value={watch('collaborators')}
              onChange={(collaborators) => setValue('collaborators', collaborators)}
              error={errors.collaborators?.message}
              validate={(value) => {
                const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
                if (value && !emailPattern.test(value)) {
                  return 'Please enter a valid email address'
                }
                return true
              }}
            />
            <p className="text-sm text-gray-500 mt-1">
              {selectedAction === 'add_collaborators'
                ? 'These collaborators will be added to all selected artifacts'
                : 'These collaborators will be removed from selected artifacts (if present)'
              }
            </p>
          </div>
        )

      default:
        return null
    }
  }

  const canApplyChanges = () => {
    switch (selectedAction) {
      case 'add_technologies':
      case 'remove_technologies':
        return formValues.technologies && formValues.technologies.length > 0
      case 'update_type':
        return formValues.artifact_type
      case 'add_collaborators':
      case 'remove_collaborators':
        return formValues.collaborators && formValues.collaborators.length > 0
      default:
        return false
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Bulk Edit (${selectedArtifacts.length} artifacts selected)`}
      size="lg"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <Select
            label="Action"
            options={BULK_ACTIONS}
            error={errors.action?.message}
            {...register('action', { required: 'Action is required' })}
          />
        </div>

        {renderActionFields()}

        <BulkPreview
          artifacts={selectedArtifacts}
          action={selectedAction}
          values={formValues}
        />

        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <svg className="w-5 h-5 text-amber-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div>
              <h4 className="font-medium text-amber-800">
                This will update {selectedArtifacts.length} artifacts
              </h4>
              <p className="text-amber-700 text-sm mt-1">
                This action cannot be undone. Please review the preview above before proceeding.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={isProcessing}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={!canApplyChanges() || isProcessing}
            loading={isProcessing}
          >
            Apply Changes
          </Button>
        </div>
      </form>
    </Modal>
  )
}