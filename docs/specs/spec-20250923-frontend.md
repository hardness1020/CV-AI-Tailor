# Tech Spec — Frontend

**Version:** v1.0.0
**File:** docs/specs/spec-20250923-frontend.md
**Status:** Draft
**PRD:** `prd-20250923.md`
**Contract Versions:** Frontend v1.0 • API Client v1.0 • Component Library v1.0

## Overview & Goals

Build a modern, responsive React SPA frontend that provides an intuitive interface for artifact upload, job description input, CV/cover letter generation, and document export. Target sub-200ms UI interactions, mobile-responsive design, and accessibility compliance (WCAG AA).

Links to latest PRD: `docs/prds/prd-20250923.md`

## Architecture (Detailed)

### Topology (frameworks)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Browser Environment                               │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────┐  │
│  │   Service       │   State         │    UI Layer     │   Routing   │  │
│  │   Worker        │   Management    │   (React)       │  (React     │  │
│  │   (PWA)         │   (Zustand)     │                 │   Router)   │  │
│  └─────────────────┼─────────────────┼─────────────────┼─────────────┘  │
└──────────────────┬─┼─────────────────┼─────────────────┼─────────────────┘
                   │ │                 │                 │
┌──────────────────▼─▼─────────────────▼─────────────────▼─────────────────┐
│                      React Application                                  │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────┐  │
│  │     Pages       │   Components    │    Hooks        │   Utils     │  │
│  │  ┌───────────┐  │  ┌───────────┐  │  ┌───────────┐  │             │  │
│  │  │Dashboard  │  │  │ArtifactCard│  │  │useAuth    │  │             │  │
│  │  │Upload     │  │  │CVPreview  │  │  │useGenerate│  │             │  │
│  │  │Generate   │  │  │ExportBtn  │  │  │useUpload  │  │             │  │
│  │  │Profile    │  │  │...        │  │  │...        │  │             │  │
│  │  └───────────┘  │  └───────────┘  │  └───────────┘  │             │  │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────┘  │
└──────────────────┬─────────────────────────────────────────────────────┘
                   │ HTTP REST API
┌──────────────────▼─────────────────────────────────────────────────────┐
│                    API Client Layer                                    │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────┐ │
│  │   Axios         │    Auth         │    Cache        │   Error     │ │
│  │   Client        │   Interceptor   │   Manager       │  Handler    │ │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────┘ │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                      Build & Development Tools                            │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────┐   │
│  │      Vite       │   TypeScript    │     Tailwind    │   Testing   │   │
│  │   (Bundler)     │   (Type Safety) │      CSS        │  (Vitest)   │   │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘
```

### Component Inventory

| Component | Framework/Runtime | Purpose | Interfaces (in/out) | Depends On | Scale/HA | Owner |
|-----------|------------------|---------|-------------------|------------|----------|-------|
| React App | React 18 + Vite | Main SPA application | In: User interactions; Out: DOM updates, API calls | Zustand, React Router | CDN distributed | Frontend |
| State Manager | Zustand | Global state management | In: Actions; Out: State updates | React Context | Client-side only | Frontend |
| Router | React Router v6 | Client-side navigation | In: Route changes; Out: Component mounting | History API | Client-side only | Frontend |
| API Client | Axios + TypeScript | HTTP communication with backend | In: API requests; Out: HTTP calls to Django | Axios interceptors | Client-side, retry logic | Frontend |
| UI Components | React + TypeScript | Reusable UI elements | In: Props; Out: Rendered JSX | Tailwind CSS | Static, tree-shakeable | Frontend |
| Form Library | React Hook Form + Zod | Form validation and management | In: User input; Out: Validated data | Zod schemas | Client-side validation | Frontend |
| File Upload | React Dropzone | Drag-and-drop file uploads | In: File drops/selection; Out: File objects | HTML5 File API | Client-side processing | Frontend |
| Auth Guard | React + JWT | Route protection and auth state | In: Route access; Out: Redirect/render | Local storage, API client | Client-side security | Frontend |
| PWA Service Worker | Workbox | Offline capability, caching | In: Network requests; Out: Cached responses | Cache API | Browser-dependent | Frontend |
| Notification System | React Hot Toast | User feedback and alerts | In: Event triggers; Out: Toast notifications | React state | Client-side only | Frontend |

## Interfaces & Data Contracts

### Component API Contracts

#### Authentication Flow
```typescript
// Auth Hook Interface
interface UseAuthReturn {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (userData: RegisterData) => Promise<void>;
  refreshToken: () => Promise<void>;
}

