import React, { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Textarea'
import { Select } from '@/components/ui/Select'
import { TagInput } from '@/components/ui/TagInput'
import { DatePicker } from '@/components/ui/DatePicker'
import { Card } from '@/components/ui/Card'
import type { Artifact, ArtifactCreateData } from '@/types'
import { apiClient } from '@/services/apiClient'

interface ArtifactEditFormProps {
  artifact: Artifact
  onSave: (updates: Partial<ArtifactCreateData>) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

interface FormData {
  title: string
  description: string
  artifact_type: string
  start_date: string
  end_date: string
  technologies: string[]
  collaborators: string[]
}

const ARTIFACT_TYPES = [
  { value: 'project', label: 'Project' },
  { value: 'publication', label: 'Publication' },
  { value: 'presentation', label: 'Presentation' },
  { value: 'certification', label: 'Certification' },
  { value: 'experience', label: 'Work Experience' },
  { value: 'education', label: 'Education' }
]

export const ArtifactEditForm: React.FC<ArtifactEditFormProps> = ({
  artifact,
  onSave,
  onCancel,
  isLoading = false
}) => {
  const [isDirty, setIsDirty] = useState(false)
  const [technologySuggestions, setTechnologySuggestions] = useState<string[]>([])

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting }
  } = useForm<FormData>({
    defaultValues: {
      title: artifact.title,
      description: artifact.description,
      artifact_type: artifact.artifact_type,
      start_date: artifact.start_date || '',
      end_date: artifact.end_date || '',
      technologies: artifact.technologies || [],
      collaborators: artifact.collaborators || []
    }
  })

  // Watch for changes to mark form as dirty
  const watchedValues = watch()
  useEffect(() => {
    const originalValues = {
      title: artifact.title,
      description: artifact.description,
      artifact_type: artifact.artifact_type,
      start_date: artifact.start_date || '',
      end_date: artifact.end_date || '',
      technologies: artifact.technologies || [],
      collaborators: artifact.collaborators || []
    }

    const hasChanges = JSON.stringify(watchedValues) !== JSON.stringify(originalValues)
    setIsDirty(hasChanges)
  }, [watchedValues, artifact])

  // Load technology suggestions
  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        const suggestions = await apiClient.getTechnologySuggestions()
        setTechnologySuggestions(suggestions)
      } catch (error) {
        console.error('Failed to load technology suggestions:', error)
      }
    }
    loadSuggestions()
  }, [])

  const onSubmit = async (data: FormData) => {
    try {
      const updates: Partial<ArtifactCreateData> = {}

      // Only include changed fields
      if (data.title !== artifact.title) updates.title = data.title
      if (data.description !== artifact.description) updates.description = data.description
      if (data.artifact_type !== artifact.artifact_type) updates.artifact_type = data.artifact_type
      if (data.start_date !== (artifact.start_date || '')) {
        updates.start_date = data.start_date || undefined
      }
      if (data.end_date !== (artifact.end_date || '')) {
        updates.end_date = data.end_date || undefined
      }
      if (JSON.stringify(data.technologies) !== JSON.stringify(artifact.technologies || [])) {
        updates.technologies = data.technologies
      }
      if (JSON.stringify(data.collaborators) !== JSON.stringify(artifact.collaborators || [])) {
        updates.collaborators = data.collaborators
      }

      // Only call onSave if there are actual changes
      if (Object.keys(updates).length > 0) {
        await onSave(updates)
        setIsDirty(false)
      } else {
        // No changes, just close the modal
        onCancel()
      }
    } catch (error) {
      console.error('Failed to update artifact:', error)
      // Let the parent component handle error display
      throw error
    }
  }

  const handleCancel = () => {
    if (isDirty) {
      if (window.confirm('You have unsaved changes. Are you sure you want to cancel?')) {
        onCancel()
      }
    } else {
      onCancel()
    }
  }

  const validateDates = (startDate: string, endDate: string) => {
    if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
      return 'End date must be after start date'
    }
    return true
  }

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Edit Artifact: {artifact.title}
        </h2>
        <p className="text-gray-600 mt-1">
          Update your artifact information and evidence
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <Input
            label="Title"
            placeholder="Enter artifact title"
            error={errors.title?.message}
            required
            {...register('title', {
              required: 'Title is required',
              maxLength: { value: 255, message: 'Title must be less than 255 characters' }
            })}
          />
        </div>

        <div>
          <Textarea
            label="Description"
            placeholder="Describe your artifact, its purpose, and key achievements"
            rows={5}
            error={errors.description?.message}
            required
            {...register('description', {
              required: 'Description is required',
              maxLength: { value: 5000, message: 'Description must be less than 5000 characters' }
            })}
          />
        </div>

        <div>
          <Select
            label="Type"
            options={ARTIFACT_TYPES}
            error={errors.artifact_type?.message}
            {...register('artifact_type', { required: 'Type is required' })}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <DatePicker
              label="Start Date"
              value={watch('start_date')}
              onChange={(date) => setValue('start_date', date, { shouldDirty: true })}
              error={errors.start_date?.message}
            />
          </div>
          <div>
            <DatePicker
              label="End Date"
              value={watch('end_date')}
              onChange={(date) => setValue('end_date', date, { shouldDirty: true })}
              error={errors.end_date?.message}
              validate={(date) => validateDates(watch('start_date'), date)}
            />
          </div>
        </div>

        <div>
          <TagInput
            label="Technologies"
            placeholder="Add technologies used (press Enter to add)"
            value={watch('technologies')}
            onChange={(technologies) => setValue('technologies', technologies, { shouldDirty: true })}
            suggestions={technologySuggestions}
            error={errors.technologies?.message}
          />
          <p className="text-sm text-gray-500 mt-1">
            Add technologies, frameworks, and tools used in this artifact
          </p>
        </div>

        <div>
          <TagInput
            label="Collaborators"
            placeholder="Add collaborator email addresses"
            value={watch('collaborators')}
            onChange={(collaborators) => setValue('collaborators', collaborators, { shouldDirty: true })}
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
            Add email addresses of people who collaborated on this artifact
          </p>
        </div>

        <div className="flex items-center justify-between pt-6 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            {isDirty && (
              <span className="text-sm text-amber-600 flex items-center">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                Unsaved changes
              </span>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <Button
              type="button"
              variant="secondary"
              onClick={handleCancel}
              disabled={isSubmitting || isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!isDirty || isSubmitting || isLoading}
              loading={isSubmitting || isLoading}
            >
              Save Changes
            </Button>
          </div>
        </div>
      </form>
    </Card>
  )
}