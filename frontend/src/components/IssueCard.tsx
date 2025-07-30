'use client';

import React from 'react';
import { GitHubIssue } from '@/lib/types';

interface IssueCardProps {
  issue: GitHubIssue;
  onScopeIssue: (issue: GitHubIssue) => void;
  onResolveIssue: (issue: GitHubIssue) => void;
}

export default function IssueCard({ issue, onScopeIssue, onResolveIssue }: IssueCardProps) {
  const getStateColor = (state: string) => {
    return state === 'open' ? 'bg-green-100 text-green-800' : 'bg-purple-100 text-purple-800';
  };

  const getLabelColor = (color: string) => {
    return `#${color}`;
  };

  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Issue Header */}
          <div className="flex items-center space-x-3 mb-2">
            <h3 className="text-lg font-medium text-gray-900 truncate">
              #{issue.number} {issue.title}
            </h3>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStateColor(issue.state)}`}>
              {issue.state}
            </span>
          </div>

          {/* Issue Body Preview */}
          {issue.body && (
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
              {issue.body.substring(0, 200)}
              {issue.body.length > 200 && '...'}
            </p>
          )}

          {/* Labels */}
          {issue.labels && issue.labels.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {issue.labels.map((label) => (
                <span
                  key={label.id}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white"
                  style={{ backgroundColor: getLabelColor(label.color) }}
                >
                  {label.name}
                </span>
              ))}
            </div>
          )}

          {/* Assignees */}
          {issue.assignees && issue.assignees.length > 0 && (
            <div className="flex items-center space-x-2 mb-3">
              <span className="text-sm text-gray-500">Assigned to:</span>
              <div className="flex -space-x-2">
                {issue.assignees.slice(0, 3).map((assignee) => (
                  <img
                    key={assignee.id}
                    className="h-6 w-6 rounded-full border-2 border-white"
                    src={assignee.avatar_url}
                    alt={assignee.login}
                    title={assignee.login}
                    // eslint-disable-next-line @next/next/no-img-element
                  />
                ))}
                {issue.assignees.length > 3 && (
                  <span className="text-sm text-gray-500 ml-2">
                    +{issue.assignees.length - 3} more
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Timestamps */}
          <div className="text-xs text-gray-500">
            Created: {issue.created_at ? new Date(issue.created_at).toLocaleDateString() : 'N/A'} • 
            Updated: {issue.updated_at ? new Date(issue.updated_at).toLocaleDateString() : 'N/A'}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col space-y-2 ml-6">
          <button
            onClick={() => onScopeIssue(issue)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          >
            Scope with Devin
          </button>
          <button
            onClick={() => onResolveIssue(issue)}
            className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
          >
            Resolve with Devin
          </button>
          <a
            href={issue.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors text-center"
          >
            View on GitHub
          </a>
        </div>
      </div>
    </div>
  );
}
