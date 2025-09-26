import { useState, useEffect, useMemo } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
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
  Video,
  Settings,
  ArrowRight,
  Sparkles,
  FolderOpen,
  Filter
} from 'lucide-react'
import { useArtifactStore } from '@/stores/artifactStore'
import { useArtifacts } from '@/hooks/useArtifacts'
import ArtifactUpload from '@/components/ArtifactUpload'
import { BulkEditDialog } from '@/components/BulkEditDialog'
import { Button } from '@/components/ui/Button'
import { formatDateRange } from '@/utils/formatters'
import { cn } from '@/utils/cn'
import type { Artifact } from '@/types'

const evidenceTypeIcons = {
  github: Github,
  live_app: Globe,
  document: FileText,
  website: Globe,
  portfolio: ExternalLink,
  paper: FileText,
  video: Video,
  other: ExternalLink,
} as const

export default function ArtifactsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const [showUpload, setShowUpload] = useState(false)
  const [showBulkEdit, setShowBulkEdit] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'active' | 'archived'>('all')

  const { selectedArtifacts, toggleSelection, clearSelection, artifacts } = useArtifactStore()
  const { isLoading, loadArtifacts, deleteArtifact, bulkDelete } = useArtifacts()

  // Memoize filters to prevent unnecessary re-renders
  const filters = useMemo(() => ({
    search: searchQuery || undefined,
    status: selectedStatus === 'all' ? undefined : selectedStatus,
  }), [searchQuery, selectedStatus])

  // Load artifacts on mount and when filters change
  useEffect(() => {
    loadArtifacts(filters)
  }, [filters]) // loadArtifacts is stable from Zustand, so we don't need it in dependencies

  // Handle URL parameter for showing upload modal
  useEffect(() => {
    const shouldShowUpload = searchParams.get('action') === 'upload'
    setShowUpload(shouldShowUpload)
  }, [searchParams])

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

  const closeUpload = () => {
    console.log('closeUpload called, current URL:', window.location.href)
    console.log('current searchParams:', searchParams.toString())
    setShowUpload(false)
    // Clean URL parameters using setSearchParams (recommended way per Context7)
    if (searchParams.get('action')) {
      console.log('Cleaning action parameter from URL')
      const newParams = new URLSearchParams(searchParams)
      newParams.delete('action')
      console.log('New params will be:', newParams.toString())
      setSearchParams(newParams, { replace: true })
    }
  }

  const handleUploadComplete = () => {
    // Refresh the artifacts list to show the new upload and then close the modal
    loadArtifacts(filters).then(() => {
      closeUpload()
    })
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

  const handleBulkEditSuccess = () => {
    setShowBulkEdit(false)
    clearSelection()
    loadArtifacts(filters)
  }

  const getSelectedArtifactsData = () => {
    return artifacts.filter(artifact => selectedArtifacts.includes(artifact.id))
  }

  return (
    <>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-full mb-3">
              <FolderOpen className="h-4 w-4 text-purple-600" />
              <span className="text-sm font-medium text-purple-700">Portfolio Management</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight mb-2">
              Professional
              <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent"> Portfolio</span>
            </h1>
            <p className="text-gray-600 max-w-2xl">
              Manage your professional projects and documents with AI-powered insights.
            </p>
          </div>
          <Button
            onClick={() => setShowUpload(true)}
            className="group bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
          >
            <div className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              <span>Upload Artifact</span>
              <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform duration-200" />
            </div>
          </Button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-300">
        <div className="p-4 sm:p-6">
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
            {/* Search */}
            <div className="flex-1 max-w-lg">
              <label className="block text-sm font-bold text-gray-800 mb-2">Search Artifacts</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search by title, description, or technology..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3 border-2 border-gray-200 rounded-xl text-sm font-medium placeholder-gray-400 focus:ring-4 focus:ring-purple-100 focus:border-purple-500 transition-all duration-200"
                />
              </div>
            </div>

            <div className="flex items-end gap-3">
              {/* Status Filter */}
              <div>
                <label className="block text-sm font-bold text-gray-800 mb-2">Status</label>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value as 'all' | 'active' | 'archived')}
                  className="px-4 py-3 border-2 border-gray-200 rounded-xl text-sm font-semibold focus:ring-4 focus:ring-purple-100 focus:border-purple-500 bg-white min-w-[120px] transition-all duration-200"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="archived">Archived</option>
                </select>
              </div>

              {/* View Mode Toggle */}
              <div>
                <label className="block text-sm font-bold text-gray-800 mb-2">View</label>
                <div className="inline-flex rounded-xl border-2 border-gray-200 bg-gray-50 p-1">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={cn(
                      'inline-flex items-center justify-center px-3 py-2 text-sm font-bold rounded-lg transition-all duration-200',
                      viewMode === 'grid'
                        ? 'bg-white text-purple-700 shadow-md'
                        : 'text-gray-600 hover:text-gray-900'
                    )}
                  >
                    <Grid className="h-4 w-4" />
                    <span className="ml-1.5 hidden sm:inline">Grid</span>
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={cn(
                      'inline-flex items-center justify-center px-3 py-2 text-sm font-bold rounded-lg transition-all duration-200',
                      viewMode === 'list'
                        ? 'bg-white text-purple-700 shadow-md'
                        : 'text-gray-600 hover:text-gray-900'
                    )}
                  >
                    <List className="h-4 w-4" />
                    <span className="ml-1.5 hidden sm:inline">List</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Selection Actions */}
        {selectedArtifacts.length > 0 && (
          <div className="border-t border-gray-200 bg-purple-50 p-4 rounded-b-xl">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 bg-purple-600 text-white text-xs font-semibold rounded-full">
                  {selectedArtifacts.length}
                </div>
                <span className="text-sm font-medium text-purple-900">
                  {selectedArtifacts.length} artifact{selectedArtifacts.length !== 1 ? 's' : ''} selected
                </span>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={clearSelection}
                  className="text-sm font-medium text-purple-600 hover:text-purple-800 transition-colors"
                >
                  Clear selection
                </button>
                <div className="flex gap-2">
                  <Button
                    onClick={() => setShowBulkEdit(true)}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    <Settings className="h-4 w-4" />
                    Bulk Edit
                  </Button>
                  <Button
                    onClick={handleBulkDelete}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete Selected
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Artifacts Grid/List */}
      <div className="mt-6">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-sm text-gray-600">Loading artifacts...</p>
          </div>
        ) : filteredArtifacts.length > 0 ? (
          viewMode === 'grid' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredArtifacts.map((artifact) => (
                <ArtifactCard
                  key={artifact.id}
                  artifact={artifact}
                  isSelected={selectedArtifacts.includes(artifact.id)}
                  onToggleSelect={() => toggleSelection(artifact.id)}
                  onDelete={() => handleDelete(artifact.id)}
                  onEdit={() => navigate(`/artifacts/${artifact.id}`)}
                />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredArtifacts.map((artifact) => (
                <ArtifactListItem
                  key={artifact.id}
                  artifact={artifact}
                  isSelected={selectedArtifacts.includes(artifact.id)}
                  onToggleSelect={() => toggleSelection(artifact.id)}
                  onDelete={() => handleDelete(artifact.id)}
                  onEdit={() => navigate(`/artifacts/${artifact.id}`)}
                />
              ))}
            </div>
          )
        ) : (
          <div className="text-center py-16">
            <div className="w-16 h-16 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
              <FileText className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No artifacts found</h3>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              {searchQuery || selectedStatus !== 'all'
                ? 'Try adjusting your search or filters to find what you\'re looking for.'
                : 'Get started by uploading your first project or document to build your portfolio.'}
            </p>
            {!searchQuery && selectedStatus === 'all' && (
              <Button
                onClick={() => setShowUpload(true)}
                className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
              >
                <Plus className="h-5 w-5" />
                Upload First Artifact
              </Button>
            )}
          </div>
        )}
      </div>
      </div>

      {/* Bulk Edit Dialog */}
      <BulkEditDialog
        selectedArtifacts={getSelectedArtifactsData()}
        isOpen={showBulkEdit}
        onClose={() => setShowBulkEdit(false)}
        onSuccess={handleBulkEditSuccess}
      />

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onClick={closeUpload}></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              <ArtifactUpload
                onUploadComplete={handleUploadComplete}
                onClose={closeUpload}
              />
            </div>
          </div>
        </div>
      )}
    </>
  )
}

