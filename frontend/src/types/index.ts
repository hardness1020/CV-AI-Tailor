// Core API Types
export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  profile_image?: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  website_url?: string;
  bio?: string;
  location?: string;
  preferred_cv_template?: number;
  email_notifications?: boolean;
  created_at: string;
  updated_at: string;
}

// Authentication Types
export interface AuthResponse {
  user: User;
  access: string;
  refresh: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
}

// Artifact Types
export interface Artifact {
  id: number;
  title: string;
  description: string;
  artifact_type: 'project' | 'experience' | 'education' | 'certification' | 'other';
  start_date: string;
  end_date?: string;
  technologies: string[];
  collaborators: string[];
  evidence_links: EvidenceLink[];
  labels: Label[];
  status: 'active' | 'archived';
  extracted_metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface EvidenceLink {
  id: number;
  url: string;
  link_type: 'github' | 'live_app' | 'document' | 'website' | 'portfolio' | 'other';
  description: string;
  file_path?: string;
  mime_type?: string;
  is_accessible?: boolean;
  last_validated?: string;
  validation_metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface Label {
  id: number;
  name: string;
  color: string;
  description?: string;
}

export interface ArtifactCreateData {
  title: string;
  description: string;
  artifact_type?: 'project' | 'experience' | 'education' | 'certification' | 'other';
  start_date?: string;
  end_date?: string;
  technologies?: string[];
  collaborators?: string[];
  evidence_links?: Omit<EvidenceLink, 'id' | 'is_accessible' | 'last_validated' | 'validation_metadata'>[];
  labelIds?: number[];
}

export interface BulkUploadResponse {
  artifact_id: number;
  status: string;
  task_id: string;
  estimated_completion: string;
  uploaded_files_count: number;
  evidence_links_count: number;
}

export interface ArtifactProcessingStatus {
  artifact_id: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  error_message?: string;
  processed_evidence_count: number;
  total_evidence_count: number;
  created_at: string;
  completed_at?: string;
}

// Generation Types
export interface CVGenerationRequest {
  jobDescription: string;
  companyName: string;
  roleTitle: string;
  labelIds: number[];
  templateId?: number;
  customSections?: Record<string, any>;
  generationPreferences?: {
    tone: 'professional' | 'technical' | 'creative';
    length: 'concise' | 'detailed';
    focusAreas: string[];
  };
}

export interface GeneratedDocument {
  id: string;
  type: 'cv' | 'cover_letter';
  status: 'processing' | 'completed' | 'failed';
  progressPercentage: number;
  content?: DocumentContent;
  metadata?: {
    artifactsUsed: number[];
    skillMatchScore: number;
    missingSkills: string[];
    generationTime: number;
    modelUsed: string;
  };
  createdAt: string;
  completedAt?: string;
  jobDescriptionHash: string;
}

export interface DocumentContent {
  professionalSummary: string;
  keySkills: string[];
  experience: ExperienceEntry[];
  projects: ProjectEntry[];
  education: EducationEntry[];
  certifications: CertificationEntry[];
}

export interface ExperienceEntry {
  title: string;
  organization: string;
  duration: string;
  achievements: string[];
  technologiesUsed: string[];
  evidenceReferences: string[];
}

export interface ProjectEntry {
  name: string;
  description: string;
  technologies: string[];
  evidenceUrl: string;
  impactMetrics: string;
}

export interface EducationEntry {
  institution: string;
  degree: string;
  field: string;
  year: string;
  gpa?: string;
}

export interface CertificationEntry {
  name: string;
  issuer: string;
  issueDate: string;
  expiryDate?: string;
  credentialId?: string;
}

// Export Types
export interface ExportRequest {
  format: 'pdf' | 'docx';
  templateId: number;
  options: {
    includeEvidence: boolean;
    evidenceFormat: 'hyperlinks' | 'footnotes' | 'qr_codes';
    pageMargins: 'narrow' | 'normal' | 'wide';
    fontSize: number;
    colorScheme: 'monochrome' | 'accent' | 'full_color';
  };
  sections: {
    includeProfessionalSummary: boolean;
    includeSkills: boolean;
    includeExperience: boolean;
    includeProjects: boolean;
    includeEducation: boolean;
    includeCertifications: boolean;
  };
  watermark?: {
    text: string;
    opacity: number;
  };
}

export interface ExportJob {
  id: string;
  status: 'processing' | 'completed' | 'failed';
  progressPercentage: number;
  errorMessage?: string;
  fileSize?: number;
  downloadUrl?: string;
  expiresAt?: string;
}

// API Response Types
export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

// UI State Types
export interface ArtifactFilters {
  search?: string;
  technologies?: string[];
  labelIds?: number[];
  status?: 'active' | 'archived';
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface UploadProgress {
  fileName: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  error?: string;
}