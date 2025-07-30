'use client';

import React from 'react';
import { IssueFilters as IssueFiltersType } from '@/lib/types';

interface IssueFiltersProps {
  filters: IssueFiltersType;
  onFiltersChange: (filters: IssueFiltersType) => void;
  onRefresh: () => void;
}

export default function IssueFilters({ filters, onFiltersChange, onRefresh }: IssueFiltersProps) {
  const handleStateChange = (state: 'open' | 'closed' | 'all') => {
    onFiltersChange({ ...filters, state });
  };

  const handleSearchChange = (search: string) => {
    onFiltersChange({ ...filters, search });
  };

  const handleLabelsChange = (labels: string) => {
    onFiltersChange({ ...filters, labels: labels || undefined });
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow border">
      <div className="flex flex-wrap items-center gap-4">
        {/* State Filter */}
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">State:</label>
          <select
            value={filters.state}
            onChange={(e) => handleStateChange(e.target.value as 'open' | 'closed' | 'all')}
            className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="open">Open</option>
            <option value="closed">Closed</option>
            <option value="all">All</option>
          </select>
        </div>

        {/* Labels Filter */}
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Labels:</label>
          <input
            type="text"
            placeholder="e.g., bug,enhancement"
            value={filters.labels || ''}
            onChange={(e) => handleLabelsChange(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-48"
          />
        </div>

        {/* Search Filter */}
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Search:</label>
          <input
            type="text"
            placeholder="Search issues..."
            value={filters.search || ''}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
          />
        </div>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          className="bg-blue-600 text-white px-4 py-1 rounded-md text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Refresh
        </button>
      </div>
    </div>
  );
}
