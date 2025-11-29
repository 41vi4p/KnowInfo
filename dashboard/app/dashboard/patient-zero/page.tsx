'use client';

import { useEffect, useState, useRef } from 'react';
import { getPatientZero, PatientZeroNode, PatientZeroLink } from '@/lib/api';
import { Network, Users, Share2, AlertTriangle } from 'lucide-react';

// Simple network visualization component
function NetworkGraph({ nodes, links }: { nodes: PatientZeroNode[]; links: PatientZeroLink[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // Simple force-directed layout simulation
    const nodePositions = nodes.map((_, i) => ({
      x: canvas.width / 2 + Math.cos((i * 2 * Math.PI) / nodes.length) * 150,
      y: canvas.height / 2 + Math.sin((i * 2 * Math.PI) / nodes.length) * 150,
    }));

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw links
    ctx.strokeStyle = '#cbd5e1';
    ctx.lineWidth = 2;
    links.forEach((link) => {
      const sourceIdx = nodes.findIndex((n) => n.id === link.source);
      const targetIdx = nodes.findIndex((n) => n.id === link.target);
      if (sourceIdx >= 0 && targetIdx >= 0) {
        const source = nodePositions[sourceIdx];
        const target = nodePositions[targetIdx];
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      }
    });

    // Draw nodes
    nodes.forEach((node, i) => {
      const pos = nodePositions[i];
      const radius = node.type === 'original' ? 25 : node.type === 'amplifier' ? 20 : 15;

      // Node circle
      ctx.fillStyle = node.type === 'original' ? '#ef4444' : node.type === 'amplifier' ? '#f59e0b' : '#3b82f6';
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI);
      ctx.fill();

      // Node border
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 3;
      ctx.stroke();

      // Node label
      ctx.fillStyle = '#1f2937';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(`@${node.username.slice(0, 10)}`, pos.x, pos.y + radius + 15);
    });
  }, [nodes, links]);

  return <canvas ref={canvasRef} className="w-full h-full" />;
}

export default function PatientZeroPage() {
  const [data, setData] = useState<{ nodes: PatientZeroNode[]; links: PatientZeroLink[] } | null>(null);
  const [selectedNode, setSelectedNode] = useState<PatientZeroNode | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const patientZeroData = await getPatientZero('claim_001');
        setData(patientZeroData);
      } catch (error) {
        console.error('Error loading patient zero data:', error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No patient zero data available</p>
      </div>
    );
  }

  const totalShares = data.links.reduce((sum, link) => sum + link.shares, 0);
  const amplifierCount = data.nodes.filter((n) => n.type === 'amplifier').length;
  const originalPoster = data.nodes.find((n) => n.type === 'original');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Patient Zero Tracking</h1>
        <p className="text-gray-600 mt-2">
          Trace the origin and propagation path of misinformation
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Nodes</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {data.nodes.length}
              </p>
            </div>
            <Network className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Amplifiers</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {amplifierCount}
              </p>
            </div>
            <AlertTriangle className="h-8 w-8 text-orange-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Shares</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {totalShares.toLocaleString()}
              </p>
            </div>
            <Share2 className="h-8 w-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Reach Potential</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {(data.nodes.reduce((sum, n) => sum + n.followers, 0) / 1000).toFixed(1)}K
              </p>
            </div>
            <Users className="h-8 w-8 text-purple-600" />
          </div>
        </div>
      </div>

      {/* Network Visualization */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Propagation Network
        </h2>
        <div className="h-96 bg-gray-50 rounded-lg border border-gray-200">
          <NetworkGraph nodes={data.nodes} links={data.links} />
        </div>
        <div className="mt-4 flex items-center justify-center space-x-6 text-sm">
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full bg-red-500 mr-2"></div>
            <span className="text-gray-600">Original Poster</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full bg-orange-500 mr-2"></div>
            <span className="text-gray-600">Amplifier</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full bg-blue-500 mr-2"></div>
            <span className="text-gray-600">Sharer</span>
          </div>
        </div>
      </div>

      {/* Original Poster Details */}
      {originalPoster && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-900 mb-4">
            Patient Zero Identified
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-red-700 mb-1">Username</p>
              <p className="font-medium text-red-900">@{originalPoster.username}</p>
            </div>
            <div>
              <p className="text-sm text-red-700 mb-1">Platform</p>
              <p className="font-medium text-red-900">{originalPoster.platform}</p>
            </div>
            <div>
              <p className="text-sm text-red-700 mb-1">Followers</p>
              <p className="font-medium text-red-900">
                {originalPoster.followers.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-red-700 mb-1">First Posted</p>
              <p className="font-medium text-red-900">
                {new Date(originalPoster.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Node List */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          All Propagators
        </h3>
        <div className="space-y-3">
          {data.nodes.map((node) => (
            <div
              key={node.id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
              onClick={() => setSelectedNode(node)}
            >
              <div className="flex items-center space-x-4">
                <div
                  className={`w-3 h-3 rounded-full ${
                    node.type === 'original'
                      ? 'bg-red-500'
                      : node.type === 'amplifier'
                      ? 'bg-orange-500'
                      : 'bg-blue-500'
                  }`}
                ></div>
                <div>
                  <p className="font-medium text-gray-900">@{node.username}</p>
                  <p className="text-sm text-gray-600">
                    {node.followers.toLocaleString()} followers • {node.platform}
                  </p>
                </div>
              </div>
              <div className="text-right">
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
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(node.timestamp).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
