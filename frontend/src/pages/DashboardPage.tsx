import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  FolderOpen,
  Zap,
  Download,
  TrendingUp,
  FileText,
  Clock,
  Award,
  LogIn,
  User,
  LogOut
} from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { useArtifactStore } from '@/stores/artifactStore'
import { useGenerationStore } from '@/stores/generationStore'
import { apiClient } from '@/services/apiClient'
import Layout from '@/components/Layout'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { isAuthenticated, user, clearAuth } = useAuthStore()
  const { artifacts, setArtifacts, setLoading } = useArtifactStore()
  const { completedDocuments } = useGenerationStore()
  const [stats, setStats] = useState({
    totalArtifacts: 0,
    totalGenerations: 0,
    recentActivity: 0
  })

  const handleLogout = async () => {
    try {
      await apiClient.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuth()
    }
  }

  const handleProtectedAction = (path: string) => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: { pathname: path } } })
    } else {
      navigate(path)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
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
    }
  }, [isAuthenticated, setArtifacts, setLoading, completedDocuments.length])

  const recentArtifacts = isAuthenticated ? artifacts.slice(0, 3) : []
  const recentGenerations = isAuthenticated ? completedDocuments.slice(0, 3) : []

  // Dashboard content component for authenticated users
  const DashboardContent = () => (
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
              <p className="text-sm text-gray-500">Coming soon</p>
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

  // Return conditional layout based on authentication
  if (isAuthenticated) {
    return (
      <Layout>
        <DashboardContent />
      </Layout>
    )
  }

  // Public dashboard for unauthenticated users
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2">
              <FileText className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">CV Tailor</span>
            </Link>

            {/* Navigation Links & Auth */}
            <div className="flex items-center space-x-4">
              {!isAuthenticated ? (
                <>
                  <Link
                    to="/register"
                    className="text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    Sign Up
                  </Link>
                  <Link
                    to="/login"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                  >
                    <LogIn className="h-4 w-4 mr-2" />
                    Sign In
                  </Link>
                </>
              ) : (
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => handleProtectedAction('/profile')}
                    className="flex items-center space-x-2 text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                      <span className="text-sm font-medium text-blue-600">
                        {user?.firstName?.[0]}{user?.lastName?.[0]}
                      </span>
                    </div>
                    <span className="text-sm font-medium">{user?.firstName} {user?.lastName}</span>
                  </button>
                  <button
                    onClick={handleLogout}
                    className="text-gray-400 hover:text-gray-500 transition-colors"
                    title="Logout"
                  >
                    <LogOut className="h-5 w-5" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {isAuthenticated ? 'Dashboard' : 'Welcome to CV Tailor'}
            </h1>
            <p className="mt-2 text-gray-600">
              {isAuthenticated
                ? "Welcome back! Here's an overview of your CV generation journey."
                : 'Generate targeted CVs with evidence from your professional artifacts. Sign in to get started.'
              }
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Artifacts</p>
                  <p className="text-3xl font-bold text-gray-900">—</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-full">
                  <FolderOpen className="h-6 w-6 text-blue-600" />
                </div>
              </div>
              <div className="mt-4">
                <button
                  onClick={() => handleProtectedAction('/artifacts')}
                  className="text-sm text-blue-600 hover:text-blue-500 font-medium"
                >
                  Sign in to view →
                </button>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">CVs Generated</p>
                  <p className="text-3xl font-bold text-gray-900">—</p>
                </div>
                <div className="p-3 bg-green-100 rounded-full">
                  <Zap className="h-6 w-6 text-green-600" />
                </div>
              </div>
              <div className="mt-4">
                <button
                  onClick={() => handleProtectedAction('/generate')}
                  className="text-sm text-green-600 hover:text-green-500 font-medium"
                >
                  Sign in to generate →
                </button>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Recent Activity</p>
                  <p className="text-3xl font-bold text-gray-900">—</p>
                </div>
                <div className="p-3 bg-purple-100 rounded-full">
                  <TrendingUp className="h-6 w-6 text-purple-600" />
                </div>
              </div>
              <p className="mt-4 text-sm text-gray-500">Sign in to track activity</p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => handleProtectedAction('/artifacts?action=upload')}
                className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
              >
                <div className="p-2 bg-blue-100 rounded-md">
                  <FolderOpen className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Upload Artifact</p>
                  <p className="text-sm text-gray-500">Sign in to upload artifacts</p>
                </div>
              </button>

              <button
                onClick={() => handleProtectedAction('/generate')}
                className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-colors"
              >
                <div className="p-2 bg-green-100 rounded-md">
                  <Zap className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Generate CV</p>
                  <p className="text-sm text-gray-500">Sign in to generate CVs</p>
                </div>
              </button>

              <button
                disabled
                className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg opacity-50 cursor-not-allowed"
              >
                <div className="p-2 bg-gray-100 rounded-md">
                  <Download className="h-5 w-5 text-gray-400" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Export Documents</p>
                  <p className="text-sm text-gray-500">Coming soon</p>
                </div>
              </button>
            </div>
          </div>

          {/* Call to Action for Unauthenticated Users */}
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="max-w-2xl mx-auto">
              <FileText className="h-16 w-16 text-blue-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Ready to Build Your Perfect CV?
              </h2>
              <p className="text-gray-600 mb-6">
                Upload your professional artifacts, add evidence links, and generate targeted CVs
                that highlight your relevant experience for each job application.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  to="/register"
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                  Get Started Free
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                  Sign In
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}