export interface GitHubIssue {
  number: number;
  title: string;
  body?: string;
  state: string;
  labels: Array<{
    id: number;
    name: string;
    color: string;
  }>;
  assignees: Array<{
    id: number;
    login: string;
    avatar_url: string;
  }>;
  html_url: string;
  created_at: string;
  updated_at: string;
}

export interface DevinSession {
  id: number;
  issue_number: number;
  issue_title: string;
  devin_session_id: string;
  action_plan?: string;
  confidence_score?: number;
  status: 'scoping' | 'resolving' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface IssueFilters {
  state: 'open' | 'closed' | 'all';
  labels?: string;
  assignee?: string;
  search?: string;
}

export interface ScopeRequest {
  issue_number: number;
  issue_title: string;
  issue_body?: string;
}

export interface ResolveRequest {
  issue_number: number;
}

export interface APIResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}
