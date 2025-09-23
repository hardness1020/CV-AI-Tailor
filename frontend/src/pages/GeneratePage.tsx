import { useState } from 'react'
import { Plus, History, Zap, FileText, Download } from 'lucide-react'
import CVGenerationFlow from '@/components/CVGenerationFlow'
import ExportDialog from '@/components/ExportDialog'
import { useGeneration } from '@/hooks/useGeneration'
import { formatDate } from '@/utils/formatters'
import type { GeneratedDocument } from '@/types'

export default function GeneratePage() {
  const [showGenerationFlow, setShowGenerationFlow] = useState(false)
  const { completedDocuments, activeGenerations } = useGeneration()

  const handleGenerationComplete = () => {
    setShowGenerationFlow(false)
  }

  if (showGenerationFlow) {
    return (
      <CVGenerationFlow
        onComplete={handleGenerationComplete}
        onClose={() => setShowGenerationFlow(false)}
      />
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Generate CV</h1>
          <p className="mt-2 text-gray-600">
            Create targeted CVs by analyzing job descriptions and matching them with your artifacts.
          </p>
        </div>
        <button
          onClick={() => setShowGenerationFlow(true)}
          className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <Plus className="h-5 w-5" />
          <span>New Generation</span>
        </button>
      </div>

      {/* Active Generations */}
      {activeGenerations.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Generations</h2>
          <div className="space-y-4">
            {activeGenerations.map((generation) => (
              <div key={generation.id} className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Zap className="h-5 w-5 text-blue-600" />
                    <span className="font-medium text-blue-900">
                      {generation.type === 'cv' ? 'CV Generation' : 'Cover Letter Generation'}
                    </span>
                  </div>
                  <span className="text-sm text-blue-700">
                    {generation.progressPercentage}% complete
                  </span>
                </div>
                <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${generation.progressPercentage}%` }}
                  />
                </div>
                <p className="text-sm text-blue-700">
                  Started {formatDate(generation.createdAt)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Generations */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">Recent Generations</h2>
          {completedDocuments.length > 5 && (
            <button className="text-sm text-blue-600 hover:text-blue-500 flex items-center space-x-1">
              <History className="h-4 w-4" />
              <span>View All</span>
            </button>
          )}
        </div>

        {completedDocuments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {completedDocuments.slice(0, 6).map((document) => (
              <GenerationCard key={document.id} document={document} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Zap className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No generations yet</h3>
            <p className="text-gray-500 mb-6">
              Create your first CV by analyzing a job description and matching it with your artifacts.
            </p>
            <button
              onClick={() => setShowGenerationFlow(true)}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="h-5 w-5" />
              <span>Generate First CV</span>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

interface GenerationCardProps {
  document: GeneratedDocument
}

function GenerationCard({ document }: GenerationCardProps) {
  const [showExportDialog, setShowExportDialog] = useState(false)

  return (
    <>
      <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-green-100 rounded-lg">
              <FileText className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">
                {document.type === 'cv' ? 'CV Generation' : 'Cover Letter'}
              </h3>
              <p className="text-sm text-gray-500">
                {formatDate(document.createdAt)}
              </p>
            </div>
          </div>
          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
            Completed
          </span>
        </div>

        {document.metadata && (
          <div className="space-y-2 mb-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Skill Match:</span>
              <span className="font-medium text-gray-900">
                {document.metadata.skillMatchScore}%
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Artifacts Used:</span>
              <span className="font-medium text-gray-900">
                {document.metadata.artifactsUsed.length}
              </span>
            </div>
          </div>
        )}

        <div className="flex space-x-2">
          <button
            onClick={() => setShowExportDialog(true)}
            className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-center space-x-1"
          >
            <Download className="h-4 w-4" />
            <span>Export</span>
          </button>
          <button className="px-3 py-2 border border-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500">
            View
          </button>
        </div>
      </div>

      {showExportDialog && (
        <ExportDialog
          generationId={document.id}
          isOpen={showExportDialog}
          onClose={() => setShowExportDialog(false)}
          onExportComplete={() => setShowExportDialog(false)}
        />
      )}
    </>
  )
}