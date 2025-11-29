'use client';

import { Claim } from '@/lib/api';
import { CheckCircle, XCircle, AlertTriangle, Search, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface ClaimCardProps {
  claim: Claim;
  onClick?: () => void;
}

export default function ClaimCard({ claim, onClick }: ClaimCardProps) {
  const getStatusConfig = () => {
    switch (claim.status) {
      case 'TRUE':
        return { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-50', borderColor: 'border-green-200' };
      case 'FALSE':
        return { icon: XCircle, color: 'text-red-600', bgColor: 'bg-red-50', borderColor: 'border-red-200' };
      case 'MISLEADING':
        return { icon: AlertTriangle, color: 'text-yellow-600', bgColor: 'bg-yellow-50', borderColor: 'border-yellow-200' };
      case 'UNVERIFIED':
        return { icon: Search, color: 'text-gray-600', bgColor: 'bg-gray-50', borderColor: 'border-gray-200' };
      default:
        return { icon: Clock, color: 'text-blue-600', bgColor: 'bg-blue-50', borderColor: 'border-blue-200' };
    }
  };

  const getPriorityColor = () => {
    switch (claim.priority) {
      case 'P0':
        return 'bg-red-600';
      case 'P1':
        return 'bg-orange-500';
      case 'P2':
        return 'bg-yellow-500';
      default:
        return 'bg-blue-500';
    }
  };

  const config = getStatusConfig();
  const StatusIcon = config.icon;

  return (
    <div
      className={`bg-white rounded-lg border ${config.borderColor} p-4 cursor-pointer hover:shadow-md transition-shadow`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className={`p-2 rounded-full ${config.bgColor}`}>
            <StatusIcon className={`h-4 w-4 ${config.color}`} />
          </div>
          <span className={`text-sm font-semibold ${config.color}`}>
            {claim.status}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs font-medium text-white rounded ${getPriorityColor()}`}>
            {claim.priority}
          </span>
          <span className="text-xs text-gray-500">{claim.confidence_score}%</span>
        </div>
      </div>

      <h3 className="text-sm font-medium text-gray-900 mb-2 line-clamp-2">
        {claim.claim_text}
      </h3>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-4">
          <span className="px-2 py-1 bg-gray-100 rounded">{claim.category}</span>
          <span>{claim.source_platform}</span>
        </div>
        <span>{formatDistanceToNow(new Date(claim.created_at), { addSuffix: true })}</span>
      </div>

      {claim.verification_time && (
        <div className="mt-2 text-xs text-gray-500">
          Verified in {claim.verification_time}min
        </div>
      )}
    </div>
  );
}
