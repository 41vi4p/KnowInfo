'use client';

import { useEffect, useState } from 'react';
import { getClaims, Claim } from '@/lib/api';
import ClaimCard from '@/components/ClaimCard';
import { Search, Filter } from 'lucide-react';

export default function ClaimsPage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [filteredClaims, setFilteredClaims] = useState<Claim[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadClaims() {
      try {
        const data = await getClaims({});
        setClaims(data);
        setFilteredClaims(data);
      } catch (error) {
        console.error('Error loading claims:', error);
      } finally {
        setLoading(false);
      }
    }

    loadClaims();
  }, []);

  useEffect(() => {
    let filtered = claims;

    if (searchQuery) {
      filtered = filtered.filter((claim) =>
        claim.claim_text.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (statusFilter !== 'ALL') {
      filtered = filtered.filter((claim) => claim.status === statusFilter);
    }

    if (priorityFilter !== 'ALL') {
      filtered = filtered.filter((claim) => claim.priority === priorityFilter);
    }

    setFilteredClaims(filtered);
  }, [searchQuery, statusFilter, priorityFilter, claims]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Claim Verification</h1>
        <p className="text-gray-600 mt-2">
          Track and verify claims from multiple sources
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search claims..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="ALL">All Status</option>
              <option value="TRUE">True</option>
              <option value="FALSE">False</option>
              <option value="MISLEADING">Misleading</option>
              <option value="UNVERIFIED">Unverified</option>
            </select>
          </div>

          {/* Priority Filter */}
          <div>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="ALL">All Priority</option>
              <option value="P0">P0 - Critical</option>
              <option value="P1">P1 - High</option>
              <option value="P2">P2 - Medium</option>
              <option value="P3">P3 - Low</option>
            </select>
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
          <span>
            Showing {filteredClaims.length} of {claims.length} claims
          </span>
          <button className="flex items-center space-x-2 text-blue-600 hover:text-blue-700">
            <Filter className="h-4 w-4" />
            <span>More Filters</span>
          </button>
        </div>
      </div>

      {/* Claims Grid */}
      <div className="grid grid-cols-1 gap-4">
        {filteredClaims.map((claim) => (
          <ClaimCard
            key={claim.claim_id}
            claim={claim}
            onClick={() => {
              window.location.href = `/dashboard/claims/${claim.claim_id}`;
            }}
          />
        ))}
      </div>

      {filteredClaims.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center border border-gray-200">
          <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No claims found
          </h3>
          <p className="text-gray-600">
            Try adjusting your filters or search query
          </p>
        </div>
      )}
    </div>
  );
}