// User Type
interface User {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  profile: UserProfile;
}
```

#### Artifact Management
```typescript
// Artifact Types
interface Artifact {
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

interface EvidenceLink {
  id: number;
  url: string;
  type: 'github' | 'live_app' | 'paper' | 'video' | 'other';
  description: string;
  validationStatus: 'pending' | 'valid' | 'invalid';
  lastValidated?: string;
}

// Upload Hook Interface
interface UseArtifactUploadReturn {
  uploadArtifact: (data: ArtifactCreateData) => Promise<Artifact>;
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
}
```

#### Generation System
```typescript
// Generation Types
interface CVGenerationRequest {
  jobDescription: string;
  companyName: string;
  roleTitle: string;
  labelIds: number[];
  templateId?: number;
  customSections?: Record<string, any>;
}

interface GeneratedDocument {
  id: number;
  type: 'cv' | 'cover_letter';
  status: 'processing' | 'completed' | 'failed';
  content?: DocumentContent;
  evidenceLinks: EvidenceReference[];
  createdAt: string;
  completedAt?: string;
  jobDescriptionHash: string;
}

// Generation Hook Interface
interface UseGenerationReturn {
  generateCV: (request: CVGenerationRequest) => Promise<string>; // returns generation ID
  generateCoverLetter: (request: CoverLetterRequest) => Promise<string>;
  pollGeneration: (id: string) => Promise<GeneratedDocument>;
  isGenerating: boolean;
  error: string | null;
}
```

### API Client Interface
```typescript
// API Client Service
class ApiClient {
  // Authentication
  async login(email: string, password: string): Promise<AuthResponse>;
  async register(userData: RegisterData): Promise<AuthResponse>;
  async refreshToken(): Promise<TokenResponse>;

  // Artifacts
  async getArtifacts(filters?: ArtifactFilters): Promise<PaginatedResponse<Artifact>>;
  async createArtifact(data: ArtifactCreateData): Promise<Artifact>;
  async updateArtifact(id: number, data: Partial<Artifact>): Promise<Artifact>;
  async deleteArtifact(id: number): Promise<void>;

  // Generation
  async generateCV(request: CVGenerationRequest): Promise<GenerationResponse>;
  async getGeneration(id: string): Promise<GeneratedDocument>;
  async exportDocument(id: string, format: 'pdf' | 'docx'): Promise<Blob>;

  // Labels and Skills
  async getLabels(): Promise<Label[]>;
  async createLabel(data: LabelCreateData): Promise<Label>;
  async suggestSkills(query: string): Promise<SkillSuggestion[]>;
}
```

## Data & Storage

### Client-Side State Management

#### Zustand Store Structure
```typescript
// Auth Store
interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setUser: (user: User) => void;
  setTokens: (access: string, refresh: string) => void;
  clearAuth: () => void;
}

// Artifact Store
interface ArtifactState {
  artifacts: Artifact[];
  selectedArtifacts: number[];
  filters: ArtifactFilters;
  isLoading: boolean;
  error: string | null;

  // Actions
  setArtifacts: (artifacts: Artifact[]) => void;
  addArtifact: (artifact: Artifact) => void;
  updateArtifact: (id: number, updates: Partial<Artifact>) => void;
  deleteArtifact: (id: number) => void;
  setFilters: (filters: ArtifactFilters) => void;
  toggleSelection: (id: number) => void;
}

// Generation Store
interface GenerationState {
  activeGenerations: Map<string, GeneratedDocument>;
  completedDocuments: GeneratedDocument[];
  isGenerating: boolean;

  // Actions
  startGeneration: (id: string, type: 'cv' | 'cover_letter') => void;
  updateGeneration: (id: string, document: GeneratedDocument) => void;
  completeGeneration: (id: string, document: GeneratedDocument) => void;
}
```

#### Local Storage Strategy
```typescript
// Persistent Storage Keys
const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_access_token',
  REFRESH_TOKEN: 'auth_refresh_token',
  USER_PREFERENCES: 'user_preferences',
  DRAFT_ARTIFACTS: 'draft_artifacts',
  RECENT_SEARCHES: 'recent_searches',
} as const;

// Storage Service
class StorageService {
  static setSecure(key: string, value: any): void {
    // Encrypt sensitive data before storage
    const encrypted = encrypt(JSON.stringify(value));
    localStorage.setItem(key, encrypted);
  }

  static getSecure(key: string): any {
    const encrypted = localStorage.getItem(key);
    if (!encrypted) return null;

    try {
      return JSON.parse(decrypt(encrypted));
    } catch {
      return null;
    }
  }
}
```

### Caching Strategy
```typescript
// API Response Caching
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in ms
}

class CacheManager {
  private cache = new Map<string, CacheEntry<any>>();

  set<T>(key: string, data: T, ttl: number = 300000): void { // 5 min default
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }
}
```

## Reliability & SLIs/SLOs

### Frontend Performance Metrics
- **First Contentful Paint (FCP):** ≤1.5s
- **Largest Contentful Paint (LCP):** ≤2.5s
- **First Input Delay (FID):** ≤100ms
- **Cumulative Layout Shift (CLS):** ≤0.1
- **Time to Interactive (TTI):** ≤3s

### Reliability Mechanisms
```typescript
// Error Boundary Component
class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to monitoring service
    logger.error('React Error Boundary', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack
    });
  }
}

