import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { apiClient } from '@/services/apiClient'
import Layout from '@/components/Layout'
import PublicLayout from '@/components/PublicLayout'
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
      {/* Default route - Dashboard first approach */}
      <Route path="/" element={<DashboardPage />} />

      {/* Public routes */}
      <Route path="/login" element={
        <PublicLayout>
          <LoginPage />
        </PublicLayout>
      } />
      <Route path="/register" element={
        <PublicLayout>
          <RegisterPage />
        </PublicLayout>
      } />

      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={<DashboardPage />}
      />
      <Route
        path="/artifacts"
        element={
          <ProtectedRoute>
            <Layout>
              <ArtifactsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/generate"
        element={
          <ProtectedRoute>
            <Layout>
              <GeneratePage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <Layout>
              <ProfilePage />
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App