# Tech Spec — Frontend (Updated with Authentication)

**Version:** v2.0.0
**File:** docs/specs/spec-20250923-frontend-v2.md
**Status:** Current
**PRD:** `prd-20250923.md`
**Contract Versions:** Frontend v2.0 • API Client v2.0 • Component Library v2.0
**Supersedes:** `spec-20250923-frontend.md`

## Overview & Goals

Build a modern, responsive React SPA frontend with comprehensive JWT authentication that provides an intuitive interface for user registration, login, profile management, artifact upload, job description input, CV/cover letter generation, and document export. Target sub-200ms UI interactions, mobile-responsive design, and accessibility compliance (WCAG AA).

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
│  │                 │   + Auth Store  │                 │ + Protected │  │
│  └─────────────────┼─────────────────┼─────────────────┼─────────────┘  │
└──────────────────┬─┼─────────────────┼─────────────────┼─────────────────┘
                   │ │                 │                 │
┌──────────────────▼─▼─────────────────▼─────────────────▼─────────────────┐
│                      React Application                                  │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────┐  │
│  │     Pages       │   Components    │    Hooks        │   Utils     │  │
│  │  ┌───────────┐  │  ┌───────────┐  │  ┌───────────┐  │             │  │
│  │  │Login      │  │  │AuthGuard  │  │  │useAuth    │  │             │  │
│  │  │Register   │  │  │ArtifactCard│  │  │useGenerate│  │             │  │
│  │  │Dashboard  │  │  │CVPreview  │  │  │useUpload  │  │             │  │
│  │  │Profile    │  │  │ExportBtn  │  │  │useProfile │  │             │  │
│  │  │Upload     │  │  │UserMenu   │  │  │...        │  │             │  │
│  │  │Generate   │  │  │...        │  │  │           │  │             │  │
│  │  └───────────┘  │  └───────────┘  │  └───────────┘  │             │  │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────┘  │
└──────────────────┬─────────────────────────────────────────────────────┘
                   │ HTTP REST API + JWT Tokens
┌──────────────────▼─────────────────────────────────────────────────────┐
│                    API Client Layer                                    │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────┐ │
│  │   Axios         │    JWT Auth     │    Cache        │   Error     │ │
│  │   Client        │   Interceptor   │   Manager       │  Handler    │ │
│  │                 │ + Token Refresh │                 │ + Auth Retry│ │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────┘ │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                           Build System                                   │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────┐  │
│  │     Vite        │   TypeScript    │      ESLint     │  Prettier   │  │
│  │   (Dev Server   │   (Type Safety  │   (Code Quality │  (Code      │  │
│  │   + HMR)        │   + Validation) │   + Standards)  │   Format)   │  │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

### Component Inventory

| Component | Framework/Runtime | Purpose | Interfaces (in/out) | Depends On | Scale/HA | Owner |
|-----------|------------------|---------|-------------------|------------|----------|-------|
| React App | React 18 + Vite | Main application shell | In: User interactions; Out: API calls, DOM updates | State stores, Router | Client-side, stateless | Frontend |
| Authentication System | React + Zustand + JWT | User auth state management | In: Login/logout events; Out: API auth headers | Auth API, Local storage | Client-side, persistent | Frontend |
| Routing System | React Router v6 | SPA navigation with auth guards | In: URL changes; Out: Component rendering | Auth store, Route guards | Client-side, stateless | Frontend |
| State Management | Zustand | Global app state (auth, user, app data) | In: Actions; Out: State updates | React context, Persist middleware | Client-side, persistent | Frontend |
| API Client | Axios + Interceptors | HTTP client with auto auth | In: API calls; Out: HTTP requests with JWT headers | Auth store, Error handling | Client-side, stateless | Frontend |
| Form System | React Hook Form + Zod | Form validation and submission | In: User input; Out: Validated data, Error states | Validation schemas | Client-side, stateless | Frontend |
| UI Components | Custom React + Tailwind | Reusable interface elements | In: Props; Out: Rendered components | Design system, Icons | Client-side, stateless | Frontend |
| Auth Guards | React HOC/Components | Route protection and redirects | In: User auth state; Out: Conditional rendering | Auth store, Router | Client-side, stateless | Frontend |
| Error Boundaries | React Error Boundary | Error handling and recovery | In: Component errors; Out: Error UI, Logging | Error reporting service | Client-side, stateless | Frontend |
| PWA Service Worker | Service Worker API | Offline support and caching | In: Network requests; Out: Cache responses | Browser APIs, Cache API | Client-side, persistent | Frontend |

## Authentication Integration

### Authentication State Management

