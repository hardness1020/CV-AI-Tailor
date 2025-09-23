import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { apiClient } from '@/services/apiClient'
import Layout from '@/components/Layout'
import ProtectedRoute from '@/components/ProtectedRoute'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import DashboardPage from '@/pages/DashboardPage'
import ArtifactsPage from '@/pages/ArtifactsPage'
import GeneratePage from '@/pages/GeneratePage'
import ProfilePage from '@/pages/ProfilePage'

function App() {
  const { isAuthenticated, setUser, setLoading, clearAuth } = useAuthStore()

  useEffect(() => {
    // Check if user is authenticated on app load
    const initializeAuth = async () => {
      if (isAuthenticated) {
        setLoading(true)
        try {
          const user = await apiClient.getCurrentUser()
          setUser(user)
        } catch (error) {
          console.error('Failed to get current user:', error)
          clearAuth()
        } finally {
          setLoading(false)
        }
      }
    }

    initializeAuth()
  }, [isAuthenticated, setUser, setLoading, clearAuth])

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected routes */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/artifacts" element={<ArtifactsPage />} />
                <Route path="/generate" element={<GeneratePage />} />
                <Route path="/profile" element={<ProfilePage />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App