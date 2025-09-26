import { useState, useEffect } from 'react'
import {
  BarChart3,
  TrendingUp,
  FileText,
  Download,
  Clock,
  Target,
  Users,
  Award,
  Zap,
  Calendar,
  RefreshCw
} from 'lucide-react'
import toast from 'react-hot-toast'
import { apiClient } from '@/services/apiClient'
import type { GenerationAnalytics, ExportAnalytics } from '@/types'
import { cn } from '@/utils/cn'

export default function AnalyticsPage() {
  const [generationAnalytics, setGenerationAnalytics] = useState<GenerationAnalytics | null>(null)
  const [exportAnalytics, setExportAnalytics] = useState<ExportAnalytics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [activeTab, setActiveTab] = useState<'generation' | 'export'>('generation')

  const loadAnalytics = async () => {
    try {
      const [genAnalytics, expAnalytics] = await Promise.all([
        apiClient.getGenerationAnalytics(),
        apiClient.getExportAnalytics()
      ])
      setGenerationAnalytics(genAnalytics)
      setExportAnalytics(expAnalytics)
    } catch (error) {
      console.error('Failed to load analytics:', error)
      toast.error('Failed to load analytics data')
    }
  }

  const refreshData = async () => {
    setIsRefreshing(true)
    await loadAnalytics()
    setIsRefreshing(false)
    toast.success('Analytics refreshed')
  }

  useEffect(() => {
    loadAnalytics().finally(() => setIsLoading(false))
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="mt-2 text-gray-600">
            Track your CV generation performance, usage patterns, and success metrics.
          </p>
        </div>
        <button
          onClick={refreshData}
          disabled={isRefreshing}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <RefreshCw className={cn('h-5 w-5', isRefreshing && 'animate-spin')} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { id: 'generation', name: 'CV Generation', icon: FileText },
              { id: 'export', name: 'Document Export', icon: Download },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={cn(
                  'flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors',
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
              >
                <tab.icon className="h-4 w-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Generation Analytics Tab */}
          {activeTab === 'generation' && generationAnalytics && (
            <div className="space-y-8">
              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-100">Total Generations</p>
                      <p className="text-3xl font-bold">{generationAnalytics.total_generations}</p>
                    </div>
                    <FileText className="h-8 w-8 text-blue-200" />
                  </div>
                </div>

                <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-100">Success Rate</p>
                      <p className="text-3xl font-bold">{Math.round(generationAnalytics.success_rate * 100)}%</p>
                    </div>
                    <Target className="h-8 w-8 text-green-200" />
                  </div>
                </div>

                <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-purple-100">Avg Generation Time</p>
                      <p className="text-3xl font-bold">{Math.round(generationAnalytics.avg_generation_time_seconds)}s</p>
                    </div>
                    <Clock className="h-8 w-8 text-purple-200" />
                  </div>
                </div>

                <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-orange-100">Cover Letters</p>
                      <p className="text-3xl font-bold">{generationAnalytics.generations_by_type.cover_letter}</p>
                    </div>
                    <Zap className="h-8 w-8 text-orange-200" />
                  </div>
                </div>
              </div>

              {/* Generation Types Breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Generation Types</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-4 h-4 bg-blue-500 rounded"></div>
                        <span className="text-gray-700">CVs</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">{generationAnalytics.generations_by_type.cv}</span>
                        <span className="text-sm text-gray-500">
                          ({Math.round((generationAnalytics.generations_by_type.cv / generationAnalytics.total_generations) * 100)}%)
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-4 h-4 bg-orange-500 rounded"></div>
                        <span className="text-gray-700">Cover Letters</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">{generationAnalytics.generations_by_type.cover_letter}</span>
                        <span className="text-sm text-gray-500">
                          ({Math.round((generationAnalytics.generations_by_type.cover_letter / generationAnalytics.total_generations) * 100)}%)
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Average Generation Time</span>
                      <span className="font-medium text-gray-900">{generationAnalytics.avg_generation_time_seconds.toFixed(1)}s</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Success Rate</span>
                      <span className="font-medium text-gray-900">{(generationAnalytics.success_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Total Generations</span>
                      <span className="font-medium text-gray-900">{generationAnalytics.total_generations}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Most Used Templates */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Most Used Templates</h3>
                <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Template ID</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usage Count</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Percentage</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {generationAnalytics.most_used_templates.map((template, index) => (
                          <tr key={template.template_id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              Template {template.template_id}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{template.usage_count}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {Math.round((template.usage_count / generationAnalytics.total_generations) * 100)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Most Used Artifacts */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Most Referenced Artifacts</h3>
                <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Artifact ID</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usage Count</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Percentage</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {generationAnalytics.artifacts_usage.map((artifact) => (
                          <tr key={artifact.artifact_id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              Artifact {artifact.artifact_id}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{artifact.usage_count}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {Math.round((artifact.usage_count / generationAnalytics.total_generations) * 100)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Export Analytics Tab */}
          {activeTab === 'export' && exportAnalytics && (
            <div className="space-y-8">
              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-100">Total Exports</p>
                      <p className="text-3xl font-bold">{exportAnalytics.total_exports}</p>
                    </div>
                    <Download className="h-8 w-8 text-blue-200" />
                  </div>
                </div>

                <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-100">Success Rate</p>
                      <p className="text-3xl font-bold">{Math.round(exportAnalytics.success_rate * 100)}%</p>
                    </div>
                    <Target className="h-8 w-8 text-green-200" />
                  </div>
                </div>

                <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-purple-100">Avg Export Time</p>
                      <p className="text-3xl font-bold">{Math.round(exportAnalytics.avg_export_time_seconds)}s</p>
                    </div>
                    <Clock className="h-8 w-8 text-purple-200" />
                  </div>
                </div>

                <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-orange-100">Avg File Size</p>
                      <p className="text-3xl font-bold">{exportAnalytics.file_size_stats.avg_size_mb.toFixed(1)}MB</p>
                    </div>
                    <BarChart3 className="h-8 w-8 text-orange-200" />
                  </div>
                </div>
              </div>

              {/* Export Formats Breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Export Formats</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-4 h-4 bg-red-500 rounded"></div>
                        <span className="text-gray-700">PDF</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">{exportAnalytics.exports_by_format.pdf}</span>
                        <span className="text-sm text-gray-500">
                          ({Math.round((exportAnalytics.exports_by_format.pdf / exportAnalytics.total_exports) * 100)}%)
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-4 h-4 bg-blue-500 rounded"></div>
                        <span className="text-gray-700">DOCX</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">{exportAnalytics.exports_by_format.docx}</span>
                        <span className="text-sm text-gray-500">
                          ({Math.round((exportAnalytics.exports_by_format.docx / exportAnalytics.total_exports) * 100)}%)
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">File Size Statistics</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Average Size</span>
                      <span className="font-medium text-gray-900">{exportAnalytics.file_size_stats.avg_size_mb.toFixed(1)} MB</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Minimum Size</span>
                      <span className="font-medium text-gray-900">{exportAnalytics.file_size_stats.min_size_mb.toFixed(1)} MB</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Maximum Size</span>
                      <span className="font-medium text-gray-900">{exportAnalytics.file_size_stats.max_size_mb.toFixed(1)} MB</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Most Used Templates */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Most Used Export Templates</h3>
                <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Template ID</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usage Count</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Percentage</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {exportAnalytics.most_used_templates.map((template) => (
                          <tr key={template.template_id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              Template {template.template_id}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{template.usage_count}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {Math.round((template.usage_count / exportAnalytics.total_exports) * 100)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}