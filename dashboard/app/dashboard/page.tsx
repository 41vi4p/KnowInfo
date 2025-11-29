'use client';

import { useEffect, useState } from 'react';
import { getMetrics, getClaims, getTrends, Claim, VerificationMetrics, TrendData } from '@/lib/api';
import MetricCard from '@/components/MetricCard';
import ClaimCard from '@/components/ClaimCard';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  Activity,
  Globe,
  Zap,
  Shield,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const STATUS_COLORS = {
  TRUE: '#10b981',
  FALSE: '#ef4444',
  MISLEADING: '#f59e0b',
  UNVERIFIED: '#6b7280',
  OUTDATED: '#9ca3af',
};

const PLATFORM_COLORS: Record<string, string> = {
  Twitter: '#1DA1F2',
  Facebook: '#4267B2',
  Reddit: '#FF4500',
  Telegram: '#0088cc',
  WhatsApp: '#25D366',
};

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<VerificationMetrics | null>(null);
  const [recentClaims, setRecentClaims] = useState<Claim[]>([]);
  const [allClaims, setAllClaims] = useState<Claim[]>([]);
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [metricsData, claimsData, trendsData, allClaimsData] = await Promise.all([
          getMetrics(),
          getClaims({ limit: 5 }),
          getTrends(24),
          getClaims({ limit: 100 }), // Get all claims for statistics
        ]);
        setMetrics(metricsData);
        setRecentClaims(claimsData);
        setTrends(trendsData);
        setAllClaims(allClaimsData);
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const pieData = metrics
    ? [
        { name: 'True', value: metrics.verified_count - metrics.false_claims - metrics.misleading_claims, color: STATUS_COLORS.TRUE },
        { name: 'False', value: metrics.false_claims, color: STATUS_COLORS.FALSE },
        { name: 'Misleading', value: metrics.misleading_claims, color: STATUS_COLORS.MISLEADING },
      ]
    : [];

  // Calculate category distribution
  const categoryData = allClaims.reduce((acc: Record<string, number>, claim) => {
    acc[claim.category] = (acc[claim.category] || 0) + 1;
    return acc;
  }, {});
  const categoryChartData = Object.entries(categoryData)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  // Calculate platform distribution
  const platformData = allClaims.reduce((acc: Record<string, number>, claim) => {
    acc[claim.source_platform] = (acc[claim.source_platform] || 0) + 1;
    return acc;
  }, {});
  const platformChartData = Object.entries(platformData)
    .map(([name, value]) => ({ name, value, color: PLATFORM_COLORS[name] || '#6b7280' }))
    .sort((a, b) => b.value - a.value);

  // Calculate priority distribution
  const priorityData = allClaims.reduce((acc: Record<string, number>, claim) => {
    acc[claim.priority] = (acc[claim.priority] || 0) + 1;
    return acc;
  }, {});
  const priorityChartData = Object.entries(priorityData)
    .map(([name, value]) => ({
      name,
      value,
      color: name === 'P0' ? '#ef4444' : name === 'P1' ? '#f59e0b' : name === 'P2' ? '#3b82f6' : '#6b7280'
    }))
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
        <p className="text-gray-600 mt-2">
          Real-time crisis misinformation detection and verification
        </p>
      </div>

      {/* Metrics Grid */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Claims Today"
            value={metrics.total_claims_today.toLocaleString()}
            icon={Activity}
            iconColor="text-blue-600"
            change={12}
            trend="up"
          />
          <MetricCard
            title="Verified Claims"
            value={metrics.verified_count.toLocaleString()}
            icon={CheckCircle}
            iconColor="text-green-600"
            change={8}
            trend="up"
          />
          <MetricCard
            title="False Claims"
            value={metrics.false_claims.toLocaleString()}
            icon={XCircle}
            iconColor="text-red-600"
            change={-5}
            trend="down"
          />
          <MetricCard
            title="Avg. Verify Time"
            value={`${metrics.avg_verification_time}min`}
            icon={Clock}
            iconColor="text-purple-600"
            change={-15}
            trend="down"
          />
        </div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend Chart */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            24-Hour Trend Analysis
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) =>
                  new Date(value).toLocaleTimeString('en-US', { hour: '2-digit' })
                }
              />
              <YAxis />
              <Tooltip
                labelFormatter={(value) =>
                  new Date(value).toLocaleString('en-US')
                }
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="claims_detected"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Total Claims"
              />
              <Line
                type="monotone"
                dataKey="false_claims"
                stroke="#ef4444"
                strokeWidth={2}
                name="False Claims"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Status Distribution */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Verification Status Distribution
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name}: ${(percent * 100).toFixed(0)}%`
                }
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Accuracy Rate</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {metrics.accuracy_rate}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
            <div className="mt-4 bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${metrics.accuracy_rate}%` }}
              ></div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Active Crises
                </p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {metrics.active_crises}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-600" />
            </div>
            <p className="text-xs text-gray-500 mt-4">
              Currently monitoring across multiple platforms
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Misleading Claims
                </p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {metrics.misleading_claims}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-yellow-600" />
            </div>
            <p className="text-xs text-gray-500 mt-4">
              Require additional context or expert review
            </p>
          </div>
        </div>
      )}

      {/* Additional Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Distribution */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-600" />
            Top Crisis Categories
          </h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={categoryChartData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Platform Distribution */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Globe className="h-5 w-5 text-purple-600" />
            Platform Distribution
          </h2>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={platformChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name}: ${(percent * 100).toFixed(0)}%`
                }
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {platformChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Priority Distribution */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-600" />
            Priority Levels
          </h2>
          <div className="space-y-4 mt-6">
            {priorityChartData.map((priority) => (
              <div key={priority.name}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    {priority.name === 'P0' ? 'Critical (P0)' :
                     priority.name === 'P1' ? 'High (P1)' :
                     priority.name === 'P2' ? 'Medium (P2)' : 'Low (P3)'}
                  </span>
                  <span className="text-sm font-semibold text-gray-900">
                    {priority.value}
                  </span>
                </div>
                <div className="bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full transition-all duration-500"
                    style={{
                      width: `${(priority.value / allClaims.length) * 100}%`,
                      backgroundColor: priority.color,
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Real-Time Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Breakdown */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Verification Status Breakdown
          </h2>
          <div className="space-y-3">
            {allClaims.reduce((acc: Record<string, number>, claim) => {
              acc[claim.status] = (acc[claim.status] || 0) + 1;
              return acc;
            }, {} as Record<string, number>) &&
              Object.entries(
                allClaims.reduce((acc: Record<string, number>, claim) => {
                  acc[claim.status] = (acc[claim.status] || 0) + 1;
                  return acc;
                }, {} as Record<string, number>)
              ).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: STATUS_COLORS[status as keyof typeof STATUS_COLORS] }}
                    ></div>
                    <span className="font-medium text-gray-700">{status}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-2xl font-bold text-gray-900">{count}</span>
                    <span className="text-sm text-gray-500">
                      ({((count / allClaims.length) * 100).toFixed(1)}%)
                    </span>
                  </div>
                </div>
              ))
            }
          </div>
        </div>

        {/* Verification Speed Stats */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Verification Performance
          </h2>
          <div className="space-y-4">
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-green-800">Fastest Verification</span>
                <span className="text-2xl font-bold text-green-900">
                  {Math.min(...allClaims.map(c => c.verification_time || 99)).toFixed(1)}min
                </span>
              </div>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-blue-800">Average Time</span>
                <span className="text-2xl font-bold text-blue-900">
                  {metrics?.avg_verification_time}min
                </span>
              </div>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-orange-800">Slowest Verification</span>
                <span className="text-2xl font-bold text-orange-900">
                  {Math.max(...allClaims.map(c => c.verification_time || 0)).toFixed(1)}min
                </span>
              </div>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-purple-800">Total Processed</span>
                <span className="text-2xl font-bold text-purple-900">
                  {allClaims.length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Claims */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">
            Recent Claims
          </h2>
          <a
            href="/dashboard/claims"
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            View All →
          </a>
        </div>
        <div className="space-y-4">
          {recentClaims.map((claim) => (
            <ClaimCard
              key={claim.claim_id}
              claim={claim}
              onClick={() => {
                window.location.href = `/dashboard/claims/${claim.claim_id}`;
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
