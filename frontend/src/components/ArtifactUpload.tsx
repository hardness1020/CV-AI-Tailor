import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import {
  Upload,
  X,
  Plus,
  FileText,
  Link as LinkIcon,
  Github,
  Globe,
  Video,
  Loader2
} from 'lucide-react'
import { useArtifactStore } from '@/stores/artifactStore'
import { apiClient } from '@/services/apiClient'
import { cn } from '@/utils/cn'

const evidenceLinkSchema = z.object({
  url: z.string().url('Please enter a valid URL'),
  type: z.enum(['github', 'live_app', 'paper', 'video', 'other']),
  description: z.string().min(1, 'Description is required'),
})

const artifactSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  startDate: z.string().min(1, 'Start date is required'),
  endDate: z.string().optional(),
  technologies: z.array(z.string()).min(1, 'At least one technology is required'),
  collaborators: z.array(z.string()),
  evidenceLinks: z.array(evidenceLinkSchema),
  labelIds: z.array(z.number()),
})

type ArtifactForm = z.infer<typeof artifactSchema>

interface ArtifactUploadProps {
  onUploadComplete?: (artifact: any) => void
  onClose?: () => void
}

const evidenceTypeIcons = {
  github: Github,
  live_app: Globe,
  paper: FileText,
  video: Video,
  other: LinkIcon,
}

const evidenceTypeLabels = {
  github: 'GitHub Repository',
  live_app: 'Live Application',
  paper: 'Research Paper',
  video: 'Video Demo',
  other: 'Other Link',
}

