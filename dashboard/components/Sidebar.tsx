'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Shield,
  Network,
  Map,
  Settings,
  AlertTriangle,
  Activity,
} from 'lucide-react';

const navigation = [
  { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Real-Time Monitoring', href: '/dashboard/monitoring', icon: Activity },
  { name: 'Claim Verification', href: '/dashboard/claims', icon: Shield },
  { name: 'Patient Zero Tracking', href: '/dashboard/patient-zero', icon: Network },
  { name: 'Geographic Spread', href: '/dashboard/geographic', icon: Map },
  { name: 'Active Alerts', href: '/dashboard/alerts', icon: AlertTriangle },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col w-64 bg-gray-900 h-screen fixed left-0 top-0">
      {/* Logo */}
      <div className="flex items-center h-16 px-6 bg-gray-950 border-b border-gray-800">
        <Shield className="h-8 w-8 text-blue-500" />
        <span className="ml-3 text-xl font-bold text-white">KnowInfo</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <Icon className="h-5 w-5 mr-3" />
              <span className="text-sm font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>System Status</span>
          <span className="flex items-center">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
            Online
          </span>
        </div>
      </div>
    </div>
  );
}
