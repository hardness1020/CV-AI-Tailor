# Technical Specification: Google Authentication System Integration

**Document ID:** SPEC-20250924-SYSTEM
**Date:** 2024-09-24
**Status:** Draft
**Author:** Claude Code
**Related PRD:** PRD-20250924

## Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend (React)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Auth Pages    │  │  Google Sign-In │  │   Auth Store    │ │
│  │  (Login/Reg)    │  │   Components    │  │   (Zustand)     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│           │                     │                     │         │
│           └─────────────────────┼─────────────────────┘         │
│                                 │                               │
├─────────────────────────────────┼───────────────────────────────┤
│                          API Client                             │
│                                 │                               │
└─────────────────────────────────┼───────────────────────────────┘
                                  │ HTTPS
┌─────────────────────────────────┼───────────────────────────────┐
│                          Django Backend                         │
├─────────────────────────────────┼───────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Django-Allauth  │  │   Custom Views  │  │   JWT Tokens    │ │
│  │  Google Provider│  │  (Auth Logic)   │  │   Management    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│           │                     │                     │         │
│           └─────────────────────┼─────────────────────┘         │
│                                 │                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    User Model                               │ │
│  │              (Extended AbstractUser)                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┼───────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                 Google OAuth 2.0                  │
        │                    Services                       │
        └───────────────────────────────────────────────────┘