```typescript
// Auth Store Implementation (Zustand)
interface AuthState {
  // State
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean

  // Actions
  setUser: (user: User) => void
  setTokens: (access: string, refresh: string) => void
  clearAuth: () => void
  updateProfile: (updates: Partial<User>) => void
}

// Authentication Hook
export const useAuth = () => {
  const {
    user,
    isAuthenticated,
    setUser,
    setTokens,
    clearAuth,
    updateProfile
  } = useAuthStore()

  const login = async (email: string, password: string) => {
    const response = await apiClient.login(email, password)
    setUser(response.user)
    setTokens(response.access, response.refresh)
  }

  const logout = async () => {
    try {
      await apiClient.logout()
    } finally {
      clearAuth()
    }
  }

  const register = async (userData: RegisterData) => {
    const response = await apiClient.register(userData)
    setUser(response.user)
    setTokens(response.access, response.refresh)
  }

  return {
    user,
    isAuthenticated,
    login,
    logout,
    register,
    updateProfile
  }
}
```

### Dashboard-First Navigation Design

The application implements a dashboard-first approach where users can immediately see the main interface:

#### Navigation Strategy
- **Default Route**: Root path (`/`) shows dashboard directly to all users
- **Public Dashboard View**: Dashboard displays with login button in top-right corner
- **Progressive Authentication**: Users can explore the interface before being prompted to login
- **Protected Action Gating**: Specific actions require authentication, triggering login modal or redirect

#### User Experience Flow
1. **Initial Visit**: `www.app.com/` → immediately shows dashboard interface
2. **Feature Discovery**: User can see dashboard layout and available features
3. **Protected Action**: Click protected features (Generate CV, Upload Artifacts) → prompt for login
4. **Authentication**: User clicks login button → modal or redirect to login page
5. **Post-Authentication**: After login → return to dashboard with full access

#### Implementation Pattern
```typescript
// Dashboard-first routing configuration
<Route path="/" element={<DashboardPage />} />
<Route path="/login" element={<LoginPage />} />

// Dashboard with conditional authentication
const DashboardPage = () => {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen">
      <nav className="flex justify-between items-center p-4">
        <Logo />
        {!isAuthenticated && <LoginButton />}
        {isAuthenticated && <UserMenu />}
      </nav>
      <DashboardContent showProtectedFeatures={isAuthenticated} />
    </div>
  )
}
```

### Route Protection System

```typescript
// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode
  requireAuth?: boolean
  redirectTo?: string
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAuth = true,
  redirectTo = '/login'
}) => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (requireAuth && !isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  if (!requireAuth && isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}

// Router Configuration with Auth Guards
export const AppRouter = () => (
  <BrowserRouter>
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={
        <ProtectedRoute requireAuth={false}>
          <LoginPage />
        </ProtectedRoute>
      } />
      <Route path="/register" element={
        <ProtectedRoute requireAuth={false}>
          <RegisterPage />
        </ProtectedRoute>
      } />

      {/* Protected Routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <DashboardPage />
        </ProtectedRoute>
      } />
      <Route path="/profile" element={
        <ProtectedRoute>
          <ProfilePage />
        </ProtectedRoute>
      } />

      {/* Default Route - Dashboard-First Approach */}
      <Route path="/" element={<DashboardPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  </BrowserRouter>
)
```

### API Client with Authentication

```typescript
// Enhanced API Client with JWT Authentication
class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = useAuthStore.getState().accessToken
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const refreshToken = useAuthStore.getState().refreshToken
            if (refreshToken) {
              const response = await this.refreshToken()
              useAuthStore.getState().setTokens(response.access, response.refresh)
              return this.client(originalRequest)
            }
          } catch (refreshError) {
            useAuthStore.getState().clearAuth()
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        }

        // Show error toast for user-facing errors
        if (error.response?.status >= 400 && error.response?.status < 500) {
          const message = error.response?.data?.message || 'An error occurred'
          toast.error(message)
        }

        return Promise.reject(error)
      }
    )
  }

  // Authentication Methods
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/v1/auth/login/', {
      email,
      password,
    })
    return response.data
  }

  async register(userData: RegisterData): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/v1/auth/register/', userData)
    return response.data
  }

  async refreshToken(): Promise<{ access: string; refresh: string }> {
    const refreshToken = useAuthStore.getState().refreshToken
    const response = await this.client.post<{ access: string; refresh: string }>(
      '/v1/auth/token/refresh/',
      { refresh: refreshToken }
    )
    return response.data
  }

  async logout(): Promise<void> {
    const refreshToken = useAuthStore.getState().refreshToken
    try {
      await this.client.post('/v1/auth/logout/', { refresh: refreshToken })
    } catch (error) {
      console.warn('Logout request failed:', error)
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/v1/auth/profile/')
    return response.data
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await this.client.patch<User>('/v1/auth/profile/', data)
    return response.data
  }

  async changePassword(data: {
    current_password: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<void> {
    await this.client.post('/v1/auth/change-password/', data)
  }

  async requestPasswordReset(email: string): Promise<void> {
    await this.client.post('/v1/auth/password-reset/', { email })
  }
}
```