// Network Retry Logic
const apiClientWithRetry = axios.create({
  timeout: 10000,
  retries: 3,
  retryDelay: (retryCount) => Math.pow(2, retryCount) * 1000, // Exponential backoff
});

// Offline Detection
const useOnlineStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
};
```

### Progressive Web App Features
```typescript
// Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration);
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}

// App Manifest
{
  "name": "CV Auto-Tailor",
  "short_name": "CVTailor",
  "description": "Generate targeted CVs with evidence",
  "theme_color": "#007bff",
  "background_color": "#ffffff",
  "display": "standalone",
  "start_url": "/",
  "icons": [
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

## Security & Privacy

### Client-Side Security
```typescript
// JWT Token Management
class TokenManager {
  private static readonly ACCESS_TOKEN_KEY = 'access_token';
  private static readonly REFRESH_TOKEN_KEY = 'refresh_token';

  static setTokens(accessToken: string, refreshToken: string): void {
    // Store in httpOnly cookies in production
    if (process.env.NODE_ENV === 'production') {
      // Use secure cookie storage
      document.cookie = `${this.ACCESS_TOKEN_KEY}=${accessToken}; Secure; SameSite=Strict`;
    } else {
      localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
      localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
    }
  }

  static getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }
}

// Input Sanitization
const sanitizeInput = (input: string): string => {
  return DOMPurify.sanitize(input, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: []
  });
};

// XSS Protection
const XSSProtectedTextarea: React.FC<Props> = ({ value, onChange }) => {
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const sanitized = sanitizeInput(e.target.value);
    onChange(sanitized);
  };

  return <textarea value={value} onChange={handleChange} />;
};
```

### Content Security Policy
```typescript
// CSP Headers (to be set by CDN/server)
const CSP_DIRECTIVES = {
  'default-src': "'self'",
  'script-src': "'self' 'unsafe-inline'", // Only for development
  'style-src': "'self' 'unsafe-inline'",
  'img-src': "'self' data: https:",
  'connect-src': "'self' https://api.cv-tailor.com",
  'font-src': "'self' https://fonts.gstatic.com",
  'frame-ancestors': "'none'",
  'base-uri': "'self'",
  'form-action': "'self'"
};
```

## Evaluation Plan

### Testing Strategy
```typescript
// Unit Tests with Vitest
describe('useArtifactUpload', () => {
  it('should upload artifact successfully', async () => {
    const { result } = renderHook(() => useArtifactUpload());

    const artifactData = {
      title: 'Test Project',
      description: 'Test description',
      technologies: ['React', 'TypeScript']
    };

    await act(async () => {
      await result.current.uploadArtifact(artifactData);
    });

    expect(result.current.isUploading).toBe(false);
    expect(result.current.error).toBeNull();
  });
});

// Integration Tests with Testing Library
describe('CV Generation Flow', () => {
  it('should generate CV from uploaded artifacts', async () => {
    render(<App />);

    // Upload artifact
    const fileInput = screen.getByLabelText(/upload/i);
    const file = new File(['content'], 'resume.pdf', { type: 'application/pdf' });
    fireEvent.change(fileInput, { target: { files: [file] } });

    // Generate CV
    const generateButton = await screen.findByRole('button', { name: /generate cv/i });
    fireEvent.click(generateButton);

    // Verify result
    expect(await screen.findByText(/cv generated/i)).toBeInTheDocument();
  });
});

// E2E Tests with Playwright
test('complete user journey', async ({ page }) => {
  await page.goto('/');

  // Login
  await page.fill('[data-testid="email"]', 'test@example.com');
  await page.fill('[data-testid="password"]', 'password');
  await page.click('[data-testid="login"]');

  // Upload artifact
  await page.setInputFiles('[data-testid="file-upload"]', 'test-files/sample.pdf');
  await page.click('[data-testid="upload-submit"]');

  // Generate CV
  await page.fill('[data-testid="job-description"]', 'Software Engineer position...');
  await page.click('[data-testid="generate-cv"]');

  // Download export
  await page.waitForSelector('[data-testid="download-pdf"]');
  await page.click('[data-testid="download-pdf"]');
});
```

### Performance Testing
```typescript
// Bundle Size Analysis
import { defineConfig } from 'vite';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    visualizer({
      filename: 'dist/stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        },
      },
    },
  },
});

// Lighthouse CI Configuration
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000'],
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],
      },
    },
  },
};
```

## Rollout & Ops Impact

### Feature Flags Frontend Integration
```typescript
// Feature Flag Hook
const useFeatureFlag = (flagName: string): boolean => {
  const [isEnabled, setIsEnabled] = useState(false);

  useEffect(() => {
    // Check feature flag from API or local config
    apiClient.getFeatureFlag(flagName)
      .then(setIsEnabled)
      .catch(() => setIsEnabled(false));
  }, [flagName]);

  return isEnabled;
};

// Conditional Rendering
const CVGenerationPage: React.FC = () => {
  const isCoverLetterEnabled = useFeatureFlag('frontend.cover_letter.enabled');

  return (
    <div>
      <CVGenerationForm />
      {isCoverLetterEnabled && <CoverLetterSection />}
    </div>
  );
};
```

### Analytics Integration
```typescript
// Analytics Service
class AnalyticsService {
  static track(event: string, properties?: Record<string, any>): void {
    // Google Analytics 4
    gtag('event', event, {
      custom_properties: properties,
      user_id: getCurrentUserId(),
    });

    // Custom analytics
    fetch('/api/analytics/track', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event,
        properties,
        timestamp: Date.now(),
        user_agent: navigator.userAgent,
      }),
    });
  }

  static page(pageName: string): void {
    gtag('config', 'GA_MEASUREMENT_ID', {
      page_title: pageName,
      page_location: window.location.href,
    });
  }
}

// Usage in Components
const ArtifactUpload: React.FC = () => {
  const handleUpload = (artifact: Artifact) => {
    AnalyticsService.track('artifact_uploaded', {
      artifact_type: artifact.type,
      technologies: artifact.technologies,
      evidence_count: artifact.evidenceLinks.length,
    });
  };
};
```

### Deployment Configuration
```typescript
// Environment Configuration
interface Config {
  apiBaseUrl: string;
  sentryDsn: string;
  googleAnalyticsId: string;
  featureFlagsUrl: string;
  maxFileSize: number;
  supportedFileTypes: string[];
}

const getConfig = (): Config => {
  const env = process.env.NODE_ENV || 'development';

  const configs: Record<string, Config> = {
    development: {
      apiBaseUrl: 'http://localhost:8000',
      sentryDsn: '',
      googleAnalyticsId: '',
      featureFlagsUrl: 'http://localhost:8000/api/feature-flags',
      maxFileSize: 10 * 1024 * 1024, // 10MB
      supportedFileTypes: ['.pdf', '.doc', '.docx'],
    },
    production: {
      apiBaseUrl: 'https://api.cv-tailor.com',
      sentryDsn: process.env.VITE_SENTRY_DSN!,
      googleAnalyticsId: process.env.VITE_GA_ID!,
      featureFlagsUrl: 'https://api.cv-tailor.com/api/feature-flags',
      maxFileSize: 10 * 1024 * 1024,
      supportedFileTypes: ['.pdf', '.doc', '.docx'],
    },
  };

  return configs[env];
};
```

## Risks & Rollback

### Frontend-Specific Risks
1. **Bundle Size Growth**
   - Risk: Large dependencies increase load time
   - Detection: Bundle analyzer, lighthouse CI
   - Mitigation: Code splitting, tree shaking, lazy loading
   - Rollback: Remove heavy dependencies, revert to lighter alternatives

2. **Browser Compatibility Issues**
   - Risk: Modern JS features break in older browsers
   - Detection: BrowserStack testing, error monitoring
   - Mitigation: Polyfills, transpilation, progressive enhancement
   - Rollback: Target lower ES version, add more polyfills

3. **State Management Complexity**
   - Risk: Complex state leads to bugs and performance issues
   - Detection: React DevTools, performance profiling
   - Mitigation: State normalization, memoization, code splitting
   - Rollback: Simplify state structure, remove complex computations

### Deployment Rollback Strategy
```typescript
// Blue-Green Deployment Support
const VersionCheck: React.FC = () => {
  const [isOutdated, setIsOutdated] = useState(false);

  useEffect(() => {
    // Check if current version is outdated
    fetch('/api/version')
      .then(res => res.json())
      .then(({ latest_version }) => {
        const currentVersion = process.env.VITE_APP_VERSION;
        setIsOutdated(currentVersion !== latest_version);
      });
  }, []);

  if (isOutdated) {
    return (
      <div className="update-banner">
        A new version is available.
        <button onClick={() => window.location.reload()}>
          Refresh to update
        </button>
      </div>
    );
  }

  return null;
};
```

## Open Questions

1. **Offline Support Scope:** Full offline editing vs read-only cached data
2. **Real-time Updates:** WebSocket integration for generation progress
3. **Mobile App Strategy:** PWA vs native mobile application
4. **Internationalization:** Multi-language support priority and scope
5. **Accessibility Standards:** WCAG AA vs AAA compliance requirements

## Changelog

- 2025-09-23: Draft created; React architecture defined; state management strategy established; component structure planned; security patterns implemented