```

### Component Inventory

| Component | Framework | Purpose | Dependencies |
|-----------|-----------|---------|--------------|
| **Frontend Auth UI** | React + TypeScript | User authentication interface | Google Identity Services, Zustand |
| **Django-Allauth** | Django | OAuth provider integration | requests, django, oauthlib |
| **JWT Authentication** | DRF SimpleJWT | Token management | PyJWT, djangorestframework |
| **Google OAuth Client** | JavaScript SDK | Frontend Google sign-in | google-auth-library |
| **User Model** | Django ORM | User data persistence | PostgreSQL/SQLite |
| **API Client** | Axios | HTTP communication | axios, interceptors |

## Technical Implementation

### Backend Architecture

#### Django-Allauth Integration

```python
# settings.py additions
INSTALLED_APPS = [
    # existing apps...
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'
```

#### Custom Social Account Adapter

```python
# accounts/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """Handle user linking and JWT token generation."""
        user = sociallogin.user
        if user.id:
            return

        try:
            # Check if user with email already exists
            existing_user = User.objects.get(email=user.email)
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """Custom user creation with profile data from Google."""
        user = super().save_user(request, sociallogin, form)
        extra_data = sociallogin.account.extra_data

        # Populate profile fields from Google data
        if 'name' in extra_data:
            names = extra_data['name'].split(' ', 1)
            user.first_name = names[0]
            user.last_name = names[1] if len(names) > 1 else ''

        if 'picture' in extra_data:
            # Handle profile image URL
            pass

        user.save()
        return user
```

#### API Endpoints

```python
# accounts/views.py
from allauth.socialaccount.models import SocialToken
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def google_auth(request):
    """
    Exchange Google OAuth token for JWT tokens.
    Expects: { "access_token": "google_oauth_token" }
    Returns: { "access": "jwt_access", "refresh": "jwt_refresh", "user": {...} }
    """
    google_token = request.data.get('access_token')
    if not google_token:
        return Response({'error': 'Google access token required'},
                       status=status.HTTP_400_BAD_REQUEST)

    try:
        # Verify Google token and get user info
        google_user_info = verify_google_token(google_token)
        user, created = get_or_create_user_from_google(google_user_info)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data,
            'created': created
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def verify_google_token(token):
    """Verify Google OAuth token and return user info."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        return idinfo
    except ValueError as e:
        raise ValueError(f'Invalid Google token: {e}')
```

### Frontend Architecture

#### Google Sign-In Integration

```typescript
// services/googleAuth.ts
import { GoogleAuth } from 'google-auth-library';

interface GoogleSignInResponse {
  credential: string;
  select_by: string;
}

export class GoogleAuthService {
  private client_id: string;

  constructor() {
    this.client_id = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  }

  async initializeGoogleSignIn(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (typeof window === 'undefined' || !window.google) {
        reject(new Error('Google Identity Services not loaded'));
        return;
      }

      window.google.accounts.id.initialize({
        client_id: this.client_id,
        callback: this.handleGoogleSignIn,
        auto_select: false,
        cancel_on_tap_outside: false,
      });

      resolve();
    });
  }

  async signInWithGoogle(): Promise<GoogleSignInResponse> {
    return new Promise((resolve, reject) => {
      window.google.accounts.id.prompt((notification: any) => {
        if (notification.isNotDisplayed()) {
          reject(new Error('Google Sign-In not available'));
        }
      });
    });
  }

  private handleGoogleSignIn = async (response: GoogleSignInResponse) => {
    try {
      // Send credential to backend
      const result = await apiClient.post('/auth/google/', {
        credential: response.credential
      });

      // Update auth store
      const { access, refresh, user } = result.data;
      useAuthStore.getState().setTokens(access, refresh);
      useAuthStore.getState().setUser(user);

    } catch (error) {
      console.error('Google sign-in error:', error);
      throw error;
    }
  };
}
```

#### React Components

```tsx
// components/GoogleSignInButton.tsx
import React from 'react';
import { GoogleAuthService } from '@/services/googleAuth';

interface GoogleSignInButtonProps {
  onSuccess?: (user: User) => void;
  onError?: (error: Error) => void;
  disabled?: boolean;
}

export const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  onSuccess,
  onError,
  disabled = false
}) => {
  const googleAuthService = new GoogleAuthService();

  const handleGoogleSignIn = async () => {
    try {
      await googleAuthService.signInWithGoogle();
      // Success handled in service callback
      onSuccess?.(useAuthStore.getState().user!);
    } catch (error) {
      onError?.(error as Error);
    }
  };

  return (
    <button
      type="button"
      onClick={handleGoogleSignIn}
      disabled={disabled}
      className="flex items-center justify-center w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
    >
      <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
        {/* Google logo SVG */}
      </svg>
      Continue with Google
    </button>
  );
};
```

## Database Schema Changes

### User Model Extensions

```python
# accounts/models.py - No changes required
# Existing User model already supports social authentication
# Social account data handled by django-allauth models:
# - SocialAccount
# - SocialApp
# - SocialToken
```

### Migration Strategy

```python
# accounts/migrations/0002_add_social_auth.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('socialaccount', '0001_initial'),  # django-allauth migration
    ]

    operations = [
        # No custom operations needed
        # django-allauth handles social account tables
    ]
```

## Security Considerations

### OAuth 2.0 Security

1. **PKCE Implementation**: Enabled in settings to prevent authorization code interception
2. **Token Validation**: Server-side validation of Google ID tokens
3. **Secure Storage**: JWT tokens stored in httpOnly cookies (consideration)
4. **CSRF Protection**: Maintained for all non-OAuth endpoints

### Data Privacy

```python
# Privacy compliance settings
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_STORE_TOKENS = False  # Don't store OAuth tokens long-term
```

## API Specification

### Authentication Endpoints

```yaml
# OpenAPI spec excerpt
paths:
  /api/auth/google/:
    post:
      summary: Authenticate with Google OAuth
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                credential:
                  type: string
                  description: Google ID token
              required:
                - credential
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  access:
                    type: string
                  refresh:
                    type: string
                  user:
                    $ref: '#/components/schemas/User'
                  created:
                    type: boolean
        400:
          description: Invalid credentials
```

## Performance Requirements

### Load Testing Scenarios

1. **Concurrent Google Sign-ins**: 100 simultaneous OAuth flows
2. **Token Refresh Rate**: 1000 token refreshes per minute
3. **Database Query Optimization**: < 50ms user lookup time

### Caching Strategy

```python
# Cache user profile data
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'cvtailor',
        'TIMEOUT': 300,  # 5 minutes
    }
}
```

## Error Handling

### Frontend Error States

```typescript
// Error handling types
interface GoogleAuthError {
  type: 'GOOGLE_UNAVAILABLE' | 'TOKEN_INVALID' | 'USER_CANCELLED' | 'NETWORK_ERROR';
  message: string;
  recoverable: boolean;
}

// Error recovery strategies
const handleGoogleAuthError = (error: GoogleAuthError) => {
  switch (error.type) {
    case 'GOOGLE_UNAVAILABLE':
      // Show fallback login form
      break;
    case 'USER_CANCELLED':
      // Silent fail, no action needed
      break;
    case 'TOKEN_INVALID':
      // Retry authentication flow
      break;
    case 'NETWORK_ERROR':
      // Show retry button
      break;
  }
};
```

### Backend Error Responses

```python
# Standardized error responses
class GoogleAuthError(Exception):
    """Google authentication related errors."""
    pass

@api_view(['POST'])
def google_auth(request):
    try:
        # Authentication logic
        pass
    except GoogleAuthError as e:
        return Response({
            'error': 'google_auth_failed',
            'message': str(e),
            'recoverable': True
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f'Unexpected Google auth error: {e}')
        return Response({
            'error': 'internal_error',
            'message': 'Authentication service temporarily unavailable'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

## Testing Strategy

### Unit Tests

```python
# tests/test_google_auth.py
class GoogleAuthTestCase(TestCase):
    def test_valid_google_token_creates_user(self):
        """Test user creation from valid Google token."""
        pass

    def test_existing_user_login_with_google(self):
        """Test existing user can link Google account."""
        pass

    def test_invalid_token_rejection(self):
        """Test invalid Google tokens are rejected."""
        pass
```

### Integration Tests

```typescript
// __tests__/googleAuth.integration.test.ts
describe('Google Authentication Flow', () => {
  it('should complete full OAuth flow', async () => {
    // Mock Google sign-in
    // Verify API calls
    // Check auth state updates
  });

  it('should handle authentication errors gracefully', async () => {
    // Test error scenarios
  });
});
```

## Deployment Considerations

### Environment Variables

```bash
# .env additions
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback/
```

### Production Configuration

```python
# Production settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_AUTO_SIGNUP = True
```