## User Interface Components

### Authentication Forms

#### Registration Form Component
```typescript
// Registration Form with Validation
export const RegisterForm: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()
  const { register: registerUser } = useAuth()

  const form = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true)
    try {
      const { confirmPassword, firstName, lastName, ...formData } = data
      const registerData = {
        ...formData,
        first_name: firstName,
        last_name: lastName,
        password_confirm: confirmPassword,
      }

      await registerUser(registerData)
      toast.success('Account created successfully!')
      navigate('/dashboard', { replace: true })
    } catch (error: any) {
      // Enhanced error handling with specific API error messages
      if (error.response?.data) {
        const errorData = error.response.data
        if (errorData.email) {
          toast.error(`Email: ${errorData.email[0]}`)
        } else if (errorData.username) {
          toast.error(`Username: ${errorData.username[0]}`)
        } else if (errorData.password) {
          toast.error(`Password: ${errorData.password[0]}`)
        } else {
          toast.error('Failed to create account. Please check your information.')
        }
      } else {
        toast.error('Failed to create account. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* Form fields with validation */}
      <Input
        {...form.register('firstName')}
        label="First Name"
        error={form.formState.errors.firstName?.message}
        required
      />
      <Input
        {...form.register('lastName')}
        label="Last Name"
        error={form.formState.errors.lastName?.message}
        required
      />
      <Input
        {...form.register('username')}
        label="Username"
        error={form.formState.errors.username?.message}
        required
      />
      <Input
        {...form.register('email')}
        type="email"
        label="Email"
        error={form.formState.errors.email?.message}
        required
      />
      <PasswordInput
        {...form.register('password')}
        label="Password"
        error={form.formState.errors.password?.message}
        required
      />
      <PasswordInput
        {...form.register('confirmPassword')}
        label="Confirm Password"
        error={form.formState.errors.confirmPassword?.message}
        required
      />

      <Button
        type="submit"
        loading={isLoading}
        disabled={!form.formState.isValid}
        fullWidth
      >
        Create Account
      </Button>
    </form>
  )
}
```

#### Login Form Component
```typescript
// Login Form with Enhanced Error Handling
export const LoginForm: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuth()

  const form = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true)
    try {
      await login(data.email, data.password)
      toast.success('Welcome back!')
      navigate('/dashboard', { replace: true })
    } catch (error: any) {
      if (error.response?.status === 400) {
        toast.error('Invalid email or password')
      } else {
        toast.error('Login failed. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <Input
        {...form.register('email')}
        type="email"
        label="Email"
        error={form.formState.errors.email?.message}
        required
      />
      <PasswordInput
        {...form.register('password')}
        label="Password"
        error={form.formState.errors.password?.message}
        required
      />

      <Button
        type="submit"
        loading={isLoading}
        disabled={!form.formState.isValid}
        fullWidth
      >
        Sign In
      </Button>

      <div className="text-center mt-4">
        <Link to="/register" className="text-blue-600 hover:text-blue-500">
          Don't have an account? Sign up
        </Link>
      </div>
    </form>
  )
}
```

### User Interface Navigation

#### User Menu Component
```typescript
// User Menu with Profile and Logout
export const UserMenu: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await logout()
      toast.success('Logged out successfully')
      navigate('/login')
    } catch (error) {
      toast.error('Logout failed')
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <Avatar className="h-8 w-8">
            <AvatarImage src={user?.profile_image} alt={user?.first_name} />
            <AvatarFallback>
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-xs leading-none text-muted-foreground">
              {user?.email}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => navigate('/profile')}>
          <User className="mr-2 h-4 w-4" />
          <span>Profile</span>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => navigate('/settings')}>
          <Settings className="mr-2 h-4 w-4" />
          <span>Settings</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

## TypeScript Types & Interfaces

### Authentication Types
```typescript
// Core Authentication Types
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

export interface LoginData {
  email: string;
  password: string;
}

// Form Validation Schemas
export const registerSchema = z.object({
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

export const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})
```

## Performance & Optimization

### Authentication Performance
- **Token Storage**: Secure storage in memory + httpOnly cookies for refresh tokens
- **Automatic Refresh**: Background token refresh without user interruption
- **Route-Based Code Splitting**: Lazy load authenticated vs public components
- **State Persistence**: Zustand persist middleware for authentication state
- **Optimistic Updates**: Immediate UI feedback for authentication actions

### Bundle Optimization
```typescript
// Lazy Loading for Authentication Pages
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))

