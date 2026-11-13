import React, { useState, useEffect } from 'react';
import { 
  UserCheck, UserX, Edit2, RotateCcw, 
  CheckCircle2, AlertCircle
} from 'lucide-react';
import { GlassCard } from '../components/glass/GlassCard';
import { GlassButton } from '../components/glass/GlassButton';
import { GlassModal } from '../components/glass/GlassModal';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { apiClient } from '../services/api';
import type { User, UserRole } from '../types';

export const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Edit role modal
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [selectedRole, setSelectedRole] = useState<UserRole>('SCREENING_OFFICER');
  const [isUpdatingRole, setIsUpdatingRole] = useState(false);

  const fetchUsers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/admin/users');
      setUsers(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch user directory.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleStatus = async (user: User) => {
    try {
      const res = await apiClient.patch(`/admin/users/${user.id}/status`, {
        is_active: !user.is_active,
      });
      setUsers((prev) => prev.map((u) => (u.id === user.id ? res.data : u)));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to toggle account activation.');
    }
  };

  const handleSaveRole = async () => {
    if (!editingUser) return;
    setIsUpdatingRole(true);
    try {
      const res = await apiClient.patch(`/admin/users/${editingUser.id}/role`, {
        role: selectedRole,
      });
      setUsers((prev) => prev.map((u) => (u.id === editingUser.id ? res.data : u)));
      setEditingUser(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update user security role.');
    } finally {
      setIsUpdatingRole(false);
    }
  };

  const getRoleBadge = (role: UserRole) => {
    switch (role) {
      case 'ADMINISTRATOR':
        return 'bg-purple-50 text-purple-700 border-purple-200 font-bold';
      case 'SENIOR_REVIEWER':
        return 'bg-blue-50 text-blue-700 border-blue-200 font-semibold';
      case 'SCREENING_OFFICER':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200 font-medium';
      case 'AUDITOR':
        return 'bg-amber-50 text-amber-700 border-amber-200 font-semibold';
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            Officer & Role Management
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold font-mono">
              RBAC Governed
            </span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Maintain security personnel credentials, role assignments, and account access permissions.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={fetchUsers}
            icon={<RotateCcw className="w-4 h-4" />}
          >
            Refresh Users
          </GlassButton>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Users Table */}
      {isLoading ? (
        <div className="space-y-3">
          <LoadingSkeleton className="h-12 w-full" count={5} />
        </div>
      ) : (
        <GlassCard className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50/70">
                  <th className="py-3 px-4">Officer Name & Badge</th>
                  <th className="py-3 px-4">Email Address</th>
                  <th className="py-3 px-4">Assigned Role</th>
                  <th className="py-3 px-4">Account Status</th>
                  <th className="py-3 px-4">Created Timestamp</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{u.full_name}</div>
                      <div className="font-mono text-[10px] text-slate-400">
                        Badge: {u.badge_number || 'N/A'}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-700">{u.email}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] border ${getRoleBadge(u.role)}`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {u.is_active ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-green-700 bg-green-50 px-2 py-0.5 rounded-full border border-green-200">
                          <CheckCircle2 className="w-3 h-3" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-red-700 bg-red-50 px-2 py-0.5 rounded-full border border-red-200">
                          Deactivated
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-500">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <GlassButton
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setEditingUser(u);
                          setSelectedRole(u.role);
                        }}
                        icon={<Edit2 className="w-3.5 h-3.5" />}
                      >
                        Change Role
                      </GlassButton>
                      <GlassButton
                        size="sm"
                        variant={u.is_active ? 'destructive' : 'secondary'}
                        onClick={() => handleToggleStatus(u)}
                        icon={u.is_active ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                      >
                        {u.is_active ? 'Deactivate' : 'Activate'}
                      </GlassButton>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}

      {/* Role Change Modal */}
      {editingUser && (
        <GlassModal
          isOpen={true}
          onClose={() => setEditingUser(null)}
          title={`Modify Security Role: ${editingUser.full_name}`}
        >
          <div className="space-y-4 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Select New Access Level
              </label>
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value as UserRole)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="SCREENING_OFFICER">SCREENING_OFFICER — Document intake, OCR correction, case triage</option>
                <option value="SENIOR_REVIEWER">SENIOR_REVIEWER — Forensic deep inspection & manual risk override authority</option>
                <option value="AUDITOR">AUDITOR — Read-only access to cryptographic ledger & statutory dossiers</option>
                <option value="ADMINISTRATOR">ADMINISTRATOR — Full system governance & role configuration</option>
              </select>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
              <GlassButton
                variant="ghost"
                size="sm"
                onClick={() => setEditingUser(null)}
              >
                Cancel
              </GlassButton>
              <GlassButton
                variant="primary"
                size="sm"
                disabled={isUpdatingRole}
                onClick={handleSaveRole}
              >
                {isUpdatingRole ? 'Updating...' : 'Confirm Role Assignment'}
              </GlassButton>
            </div>
          </div>
        </GlassModal>
      )}
    </div>
  );
};
