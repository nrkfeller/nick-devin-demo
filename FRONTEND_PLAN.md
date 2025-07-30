# Frontend Implementation Plan

## Overview
Build a Next.js-based dashboard for GitHub Issues Devin Integration with comprehensive issue management, scoping, and automated resolution capabilities.

## Component Architecture

### 1. Main App Layout (`src/app/layout.tsx`)
- Root layout component with global providers
- Error boundary for handling unexpected errors
- Theme provider and global context setup
- Global CSS and font imports

### 2. Dashboard Page (`src/app/page.tsx`)
- Main dashboard page component
- Server-side rendering for initial issue data
- Client-side interactivity for real-time updates

### 2. Dashboard Layout (`components/Dashboard.tsx`)
- Main dashboard view displaying GitHub issues
- Header with repository information and filters
- Sidebar for navigation and settings
- Main content area for issue list and details

### 3. Issue Management Components

#### `components/IssueList.tsx`
- Display list of GitHub issues in card/table format
- Filtering capabilities (open/closed, labels, assignees)
- Pagination for large issue lists
- Search functionality

#### `components/IssueCard.tsx`
- Individual issue display component
- Shows: Title, Number, Labels, Assignees, Status (Open/Closed)
- Action buttons: "Scope with Devin" and "Resolve with Devin"
- Click to expand for more details

#### `components/IssueFilters.tsx`
- Filter controls for issue state, labels, assignees
- Search input for issue titles/descriptions
- Sort options (date, priority, status)

### 4. Devin Integration Components

#### `components/DevinModal.tsx`
- Modal/dialog for showing Devin's progress updates
- Real-time session status display
- Action plan visualization
- Confidence score display
- Progress indicators and logs

#### `components/DevinSessionCard.tsx`
- Compact view of Devin session information
- Session status, timestamps, issue association
- Quick actions (view details, cancel session)

### 5. UI Components (using shadcn/ui)
- `components/ui/Button.tsx` - Action buttons
- `components/ui/Card.tsx` - Issue cards and containers
- `components/ui/Badge.tsx` - Labels and status indicators
- `components/ui/Dialog.tsx` - Modals and overlays
- `components/ui/Input.tsx` - Search and filter inputs
- `components/ui/Select.tsx` - Dropdown filters
- `components/ui/Progress.tsx` - Progress indicators
- `components/ui/Alert.tsx` - Error messages and notifications

## State Management

### 1. Global State (React Context + useReducer)
```typescript
interface AppState {
  issues: GitHubIssue[];
  sessions: DevinSession[];
  filters: IssueFilters;
  loading: boolean;
  error: string | null;
  selectedIssue: GitHubIssue | null;
  activeModal: 'devin' | 'issue-details' | null;
}
```

### 2. API State Management
- Custom hooks for API calls (`useGitHubAPI`, `useDevinAPI`)
- Error handling and retry logic
- Loading states and optimistic updates

## API Integration

### 1. Backend API Client (`services/api.ts`)
```typescript
class APIClient {
  private baseURL: string;
  
  // GitHub Issues
  async getIssues(filters?: IssueFilters): Promise<GitHubIssue[]>
  async getIssue(number: number): Promise<GitHubIssue>
  
  // Devin Integration
  async scopeIssue(request: ScopeRequest): Promise<DevinSession>
  async resolveIssue(request: ResolveRequest): Promise<DevinSession>
  async getSessions(): Promise<DevinSession[]>
  async getSession(id: string): Promise<DevinSession>
}
```

### 2. Environment Configuration
- `.env.local` file for API configuration
- `REACT_APP_API_URL=http://localhost:8000`
- Environment-specific settings

### 3. Error Handling Strategy
- Network error handling with retry logic
- API key validation and user feedback
- Graceful degradation for missing features
- User-friendly error messages with actionable suggestions

## UI/UX Design

