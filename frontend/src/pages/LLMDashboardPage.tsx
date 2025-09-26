import { useState, useEffect } from 'react'
import {
  Activity,
  Brain,
  DollarSign,
  Zap,
  AlertTriangle,
  TrendingUp,
  RefreshCw,
  Settings,
  BarChart3,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react'
import toast from 'react-hot-toast'
import { apiClient } from '@/services/apiClient'
import type {
  LLMModelStats,
  LLMSystemHealth,
  LLMPerformanceMetric,
  LLMCostTracking,
  PaginatedResponse
} from '@/types'
import { formatDate } from '@/utils/formatters'
import { cn } from '@/utils/cn'

export default function LLMDashboardPage() {
  const [modelStats, setModelStats] = useState<LLMModelStats[]>([])
  const [systemHealth, setSystemHealth] = useState<LLMSystemHealth | null>(null)
  const [performanceMetrics, setPerformanceMetrics] = useState<LLMPerformanceMetric[]>([])
  const [costTracking, setCostTracking] = useState<LLMCostTracking[]>([])
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [circuitBreakers, setCircuitBreakers] = useState<any>(null)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'costs' | 'management'>('overview')

  const loadDashboardData = async () => {
    try {
      const [
        statsData,
        healthData,
        modelsData,
        breakersData,
        metricsData,
        costsData
      ] = await Promise.all([
        apiClient.getLLMModelStats(),
        apiClient.getLLMSystemHealth(),
        apiClient.getAvailableLLMModels(),
        apiClient.getLLMCircuitBreakers(),
        apiClient.getLLMPerformanceMetrics({ limit: '20' }),
        apiClient.getLLMCostTracking({ limit: '20' })
      ])

      setModelStats(statsData)
      setSystemHealth(healthData)
      setAvailableModels(modelsData)
      setCircuitBreakers(breakersData)
      setPerformanceMetrics(metricsData.results)
      setCostTracking(costsData.results)
    } catch (error) {
      console.error('Failed to load LLM dashboard data:', error)
      toast.error('Failed to load dashboard data')
    }
  }

  const refreshData = async () => {
    setIsRefreshing(true)
    await loadDashboardData()
    setIsRefreshing(false)
    toast.success('Dashboard refreshed')
  }

  const selectModel = async (modelId: string) => {
    try {
      await apiClient.selectLLMModel(modelId)
      setSelectedModel(modelId)
      toast.success(`Switched to ${modelId}`)
      await refreshData()
    } catch (error) {
      console.error('Failed to select model:', error)
      toast.error('Failed to select model')
    }
  }

  useEffect(() => {
    loadDashboardData().finally(() => setIsLoading(false))
  }, [])

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100'
      case 'degraded': return 'text-yellow-600 bg-yellow-100'
      case 'down': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getCircuitBreakerColor = (state: string) => {
    switch (state) {
      case 'closed': return 'text-green-600'
      case 'half-open': return 'text-yellow-600'
      case 'open': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

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
          <h1 className="text-3xl font-bold text-gray-900">LLM Services</h1>
          <p className="mt-2 text-gray-600">
            Monitor and manage your AI model integrations, performance, and costs.
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

      {/* System Health Status */}
      {systemHealth && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">System Health</h2>
            <span className={cn('px-3 py-1 rounded-full text-sm font-medium', getHealthStatusColor(systemHealth.status))}>
              {systemHealth.status.toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {Object.entries(systemHealth.models).map(([modelId, modelHealth]) => (
              <div key={modelId} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900 truncate">{modelId}</h3>
                  {modelHealth.status === 'available' ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Response Time:</span>
                    <span className="font-medium">{modelHealth.response_time_ms}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Last Check:</span>
                    <span className="font-medium">{new Date(modelHealth.last_check).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { id: 'overview', name: 'Overview', icon: Activity },
              { id: 'performance', name: 'Performance', icon: BarChart3 },
              { id: 'costs', name: 'Cost Tracking', icon: DollarSign },
              { id: 'management', name: 'Model Management', icon: Settings },
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
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-100">Total Requests</p>
                      <p className="text-3xl font-bold">
                        {modelStats.reduce((sum, stat) => sum + stat.requests_count, 0).toLocaleString()}
                      </p>
                    </div>
                    <Brain className="h-8 w-8 text-blue-200" />
                  </div>
                </div>

                <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-100">Success Rate</p>
                      <p className="text-3xl font-bold">
                        {modelStats.length > 0
                          ? Math.round(modelStats.reduce((sum, stat) => sum + stat.success_rate, 0) / modelStats.length)
                          : 0}%
                      </p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-200" />
                  </div>
                </div>

                <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-purple-100">Avg Response Time</p>
                      <p className="text-3xl font-bold">
                        {modelStats.length > 0
                          ? Math.round(modelStats.reduce((sum, stat) => sum + stat.avg_response_time, 0) / modelStats.length)
                          : 0}ms
                      </p>
                    </div>
                    <Clock className="h-8 w-8 text-purple-200" />
                  </div>
                </div>
              </div>

              {/* Model Statistics */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Model Statistics</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requests</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Success Rate</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Response</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tokens Used</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost (USD)</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {modelStats.map((stat) => (
                        <tr key={stat.model_id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{stat.model_id}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stat.requests_count.toLocaleString()}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{Math.round(stat.success_rate)}%</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{Math.round(stat.avg_response_time)}ms</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stat.total_tokens_used.toLocaleString()}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${stat.cost_usd.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Circuit Breakers */}
              {circuitBreakers && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Circuit Breakers</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(circuitBreakers).map(([modelId, breaker]: [string, any]) => (
                      <div key={modelId} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{modelId}</h4>
                          <span className={cn('font-medium', getCircuitBreakerColor(breaker.state))}>
                            {breaker.state.toUpperCase()}
                          </span>
                        </div>
                        <div className="space-y-1 text-sm text-gray-600">
                          <div>Failures: {breaker.failure_count}</div>
                          {breaker.last_failure && (
                            <div>Last Failure: {formatDate(breaker.last_failure)}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Performance Tab */}
          {activeTab === 'performance' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Recent Performance Metrics</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Request Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Response Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tokens</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {performanceMetrics.map((metric) => (
                      <tr key={metric.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(metric.created_at)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{metric.model_id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{metric.request_type}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{metric.response_time_ms}ms</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{metric.tokens_used}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${metric.cost_usd.toFixed(4)}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {metric.success ? (
                            <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">Success</span>
                          ) : (
                            <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">Failed</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Costs Tab */}
          {activeTab === 'costs' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total Cost (30 days)</p>
                      <p className="text-2xl font-bold text-gray-900">
                        ${costTracking.reduce((sum, cost) => sum + cost.total_cost_usd, 0).toFixed(2)}
                      </p>
                    </div>
                    <DollarSign className="h-8 w-8 text-green-500" />
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total Tokens</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {costTracking.reduce((sum, cost) => sum + cost.total_tokens, 0).toLocaleString()}
                      </p>
                    </div>
                    <Zap className="h-8 w-8 text-blue-500" />
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Avg Cost/Request</p>
                      <p className="text-2xl font-bold text-gray-900">
                        ${costTracking.length > 0
                          ? (costTracking.reduce((sum, cost) => sum + cost.avg_cost_per_request, 0) / costTracking.length).toFixed(4)
                          : '0.0000'}
                      </p>
                    </div>
                    <TrendingUp className="h-8 w-8 text-purple-500" />
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Daily Cost Breakdown</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requests</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Tokens</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Cost</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg/Request</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {costTracking.map((cost) => (
                        <tr key={cost.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(cost.date).toLocaleDateString()}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{cost.model_id}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cost.total_requests.toLocaleString()}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cost.total_tokens.toLocaleString()}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${cost.total_cost_usd.toFixed(2)}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${cost.avg_cost_per_request.toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Management Tab */}
          {activeTab === 'management' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Model Selection</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {availableModels.map((model) => (
                    <div
                      key={model}
                      className={cn(
                        'border-2 rounded-lg p-4 cursor-pointer transition-all',
                        selectedModel === model
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                      onClick={() => selectModel(model)}
                    >
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-gray-900">{model}</h4>
                        {selectedModel === model && (
                          <CheckCircle className="h-5 w-5 text-blue-500" />
                        )}
                      </div>
                      {modelStats.find(stat => stat.model_id === model) && (
                        <div className="mt-2 text-sm text-gray-600">
                          <div>Success Rate: {Math.round(modelStats.find(stat => stat.model_id === model)!.success_rate)}%</div>
                          <div>Avg Response: {Math.round(modelStats.find(stat => stat.model_id === model)!.avg_response_time)}ms</div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t border-gray-200 pt-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">System Configuration</h3>
                  <span className="text-sm text-gray-500">Settings are managed via environment variables</span>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-900">Current Active Model:</span>
                      <span className="ml-2 text-gray-600">{selectedModel || 'Auto-select'}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-900">Available Models:</span>
                      <span className="ml-2 text-gray-600">{availableModels.length}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-900">Circuit Breakers:</span>
                      <span className="ml-2 text-gray-600">Enabled</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-900">Health Monitoring:</span>
                      <span className="ml-2 text-gray-600">Active</span>
                    </div>
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