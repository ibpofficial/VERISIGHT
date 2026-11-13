import React from 'react';
import { Outlet } from 'react-router-dom';
import { GlassSidebar } from './GlassSidebar';
import { GlassTopbar } from './GlassTopbar';

export const AppShell: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 flex">
      {/* Permanent Fixed Glass Sidebar */}
      <GlassSidebar />

      {/* Main Execution Surface */}
      <div className="flex-1 pl-64 flex flex-col min-h-screen">
        {/* Fixed Topbar */}
        <GlassTopbar />

        {/* Dynamic Route Content */}
        <main className="flex-1 pt-16 p-6 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