### 1. Dashboard Layout
```
┌─────────────────────────────────────────────────────────┐
│ Header: GitHub Issues Devin Integration                 │
├─────────────────────────────────────────────────────────┤
│ Filters: [State] [Labels] [Assignees] [Search]         │
├─────────────────────────────────────────────────────────┤
│ Issue List:                                             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ #897 [JAX] Refactor adstock_hill module             │ │
│ │ Labels: [enhancement] [jax]                         │ │
│ │ Assignee: @user123                                  │ │
│ │ Status: Open                                        │ │
│ │ [Scope with Devin] [Resolve with Devin]            │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ #896 Document MMM schema                            │ │
│ │ ...                                                 │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Devin Sessions Panel (collapsible):                    │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Session: abc123 | Issue #897 | Status: Scoping     │ │
│ │ Confidence: 85% | Started: 2 min ago               │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2. Devin Modal Design
```
┌─────────────────────────────────────────────────────────┐
│ Devin AI Session - Issue #897                          │
├─────────────────────────────────────────────────────────┤
│ Status: [●] Analyzing Issue                             │
│ Confidence Score: 85%                                  │
│ Session ID: abc123-def456                              │
├─────────────────────────────────────────────────────────┤
│ Action Plan:                                            │
│ 1. ✓ Analyze current adstock_hill module structure     │
│ 2. ● Identify backend-specific dependencies            │
│ 3. ○ Create abstract base classes                      │
│ 4. ○ Implement JAX-specific implementation             │
│ 5. ○ Add comprehensive tests                           │
├─────────────────────────────────────────────────────────┤
│ Progress Log:                                           │
│ [14:30] Session started                                 │
│ [14:31] Analyzing codebase structure...                │
│ [14:32] Found 3 backend-specific dependencies          │
├─────────────────────────────────────────────────────────┤
│ [Close] [View on GitHub] [Cancel Session]              │
└─────────────────────────────────────────────────────────┘
```

### 3. Color Scheme & Styling
- Use Tailwind CSS utility classes
- Dark/light theme support
- Consistent spacing and typography
- Accessible color contrasts
- Responsive design for mobile/tablet

## Error Handling & User Experience

### 1. Error Types & Handling
- **Network Errors**: Retry button, offline indicator
- **API Key Issues**: Clear instructions for setup
- **Rate Limiting**: Automatic retry with backoff
- **Invalid Responses**: Fallback UI with error details
- **Session Failures**: Option to restart or contact support

### 2. Loading States
- Skeleton loaders for issue cards
- Progress indicators for Devin sessions
- Optimistic updates for user actions
- Graceful handling of slow API responses

### 3. User Feedback
- Toast notifications for actions
- Success/error states with clear messaging
- Progress indicators for long-running operations
- Confirmation dialogs for destructive actions

## File Structure
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Dashboard page
│   │   ├── globals.css   # Global styles
│   │   └── api/          # API routes (if needed)
│   ├── components/
│   │   ├── ui/           # shadcn/ui components
│   │   ├── Dashboard.tsx
│   │   ├── IssueList.tsx
│   │   ├── IssueCard.tsx
│   │   ├── IssueFilters.tsx
│   │   ├── DevinModal.tsx
│   │   └── DevinSessionCard.tsx
│   ├── lib/
│   │   ├── api.ts        # API client
│   │   ├── types.ts      # TypeScript interfaces
│   │   └── utils.ts      # Utility functions
│   ├── hooks/
│   │   ├── useGitHubAPI.ts
│   │   ├── useDevinAPI.ts
│   │   └── useLocalStorage.ts
│   └── context/
│       └── AppContext.tsx
├── .env.local
├── next.config.js
└── package.json
```

## Implementation Priority
1. **Phase 1**: Basic dashboard with issue listing
2. **Phase 2**: GitHub API integration and filtering
3. **Phase 3**: Devin integration (scope/resolve actions)
4. **Phase 4**: Real-time updates and session management
5. **Phase 5**: Error handling and polish

## Testing Strategy
- Unit tests for components and utilities
- Integration tests for API calls
- E2E tests for critical user flows
- Error scenario testing
- Accessibility testing

This plan provides a comprehensive foundation for implementing the GitHub Issues Devin Integration frontend with all required functionality, proper error handling, and excellent user experience.
