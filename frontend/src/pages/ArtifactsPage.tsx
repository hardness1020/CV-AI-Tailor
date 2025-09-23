import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Plus,
  Search,
  Grid,
  List,
  FileText,
  Users,
  ExternalLink,
  Edit,
  Trash2,
  Github,
  Globe,
  Video
} from 'lucide-react'
import { useArtifactStore } from '@/stores/artifactStore'
import { useArtifacts } from '@/hooks/useArtifacts'
import ArtifactUpload from '@/components/ArtifactUpload'
import { formatDateRange } from '@/utils/formatters'
import { cn } from '@/utils/cn'
import type { Artifact } from '@/types'

const evidenceTypeIcons = {
  github: Github,
  live_app: Globe,
  paper: FileText,
  video: Video,
  other: ExternalLink,
}

export default function ArtifactsPage() {
  const [searchParams] = useSearchParams()
  const [showUpload, setShowUpload] = useState(searchParams.get('action') === 'upload')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'active' | 'archived'>('all')

  const { selectedArtifacts, toggleSelection, clearSelection } = useArtifactStore()
  const { artifacts, isLoading, loadArtifacts, deleteArtifact, bulkDelete } = useArtifacts()

  useEffect(() => {
    loadArtifacts({
      search: searchQuery || undefined,
      status: selectedStatus === 'all' ? undefined : selectedStatus,
    })
  }, [selectedStatus, searchQuery, loadArtifacts])

  const filteredArtifacts = artifacts.filter(artifact => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        artifact.title.toLowerCase().includes(query) ||
        artifact.description.toLowerCase().includes(query) ||
        artifact.technologies.some(tech => tech.toLowerCase().includes(query))
      )
    }
    return true
  })

  const handleUploadComplete = () => {
    setShowUpload(false)
    // Artifacts will be reloaded automatically by the hook
  }

  const handleBulkDelete = async () => {
    if (selectedArtifacts.length === 0) return
    if (window.confirm(`Delete ${selectedArtifacts.length} selected artifacts?`)) {
      await bulkDelete(selectedArtifacts)
      clearSelection()
    }
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this artifact?')) {
      await deleteArtifact(id)
    }
  }

  if (showUpload) {
    return (
      <ArtifactUpload
        onUploadComplete={handleUploadComplete}
        onClose={() => setShowUpload(false)}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Artifacts</h1>
          <p className="mt-2 text-gray-600">
            Manage your professional projects, documents, and work samples.
          </p>
        </div>
        <button
          onClick={() => setShowUpload(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <Plus className="h-5 w-5" />
          <span>Upload Artifact</span>
        </button>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search artifacts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex items-center space-x-4">
            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as 'all' | 'active' | 'archived')}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>

            {/* View Mode Toggle */}
            <div className="flex rounded-md border border-gray-300">
              <button
                onClick={() => setViewMode('grid')}
                className={cn(
                  'px-3 py-2 text-sm font-medium rounded-l-md',
                  viewMode === 'grid'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:text-gray-900'
                )}
              >
                <Grid className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  'px-3 py-2 text-sm font-medium rounded-r-md border-l border-gray-300',
                  viewMode === 'list'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:text-gray-900'
                )}
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Selection Actions */}
        {selectedArtifacts.length > 0 && (
          <div className="mt-4 p-3 bg-blue-50 rounded-md">
            <div className="flex items-center justify-between">
              <span className="text-sm text-blue-800">
                {selectedArtifacts.length} artifact{selectedArtifacts.length !== 1 ? 's' : ''} selected
              </span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={clearSelection}
                  className="text-sm text-blue-600 hover:text-blue-500"
                >
                  Clear selection
                </button>
                <button
                  onClick={handleBulkDelete}
                  className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                >
                  Delete Selected
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Artifacts Grid/List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : filteredArtifacts.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredArtifacts.map((artifact) => (
              <ArtifactCard
                key={artifact.id}
                artifact={artifact}
                isSelected={selectedArtifacts.includes(artifact.id)}
                onToggleSelect={() => toggleSelection(artifact.id)}
                onDelete={() => handleDelete(artifact.id)}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredArtifacts.map((artifact) => (
              <ArtifactListItem
                key={artifact.id}
                artifact={artifact}
                isSelected={selectedArtifacts.includes(artifact.id)}
                onToggleSelect={() => toggleSelection(artifact.id)}
                onDelete={() => handleDelete(artifact.id)}
              />
            ))}
          </div>
        )
      ) : (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No artifacts found</h3>
          <p className="text-gray-500 mb-6">
            {searchQuery || selectedStatus !== 'all'
              ? 'Try adjusting your search or filters.'
              : 'Get started by uploading your first artifact.'}
          </p>
          {!searchQuery && selectedStatus === 'all' && (
            <button
              onClick={() => setShowUpload(true)}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="h-5 w-5" />
              <span>Upload First Artifact</span>
            </button>
          )}
        </div>
      )}
    </div>
  )
}

