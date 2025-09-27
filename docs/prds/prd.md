# PRD — CV & Cover-Letter Auto-Tailor

**Version:** v1.1.0
**File:** docs/prds/prd.md
**Owners:** Product (TBD), Engineering (TBD)
**Last_updated:** 2025-09-27

## Summary

Upload your work once with proof. For any job description + company, the app assembles a targeted, ATS-friendly CV and cover letter with quantified, defensible achievement bullets—grounded by linked evidence. Targeting job seekers from students to senior engineers/PMs/DS who need credible, consistent, reusable career documents with seamless authentication and comprehensive artifact management.

## Problem & Context

**Problem:** Tailoring CVs is slow, error-prone, and often unsubstantiated. Job seekers repeat vague claims that don't map tightly to job descriptions and fail automated ATS screens, leading to missed opportunities and prolonged job searches. Additionally, traditional authentication creates friction, and inflexible artifact management prevents users from maintaining accurate, up-to-date portfolios.

**Why now:** LLMs can parse job descriptions, map skills, and write strong bullets—but they need trusted, structured inputs and verifiable evidence to produce credible, consistent outputs that pass both ATS systems and human review. Modern users expect seamless social authentication and flexible content management.

**Evidence:** Manual CV tailoring takes 2-4 hours per application; 75% of resumes are filtered by ATS before human review; unsubstantiated claims reduce credibility with hiring managers; traditional registration creates 30-40% abandonment rates; users require artifact editing capabilities for portfolio maintenance.

## Users & Use Cases

**Primary persona:** Job seekers (student → senior engineer/PM/DS) actively applying for roles

**Key jobs-to-be-done:**
1. "Show me the best version of my CV for this role at this company, grounded in my real work"
2. "Draft a concise, specific cover letter that cites relevant proof"
3. "Keep versions for different roles without duplicating effort"
4. "Ensure my application passes ATS screening with proper keywords"
5. "Provide verifiable evidence for my achievements when requested"
6. "Sign in quickly without creating another password"
7. "Update my work samples and project descriptions as they evolve"
8. "Maintain accurate, current portfolio information"

## Scope (MoSCoW)

**Must:**
- **Core CV/Cover Letter Generation:**
  - Artifact ingestion (repos, papers, talks, datasets, dashboards, PRDs)
  - Evidence linking (GitHub PRs, live apps, arXiv, demo videos)
  - Role-based labeling system with skill taxonomy
  - Job description parsing and matching engine
  - ATS-optimized CV generation with keyword preservation
  - Cover letter generation with evidence citations
  - PDF/Docx export with clean formatting
  - Version tracking and evidence link management
- **Authentication & User Management:**
  - Google OAuth integration with one-click sign-in
  - Seamless profile creation from Google account information
  - Account linking for existing email/password users
  - Fallback email/password authentication option
- **Artifact Management:**
  - Comprehensive artifact editing capabilities
  - Metadata modification (title, description, dates, technologies, collaborators)
  - Evidence link management (add, edit, remove with validation)
  - File upload, replacement, and management
  - Data validation and integrity preservation

**Should:**
- QR code/footnote evidence linking in exports
- Reusable label templates for role families
- STAR/CAR achievement framework integration
- Company-specific customization signals
- Browser extension for job posting ingestion
- Bulk artifact editing operations
- Advanced form validation with real-time feedback

**Could:**
- Team/collaborative workspace features
- Interview preparation based on submitted evidence
- Performance analytics and application tracking
- Integration with job boards and LinkedIn
- Version history and change tracking for artifacts
- AI-powered content suggestions during editing

**Won't:**
- Social media profile optimization (future PRD)
- Salary negotiation tools (future PRD)
- Background check preparation (future PRD)
- Enterprise SSO integration (future PRD)
- Multi-provider social authentication beyond Google (future PRD)

## Success Metrics

**Primary:**
- Time to create tailored CV+cover letter: baseline 3 hours → target 15 minutes (90% reduction by 2025-12-31)
- ATS pass rate: baseline 25% → target 65% (40pp improvement by 2025-12-31)
- User retention: 70% monthly active users after 3 months
- Registration conversion rate: +25% with Google authentication
- Time-to-first-value: from 5 minutes → under 2 minutes

**Guardrails:**
- Evidence link accuracy ≥95% (verified working links)
- Generated content relevance score ≥8/10 (user-rated)
- Export formatting quality ≥95% ATS compatibility
- Response time ≤30 seconds for CV generation
- Authentication flow completion ≤3 seconds
- Artifact edit operations complete ≤2 seconds for metadata changes
- Support ticket reduction: 60% decrease in authentication-related issues

## Non-Goals

This PRD explicitly excludes:
- Real-time collaboration features (v1)
- Advanced analytics dashboard (v1)
- Interview scheduling or tracking
- Salary benchmarking or negotiation
- Background verification services
- Social media optimization beyond LinkedIn basics
- Enterprise SSO for v1
- Multiple linked social accounts
- Advanced artifact workflow states (draft, review, published)

## Requirements

### Functional

**Core CV/Cover Letter Generation:**
- As a job seeker, I upload my projects/work history with supporting evidence links
- As a job seeker, I paste a job description and get a relevance-ranked CV within 30 seconds
- As a job seeker, I receive a cover letter that specifically cites 2-3 pieces of evidence
- As a job seeker, I can export clean PDF/Docx that passes ATS parsing
- As a job seeker, I can track which evidence was included in each application version
- As a job seeker, I can reuse role labels for similar positions without re-uploading

**Authentication & User Management:**
- As a new user, I can sign in with my Google account in one click without creating passwords
- As an existing user, I can link my Google account to my current email/password account
- As a user without Google, I can still register with email/password as a fallback
- As a returning user, I am automatically logged in when I click Google sign-in