// Route-based code splitting
export const AppRouter = () => (
  <BrowserRouter>
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        } />
      </Routes>
    </Suspense>
  </BrowserRouter>
)
```

## Testing Strategy

### Authentication Testing
```typescript
// Authentication Hook Testing
describe('useAuth', () => {
  test('should handle login flow', async () => {
    const { result } = renderHook(() => useAuth())

    await act(async () => {
      await result.current.login('test@example.com', 'password123')
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user).toMatchObject({
      email: 'test@example.com'
    })
  })

  test('should handle logout flow', async () => {
    const { result } = renderHook(() => useAuth())

    // Setup authenticated state
    await act(async () => {
      await result.current.login('test@example.com', 'password123')
    })

    // Test logout
    await act(async () => {
      await result.current.logout()
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBeNull()
  })
})

// Protected Route Testing
describe('ProtectedRoute', () => {
  test('should redirect unauthenticated users to login', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </MemoryRouter>
    )

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    // Should redirect to login
  })

  test('should render content for authenticated users', () => {
    // Mock authenticated state
    useAuthStore.setState({
      isAuthenticated: true,
      user: mockUser
    })

    render(
      <MemoryRouter>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </MemoryRouter>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })
})
```

## Security Implementation

### Client-Side Security
- **Token Storage**: Access tokens in memory, refresh tokens in httpOnly cookies
- **CSRF Protection**: CSRF tokens for sensitive operations
- **XSS Prevention**: Sanitized user inputs, CSP headers
- **Route Guards**: Client-side authentication checks with server validation
- **Automatic Logout**: Token expiration handling and forced logout

### Error Handling & Recovery
```typescript
// Global Error Boundary for Authentication
export class AuthErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log authentication errors
    console.error('Authentication error:', error, errorInfo)

    // Clear potentially corrupted auth state
    if (error.message.includes('auth') || error.message.includes('token')) {
      useAuthStore.getState().clearAuth()
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-2">Authentication Error</h2>
            <p className="text-gray-600 mb-4">
              There was a problem with your session. Please log in again.
            </p>
            <Button onClick={() => window.location.href = '/login'}>
              Go to Login
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
```

## Changes from Previous Version

### New Features (v2.0.0)
1. **Complete Authentication System**: Registration, login, logout, profile management
2. **Dashboard-First User Experience**: Dashboard as default route with progressive authentication
3. **JWT Token Management**: Automatic refresh, secure storage, blacklisting support
4. **Progressive Authentication**: Users can explore interface before login requirement
5. **Enhanced State Management**: Authentication state with persistence
6. **Form Validation**: Comprehensive validation with user-friendly error messages
7. **User Profile Management**: Profile viewing, editing, and preference management
7. **Security Enhancements**: Token rotation, automatic logout, error boundaries

### Component Updates
1. **New Pages**: LoginPage, RegisterPage, ProfilePage with comprehensive forms
2. **New Components**: UserMenu, AuthGuard, PasswordInput, Avatar components
3. **Enhanced API Client**: JWT authentication interceptors with automatic token refresh
4. **Updated Navigation**: User authentication state integration

### Architecture Changes
1. **Authentication-First Design**: All routes and components auth-aware
2. **Enhanced Error Handling**: Authentication-specific error boundaries and recovery
3. **Performance Optimization**: Route-based code splitting for auth vs public content
4. **Type Safety**: Comprehensive TypeScript types for all authentication flows

## Deployment & Operations

### Build Configuration
```typescript
// Vite configuration with authentication optimizations
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          auth: ['@/stores/authStore', '@/services/apiClient'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        },
      },
    },
  },
})
```

### Environment Configuration
```bash
# Development Environment Variables
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_TITLE=CV Tailor
VITE_ENABLE_AUTH_DEBUG=true

# Production Environment Variables
VITE_API_BASE_URL=https://api.cvtailor.com/api
VITE_APP_TITLE=CV Tailor
VITE_ENABLE_AUTH_DEBUG=false
```

## Monitoring & Analytics

### Authentication Metrics
- **Registration Conversion Rate**: Users completing registration flow
- **Login Success Rate**: Successful vs failed login attempts
- **Session Duration**: Average authenticated session length
- **Token Refresh Rate**: Automatic token refresh frequency
- **Error Rates**: Authentication-related error occurrences

### User Experience Metrics
- **Form Completion Time**: Time to complete registration/login
- **Error Recovery Rate**: Users successfully recovering from auth errors
- **Profile Update Frequency**: User engagement with profile management
- **Feature Adoption**: Usage of authentication-gated features

## Changelog

- **2025-09-23**: v2.0.0 - Complete authentication system implementation
  - Added comprehensive JWT authentication with token management
  - Implemented user registration, login, logout, and profile management
  - Added protected routing and authentication guards
  - Enhanced API client with automatic token refresh
  - Added comprehensive form validation and error handling
  - Implemented user menu and profile management interfaces
  - Added authentication state persistence and security measures
  - Updated component architecture for authentication-first design

- **2025-09-23**: v1.0.0 - Initial frontend specification (superseded)