'use client';

import React from 'react';
import { GitHubIssue } from '@/lib/types';
import IssueCard from './IssueCard';

interface IssueListProps {
  issues: GitHubIssue[];
  loading: boolean;
  onScopeIssue: (issue: GitHubIssue) => void;
  onResolveIssue: (issue: GitHubIssue) => void;
}

export default function IssueList({ issues, loading, onScopeIssue, onResolveIssue }: IssueListProps) {
  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading issues...</span>
        </div>
      </div>
    );
  }

  if (issues.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No issues found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your filters or check your API configuration.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-200">
      {issues.map((issue) => (
        <IssueCard
          key={issue.number}
          issue={issue}
          onScopeIssue={onScopeIssue}
          onResolveIssue={onResolveIssue}
        />
      ))}
    </div>
  );
}
