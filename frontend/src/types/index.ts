// Core API Types
export interface User {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  profile: UserProfile;
}

export interface UserProfile {
  id: number;
  bio?: string;
  location?: string;
  website?: string;
  createdAt: string;
  updatedAt: string;
}

// Authentication Types
export interface AuthResponse {
  user: User;
  access: string;
  refresh: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

// Artifact Types
export interface Artifact {
  id: number;
  title: string;
  description: string;
  startDate: string;
  endDate?: string;
  technologies: string[];
  collaborators: string[];
  evidenceLinks: EvidenceLink[];
  labels: Label[];
  status: 'active' | 'archived';
  createdAt: string;
  updatedAt: string;
}

export interface EvidenceLink {
  id: number;
  url: string;
  type: 'github' | 'live_app' | 'paper' | 'video' | 'other';
  description: string;
  validationStatus: 'pending' | 'valid' | 'invalid';
  lastValidated?: string;
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
  startDate: string;
  endDate?: string;
  technologies: string[];
  collaborators: string[];
  evidenceLinks: Omit<EvidenceLink, 'id' | 'validationStatus' | 'lastValidated'>[];
  labelIds: number[];
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