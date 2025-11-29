'use client';

import { useEffect, useState } from 'react';
import { use } from 'react';
import { getClaimDetails, getPatientZero } from '@/lib/api';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  ExternalLink,
  Share2,
  TrendingUp,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function ClaimDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [claim, setClaim] = useState<any>(null);
  const [patientZero, setPatientZero] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [claimData, patientZeroData] = await Promise.all([
          getClaimDetails(resolvedParams.id),
          getPatientZero(resolvedParams.id),
        ]);
        setClaim(claimData);
        setPatientZero(patientZeroData);
      } catch (error) {
        console.error('Error loading claim details:', error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [resolvedParams.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Claim not found</p>
      </div>
    );
  }

  const getStatusIcon = () => {
    switch (claim.status) {
      case 'TRUE':
        return <CheckCircle className="h-8 w-8 text-green-600" />;
      case 'FALSE':
        return <XCircle className="h-8 w-8 text-red-600" />;
      case 'MISLEADING':
        return <AlertTriangle className="h-8 w-8 text-yellow-600" />;
      default:
        return <Clock className="h-8 w-8 text-gray-600" />;
    }
  };

  const getStatusColor = () => {
    switch (claim.status) {
      case 'TRUE':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'FALSE':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'MISLEADING':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => window.history.back()}
          className="text-blue-600 hover:text-blue-700 mb-4"
        >
          ← Back to Claims
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Claim Analysis</h1>
      </div>

      {/* Status Banner */}
      <div className={`rounded-lg border p-6 ${getStatusColor()}`}>
        <div className="flex items-start space-x-4">
          {getStatusIcon()}
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-2">{claim.status}</h2>
            <p className="text-lg">{claim.claim_text}</p>
            <div className="flex items-center space-x-6 mt-4 text-sm">
              <span>Confidence: {claim.confidence_score}%</span>
              <span>Priority: {claim.priority}</span>
              <span>Category: {claim.category}</span>
              <span>
                {formatDistanceToNow(new Date(claim.created_at), {
                  addSuffix: true,
                })}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Explanation */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Verification Explanation
        </h3>
        <p className="text-gray-700 leading-relaxed">{claim.explanation}</p>
      </div>

      {/* Sources */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Authoritative Sources
        </h3>
        <div className="space-y-3">
          {claim.sources.map((source: any, index: number) => (
            <div
              key={index}
              className="flex items-start justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <div className="flex-1">
                <h4 className="font-medium text-gray-900">{source.title}</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Credibility: <span className="capitalize">{source.credibility}</span>
                </p>
              </div>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700"
              >
                <ExternalLink className="h-5 w-5" />
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Propagation Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Propagation Tree Size
              </p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {claim.propagation_tree_size?.toLocaleString() || 0}
              </p>
            </div>
            <Share2 className="h-8 w-8 text-blue-600" />
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Total accounts involved in spreading
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Patient Zero Nodes
              </p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {patientZero?.nodes?.length || 0}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-orange-600" />
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Key amplifiers identified
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">
                Verification Time
              </p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {claim.verification_time}min
              </p>
            </div>
            <Clock className="h-8 w-8 text-purple-600" />
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Time to complete verification
          </p>
        </div>
      </div>

      {/* Patient Zero Preview */}
      {patientZero && patientZero.nodes.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Key Propagators
            </h3>
            <a
              href={`/dashboard/patient-zero?claim=${claim.claim_id}`}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              View Full Network →
            </a>
          </div>
          <div className="space-y-3">
            {patientZero.nodes.slice(0, 3).map((node: any) => (
              <div
                key={node.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900">@{node.username}</p>
                  <p className="text-sm text-gray-600">
                    {node.followers.toLocaleString()} followers • {node.platform}
                  </p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    node.type === 'original'
                      ? 'bg-red-100 text-red-700'
                      : node.type === 'amplifier'
                      ? 'bg-orange-100 text-orange-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  {node.type}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