interface ArtifactCardProps {
  artifact: Artifact
  isSelected: boolean
  onToggleSelect: () => void
  onDelete: () => void
}

function ArtifactCard({ artifact, isSelected, onToggleSelect }: ArtifactCardProps) {
  return (
    <div
      className={cn(
        'bg-white rounded-lg shadow-sm border-2 p-6 cursor-pointer transition-all hover:shadow-md',
        isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
      )}
      onClick={onToggleSelect}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <FileText className="h-5 w-5 text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">{artifact.title}</h3>
            <p className="text-sm text-gray-500">
              {formatDateRange(artifact.startDate, artifact.endDate)}
            </p>
          </div>
        </div>
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelect}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          onClick={(e) => e.stopPropagation()}
        />
      </div>

      <p className="text-sm text-gray-600 mb-4 line-clamp-3">{artifact.description}</p>

      {/* Technologies */}
      <div className="flex flex-wrap gap-1 mb-4">
        {artifact.technologies.slice(0, 3).map((tech) => (
          <span
            key={tech}
            className="inline-block px-2 py-1 bg-gray-100 text-xs text-gray-700 rounded"
          >
            {tech}
          </span>
        ))}
        {artifact.technologies.length > 3 && (
          <span className="inline-block px-2 py-1 bg-gray-100 text-xs text-gray-500 rounded">
            +{artifact.technologies.length - 3} more
          </span>
        )}
      </div>

      {/* Evidence Links */}
      {artifact.evidenceLinks.length > 0 && (
        <div className="flex items-center space-x-2 mb-4">
          {artifact.evidenceLinks.slice(0, 3).map((link, index) => {
            const Icon = evidenceTypeIcons[link.type] || ExternalLink
            return (
              <div
                key={index}
                className="p-1 bg-gray-100 rounded"
                title={link.description}
              >
                <Icon className="h-3 w-3 text-gray-600" />
              </div>
            )
          })}
          {artifact.evidenceLinks.length > 3 && (
            <span className="text-xs text-gray-500">
              +{artifact.evidenceLinks.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Collaborators */}
      {artifact.collaborators.length > 0 && (
        <div className="flex items-center space-x-1 text-xs text-gray-500">
          <Users className="h-3 w-3" />
          <span>{artifact.collaborators.length} collaborator{artifact.collaborators.length !== 1 ? 's' : ''}</span>
        </div>
      )}
    </div>
  )
}

interface ArtifactListItemProps {
  artifact: Artifact
  isSelected: boolean
  onToggleSelect: () => void
  onDelete: () => void
}

function ArtifactListItem({ artifact, isSelected, onToggleSelect, onDelete }: ArtifactListItemProps) {
  return (
    <div
      className={cn(
        'bg-white rounded-lg shadow-sm border p-6 cursor-pointer transition-all hover:shadow-md',
        isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
      )}
      onClick={onToggleSelect}
    >
      <div className="flex items-start space-x-4">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelect}
          className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          onClick={(e) => e.stopPropagation()}
        />

        <div className="p-2 bg-blue-100 rounded-lg">
          <FileText className="h-6 w-6 text-blue-600" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-gray-900">{artifact.title}</h3>
              <p className="text-sm text-gray-500 mt-1">
                {formatDateRange(artifact.startDate, artifact.endDate)}
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                className="p-1 text-gray-400 hover:text-gray-600"
                title="Edit artifact"
                onClick={(e) => e.stopPropagation()}
              >
                <Edit className="h-4 w-4" />
              </button>
              <button
                className="p-1 text-gray-400 hover:text-red-600"
                title="Delete artifact"
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete()
                }}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>

          <p className="text-sm text-gray-600 mt-2">{artifact.description}</p>

          <div className="flex items-center justify-between mt-4">
            <div className="flex flex-wrap gap-1">
              {artifact.technologies.map((tech) => (
                <span
                  key={tech}
                  className="inline-block px-2 py-1 bg-gray-100 text-xs text-gray-700 rounded"
                >
                  {tech}
                </span>
              ))}
            </div>

            <div className="flex items-center space-x-4 text-sm text-gray-500">
              {artifact.evidenceLinks.length > 0 && (
                <span className="flex items-center space-x-1">
                  <ExternalLink className="h-3 w-3" />
                  <span>{artifact.evidenceLinks.length} link{artifact.evidenceLinks.length !== 1 ? 's' : ''}</span>
                </span>
              )}
              {artifact.collaborators.length > 0 && (
                <span className="flex items-center space-x-1">
                  <Users className="h-3 w-3" />
                  <span>{artifact.collaborators.length} collaborator{artifact.collaborators.length !== 1 ? 's' : ''}</span>
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}