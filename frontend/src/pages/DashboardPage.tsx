import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FolderOpen,
  Zap,
  Download,
  TrendingUp,
  FileText,
  Clock,
  Award
} from 'lucide-react'
import { useArtifactStore } from '@/stores/artifactStore'
import { useGenerationStore } from '@/stores/generationStore'
import { apiClient } from '@/services/apiClient'

export default function DashboardPage() {
  const { artifacts, setArtifacts, setLoading } = useArtifactStore()
  const { completedDocuments } = useGenerationStore()
  const [stats, setStats] = useState({
    totalArtifacts: 0,
    totalGenerations: 0,
    recentActivity: 0
  })

  useEffect(() => {
    const loadDashboardData = async () => {
      setLoading(true)
      try {
        const artifactsResponse = await apiClient.getArtifacts()
        setArtifacts(artifactsResponse.results)

        setStats({
          totalArtifacts: artifactsResponse.count,
          totalGenerations: completedDocuments.length,
          recentActivity: artifactsResponse.results.filter(
            a => new Date(a.createdAt) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
          ).length
        })
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
  }, [setArtifacts, setLoading, completedDocuments.length])

  const recentArtifacts = artifacts.slice(0, 3)
  const recentGenerations = completedDocuments.slice(0, 3)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome back! Here's an overview of your CV generation journey.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Artifacts</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalArtifacts}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <FolderOpen className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-4">
            <Link
              to="/artifacts"
              className="text-sm text-blue-600 hover:text-blue-500 font-medium"
            >
              Manage artifacts →
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">CVs Generated</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalGenerations}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <Zap className="h-6 w-6 text-green-600" />
            </div>
          </div>
          <div className="mt-4">
            <Link
              to="/generate"
              className="text-sm text-green-600 hover:text-green-500 font-medium"
            >
              Generate new CV →
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Recent Activity</p>
              <p className="text-3xl font-bold text-gray-900">{stats.recentActivity}</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <TrendingUp className="h-6 w-6 text-purple-600" />
            </div>
          </div>
          <p className="mt-4 text-sm text-gray-500">New artifacts this week</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/artifacts?action=upload"
            className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
          >
            <div className="p-2 bg-blue-100 rounded-md">
              <FolderOpen className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900">Upload Artifact</p>
              <p className="text-sm text-gray-500">Add a new project or document</p>
            </div>
          </Link>

          <Link
            to="/generate"
            className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-colors"
          >
            <div className="p-2 bg-green-100 rounded-md">
              <Zap className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900">Generate CV</p>
              <p className="text-sm text-gray-500">Create a targeted resume</p>
            </div>
          </Link>

          <button
            disabled
            className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg opacity-50 cursor-not-allowed"
          >
            <div className="p-2 bg-gray-100 rounded-md">
              <Download className="h-5 w-5 text-gray-400" />
            </div>
            <div>
              <p className="font-medium text-gray-900">Export Documents</p>
              <p className="text-sm text-gray-500">Download as PDF or Word</p>
            </div>
          </button>
        </div>
      </div>

      {/* Recent Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Artifacts */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Artifacts</h2>
            <Link to="/artifacts" className="text-sm text-blue-600 hover:text-blue-500">
              View all
            </Link>
          </div>

          {recentArtifacts.length > 0 ? (
            <div className="space-y-3">
              {recentArtifacts.map((artifact) => (
                <div key={artifact.id} className="flex items-start space-x-3 p-3 border border-gray-100 rounded-lg">
                  <div className="p-2 bg-blue-100 rounded-md">
                    <FileText className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">{artifact.title}</p>
                    <p className="text-sm text-gray-500 truncate">{artifact.description}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Clock className="h-3 w-3 text-gray-400" />
                      <span className="text-xs text-gray-500">
                        {new Date(artifact.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <FolderOpen className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No artifacts yet</p>
              <Link
                to="/artifacts"
                className="text-sm text-blue-600 hover:text-blue-500 font-medium"
              >
                Upload your first artifact
              </Link>
            </div>
          )}
        </div>

        {/* Recent Generations */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent CV Generations</h2>
            <Link to="/generate" className="text-sm text-green-600 hover:text-green-500">
              Generate new
            </Link>
          </div>

          {recentGenerations.length > 0 ? (
            <div className="space-y-3">
              {recentGenerations.map((generation) => (
                <div key={generation.id} className="flex items-start space-x-3 p-3 border border-gray-100 rounded-lg">
                  <div className="p-2 bg-green-100 rounded-md">
                    <Award className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900">CV Generation</p>
                    <p className="text-sm text-gray-500">
                      Status: {generation.status === 'completed' ? 'Completed' : 'Processing'}
                    </p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Clock className="h-3 w-3 text-gray-400" />
                      <span className="text-xs text-gray-500">
                        {new Date(generation.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <Zap className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No CV generations yet</p>
              <Link
                to="/generate"
                className="text-sm text-green-600 hover:text-green-500 font-medium"
              >
                Generate your first CV
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}