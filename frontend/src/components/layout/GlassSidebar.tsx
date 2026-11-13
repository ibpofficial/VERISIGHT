import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  ShieldAlert, LayoutDashboard, FilePlus, Briefcase, 
  History, Settings, Users, Activity, LogOut, ChevronRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import type { UserRole } from '../../types';

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
  allowedRoles: UserRole[];
  badge?: string;
}

export const GlassSidebar: React.FC = () => {
  const { user, logout, hasRole } = useAuth();

  const navItems: NavItem[] = [
    {
      name: 'Command Center',
      path: '/dashboard',
      icon: <LayoutDashboard className="w-4 h-4" />,
      allowedRoles: ['ADMINISTRATOR', 'SCREENING_OFFICER', 'SENIOR_REVIEWER', 'AUDITOR'],
    },
    {
      name: 'New Screening',
      path: '/screenings/new',
      icon: <FilePlus className="w-4 h-4" />,
      allowedRoles: ['ADMINISTRATOR', 'SCREENING_OFFICER', 'SENIOR_REVIEWER'],
    },
    {
      name: 'Investigation Cases',
      path: '/cases',
      icon: <Briefcase className="w-4 h-4" />,
      allowedRoles: ['ADMINISTRATOR', 'SCREENING_OFFICER', 'SENIOR_REVIEWER', 'AUDITOR'],
    },
    {
      name: 'Audit Trail',
      path: '/audit',
      icon: <History className="w-4 h-4" />,
      allowedRoles: ['ADMINISTRATOR', 'SENIOR_REVIEWER', 'AUDITOR'],
    },
    {
      name: 'Engine Status',
      path: '/admin/engine-status',
      icon: <Activity className="w-4 h-4" />,
      allowedRoles: ['ADMINISTRATOR', 'SCREENING_OFFICER', 'SENIOR_REVIEWER', 'AUDITOR'],
    },
    {
      name: 'User Management',
      path: '/admin/users',
      icon: <Users className="w-4 h-4" />,
      allowedRoles: ['ADMINISTRATOR'],
    },
    {
      name: 'System Config',
      path: '/admin/config',
      icon: <Settings className="w-4 h-4" />,
      allowedRoles: ['ADMINISTRATOR'],
    },
  ];

  const visibleNav = navItems.filter((item) => hasRole(item.allowedRoles));

  return (
    <aside className="w-64 bg-white/90 backdrop-blur-xl border-r border-slate-200/80 flex flex-col h-screen fixed left-0 top-0 z-30 select-none shadow-sm">
      {/* Brand Header */}
      <div className="h-16 px-5 flex items-center border-b border-slate-200/80 gap-3 bg-white/50">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 to-sky-500 flex items-center justify-center shadow-md shadow-blue-500/20">
          <ShieldAlert className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-bold tracking-wider text-slate-900 text-sm">VERISIGHT</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-mono font-medium">
              v1.0
            </span>
          </div>
          <p className="text-[10px] text-slate-500 font-mono uppercase tracking-tight">MHA • SIH 26188</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold tracking-wider text-slate-400 uppercase font-mono">
          Security Operations
        </div>
        {visibleNav.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 border border-transparent'
              }`
            }
          >
            <div className="flex items-center gap-3">
              {item.icon}
              <span>{item.name}</span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 opacity-40" />
          </NavLink>
        ))}
      </nav>

      {/* User & Station Footer */}
      <div className="p-3 border-t border-slate-200/80 bg-slate-50/50">
        <div className="p-2.5 rounded-lg bg-white border border-slate-200/80 shadow-2xs flex items-center justify-between">
          <div className="truncate mr-2">
            <p className="text-xs font-semibold text-slate-800 truncate">{user?.full_name}</p>
            <p className="text-[10px] font-mono text-blue-600 truncate">{user?.role?.replace('_', ' ')}</p>
          </div>
          <button
            onClick={logout}
            title="Terminate Session"
            className="p-1.5 rounded-md text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
