/**
 * API Integration Layer with Sample Data Fallback
 * Connects to KnowInfo Crisis Misinformation Detection Backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Error handler with fallback to sample data
async function fetchWithFallback<T>(endpoint: string, sampleData: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store', // Always get fresh data
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.warn(`API call failed for ${endpoint}, using sample data:`, error);
    return sampleData;
  }
}

// Types
export interface Claim {
  claim_id: string;
  claim_text: string;
  status: 'TRUE' | 'FALSE' | 'MISLEADING' | 'UNVERIFIED' | 'OUTDATED';
  confidence_score: number;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  category: string;
  source_platform: string;
  created_at: string;
  verification_time?: number;
}

export interface VerificationMetrics {
  total_claims_today: number;
  verified_count: number;
  false_claims: number;
  misleading_claims: number;
  avg_verification_time: number;
  accuracy_rate: number;
  active_crises: number;
}

export interface TrendData {
  timestamp: string;
  claims_detected: number;
  false_claims: number;
  velocity_spike: boolean;
}

export interface GeographicData {
  country: string;
  latitude: number;
  longitude: number;
  claims_count: number;
  false_claims_count: number;
}

export interface PatientZeroNode {
  id: string;
  type: 'original' | 'amplifier' | 'sharer';
  username: string;
  followers: number;
  timestamp: string;
  platform: string;
}

export interface PatientZeroLink {
  source: string;
  target: string;
  shares: number;
}

// Sample Data
const SAMPLE_METRICS: VerificationMetrics = {
  total_claims_today: 2847,
  verified_count: 2456,
  false_claims: 523,
  misleading_claims: 289,
  avg_verification_time: 2.8,
  accuracy_rate: 96.2,
  active_crises: 12,
};

const SAMPLE_CLAIMS: Claim[] = [
  {
    claim_id: 'claim_001',
    claim_text: 'Breaking: Earthquake magnitude 7.8 hits California coast, tsunami warning issued',
    status: 'FALSE',
    confidence_score: 97,
    priority: 'P0',
    category: 'Natural Disaster',
    source_platform: 'Twitter',
    created_at: new Date(Date.now() - 1200000).toISOString(),
    verification_time: 1.9,
  },
  {
    claim_id: 'claim_002',
    claim_text: 'Hospital reports shortage of critical medications for heart patients',
    status: 'TRUE',
    confidence_score: 94,
    priority: 'P1',
    category: 'Health/Medical',
    source_platform: 'Reddit',
    created_at: new Date(Date.now() - 2400000).toISOString(),
    verification_time: 3.2,
  },
  {
    claim_id: 'claim_003',
    claim_text: 'Wildfire spreading rapidly, 5000+ residents evacuated in northern region',
    status: 'TRUE',
    confidence_score: 99,
    priority: 'P0',
    category: 'Environmental/Climate',
    source_platform: 'Telegram',
    created_at: new Date(Date.now() - 3600000).toISOString(),
    verification_time: 1.5,
  },
  {
    claim_id: 'claim_004',
    claim_text: 'New study shows experimental drug cures cancer with 100% success rate',
    status: 'MISLEADING',
    confidence_score: 88,
    priority: 'P2',
    category: 'Health/Medical',
    source_platform: 'Facebook',
    created_at: new Date(Date.now() - 5400000).toISOString(),
    verification_time: 4.8,
  },
  {
    claim_id: 'claim_005',
    claim_text: 'Government announces mandatory evacuations due to chemical plant explosion',
    status: 'FALSE',
    confidence_score: 96,
    priority: 'P0',
    category: 'Safety/Security',
    source_platform: 'WhatsApp',
    created_at: new Date(Date.now() - 7200000).toISOString(),
    verification_time: 2.1,
  },
  {
    claim_id: 'claim_006',
    claim_text: 'Flash flooding alerts issued for metropolitan area, shelters opening',
    status: 'TRUE',
    confidence_score: 98,
    priority: 'P0',
    category: 'Natural Disaster',
    source_platform: 'Twitter',
    created_at: new Date(Date.now() - 9000000).toISOString(),
    verification_time: 1.3,
  },
  {
    claim_id: 'claim_007',
    claim_text: 'Power grid failure imminent, rolling blackouts scheduled nationwide',
    status: 'FALSE',
    confidence_score: 93,
    priority: 'P1',
    category: 'Infrastructure',
    source_platform: 'Telegram',
    created_at: new Date(Date.now() - 10800000).toISOString(),
    verification_time: 3.6,
  },
  {
    claim_id: 'claim_008',
    claim_text: 'Food safety alert: Major grocery chain recalls contaminated produce',
    status: 'TRUE',
    confidence_score: 97,
    priority: 'P1',
    category: 'Health/Medical',
    source_platform: 'Reddit',
    created_at: new Date(Date.now() - 12600000).toISOString(),
    verification_time: 2.4,
  },
  {
    claim_id: 'claim_009',
    claim_text: 'Military coup underway in neighboring country, borders closing',
    status: 'UNVERIFIED',
    confidence_score: 52,
    priority: 'P1',
    category: 'Political/Geopolitical',
    source_platform: 'Twitter',
    created_at: new Date(Date.now() - 14400000).toISOString(),
    verification_time: 8.2,
  },
  {
    claim_id: 'claim_010',
    claim_text: 'COVID-19 variant immune to all vaccines, WHO emergency meeting',
    status: 'FALSE',
    confidence_score: 99,
    priority: 'P0',
    category: 'Health/Medical',
    source_platform: 'Facebook',
    created_at: new Date(Date.now() - 16200000).toISOString(),
    verification_time: 1.7,
  },
  {
    claim_id: 'claim_011',
    claim_text: 'Drinking water supply contains high lead levels, boil water notice issued',
    status: 'MISLEADING',
    confidence_score: 76,
    priority: 'P1',
    category: 'Environmental/Climate',
    source_platform: 'WhatsApp',
    created_at: new Date(Date.now() - 18000000).toISOString(),
    verification_time: 5.9,
  },
  {
    claim_id: 'claim_012',
    claim_text: 'Hurricane category 5 expected to make landfall in 6 hours',
    status: 'OUTDATED',
    confidence_score: 91,
    priority: 'P0',
    category: 'Natural Disaster',
    source_platform: 'Twitter',
    created_at: new Date(Date.now() - 19800000).toISOString(),
    verification_time: 2.3,
  },
];

const SAMPLE_TRENDS: TrendData[] = Array.from({ length: 24 }, (_, i) => {
  const baselineClaims = 45 + Math.sin(i / 3) * 20;
  const variance = Math.random() * 15;
  const claims = Math.floor(baselineClaims + variance);
  const falseClaims = Math.floor(claims * (0.15 + Math.random() * 0.1));

  return {
    timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
    claims_detected: claims,
    false_claims: falseClaims,
    velocity_spike: i % 8 === 0 || Math.random() > 0.9,
  };
});

const SAMPLE_GEOGRAPHIC: GeographicData[] = [
  { country: 'USA', latitude: 37.0902, longitude: -95.7129, claims_count: 687, false_claims_count: 142 },
  { country: 'India', latitude: 20.5937, longitude: 78.9629, claims_count: 534, false_claims_count: 98 },
  { country: 'Brazil', latitude: -14.2350, longitude: -51.9253, claims_count: 412, false_claims_count: 87 },
  { country: 'UK', latitude: 55.3781, longitude: -3.4360, claims_count: 289, false_claims_count: 56 },
  { country: 'Nigeria', latitude: 9.0820, longitude: 8.6753, claims_count: 267, false_claims_count: 73 },
  { country: 'Mexico', latitude: 23.6345, longitude: -102.5528, claims_count: 198, false_claims_count: 45 },
  { country: 'Germany', latitude: 51.1657, longitude: 10.4515, claims_count: 176, false_claims_count: 31 },
  { country: 'Philippines', latitude: 12.8797, longitude: 121.7740, claims_count: 154, false_claims_count: 42 },
  { country: 'Turkey', latitude: 38.9637, longitude: 35.2433, claims_count: 143, false_claims_count: 38 },
  { country: 'South Africa', latitude: -30.5595, longitude: 22.9375, claims_count: 129, false_claims_count: 29 },
  { country: 'Australia', latitude: -25.2744, longitude: 133.7751, claims_count: 98, false_claims_count: 19 },
  { country: 'Japan', latitude: 36.2048, longitude: 138.2529, claims_count: 87, false_claims_count: 15 },
];

const SAMPLE_PATIENT_ZERO = {
  nodes: [
    { id: '1', type: 'original' as const, username: '@emergency_alert_fake', followers: 2847, timestamp: new Date(Date.now() - 86400000).toISOString(), platform: 'Twitter' },
    { id: '2', type: 'amplifier' as const, username: '@breaking_news_now', followers: 87234, timestamp: new Date(Date.now() - 79200000).toISOString(), platform: 'Twitter' },
    { id: '3', type: 'amplifier' as const, username: '@viral_updates_bot', followers: 234567, timestamp: new Date(Date.now() - 72000000).toISOString(), platform: 'Twitter' },
    { id: '4', type: 'sharer' as const, username: 'concerned_citizen_42', followers: 456, timestamp: new Date(Date.now() - 64800000).toISOString(), platform: 'Reddit' },
    { id: '5', type: 'sharer' as const, username: '@local_news_share', followers: 3421, timestamp: new Date(Date.now() - 57600000).toISOString(), platform: 'Twitter' },
    { id: '6', type: 'amplifier' as const, username: 'telegram_news_channel', followers: 45789, timestamp: new Date(Date.now() - 50400000).toISOString(), platform: 'Telegram' },
    { id: '7', type: 'sharer' as const, username: '@family_group_admin', followers: 189, timestamp: new Date(Date.now() - 43200000).toISOString(), platform: 'WhatsApp' },
    { id: '8', type: 'sharer' as const, username: 'reddit_news_mod', followers: 12456, timestamp: new Date(Date.now() - 36000000).toISOString(), platform: 'Reddit' },
  ],
  links: [
    { source: '1', target: '2', shares: 1247 },
    { source: '2', target: '3', shares: 4523 },
    { source: '1', target: '4', shares: 234 },
    { source: '4', target: '5', shares: 567 },
    { source: '3', target: '6', shares: 2891 },
    { source: '2', target: '7', shares: 156 },
    { source: '6', target: '8', shares: 892 },
    { source: '5', target: '8', shares: 445 },
  ],
};

// API Functions
export async function getMetrics(): Promise<VerificationMetrics> {
  return fetchWithFallback('/api/metrics', SAMPLE_METRICS);
}

export async function getClaims(filters?: {
  status?: string;
  priority?: string;
  limit?: number;
}): Promise<Claim[]> {
  const params = new URLSearchParams(filters as any);
  return fetchWithFallback(`/api/claims?${params}`, SAMPLE_CLAIMS);
}

export async function getTrends(hours: number = 24): Promise<TrendData[]> {
  return fetchWithFallback(`/api/trends?hours=${hours}`, SAMPLE_TRENDS);
}

export async function getGeographicData(): Promise<GeographicData[]> {
  return fetchWithFallback('/api/geographic', SAMPLE_GEOGRAPHIC);
}

export async function getPatientZero(claimId: string): Promise<{ nodes: PatientZeroNode[]; links: PatientZeroLink[] }> {
  return fetchWithFallback(`/api/patient-zero/${claimId}`, SAMPLE_PATIENT_ZERO);
}

export async function getClaimDetails(claimId: string): Promise<Claim & {
  explanation: string;
  sources: Array<{ title: string; url: string; credibility: string }>;
  propagation_tree_size: number;
}> {
  const claimDetailsMap: Record<string, any> = {
    claim_001: {
      ...SAMPLE_CLAIMS[0],
      explanation: 'Cross-referenced with USGS seismic monitoring systems and NOAA tsunami warning center. No earthquake of this magnitude has been detected in California. The Pacific Tsunami Warning Center has issued no alerts for the U.S. West Coast. This appears to be fabricated panic-inducing content.',
      sources: [
        { title: 'USGS Earthquake Hazards Program', url: 'https://earthquake.usgs.gov', credibility: 'high' },
        { title: 'NOAA Tsunami Warning Center', url: 'https://tsunami.gov', credibility: 'high' },
        { title: 'California Emergency Services', url: 'https://caloes.ca.gov', credibility: 'high' },
      ],
      propagation_tree_size: 2847,
    },
    claim_002: {
      ...SAMPLE_CLAIMS[1],
      explanation: 'Verified through hospital official statement and pharmaceutical supply chain databases. Local hospital has confirmed temporary shortage of specific cardiac medications due to supply chain disruption. Public health department has issued guidance for patients and alternative medication protocols.',
      sources: [
        { title: 'Hospital Official Press Release', url: 'https://hospital.org/press', credibility: 'high' },
        { title: 'FDA Drug Shortage Database', url: 'https://fda.gov/shortages', credibility: 'high' },
        { title: 'Public Health Department Alert', url: 'https://health.gov/alerts', credibility: 'high' },
      ],
      propagation_tree_size: 892,
    },
    claim_003: {
      ...SAMPLE_CLAIMS[2],
      explanation: 'Confirmed by state fire department, satellite imagery, and emergency management services. Wildfire has spread to 15,000 acres with mandatory evacuation orders for multiple communities. Air quality alerts in effect for surrounding regions.',
      sources: [
        { title: 'State Fire Department Incident Report', url: 'https://fire.state.gov/incidents', credibility: 'high' },
        { title: 'NASA FIRMS Satellite Data', url: 'https://firms.nasa.gov', credibility: 'high' },
        { title: 'Emergency Management Evacuation Orders', url: 'https://emergency.gov/evacuations', credibility: 'high' },
      ],
      propagation_tree_size: 4523,
    },
  };

  const sampleDetail = claimDetailsMap[claimId] || {
    ...SAMPLE_CLAIMS[0],
    claim_id: claimId,
    explanation: 'This claim is currently under investigation. Our verification team is cross-referencing multiple authoritative sources to determine accuracy. Preliminary analysis suggests conflicting information that requires expert review.',
    sources: [
      { title: 'Fact-Check Database', url: 'https://factcheck.org', credibility: 'high' },
      { title: 'Reuters Verification Unit', url: 'https://reuters.com/fact-check', credibility: 'high' },
      { title: 'AP Fact Check', url: 'https://apnews.com/hub/fact-checking', credibility: 'high' },
    ],
    propagation_tree_size: 1567,
  };

  return fetchWithFallback(`/api/claims/${claimId}`, sampleDetail);
}