interface ArtifactCardProps {
  artifact: Artifact
  isSelected: boolean
  onToggleSelect: () => void
  onDelete: () => void
  onEdit: () => void
}

function ArtifactCard({ artifact, isSelected, onToggleSelect, onEdit }: ArtifactCardProps) {
  return (
    <div
      className={cn(
        'group relative bg-white rounded-xl border transition-all duration-200 cursor-pointer overflow-hidden',
        'hover:shadow-lg hover:-translate-y-0.5',
        isSelected
          ? 'border-purple-500 shadow-lg ring-4 ring-purple-500/10'
          : 'border-gray-200 shadow-sm hover:border-gray-300'
      )}
      onClick={onToggleSelect}
    >
      {/* Selection overlay */}
      {isSelected && (
        <div className="absolute inset-0 bg-purple-50/50 pointer-events-none" />
      )}

      <div className="p-6">
        {/* Header with title and actions */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <div className={cn(
                'flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center transition-colors',
                isSelected
                  ? 'bg-purple-600 text-white'
                  : 'bg-purple-100 text-purple-600 group-hover:bg-purple-600 group-hover:text-white'
              )}>
                <FileText className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900 text-lg leading-6 truncate">
                  {artifact.title}
                </h3>
                <p className="text-sm text-gray-500 mt-0.5">
                  {formatDateRange(artifact.start_date, artifact.end_date)}
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 ml-4">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onEdit()
              }}
              className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all opacity-0 group-hover:opacity-100"
              title="Edit artifact"
            >
              <Edit className="h-4 w-4" />
            </button>
            <div className={cn(
              'w-5 h-5 rounded border-2 flex items-center justify-center transition-all',
              isSelected
                ? 'bg-purple-600 border-purple-600 text-white'
                : 'border-gray-300 hover:border-purple-500'
            )}>
              {isSelected && (
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </div>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 leading-relaxed mb-5 line-clamp-2">
          {artifact.description}
        </p>

        {/* Technologies */}
        {artifact.technologies.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {artifact.technologies.slice(0, 4).map((tech) => (
              <span
                key={tech}
                className="inline-flex items-center px-2.5 py-1 bg-gray-100 text-xs font-medium text-gray-700 rounded-full"
              >
                {tech}
              </span>
            ))}
            {artifact.technologies.length > 4 && (
              <span className="inline-flex items-center px-2.5 py-1 bg-gray-100 text-xs font-medium text-gray-500 rounded-full">
                +{artifact.technologies.length - 4} more
              </span>
            )}
          </div>
        )}

        {/* Footer with metadata */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          {/* Evidence Links */}
          <div className="flex items-center gap-2">
            {artifact.evidence_links.slice(0, 4).map((link, index) => {
              const Icon = evidenceTypeIcons[link.link_type] || ExternalLink
              return (
                <div
                  key={index}
                  className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                  title={link.description}
                >
                  <Icon className="h-3.5 w-3.5 text-gray-600" />
                </div>
              )
            })}
            {artifact.evidence_links.length > 4 && (
              <span className="text-xs text-gray-500 font-medium ml-1">
                +{artifact.evidence_links.length - 4}
              </span>
            )}
          </div>

          {/* Collaborators */}
          {artifact.collaborators.length > 0 && (
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <Users className="h-3.5 w-3.5" />
              <span className="font-medium">
                {artifact.collaborators.length} collaborator{artifact.collaborators.length !== 1 ? 's' : ''}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface ArtifactListItemProps {
  artifact: Artifact
  isSelected: boolean
  onToggleSelect: () => void
  onDelete: () => void
  onEdit: () => void
}

function ArtifactListItem({ artifact, isSelected, onToggleSelect, onDelete, onEdit }: ArtifactListItemProps) {
  return (
    <div
      className={cn(
        'group bg-white rounded-xl border transition-all duration-200 cursor-pointer overflow-hidden',
        'hover:shadow-md hover:border-gray-300',
        isSelected
          ? 'border-purple-500 shadow-md ring-4 ring-purple-500/10'
          : 'border-gray-200 shadow-sm'
      )}
      onClick={onToggleSelect}
    >
      {/* Selection overlay */}
      {isSelected && (
        <div className="absolute inset-0 bg-purple-50/30 pointer-events-none" />
      )}

      <div className="p-6">
        <div className="flex items-start gap-4">
          {/* Selection checkbox */}
          <div className="flex items-center pt-1">
            <div className={cn(
              'w-5 h-5 rounded border-2 flex items-center justify-center transition-all',
              isSelected
                ? 'bg-purple-600 border-purple-600 text-white'
                : 'border-gray-300 hover:border-purple-500'
            )}>
              {isSelected && (
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </div>
          </div>

          {/* Icon */}
          <div className={cn(
            'flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center transition-colors',
            isSelected
              ? 'bg-purple-600 text-white'
              : 'bg-purple-100 text-purple-600 group-hover:bg-purple-600 group-hover:text-white'
          )}>
            <FileText className="h-6 w-6" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900 text-base leading-6 truncate">
                  {artifact.title}
                </h3>
                <p className="text-sm text-gray-500 mt-1">
                  {formatDateRange(artifact.start_date, artifact.end_date)}
                </p>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1 ml-4">
                <button
                  className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                  title="Edit artifact"
                  onClick={(e) => {
                    e.stopPropagation()
                    onEdit()
                  }}
                >
                  <Edit className="h-4 w-4" />
                </button>
                <button
                  className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all opacity-0 group-hover:opacity-100"
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

            {/* Description */}
            <p className="text-sm text-gray-600 leading-relaxed mb-4 line-clamp-2">
              {artifact.description}
            </p>

            {/* Footer */}
            <div className="flex items-center justify-between">
              {/* Technologies */}
              <div className="flex flex-wrap gap-1.5">
                {artifact.technologies.slice(0, 5).map((tech) => (
                  <span
                    key={tech}
                    className="inline-flex items-center px-2.5 py-1 bg-gray-100 text-xs font-medium text-gray-700 rounded-full"
                  >
                    {tech}
                  </span>
                ))}
                {artifact.technologies.length > 5 && (
                  <span className="inline-flex items-center px-2.5 py-1 bg-gray-100 text-xs font-medium text-gray-500 rounded-full">
                    +{artifact.technologies.length - 5}
                  </span>
                )}
              </div>

              {/* Metadata */}
              <div className="flex items-center gap-4 text-sm text-gray-500">
                {artifact.evidence_links.length > 0 && (
                  <span className="flex items-center gap-1.5">
                    <ExternalLink className="h-3.5 w-3.5" />
                    <span className="font-medium">
                      {artifact.evidence_links.length} link{artifact.evidence_links.length !== 1 ? 's' : ''}
                    </span>
                  </span>
                )}
                {artifact.collaborators.length > 0 && (
                  <span className="flex items-center gap-1.5">
                    <Users className="h-3.5 w-3.5" />
                    <span className="font-medium">
                      {artifact.collaborators.length} collaborator{artifact.collaborators.length !== 1 ? 's' : ''}
                    </span>
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}