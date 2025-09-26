import React, { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Zap,
  FileText,
  CheckCircle,
  AlertCircle,
  Download,
  Edit,
  Star,
  BarChart3,
  Loader2,
  ArrowLeft,
  ArrowRight,
  Sparkles,
  Target,
  Brain
} from 'lucide-react'
import { useArtifacts } from '@/hooks/useArtifacts'
import { useGeneration } from '@/hooks/useGeneration'
import { useExport } from '@/hooks/useExport'
import { cn } from '@/utils/cn'
import type { GeneratedDocument } from '@/types'

const generationSchema = z.object({
  jobDescription: z.string().min(50, 'Job description must be at least 50 characters'),
  companyName: z.string().min(1, 'Company name is required'),
  roleTitle: z.string().min(1, 'Role title is required'),
  labelIds: z.array(z.number()).default([]),
  generationPreferences: z.object({
    tone: z.enum(['professional', 'technical', 'creative']).default('professional'),
    length: z.enum(['concise', 'detailed']).default('detailed'),
    focusAreas: z.array(z.string()).default([]),
  }).default({}),
})

type GenerationForm = z.infer<typeof generationSchema>

interface CVGenerationFlowProps {
  onComplete?: (document: GeneratedDocument) => void
  onClose?: () => void
}

export default function CVGenerationFlow({ onComplete, onClose }: CVGenerationFlowProps) {
  const [step, setStep] = useState(1)
  const [jobAnalysis, setJobAnalysis] = useState<any>(null)
  const [selectedArtifacts, setSelectedArtifacts] = useState<number[]>([])
  const [currentGeneration, setCurrentGeneration] = useState<string | null>(null)

  const { artifacts, loadArtifacts } = useArtifacts()
  const { generateCV, activeGenerations } = useGeneration()
  const { exportDocument } = useExport()

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid },
  } = useForm<GenerationForm>({
    resolver: zodResolver(generationSchema),
    mode: 'onChange',
    defaultValues: {
      generationPreferences: {
        tone: 'professional',
        length: 'detailed',
        focusAreas: [],
      }
    }
  })

  const formData = watch()

  // Load artifacts on component mount
  useEffect(() => {
    loadArtifacts()
  }, []) // loadArtifacts is stable from Zustand, so we don't need it in dependencies

  // Watch for generation completion
  useEffect(() => {
    if (currentGeneration) {
      const generation = activeGenerations.find(g => g.id === currentGeneration)
      if (generation?.status === 'completed') {
        setStep(4)
        onComplete?.(generation)
      }
    }
  }, [activeGenerations, currentGeneration, onComplete])

  const onSubmit = async (data: GenerationForm) => {
    console.log('Form submission triggered with data:', data)
    console.log('Selected artifacts:', selectedArtifacts)

    try {
      const requestData = {
        ...data,
        labelIds: selectedArtifacts,
      }
      console.log('Sending request to generateCV:', requestData)

      const generationId = await generateCV(requestData)
      console.log('Generation started with ID:', generationId)

      setCurrentGeneration(generationId)
      setStep(4)
    } catch (error) {
      console.error('Generation failed:', error)
      // Show more detailed error information
      if (error instanceof Error) {
        console.error('Error message:', error.message)
        console.error('Error stack:', error.stack)
      }
    }
  }

  const analyzeJobDescription = async () => {
    // Simulate job analysis - in real implementation, this would call an API
    const mockAnalysis = {
      keySkills: ['React', 'Node.js', 'TypeScript', 'AWS'],
      experienceLevel: 'Senior (5+ years)',
      focusAreas: ['Full-stack development', 'Team leadership', 'System architecture'],
      matchedArtifacts: artifacts
        .map(artifact => ({
          ...artifact,
          matchScore: Math.floor(Math.random() * 30) + 70, // 70-100%
        }))
        .sort((a, b) => b.matchScore - a.matchScore),
    }

    setJobAnalysis(mockAnalysis)

    // Auto-select top matching artifacts
    const topMatches = mockAnalysis.matchedArtifacts
      .filter(a => a.matchScore >= 80)
      .slice(0, 3)
      .map(a => a.id)

    setSelectedArtifacts(topMatches)
    setStep(2)
  }

  const renderJobDescriptionStep = () => (
    <div className="space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-full mb-6">
          <Target className="h-4 w-4 text-blue-600" />
          <span className="text-sm font-semibold text-blue-700">Step 1 of 4</span>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Tell us about the position</h2>
        <p className="text-gray-600 max-w-2xl mx-auto leading-relaxed">
          Paste the job description below and we'll use advanced AI to analyze requirements, extract key skills, and intelligently match them with your professional artifacts.
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 p-6 sm:p-8 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="block text-sm font-bold text-gray-800 mb-3">
              Company Name *
            </label>
            <div className="relative">
              <input
                {...register('companyName')}
                type="text"
                className={cn(
                  'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 font-medium placeholder:text-gray-400',
                  errors.companyName && 'border-red-300 focus:border-red-500 focus:ring-red-100'
                )}
                placeholder="e.g., Google, Meta, Apple"
              />
              {errors.companyName && (
                <div className="absolute -bottom-6 left-0 flex items-center gap-2 text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  <p className="text-sm font-medium">{errors.companyName.message}</p>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-bold text-gray-800 mb-3">
              Role Title *
            </label>
            <div className="relative">
              <input
                {...register('roleTitle')}
                type="text"
                className={cn(
                  'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 font-medium placeholder:text-gray-400',
                  errors.roleTitle && 'border-red-300 focus:border-red-500 focus:ring-red-100'
                )}
                placeholder="e.g., Senior Software Engineer"
              />
              {errors.roleTitle && (
                <div className="absolute -bottom-6 left-0 flex items-center gap-2 text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  <p className="text-sm font-medium">{errors.roleTitle.message}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <label className="block text-sm font-bold text-gray-800">
            Job Description *
          </label>
          <div className="relative">
            <textarea
              {...register('jobDescription')}
              rows={12}
              className={cn(
                'w-full px-4 py-4 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 font-medium placeholder:text-gray-400 resize-none',
                errors.jobDescription && 'border-red-300 focus:border-red-500 focus:ring-red-100'
              )}
              placeholder="Paste the complete job description here...

Tip: Include requirements, responsibilities, and preferred qualifications for best matching results."
            />
            <div className="absolute bottom-3 right-3 text-xs text-gray-400 font-medium">
              {formData.jobDescription?.length || 0} characters
            </div>
            {errors.jobDescription && (
              <div className="absolute -bottom-6 left-0 flex items-center gap-2 text-red-600">
                <AlertCircle className="h-4 w-4" />
                <p className="text-sm font-medium">{errors.jobDescription.message}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex justify-center">
        <button
          type="button"
          onClick={analyzeJobDescription}
          disabled={!formData.jobDescription || !formData.companyName || !formData.roleTitle}
          className="group relative overflow-hidden bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold px-8 py-4 rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105 disabled:transform-none disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-md"
        >
          <div className="flex items-center gap-3">
            <Brain className="h-5 w-5" />
            <span>Analyze with AI</span>
            <ArrowRight className="h-5 w-5 transform group-hover:translate-x-1 transition-transform duration-200" />
          </div>
          {!(!formData.jobDescription || !formData.companyName || !formData.roleTitle) && (
            <div className="absolute inset-0 bg-white/10 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
          )}
        </button>
      </div>
    </div>
  )

  const renderArtifactSelectionStep = () => (
    <div className="space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-full mb-6">
          <FileText className="h-4 w-4 text-green-600" />
          <span className="text-sm font-semibold text-green-700">Step 2 of 4</span>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Select Your Best Artifacts</h2>
        <p className="text-gray-600 max-w-2xl mx-auto leading-relaxed">
          Our AI has analyzed the job requirements and ranked your artifacts by relevance. The best matches are pre-selected, but you can customize the selection.
        </p>
      </div>

      {jobAnalysis && (
        <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-blue-50 border-2 border-blue-200 rounded-2xl p-6 sm:p-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-400/10 to-indigo-400/10 rounded-full -translate-y-16 translate-x-16" />
          <div className="relative">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg">
                <Brain className="h-5 w-5 text-white" />
              </div>
              <h3 className="font-bold text-blue-900 text-lg">AI Analysis Results</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white/60 rounded-xl p-4 border border-blue-200/50">
                <span className="font-bold text-blue-800 text-sm uppercase tracking-wide">Key Skills Found</span>
                <div className="mt-3 space-y-2">
                  {jobAnalysis.keySkills.map((skill: string) => (
                    <div key={skill} className="flex items-center gap-2 text-blue-700">
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                      <span className="text-sm font-medium">{skill}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-white/60 rounded-xl p-4 border border-blue-200/50">
                <span className="font-bold text-blue-800 text-sm uppercase tracking-wide">Experience Level</span>
                <div className="mt-3">
                  <span className="inline-flex items-center px-3 py-1.5 bg-blue-100 text-blue-800 text-sm font-bold rounded-full">
                    {jobAnalysis.experienceLevel}
                  </span>
                </div>
              </div>
              <div className="bg-white/60 rounded-xl p-4 border border-blue-200/50">
                <span className="font-bold text-blue-800 text-sm uppercase tracking-wide">Focus Areas</span>
                <div className="mt-3 space-y-2">
                  {jobAnalysis.focusAreas.map((area: string) => (
                    <div key={area} className="flex items-center gap-2 text-blue-700">
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                      <span className="text-sm font-medium">{area}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {jobAnalysis?.matchedArtifacts.map((artifact: any) => (
          <div
            key={artifact.id}
            className={cn(
              'group relative overflow-hidden border-2 rounded-2xl p-6 cursor-pointer transition-all duration-300 transform hover:scale-102 hover:shadow-lg',
              selectedArtifacts.includes(artifact.id)
                ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50 shadow-lg scale-102'
                : 'border-gray-200 hover:border-gray-300 bg-white hover:bg-gray-50'
            )}
            onClick={() => {
              setSelectedArtifacts(prev =>
                prev.includes(artifact.id)
                  ? prev.filter(id => id !== artifact.id)
                  : [...prev, artifact.id]
              )
            }}
          >
            {/* Background decoration */}
            <div className={cn(
              "absolute top-0 right-0 w-24 h-24 rounded-full -translate-y-12 translate-x-12 transition-all duration-500",
              selectedArtifacts.includes(artifact.id)
                ? "bg-gradient-to-br from-blue-400/10 to-indigo-400/10 scale-150"
                : "bg-gradient-to-br from-gray-400/5 to-gray-400/5 group-hover:scale-125"
            )} />

            <div className="relative flex items-start space-x-4">
              <div className="relative mt-1">
                <input
                  type="checkbox"
                  checked={selectedArtifacts.includes(artifact.id)}
                  onChange={() => {}} // Controlled by click handler
                  className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-2 border-gray-300 rounded-lg transition-all duration-200"
                />
                {selectedArtifacts.includes(artifact.id) && (
                  <div className="absolute inset-0 bg-blue-500 rounded-lg flex items-center justify-center">
                    <CheckCircle className="h-3 w-3 text-white" />
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center shadow-md flex-shrink-0">
                      <FileText className="h-4 w-4 text-white" />
                    </div>
                    <h3 className="font-bold text-gray-900 truncate text-base">{artifact.title}</h3>
                  </div>
                  <span className={cn(
                    'ml-2 px-3 py-1.5 text-xs font-bold rounded-full whitespace-nowrap',
                    artifact.matchScore >= 90 ? 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 border border-green-200' :
                    artifact.matchScore >= 80 ? 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-800 border border-yellow-200' :
                    'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 border border-gray-200'
                  )}>
                    {artifact.matchScore}% match
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-4 leading-relaxed line-clamp-2">{artifact.description}</p>
                <div className="flex flex-wrap gap-2">
                  {artifact.technologies.slice(0, 4).map((tech: string) => (
                    <span
                      key={tech}
                      className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-xs font-medium text-gray-700 rounded-full transition-colors duration-200"
                    >
                      {tech}
                    </span>
                  ))}
                  {artifact.technologies.length > 4 && (
                    <span className="px-3 py-1.5 bg-gray-200 text-xs font-medium text-gray-600 rounded-full">
                      +{artifact.technologies.length - 4} more
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-between items-center pt-6">
        <button
          type="button"
          onClick={() => setStep(1)}
          className="group flex items-center gap-2 px-6 py-3 border-2 border-gray-300 text-gray-700 hover:text-gray-900 font-semibold rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 transform hover:scale-105"
        >
          <ArrowLeft className="h-4 w-4 transform group-hover:-translate-x-1 transition-transform duration-200" />
          <span>Back</span>
        </button>

        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className="text-sm font-bold text-gray-900">
              {selectedArtifacts.length} artifacts selected
            </div>
            <div className="text-xs text-gray-500">
              {selectedArtifacts.length === 0 ? 'Select at least 1' : 'Ready to continue'}
            </div>
          </div>

          <button
            type="button"
            onClick={() => setStep(3)}
            disabled={selectedArtifacts.length === 0}
            className="group relative overflow-hidden bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold px-8 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 disabled:transform-none disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-md"
          >
            <div className="flex items-center gap-2">
              <span>Continue</span>
              <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform duration-200" />
            </div>
            {selectedArtifacts.length > 0 && (
              <div className="absolute inset-0 bg-white/10 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
            )}
          </button>
        </div>
      </div>
    </div>
  )

  const renderCustomizationStep = () => (
    <div className="space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-full mb-6">
          <Sparkles className="h-4 w-4 text-blue-600" />
          <span className="text-sm font-semibold text-blue-700">Step 3 of 4</span>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Personalize Your CV</h2>
        <p className="text-gray-600 max-w-2xl mx-auto leading-relaxed">
          Fine-tune the generation settings to create a CV that perfectly matches your style and the job requirements.
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 p-6 sm:p-8 space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-4">
            <label className="block text-sm font-bold text-gray-800 mb-4">
              Writing Tone
            </label>
            <div className="space-y-3">
              {[
                { value: 'professional', label: 'Professional', desc: 'Formal, business-oriented language' },
                { value: 'technical', label: 'Technical', desc: 'Focus on technical skills and expertise' },
                { value: 'creative', label: 'Creative', desc: 'Engaging, personality-driven approach' }
              ].map(option => (
                <label key={option.value} className="group flex items-start gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-blue-300 cursor-pointer transition-all duration-200 hover:shadow-md">
                  <input
                    {...register('generationPreferences.tone')}
                    type="radio"
                    value={option.value}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
                      {option.label}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {option.desc}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <label className="block text-sm font-bold text-gray-800 mb-4">
              CV Length
            </label>
            <div className="space-y-3">
              {[
                { value: 'concise', label: 'Concise', desc: '1 page - Perfect for most applications' },
                { value: 'detailed', label: 'Detailed', desc: '2 pages - Comprehensive experience showcase' }
              ].map(option => (
                <label key={option.value} className="group flex items-start gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-blue-300 cursor-pointer transition-all duration-200 hover:shadow-md">
                  <input
                    {...register('generationPreferences.length')}
                    type="radio"
                    value={option.value}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
                      {option.label}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {option.desc}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <label className="block text-sm font-bold text-gray-800 mb-4">
            Focus Areas <span className="text-gray-500 font-normal">(Optional - Select what to emphasize)</span>
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {[
              { value: 'Technical Skills', icon: '💻' },
              { value: 'Leadership', icon: '👥' },
              { value: 'Project Management', icon: '📋' },
              { value: 'Communication', icon: '💬' },
              { value: 'Problem Solving', icon: '🧩' },
              { value: 'Innovation', icon: '💡' },
            ].map((area) => (
              <label key={area.value} className="group flex items-center gap-3 p-4 rounded-xl border-2 border-gray-200 hover:border-blue-300 cursor-pointer transition-all duration-200 hover:shadow-md">
                <input
                  type="checkbox"
                  value={area.value}
                  {...register('generationPreferences.focusAreas')}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-lg">{area.icon}</span>
                <span className="text-sm font-semibold text-gray-700 group-hover:text-blue-700 transition-colors">{area.value}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center pt-6">
        <button
          type="button"
          onClick={() => setStep(2)}
          className="group flex items-center gap-2 px-6 py-3 border-2 border-gray-300 text-gray-700 hover:text-gray-900 font-semibold rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 transform hover:scale-105"
        >
          <ArrowLeft className="h-4 w-4 transform group-hover:-translate-x-1 transition-transform duration-200" />
          <span>Back</span>
        </button>

        <div className="text-center">
          <div className="text-sm font-bold text-gray-900 mb-1">
            Ready to generate!
          </div>
          <div className="text-xs text-gray-500">
            This may take 30-60 seconds
          </div>
        </div>

        <button
          type="submit"
          onClick={() => {
            console.log('Button clicked!')
            console.log('Form errors:', errors)
            console.log('Form valid:', isValid)
            console.log('Current form data:', formData)
          }}
          className="group relative overflow-hidden bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold px-8 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
        >
          <div className="flex items-center gap-3">
            <Zap className="h-5 w-5" />
            <span>Generate My CV</span>
            <Sparkles className="h-5 w-5" />
          </div>
          <div className="absolute inset-0 bg-white/10 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
        </button>
      </div>
    </div>
  )

  const renderGenerationStep = () => {
    const generation = activeGenerations.find(g => g.id === currentGeneration)
    const isGenerating = generation?.status === 'processing'
    const isCompleted = generation?.status === 'completed'
    const isFailed = generation?.status === 'failed'

    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            {isGenerating ? 'Generating Your CV' :
             isCompleted ? 'CV Generated Successfully!' :
             isFailed ? 'Generation Failed' :
             'Starting Generation...'}
          </h2>
          <p className="text-gray-600">
            {isGenerating
              ? 'Please wait while we create your personalized CV...'
              : isCompleted
              ? 'Your CV has been generated and is ready for review and export.'
              : isFailed
              ? 'Something went wrong during generation. Please try again.'
              : 'Initializing CV generation...'}
          </p>
        </div>

        {isGenerating && (
          <div className="text-center py-16 relative">
            {/* Background animation */}
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-blue-400/5 rounded-full animate-pulse" />
              <div className="absolute top-3/4 right-1/4 w-24 h-24 bg-purple-400/5 rounded-full animate-pulse animation-delay-1000" />
              <div className="absolute top-1/2 left-1/2 w-40 h-40 bg-indigo-400/5 rounded-full animate-pulse animation-delay-2000" />
            </div>

            <div className="relative">
              <div className="inline-flex items-center gap-4 mb-8">
                <div className="relative">
                  <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
                  <div className="absolute inset-0 h-12 w-12 border-4 border-blue-200 rounded-full animate-ping" />
                </div>
                <div className="text-left">
                  <div className="text-xl font-bold text-gray-900">Creating Your Perfect CV</div>
                  <div className="text-sm text-gray-500">AI is working its magic...</div>
                </div>
              </div>

              <div className="w-full max-w-lg mx-auto">
                <div className="bg-gradient-to-r from-gray-200 to-gray-300 rounded-full h-4 mb-4 shadow-inner overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 h-full rounded-full transition-all duration-700 ease-out shadow-sm relative"
                    style={{ width: `${generation?.progressPercentage || 0}%` }}
                  >
                    <div className="absolute inset-0 bg-white/20 rounded-full" />
                    <div className="absolute right-1 top-1/2 transform -translate-y-1/2 w-2 h-2 bg-white rounded-full shadow-sm" />
                  </div>
                </div>

                <div className="flex justify-between items-center text-sm">
                  <span className="font-bold text-gray-700">{generation?.progressPercentage || 0}% Complete</span>
                  <span className="text-gray-500">ETA: ~{Math.max(10, Math.ceil((100 - (generation?.progressPercentage || 0)) / 3))}s</span>
                </div>
              </div>

              <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 max-w-4xl mx-auto">
                {[
                  { icon: Brain, text: 'Analyzing job requirements', delay: '0ms' },
                  { icon: Target, text: 'Matching relevant artifacts', delay: '200ms' },
                  { icon: Sparkles, text: 'Generating content', delay: '400ms' },
                  { icon: CheckCircle, text: 'Optimizing for ATS', delay: '600ms' }
                ].map((step, index) => (
                  <div
                    key={step.text}
                    className="flex flex-col items-center gap-3 p-4 bg-white/60 rounded-2xl border border-gray-200 backdrop-blur-sm"
                    style={{ animationDelay: step.delay }}
                  >
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-lg">
                      <step.icon className="h-6 w-6 text-white" />
                    </div>
                    <div className="text-xs font-semibold text-gray-700 text-center leading-tight">
                      {step.text}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {isCompleted && generation && (
          <CVGenerationResult
            generation={generation}
            onExport={(format) => {
              exportDocument(generation.id, {
                format,
                templateId: 1,
                options: {
                  includeEvidence: true,
                  evidenceFormat: 'hyperlinks',
                  pageMargins: 'normal',
                  fontSize: 11,
                  colorScheme: 'monochrome',
                },
                sections: {
                  includeProfessionalSummary: true,
                  includeSkills: true,
                  includeExperience: true,
                  includeProjects: true,
                  includeEducation: true,
                  includeCertifications: true,
                },
              })
            }}
            onClose={onClose}
          />
        )}

        {isFailed && (
          <div className="text-center py-12">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-gray-600 mb-6">
              Generation failed. Please check your input and try again.
            </p>
            <button
              type="button"
              onClick={() => setStep(1)}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    )
  }

  const renderStepIndicator = () => (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-8 shadow-sm">
      <div className="flex items-center justify-between px-4">
        {[
          { number: 1, title: 'Job Analysis', icon: Target, completed: step > 1 },
          { number: 2, title: 'Select Artifacts', icon: FileText, completed: step > 2 },
          { number: 3, title: 'Customize', icon: Sparkles, completed: step > 3 },
          { number: 4, title: 'Generate', icon: Zap, completed: step > 4 },
        ].map((stepItem, index) => (
          <React.Fragment key={stepItem.number}>
            <div className="flex flex-col items-center min-w-0">
              <div
                className={cn(
                  'flex items-center justify-center w-12 h-12 rounded-2xl text-sm font-bold transition-all duration-300 shadow-lg',
                  step === stepItem.number
                    ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-blue-200 scale-110'
                    : stepItem.completed
                    ? 'bg-gradient-to-br from-green-500 to-emerald-600 text-white shadow-green-200'
                    : 'bg-gray-100 text-gray-500 shadow-gray-100'
                )}
              >
                {stepItem.completed ? (
                  <CheckCircle className="h-6 w-6" />
                ) : (
                  <stepItem.icon className="h-6 w-6" />
                )}
              </div>
              <div className="mt-3 text-center">
                <div className={cn(
                  'text-sm font-bold transition-colors duration-300',
                  step === stepItem.number ? 'text-blue-600' :
                  stepItem.completed ? 'text-green-600' : 'text-gray-500'
                )}>
                  {stepItem.title}
                </div>
                <div className={cn(
                  'text-xs mt-1 transition-colors duration-300',
                  step === stepItem.number ? 'text-blue-500' :
                  stepItem.completed ? 'text-green-500' : 'text-gray-400'
                )}>
                  Step {stepItem.number}
                </div>
              </div>
            </div>
            {index < 3 && (
              <div className="flex-1 h-1 bg-gray-200 mx-8 rounded-full overflow-hidden self-start mt-6">
                <div
                  className={cn(
                    'h-full rounded-full transition-all duration-500 ease-out',
                    stepItem.completed ? 'bg-gradient-to-r from-green-400 to-emerald-500 w-full' : 'bg-gray-200 w-0'
                  )}
                />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6">
      <div className="relative">
        {/* Background decoration */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-blue-400/5 to-indigo-400/5 rounded-full -translate-y-48 translate-x-48 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-72 h-72 bg-gradient-to-tr from-purple-400/5 to-pink-400/5 rounded-full translate-y-36 -translate-x-36 pointer-events-none" />

        <div className="relative">
          {renderStepIndicator()}

          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="bg-gradient-to-br from-gray-50 to-white rounded-3xl border border-gray-200 shadow-xl p-6 sm:p-10 min-h-[600px]">
              {step === 1 && renderJobDescriptionStep()}
              {step === 2 && renderArtifactSelectionStep()}
              {step === 3 && renderCustomizationStep()}
              {step === 4 && renderGenerationStep()}
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

interface CVGenerationResultProps {
  generation: GeneratedDocument
  onExport: (format: 'pdf' | 'docx') => void
  onClose?: () => void
}

function CVGenerationResult({ generation, onExport }: CVGenerationResultProps) {
  const [rating, setRating] = useState(0)
  const [showFeedback, setShowFeedback] = useState(false)

  return (
    <div className="space-y-6">
      {/* Generation Results */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-green-100 rounded-full">
            <CheckCircle className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <h3 className="font-medium text-green-900">CV Generated Successfully</h3>
            <p className="text-sm text-green-700">
              Generated on {new Date(generation.createdAt).toLocaleDateString()}
            </p>
          </div>
        </div>

        {generation.metadata && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-green-800">Skill Match:</span>
              <p className="text-green-700">{generation.metadata.skillMatchScore}% compatibility</p>
            </div>
            <div>
              <span className="font-medium text-green-800">Artifacts Used:</span>
              <p className="text-green-700">{generation.metadata.artifactsUsed.length} projects</p>
            </div>
            <div>
              <span className="font-medium text-green-800">Generation Time:</span>
              <p className="text-green-700">{(generation.metadata.generationTime / 1000).toFixed(1)}s</p>
            </div>
          </div>
        )}
      </div>

      {/* CV Preview */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="font-medium text-gray-900 mb-4">CV Preview</h3>
        <div className="bg-gray-50 rounded-lg p-6 min-h-[400px]">
          {generation.content && (
            <div className="space-y-6">
              <div className="text-center border-b border-gray-300 pb-4">
                <h1 className="text-2xl font-bold text-gray-900">John Doe</h1>
                <p className="text-gray-600">{generation.content.experience?.[0]?.title || 'Professional'}</p>
                <p className="text-sm text-gray-500">john.doe@email.com • (555) 123-4567</p>
              </div>

              {generation.content.professionalSummary && (
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 border-b border-gray-300 pb-2 mb-3">
                    Professional Summary
                  </h2>
                  <p className="text-gray-700 leading-relaxed">
                    {generation.content.professionalSummary}
                  </p>
                </div>
              )}

              {generation.content.keySkills && generation.content.keySkills.length > 0 && (
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 border-b border-gray-300 pb-2 mb-3">
                    Key Skills
                  </h2>
                  <div className="flex flex-wrap gap-2">
                    {generation.content.keySkills.slice(0, 8).map((skill, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Rating Section */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">How would you rate this CV?</h4>
        <div className="flex items-center space-x-2">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              onClick={() => setRating(star)}
              className={cn(
                'p-1 rounded transition-colors',
                star <= rating ? 'text-yellow-500' : 'text-gray-300 hover:text-yellow-400'
              )}
            >
              <Star className="h-6 w-6 fill-current" />
            </button>
          ))}
          <span className="ml-3 text-sm text-gray-600">
            {rating > 0 && `${rating}/5 stars`}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between">
        <button
          type="button"
          onClick={() => setShowFeedback(!showFeedback)}
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 flex items-center space-x-2"
        >
          <Edit className="h-4 w-4" />
          <span>Provide Feedback</span>
        </button>
        <div className="flex space-x-3">
          <button
            type="button"
            onClick={() => onExport('pdf')}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center space-x-2"
          >
            <Download className="h-4 w-4" />
            <span>Export PDF</span>
          </button>
          <button
            type="button"
            onClick={() => onExport('docx')}
            className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 flex items-center space-x-2"
          >
            <Download className="h-4 w-4" />
            <span>Export Word</span>
          </button>
        </div>
      </div>
    </div>
  )
}