export default function ArtifactUpload({ onUploadComplete, onClose }: ArtifactUploadProps) {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [currentTech, setCurrentTech] = useState('')
  const [currentCollab, setCurrentCollab] = useState('')
  const { addArtifact } = useArtifactStore()

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ArtifactForm>({
    resolver: zodResolver(artifactSchema),
    defaultValues: {
      technologies: [],
      collaborators: [],
      evidenceLinks: [],
      labelIds: [],
    },
  })

  const { fields: evidenceFields, append: appendEvidence, remove: removeEvidence } = useFieldArray({
    control,
    name: 'evidenceLinks',
  })

  const technologies = watch('technologies')
  const collaborators = watch('collaborators')

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.filter(file => {
      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        toast.error(`File ${file.name} is too large. Maximum size is 10MB.`)
        return false
      }

      // Check file type
      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
      if (!allowedTypes.includes(file.type)) {
        toast.error(`File ${file.name} is not supported. Please upload PDF or Word documents.`)
        return false
      }

      return true
    })

    setUploadedFiles(prev => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: true,
    maxFiles: 10,
  })

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const addTechnology = () => {
    if (currentTech.trim() && !technologies.includes(currentTech.trim())) {
      setValue('technologies', [...technologies, currentTech.trim()])
      setCurrentTech('')
    }
  }

  const removeTechnology = (tech: string) => {
    setValue('technologies', technologies.filter(t => t !== tech))
  }

  const addCollaborator = () => {
    if (currentCollab.trim() && !collaborators.includes(currentCollab.trim())) {
      setValue('collaborators', [...collaborators, currentCollab.trim()])
      setCurrentCollab('')
    }
  }

  const removeCollaborator = (collab: string) => {
    setValue('collaborators', collaborators.filter(c => c !== collab))
  }

  const onSubmit = async (data: ArtifactForm) => {
    setIsSubmitting(true)
    try {
      // Transform form data to match backend API schema
      const artifactData = {
        title: data.title,
        description: data.description,
        start_date: data.startDate,
        end_date: data.endDate || undefined,
        technologies: data.technologies,
        collaborators: data.collaborators,
        evidence_links: data.evidenceLinks.map(link => ({
          url: link.url,
          link_type: link.type,
          description: link.description,
        })),
        labelIds: data.labelIds,
      }

      // Create artifact
      const artifact = await apiClient.createArtifact(artifactData)

      // Upload files if any
      if (uploadedFiles.length > 0) {
        await apiClient.uploadArtifactFiles(artifact.id, uploadedFiles)
      }

      addArtifact(artifact)
      toast.success('Artifact uploaded successfully!')
      onUploadComplete?.(artifact)
    } catch (error) {
      console.error('Upload error:', error)
      toast.error('Failed to upload artifact. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="p-6">
      <div className="bg-white p-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Upload New Artifact</h2>
          <p className="mt-2 text-gray-600">
            Add a project, document, or professional work to your artifact library.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
          {/* File Upload Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-4">
              Upload Files (Optional)
            </label>

            <div
              {...getRootProps()}
              className={cn(
                'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
                isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
              )}
            >
              <input {...getInputProps()} />
              <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              {isDragActive ? (
                <p className="text-blue-600">Drop the files here...</p>
              ) : (
                <div>
                  <p className="text-gray-600 mb-2">
                    Drag & drop files here, or click to select files
                  </p>
                  <p className="text-sm text-gray-500">
                    Supports PDF and Word documents (max 10MB each)
                  </p>
                </div>
              )}
            </div>

            {/* Uploaded Files */}
            {uploadedFiles.length > 0 && (
              <div className="mt-4 space-y-2">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <FileText className="h-5 w-5 text-gray-400" />
                      <span className="text-sm font-medium text-gray-900">{file.name}</span>
                      <span className="text-xs text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title *
              </label>
              <input
                {...register('title')}
                type="text"
                className={cn(
                  'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                  errors.title && 'border-red-300 focus:border-red-500 focus:ring-red-500'
                )}
                placeholder="Project or artifact title"
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date *
                </label>
                <input
                  {...register('startDate')}
                  type="date"
                  className={cn(
                    'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                    errors.startDate && 'border-red-300 focus:border-red-500 focus:ring-red-500'
                  )}
                />
                {errors.startDate && (
                  <p className="mt-1 text-sm text-red-600">{errors.startDate.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  End Date
                </label>
                <input
                  {...register('endDate')}
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              {...register('description')}
              rows={4}
              className={cn(
                'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                errors.description && 'border-red-300 focus:border-red-500 focus:ring-red-500'
              )}
              placeholder="Describe what this artifact represents, your role, and key achievements..."
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
            )}
          </div>

          {/* Technologies */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Technologies Used *
            </label>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={currentTech}
                onChange={(e) => setCurrentTech(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTechnology())}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Add technology (e.g., React, Python, AWS)"
              />
              <button
                type="button"
                onClick={addTechnology}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {technologies.map((tech) => (
                <span
                  key={tech}
                  className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                >
                  {tech}
                  <button
                    type="button"
                    onClick={() => removeTechnology(tech)}
                    className="ml-2 text-blue-600 hover:text-blue-800"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            {errors.technologies && (
              <p className="mt-1 text-sm text-red-600">{errors.technologies.message}</p>
            )}
          </div>

          {/* Collaborators */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Collaborators
            </label>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={currentCollab}
                onChange={(e) => setCurrentCollab(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCollaborator())}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Add collaborator name"
              />
              <button
                type="button"
                onClick={addCollaborator}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {collaborators.map((collab) => (
                <span
                  key={collab}
                  className="inline-flex items-center px-3 py-1 bg-gray-100 text-gray-800 text-sm rounded-full"
                >
                  {collab}
                  <button
                    type="button"
                    onClick={() => removeCollaborator(collab)}
                    className="ml-2 text-gray-600 hover:text-gray-800"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Evidence Links */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <label className="block text-sm font-medium text-gray-700">
                Evidence Links
              </label>
              <button
                type="button"
                onClick={() => appendEvidence({ url: '', type: 'other', description: '' })}
                className="text-sm text-blue-600 hover:text-blue-500 font-medium"
              >
                + Add Link
              </button>
            </div>

            <div className="space-y-4">
              {evidenceFields.map((field, index) => {
                const linkType = watch(`evidenceLinks.${index}.type`) as keyof typeof evidenceTypeIcons
                const Icon = evidenceTypeIcons[linkType] || LinkIcon

                return (
                  <div key={field.id} className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <Icon className="h-5 w-5 text-gray-400" />
                        <span className="text-sm font-medium text-gray-700">Evidence Link {index + 1}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeEvidence(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <select
                          {...register(`evidenceLinks.${index}.type`)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                          {Object.entries(evidenceTypeLabels).map(([value, label]) => (
                            <option key={value} value={value}>
                              {label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <input
                          {...register(`evidenceLinks.${index}.url`)}
                          type="url"
                          placeholder="https://..."
                          className={cn(
                            'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                            errors.evidenceLinks?.[index]?.url && 'border-red-300 focus:border-red-500 focus:ring-red-500'
                          )}
                        />
                        {errors.evidenceLinks?.[index]?.url && (
                          <p className="mt-1 text-sm text-red-600">
                            {errors.evidenceLinks[index]?.url?.message}
                          </p>
                        )}
                      </div>

                      <div>
                        <input
                          {...register(`evidenceLinks.${index}.description`)}
                          type="text"
                          placeholder="Brief description"
                          className={cn(
                            'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                            errors.evidenceLinks?.[index]?.description && 'border-red-300 focus:border-red-500 focus:ring-red-500'
                          )}
                        />
                        {errors.evidenceLinks?.[index]?.description && (
                          <p className="mt-1 text-sm text-red-600">
                            {errors.evidenceLinks[index]?.description?.message}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <span>Upload Artifact</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}