**Artifact Management:**
- As a user with uploaded artifacts, I can edit title, description, dates, technologies, and collaborators
- As a user maintaining my artifacts, I can add, edit, and remove evidence links with URL validation
- As a user with uploaded documents, I can replace files or add new files to existing artifacts
- As a user managing multiple artifacts, I can edit multiple artifacts efficiently with bulk operations
- As a user, all my edit operations are validated and provide clear error feedback

### Non-Functional
- **Availability:** ≥99.5% uptime during business hours
- **Performance:**
  - CV generation ≤30s, evidence verification ≤10s
  - Authentication flow ≤3 seconds
  - Artifact metadata edits ≤2 seconds
  - File uploads with progress indicators
- **Security:**
  - Evidence links encrypted at rest, no credential storage
  - OAuth 2.0 compliance with PKCE
  - Secure token storage and refresh mechanisms
  - Server-side validation for all user inputs
- **Privacy:** User data isolated, GDPR/CCPA compliant deletion
- **Scalability:** Support 10,000 concurrent users, 1M+ artifacts stored
- **Usability:**
  - Intuitive editing interfaces with form validation
  - Clear authentication options presentation
  - Responsive design for mobile artifact editing

## Dependencies

**Data:**
- Skills taxonomy database (O*NET, LinkedIn Skills)
- ATS parsing validation dataset
- Company information database

**Services:**
- LLM API access (OpenAI/Anthropic) for content generation
- Document parsing service (PDF/Docx)
- URL validation and metadata extraction
- Email/authentication service
- Google Cloud Console OAuth credentials

**Legal/Policy:**
- Privacy policy review for evidence link handling and Google integration
- Terms of service for generated content liability
- GDPR compliance review for EU users

**3rd-party:**
- GitHub API for repository metadata
- Google Sign-In JavaScript SDK
- LinkedIn API for profile enhancement (future)
- Job board APIs for posting ingestion (future)

## Risks & Mitigations

**Top risks:**
1. **LLM hallucination/inaccuracy** → Detection: Human review loops, confidence scoring; Fallback: Template-based generation
2. **Evidence link degradation** → Detection: Automated link checking; Fallback: Link validation warnings, archive.org fallbacks
3. **ATS compatibility issues** → Detection: Test suite against major ATS systems; Fallback: Multiple export format options
4. **User data privacy concerns** → Detection: Security audits, penetration testing; Fallback: Enhanced encryption, data minimization
5. **OAuth integration complexity** → Detection: Comprehensive testing; Fallback: Maintain email/password authentication
6. **Data corruption during editing** → Detection: Atomic transactions, validation; Fallback: File cleanup background jobs

## Rollout Plan & Timeline

**Phase 1 (MVP - 3 months):** Core ingestion, basic matching, PDF export, Google auth
- Entry: PRD approved, tech specs complete
- Exit: 100 beta users, 80% satisfaction score, Google auth adoption >70%

**Phase 2 (Enhanced - 2 months):** Advanced matching, cover letters, evidence linking, artifact editing
- Entry: Phase 1 metrics met, user feedback incorporated
- Exit: 1,000 users, ATS pass rate >50%, artifact editing adoption >70%

**Phase 3 (Scale - 2 months):** Performance optimization, role templates, analytics, bulk operations
- Entry: Phase 2 metrics met, infrastructure scaled
- Exit: 10,000 users, target metrics achieved

## Analytics & Telemetry

**Events:**
- artifact_uploaded, artifact_edited, label_created, cv_generated, cover_letter_generated, document_exported, evidence_clicked
- google_signin_initiated, google_signin_completed, account_linked
- edit_initiated, edit_completed, bulk_edit_completed
- error_generation_failed, link_validation_failed, export_failed, auth_failed, edit_failed

**Dashboards:**
- User engagement: uploads, generations, exports per user
- Authentication: adoption rates, success rates, fallback usage
- Artifact management: edit frequency, bulk operation usage
- Performance: generation latency, success rates, error rates
- Quality: user ratings, ATS pass rates, evidence link health

**Alert thresholds:**
- Generation success rate <95%
- Average generation time >45s
- Evidence link failure rate >10%
- User error rate >5%
- Authentication success rate <98%
- Edit operation failure rate >2%

## Privacy & Compliance

**Data collected:**
- Work artifacts and metadata (titles, dates, descriptions)
- Evidence URLs and validation status
- Generated CV/cover letter versions
- User interaction and performance metrics
- Google account information (email, name, profile picture)
- Artifact edit history and timestamps

**Data retention:**
- User artifacts: retained until account deletion
- Generated documents: 90 days unless saved by user
- Analytics data: 2 years aggregated, 30 days individual
- Error logs: 30 days
- Authentication tokens: per OAuth standards

**Consent & control:**
- Explicit consent for evidence link sharing
- User consent for Google account integration
- User control over data export and deletion
- Opt-out for analytics collection
- Clear data usage disclosure

**DSR handling:**
- Data export: JSON format within 7 days
- Data deletion: complete removal within 30 days
- Data portability: standard format exports available

## Changelog

### v1.1.0 (2025-09-27)
- **Added:** Google Authentication integration requirements
- **Added:** Artifact editing functionality requirements
- **Updated:** Success metrics to include authentication and editing goals
- **Updated:** Scope to include authentication and artifact management
- **Updated:** Timeline to include authentication and editing features
- **Consolidated:** Multiple PRD files into single project PRD

### v1.0.0 (2025-09-23)
- **Initial:** Core CV & Cover-Letter Auto-Tailor PRD created
- **Defined:** Primary user personas and use cases
- **Established:** Success metrics and timeline
- **Outlined:** Core functionality and technical requirements