import { render, screen, fireEvent, waitFor } from '@/test/utils'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import ArtifactUpload from '../ArtifactUpload'
import { useArtifacts } from '@/hooks/useArtifacts'

// Mock hooks
vi.mock('@/hooks/useArtifacts', () => ({
  useArtifacts: vi.fn(),
}))

const mockUseArtifacts = vi.mocked(useArtifacts)

describe('ArtifactUpload', () => {
  const mockCreateArtifact = vi.fn()
  const mockOnUploadComplete = vi.fn()
  const mockOnClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseArtifacts.mockReturnValue({
      artifacts: [],
      createArtifact: mockCreateArtifact,
      loadArtifacts: vi.fn(),
      updateArtifact: vi.fn(),
      deleteArtifact: vi.fn(),
      bulkDelete: vi.fn(),
      uploadProgress: {},
      isLoading: false,
      error: null,
    })
  })

  it('renders upload form correctly', () => {
    render(
      <ArtifactUpload
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    )

    expect(screen.getByText('Upload Artifact')).toBeInTheDocument()
    expect(screen.getByLabelText('Title')).toBeInTheDocument()
    expect(screen.getByLabelText('Description')).toBeInTheDocument()
    expect(screen.getByText('Upload Documents')).toBeInTheDocument()
  })

  it('validates required fields', async () => {
    render(
      <ArtifactUpload
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    )

    const submitButton = screen.getByText('Create Artifact')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Title is required')).toBeInTheDocument()
    })
  })

  it('submits form with valid data', async () => {
    mockCreateArtifact.mockResolvedValue({
      id: 1,
      title: 'Test Artifact',
      description: 'Test Description',
      technologies: ['React'],
      startDate: '2023-01-01',
      endDate: '2023-12-31',
      status: 'active',
      evidenceLinks: [],
      collaborators: [],
      labels: [],
    })

    render(
      <ArtifactUpload
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    )

    // Fill in required fields
    fireEvent.change(screen.getByLabelText('Title'), {
      target: { value: 'Test Artifact' },
    })
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Test Description' },
    })

    // Submit form
    fireEvent.click(screen.getByText('Create Artifact'))

    await waitFor(() => {
      expect(mockCreateArtifact).toHaveBeenCalled()
      expect(mockOnUploadComplete).toHaveBeenCalled()
    })
  })

  it('handles form cancellation', () => {
    render(
      <ArtifactUpload
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    )

    const cancelButton = screen.getByText('Cancel')
    fireEvent.click(cancelButton)

    expect(mockOnClose).toHaveBeenCalled()
  })

  it('displays loading state during submission', async () => {
    mockCreateArtifact.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    render(
      <ArtifactUpload
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    )

    // Fill in required fields
    fireEvent.change(screen.getByLabelText('Title'), {
      target: { value: 'Test Artifact' },
    })
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Test Description' },
    })

    // Submit form
    fireEvent.click(screen.getByText('Create Artifact'))

    await waitFor(() => {
      expect(screen.getByText('Creating...')).toBeInTheDocument()
    })
  })
})