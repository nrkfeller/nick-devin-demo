'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { GitHubIssue, DevinSession, IssueFilters as IssueFiltersType } from '@/lib/types';
import { apiClient } from '@/lib/api';
import IssueList from './IssueList';
import IssueFilters from './IssueFilters';
import DevinModal from './DevinModal';

export default function Dashboard() {
  const [issues, setIssues] = useState<GitHubIssue[]>([]);
  const [sessions, setSessions] = useState<DevinSession[]>([]);
  const [filters, setFilters] = useState<IssueFiltersType>({
    repo: 'google/meridian',
    state: 'open',
    search: '',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIssue, setSelectedIssue] = useState<GitHubIssue | null>(null);
  const [activeModal, setActiveModal] = useState<'devin' | 'issue-details' | null>(null);
  const [activeSession, setActiveSession] = useState<DevinSession | null>(null);

  const loadIssues = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getIssues({
        repo: filters.repo,
        state: filters.state === 'all' ? undefined : filters.state,
        labels: filters.labels,
      });
      setIssues(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load issues');
    } finally {
      setLoading(false);
    }
  }, [filters.repo, filters.state, filters.labels]);

  useEffect(() => {
    loadIssues();
    loadSessions();
  }, [loadIssues]);

  const loadSessions = async () => {
    try {
      const data = await apiClient.getSessions();
      setSessions(data);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  };

  const handleScopeIssue = async (issue: GitHubIssue) => {
    try {
      setSelectedIssue(issue);
      const session = await apiClient.scopeIssue({
        issue_number: issue.number,
        issue_title: issue.title,
        issue_body: issue.body,
        repo: filters.repo,
      });
      setActiveSession(session);
      setActiveModal('devin');
      await loadSessions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start scoping');
    }
  };

  const handleResolveIssue = async (issue: GitHubIssue) => {
    try {
      setSelectedIssue(issue);
      const session = await apiClient.resolveIssue({
        issue_number: issue.number,
        repo: filters.repo,
      });
      setActiveSession(session);
      setActiveModal('devin');
      await loadSessions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start resolution');
    }
  };

  const closeModal = () => {
    setActiveModal(null);
    setSelectedIssue(null);
    setActiveSession(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                GitHub Issues Devin Integration
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Autonomous issue management for GitHub repositories
              </p>
              <div className="mt-4">
                <label htmlFor="repo" className="block text-sm font-medium text-gray-700 mb-2">
                  Repository (owner/repo)
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    id="repo"
                    value={filters.repo || ''}
                    onChange={(e) => setFilters(prev => ({ ...prev, repo: e.target.value }))}
                    placeholder="e.g., google/meridian"
                    className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                  <button
                    onClick={loadIssues}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                  >
                    {loading ? 'Loading...' : 'Load Issues'}
                  </button>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                {issues.length} issues • {sessions.length} sessions
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => setError(null)}
                    className="text-sm bg-red-100 text-red-800 px-3 py-1 rounded-md hover:bg-red-200"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="mb-6">
          <IssueFilters
            filters={filters}
            onFiltersChange={setFilters}
            onRefresh={loadIssues}
          />
        </div>

        {/* Issues List */}
        <div className="bg-white shadow rounded-lg">
          <IssueList
            issues={issues}
            loading={loading}
            onScopeIssue={handleScopeIssue}
            onResolveIssue={handleResolveIssue}
          />
        </div>

        {/* Sessions Panel */}
        {sessions.length > 0 && (
          <div className="mt-8 bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Active Devin Sessions</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {sessions.slice(0, 5).map((session) => (
                  <div
                    key={session.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <div className="font-medium text-gray-900">
                        Issue #{session.issue_number}: {session.issue_title}
                      </div>
                      <div className="text-sm text-gray-500">
                        Status: {session.status} • Session: {session.devin_session_id}
                      </div>
                      {session.confidence_score && (
                        <div className="text-sm text-gray-500">
                          Confidence: {session.confidence_score}%
                        </div>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">
                      {session.created_at ? new Date(session.created_at).toLocaleString() : 'N/A'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Devin Modal */}
      {activeModal === 'devin' && selectedIssue && activeSession && (
        <DevinModal
          issue={selectedIssue}
          session={activeSession}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
