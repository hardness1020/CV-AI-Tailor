import { useState } from 'react'
import { Plus, History, Zap, FileText, Download, ArrowRight, Sparkles } from 'lucide-react'
import CVGenerationFlow from '@/components/CVGenerationFlow'
import ExportDialog from '@/components/ExportDialog'
import { Button } from '@/components/ui/Button'
import { useGeneration } from '@/hooks/useGeneration'
import { formatDate } from '@/utils/formatters'
import { cn } from '@/utils/cn'
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-full mb-3">
              <Sparkles className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-700">AI-Powered Generation</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight mb-2">
              Create Perfect
              <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent"> CVs</span>
            </h1>
            <p className="text-gray-600 max-w-2xl">
              Transform job descriptions into tailored resumes using advanced AI and professional artifacts.
            </p>
          </div>

          <Button
            onClick={() => setShowGenerationFlow(true)}
            className="group bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
          >
            <div className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              <span>Start Generation</span>
              <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform duration-200" />
            </div>
          </Button>
        </div>
      </div>

      {/* Active Generations */}
      {activeGenerations.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-300 p-4 sm:p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-lg flex items-center justify-center">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Active Generations</h2>
          </div>
          <div className="space-y-4">
            {activeGenerations.map((generation) => (
              <div key={generation.id} className="relative overflow-hidden border border-blue-200 rounded-2xl p-4 bg-gradient-to-br from-blue-50 via-indigo-50/50 to-blue-50 hover:shadow-lg transition-all duration-300">
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-400/10 to-indigo-400/10 rounded-full -translate-y-16 translate-x-16" />
                <div className="relative">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg">
                        <Zap className="h-6 w-6 text-white" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-bold text-blue-900 text-lg mb-1">
                          {generation.type === 'cv' ? 'CV Generation' : 'Cover Letter Generation'}
                        </h3>
                        <p className="text-sm text-blue-700 flex items-center gap-2">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                          Started {formatDate(generation.createdAt)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/80 rounded-xl shadow-sm border border-blue-200">
                        <span className="text-2xl font-bold text-blue-700">
                          {generation.progressPercentage}%
                        </span>
                        <span className="text-sm text-blue-600 font-medium">complete</span>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="w-full bg-blue-200/60 rounded-full h-4 shadow-inner overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full rounded-full transition-all duration-700 ease-out shadow-sm relative"
                        style={{ width: `${generation.progressPercentage}%` }}
                      >
                        <div className="absolute inset-0 bg-white/20 rounded-full" />
                        <div className="absolute right-1 top-1/2 transform -translate-y-1/2 w-2 h-2 bg-white rounded-full shadow-sm" />
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-blue-600 font-medium">
                      <span>Processing artifacts...</span>
                      <span>ETA: ~{Math.max(1, Math.ceil((100 - generation.progressPercentage) / 20))} min</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Generations */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-300 p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <History className="h-4 w-4 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Recent Generations</h2>
          </div>
          {completedDocuments.length > 6 && (
            <button className="group inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-xl transition-all duration-200">
              <History className="h-4 w-4" />
              <span>View All ({completedDocuments.length})</span>
              <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform duration-200" />
            </button>
          )}
        </div>

        {completedDocuments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {completedDocuments.slice(0, 6).map((document) => (
              <GenerationCard key={document.id} document={document} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 sm:py-16">
            <div className="relative mb-6">
              <div className="w-20 h-20 mx-auto bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl flex items-center justify-center shadow-lg">
                <Zap className="h-10 w-10 text-gray-400" />
              </div>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">Ready to create your first CV?</h3>
            <p className="text-gray-600 mb-6 max-w-lg mx-auto leading-relaxed">
              Our AI will analyze job descriptions and intelligently match them with your professional artifacts to create targeted, ATS-optimized resumes that stand out.
            </p>
            <Button
              onClick={() => setShowGenerationFlow(true)}
              className="group relative overflow-hidden bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold px-8 py-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
            >
              <div className="flex items-center gap-3">
                <Plus className="h-5 w-5" />
                <span>Generate Your First CV</span>
                <ArrowRight className="h-5 w-5 transform group-hover:translate-x-1 transition-transform duration-200" />
              </div>
            </Button>
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
  const [isHovered, setIsHovered] = useState(false)

  return (
    <>
      <div
        className="group relative overflow-hidden border border-gray-200 rounded-2xl p-4 hover:shadow-xl hover:border-gray-300 bg-white transition-all duration-300 transform hover:scale-102 cursor-pointer"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Background gradient */}
        <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-green-400/5 to-blue-400/5 rounded-full -translate-y-12 translate-x-12 transition-all duration-500 group-hover:scale-150" />

        <div className="relative">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start gap-4">
              <div className="relative">
                <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                  <FileText className="h-7 w-7 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-5 h-5 bg-white rounded-full flex items-center justify-center shadow-md">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-gray-900 text-lg mb-1 truncate">
                  {document.type === 'cv' ? 'CV Generation' : 'Cover Letter'}
                </h3>
                <p className="text-sm text-gray-500 flex items-center gap-2">
                  <span>{formatDate(document.createdAt)}</span>
                </p>
              </div>
            </div>
            <div className="flex flex-col items-end gap-2">
              <span className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 text-xs font-bold rounded-full border border-green-200">
                ✓ Completed
              </span>
            </div>
          </div>

          {document.metadata && (
            <div className="space-y-4 mb-4 p-4 bg-gradient-to-br from-gray-50 to-gray-100/50 rounded-xl border border-gray-100">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-700">Match Score</span>
                  <div className="flex items-center gap-3">
                    <div className="w-20 h-3 bg-gray-200 rounded-full overflow-hidden shadow-inner">
                      <div
                        className={cn(
                          'h-full rounded-full transition-all duration-500 relative',
                          document.metadata.skillMatchScore >= 80 ? 'bg-gradient-to-r from-green-500 to-emerald-500' :
                          document.metadata.skillMatchScore >= 60 ? 'bg-gradient-to-r from-yellow-500 to-amber-500' : 'bg-gradient-to-r from-red-500 to-rose-500'
                        )}
                        style={{ width: `${document.metadata.skillMatchScore}%` }}
                      >
                        <div className="absolute inset-0 bg-white/20 rounded-full" />
                      </div>
                    </div>
                    <span className="text-sm font-bold text-gray-900 min-w-[40px] text-right">
                      {document.metadata.skillMatchScore}%
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-700">Artifacts</span>
                  <span className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 text-xs font-bold rounded-full border border-blue-200">
                    {document.metadata.artifactsUsed.length} items
                  </span>
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <Button
              onClick={() => setShowExportDialog(true)}
              className="group/btn flex-1 relative overflow-hidden bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-3 px-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
            >
              <div className="flex items-center justify-center gap-2">
                <Download className="h-4 w-4 transform group-hover/btn:-translate-y-0.5 transition-transform duration-200" />
                <span>Export</span>
              </div>
            </Button>
            <Button
              className="group/btn px-4 py-3 border-2 border-gray-200 hover:border-gray-300 text-gray-700 hover:text-gray-900 font-semibold rounded-xl hover:bg-gray-50 transition-all duration-300 transform hover:scale-105"
            >
              <span>Preview</span>
            </Button>
          </div>
        </div>

        {/* Hover effect overlay */}
        <div className={cn(
          "absolute inset-0 bg-gradient-to-br from-blue-500/5 to-indigo-500/5 rounded-2xl transition-opacity duration-300",
          isHovered ? "opacity-100" : "opacity-0"
        )} />
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