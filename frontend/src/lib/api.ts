import { GitHubIssue, DevinSession } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred');
    }
  }

  async getIssues(filters?: {
    state?: string;
    labels?: string;
  }): Promise<GitHubIssue[]> {
    const params = new URLSearchParams();
    if (filters?.state) params.append('state', filters.state);
    if (filters?.labels) params.append('labels', filters.labels);
    
    const query = params.toString();
    const endpoint = `/issues${query ? `?${query}` : ''}`;
    
    return this.request<GitHubIssue[]>(endpoint);
  }

  async scopeIssue(request: {
    issue_number: number;
    issue_title: string;
    issue_body?: string;
  }): Promise<DevinSession> {
    return this.request<DevinSession>('/scope-issue', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async resolveIssue(request: {
    issue_number: number;
  }): Promise<DevinSession> {
    return this.request<DevinSession>('/resolve-issue', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getSessions(): Promise<DevinSession[]> {
    return this.request<DevinSession[]>('/sessions');
  }
}

export const apiClient = new APIClient();
