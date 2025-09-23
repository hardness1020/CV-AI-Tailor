import { useState, useEffect } from 'react'
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
  Loader2
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
    formState: { errors },
  } = useForm<GenerationForm>({
    resolver: zodResolver(generationSchema),
    mode: 'onChange',
  })

  const formData = watch()

  useEffect(() => {
    loadArtifacts()
  }, [])

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
    try {
      const generationId = await generateCV({
        ...data,
        labelIds: selectedArtifacts,
      })
      setCurrentGeneration(generationId)
      setStep(4)
    } catch (error) {
      console.error('Generation failed:', error)
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
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Job Description</h2>
        <p className="text-gray-600">
          Paste the job description below. Our AI will analyze the requirements and match them with your artifacts.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Company Name *
          </label>
          <input
            {...register('companyName')}
            type="text"
            className={cn(
              'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
              errors.companyName && 'border-red-300 focus:border-red-500 focus:ring-red-500'
            )}
            placeholder="e.g., Google"
          />
          {errors.companyName && (
            <p className="mt-1 text-sm text-red-600">{errors.companyName.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Role Title *
          </label>
          <input
            {...register('roleTitle')}
            type="text"
            className={cn(
              'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
              errors.roleTitle && 'border-red-300 focus:border-red-500 focus:ring-red-500'
            )}
            placeholder="e.g., Senior Software Engineer"
          />
          {errors.roleTitle && (
            <p className="mt-1 text-sm text-red-600">{errors.roleTitle.message}</p>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Job Description *
        </label>
        <textarea
          {...register('jobDescription')}
          rows={12}
          className={cn(
            'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            errors.jobDescription && 'border-red-300 focus:border-red-500 focus:ring-red-500'
          )}
          placeholder="Paste the complete job description here..."
        />
        {errors.jobDescription && (
          <p className="mt-1 text-sm text-red-600">{errors.jobDescription.message}</p>
        )}
      </div>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={analyzeJobDescription}
          disabled={!formData.jobDescription || !formData.companyName || !formData.roleTitle}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          <BarChart3 className="h-4 w-4" />
          <span>Analyze & Continue</span>
        </button>
      </div>
    </div>
  )

  const renderArtifactSelectionStep = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Relevant Artifacts</h2>
        <p className="text-gray-600">
          Choose which artifacts are most relevant for this position. We've pre-selected based on the job requirements.
        </p>
      </div>

      {jobAnalysis && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-medium text-blue-900 mb-3">Job Analysis Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-blue-800">Key Skills:</span>
              <ul className="mt-1 text-blue-700">
                {jobAnalysis.keySkills.map((skill: string) => (
                  <li key={skill}>• {skill}</li>
                ))}
              </ul>
            </div>
            <div>
              <span className="font-medium text-blue-800">Experience Level:</span>
              <p className="mt-1 text-blue-700">{jobAnalysis.experienceLevel}</p>
            </div>
            <div>
              <span className="font-medium text-blue-800">Focus Areas:</span>
              <ul className="mt-1 text-blue-700">
                {jobAnalysis.focusAreas.map((area: string) => (
                  <li key={area}>• {area}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {jobAnalysis?.matchedArtifacts.map((artifact: any) => (
          <div
            key={artifact.id}
            className={cn(
              'border rounded-lg p-4 cursor-pointer transition-all',
              selectedArtifacts.includes(artifact.id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            )}
            onClick={() => {
              setSelectedArtifacts(prev =>
                prev.includes(artifact.id)
                  ? prev.filter(id => id !== artifact.id)
                  : [...prev, artifact.id]
              )
            }}
          >
            <div className="flex items-start space-x-3">
              <input
                type="checkbox"
                checked={selectedArtifacts.includes(artifact.id)}
                onChange={() => {}} // Controlled by click handler
                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <FileText className="h-5 w-5 text-blue-600" />
                  <h3 className="font-medium text-gray-900">{artifact.title}</h3>
                  <span className={cn(
                    'px-2 py-1 text-xs rounded-full',
                    artifact.matchScore >= 90 ? 'bg-green-100 text-green-800' :
                    artifact.matchScore >= 80 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  )}>
                    {artifact.matchScore}% match
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{artifact.description}</p>
                <div className="flex flex-wrap gap-1">
                  {artifact.technologies.slice(0, 3).map((tech: string) => (
                    <span
                      key={tech}
                      className="px-2 py-1 bg-gray-100 text-xs text-gray-700 rounded"
                    >
                      {tech}
                    </span>
                  ))}
                  {artifact.technologies.length > 3 && (
                    <span className="px-2 py-1 bg-gray-100 text-xs text-gray-500 rounded">
                      +{artifact.technologies.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-between">
        <button
          type="button"
          onClick={() => setStep(1)}
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
        >
          Back
        </button>
        <button
          type="button"
          onClick={() => setStep(3)}
          disabled={selectedArtifacts.length === 0}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Continue
        </button>
      </div>
    </div>
  )

  const renderCustomizationStep = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Customize Your CV</h2>
        <p className="text-gray-600">
          Adjust the generation settings to match your preferences.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Writing Tone
          </label>
          <select
            {...register('generationPreferences.tone')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="professional">Professional</option>
            <option value="technical">Technical</option>
            <option value="creative">Creative</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            CV Length
          </label>
          <select
            {...register('generationPreferences.length')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="concise">Concise (1 page)</option>
            <option value="detailed">Detailed (2 pages)</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Focus Areas
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            'Technical Skills',
            'Leadership',
            'Project Management',
            'Communication',
            'Problem Solving',
            'Innovation',
          ].map((area) => (
            <label key={area} className="flex items-center space-x-2">
              <input
                type="checkbox"
                value={area}
                {...register('generationPreferences.focusAreas')}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-sm text-gray-700">{area}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="flex justify-between">
        <button
          type="button"
          onClick={() => setStep(2)}
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
        >
          Back
        </button>
        <button
          type="submit"
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center space-x-2"
        >
          <Zap className="h-4 w-4" />
          <span>Generate CV</span>
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
          <div className="text-center py-12">
            <div className="inline-flex items-center space-x-3 mb-6">
              <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
              <span className="text-lg font-medium text-gray-900">Generating...</span>
            </div>

            <div className="w-full max-w-md mx-auto bg-gray-200 rounded-full h-3 mb-4">
              <div
                className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${generation?.progressPercentage || 0}%` }}
              />
            </div>

            <p className="text-sm text-gray-500">{generation?.progressPercentage || 0}% complete</p>

            <div className="mt-8 space-y-2 text-sm text-gray-600">
              <p>• Analyzing job requirements...</p>
              <p>• Matching relevant artifacts...</p>
              <p>• Generating professional summary...</p>
              <p>• Optimizing for ATS compatibility...</p>
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
    <div className="flex items-center justify-between mb-8">
      {[
        { number: 1, title: 'Job Description', completed: step > 1 },
        { number: 2, title: 'Select Artifacts', completed: step > 2 },
        { number: 3, title: 'Customize', completed: step > 3 },
        { number: 4, title: 'Generate', completed: step > 4 },
      ].map((stepItem, index) => (
        <div key={stepItem.number} className="flex items-center">
          <div
            className={cn(
              'flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium',
              step === stepItem.number
                ? 'bg-blue-600 text-white'
                : stepItem.completed
                ? 'bg-green-600 text-white'
                : 'bg-gray-200 text-gray-600'
            )}
          >
            {stepItem.completed ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              stepItem.number
            )}
          </div>
          <span className="ml-2 text-sm font-medium text-gray-900">
            {stepItem.title}
          </span>
          {index < 3 && (
            <div className="flex-1 h-0.5 bg-gray-200 mx-4 min-w-[60px]">
              <div
                className={cn(
                  'h-full transition-all duration-300',
                  stepItem.completed ? 'bg-green-600 w-full' : 'bg-gray-200 w-0'
                )}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-8">
        {renderStepIndicator()}

        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="min-h-[500px]">
            {step === 1 && renderJobDescriptionStep()}
            {step === 2 && renderArtifactSelectionStep()}
            {step === 3 && renderCustomizationStep()}
            {step === 4 && renderGenerationStep()}
          </div>
        </form>
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