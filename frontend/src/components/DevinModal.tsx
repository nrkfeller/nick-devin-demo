'use client';

import React from 'react';
import { GitHubIssue, DevinSession } from '@/lib/types';

interface DevinModalProps {
  issue: GitHubIssue;
  session: DevinSession;
  onClose: () => void;
}

export default function DevinModal({ issue, session, onClose }: DevinModalProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scoping':
        return 'bg-blue-100 text-blue-800';
      case 'resolving':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'scoping':
        return '🔍';
      case 'resolving':
        return '⚙️';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      default:
        return '⏳';
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Devin AI Session - Issue #{issue.number}
            </h3>
            <p className="text-sm text-gray-500 mt-1">{issue.title}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 focus:outline-none"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Session Info */}
        <div className="py-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-gray-500">Status</div>
              <div className="mt-1 flex items-center">
                <span className="text-lg mr-2">{getStatusIcon(session.status)}</span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(session.status)}`}>
                  {session.status}
                </span>
              </div>
            </div>

            {session.confidence_score && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm font-medium text-gray-500">Confidence Score</div>
                <div className="mt-1 text-2xl font-bold text-gray-900">
                  {session.confidence_score}%
                </div>
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-gray-500">Session ID</div>
              <div className="mt-1 text-sm font-mono text-gray-900 break-all">
                {session.devin_session_id}
              </div>
            </div>
          </div>

          {/* Action Plan */}
          {session.action_plan && (
            <div className="mb-6">
              <h4 className="text-md font-medium text-gray-900 mb-3">Action Plan</h4>
              <div className="bg-gray-50 p-4 rounded-lg">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {session.action_plan}
                </pre>
              </div>
            </div>
          )}

          {/* Progress Log */}
          <div className="mb-6">
            <h4 className="text-md font-medium text-gray-900 mb-3">Progress Log</h4>
            <div className="bg-gray-50 p-4 rounded-lg max-h-64 overflow-y-auto">
              <div className="space-y-2">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">[{session.created_at ? new Date(session.created_at).toLocaleTimeString() : 'N/A'}]</span> Session started
                </div>
                {session.status === 'scoping' && (
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">[{new Date().toLocaleTimeString()}]</span> Analyzing issue requirements...
                  </div>
                )}
                {session.status === 'resolving' && (
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">[{new Date().toLocaleTimeString()}]</span> Working on implementation...
                  </div>
                )}
                {session.status === 'completed' && (
                  <div className="text-sm text-green-600">
                    <span className="font-medium">[{session.updated_at ? new Date(session.updated_at).toLocaleTimeString() : 'N/A'}]</span> Session completed successfully
                  </div>
                )}
                {session.status === 'failed' && (
                  <div className="text-sm text-red-600">
                    <span className="font-medium">[{session.updated_at ? new Date(session.updated_at).toLocaleTimeString() : 'N/A'}]</span> Session failed - manual intervention required
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-between items-center pt-4 border-t">
            <div className="flex space-x-3">
              <a
                href={issue.html_url}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                View on GitHub
              </a>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
