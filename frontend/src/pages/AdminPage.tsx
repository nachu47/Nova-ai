import { useState } from 'react';
import { ShieldCheck, Building2, Users, Phone, FileText, ToggleLeft, AlertCircle, Plus, Power, Activity } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';
import { api, errorMessage } from '@/services/api';
import type { User } from '@/types';
import { ProviderSettings } from '@/components/ProviderSettings';

type Platform = {
  organizations: number;
  users: number;
  calls: number;
  usage_revenue: number;
  active_organizations?: number;
  voice_agents?: number;
  calls_today?: number;
  platform_health?: string;
};

type GlobalOrg = {
  id: string;
  name: string;
  plan: string;
  owner_email: string;
  owner_name: string;
  users: number;
  voice_agents: number;
  calls: number;
  usage: number;
  created_at: string;
};

type GlobalUser = User & {
  organization_name?: string;
};

type GlobalCall = {
  id: string;
  organization_name: string;
  caller_number: string;
  callee_number: string;
  status: string;
  duration_seconds: number;
  created_at: string;
};

type AuditLog = {
  id: string;
  action: string;
  entity_type: string;
  actor_email: string;
  organization_name: string;
  created_at: string;
};

export function AdminPage() {
  const { user } = useAuth();
  const isSuperadmin = user?.role === 'superadmin';
  const [activeTab, setActiveTab] = useState<'overview' | 'orgs' | 'users' | 'calls' | 'logs'>('overview');
  
  // Workspace-level hooks
  const { data: workspaceUsers, reload: reloadWorkspaceUsers } = useApi<User[]>('/admin/users');
  const { data: platform, reload: reloadPlatform } = useApi<Platform>('/admin/platform');
  
  // Superadmin-level hooks
  const { data: orgs, reload: reloadOrgs } = useApi<GlobalOrg[]>(isSuperadmin ? '/admin/organizations' : null);
  const { data: globalUsers, reload: reloadGlobalUsers } = useApi<GlobalUser[]>(isSuperadmin ? '/admin/global-users' : null);
  const { data: globalCalls } = useApi<{ total: number; items: GlobalCall[] }>(isSuperadmin ? '/admin/global-calls' : null);
  const { data: auditLogs } = useApi<AuditLog[]>(isSuperadmin ? '/admin/global-audit-logs' : null);

  const [message, setMessage] = useState('');
  const [newOrgName, setNewOrgName] = useState('');
  const [creatingOrg, setCreatingOrg] = useState(false);

  if (user?.role !== 'owner' && user?.role !== 'admin' && user?.role !== 'superadmin') {
    return <p className="text-destructive font-semibold p-4">Administrator access is required.</p>;
  }

  async function toggleUser(target: User) {
    try {
      await api.patch(`/admin/users/${target.id}`, { is_active: !target.is_active });
      setMessage(`${target.full_name} was ${target.is_active ? 'deactivated' : 'activated'}.`);
      await reloadWorkspaceUsers();
    } catch (err) {
      setMessage(errorMessage(err));
    }
  }

  async function handleCreateOrg(e: React.FormEvent) {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    setCreatingOrg(true);
    try {
      await api.post('/admin/organizations', { name: newOrgName, plan: 'starter' });
      setNewOrgName('');
      setMessage(`Organization "${newOrgName}" created successfully.`);
      await reloadOrgs();
      await reloadPlatform();
    } catch (err) {
      setMessage(errorMessage(err));
    } finally {
      setCreatingOrg(false);
    }
  }

  async function toggleOrgStatus(org: GlobalOrg) {
    try {
      if (org.plan === 'suspended') {
        await api.post(`/admin/organizations/${org.id}/activate`);
        setMessage(`Organization "${org.name}" activated.`);
      } else {
        await api.post(`/admin/organizations/${org.id}/suspend`);
        setMessage(`Organization "${org.name}" suspended.`);
      }
      await reloadOrgs();
      await reloadPlatform();
    } catch (err) {
      setMessage(errorMessage(err));
    }
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 sm:p-8 rounded-3xl text-white shadow-xl">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge className={isSuperadmin ? 'bg-amber-400 text-slate-900 font-bold' : 'bg-indigo-500 text-white'}>
              {isSuperadmin ? 'MASTER PLATFORM SUPERADMIN' : 'ORGANIZATION ADMIN'}
            </Badge>
            <span className="text-xs text-slate-300">• Logged in as {user.email}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            {isSuperadmin ? 'Master Control Center' : 'Workspace Administration'}
          </h1>
          <p className="text-sm text-slate-300 mt-1 max-w-xl">
            {isSuperadmin
              ? 'Full platform control across all customer organizations, global calls, users, and audit logs.'
              : 'Manage workspace users, voice providers, API keys, and operational settings.'}
          </p>
        </div>
        {isSuperadmin && (
          <div className="flex items-center gap-3">
            <Button
              onClick={() => reloadPlatform()}
              variant="outline"
              className="border-white/20 bg-white/10 hover:bg-white/20 text-white"
            >
              <Activity className="h-4 w-4 mr-2" />
              Refresh Metrics
            </Button>
          </div>
        )}
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 text-sm font-medium flex items-center justify-between shadow-sm">
          <span>{message}</span>
          <button onClick={() => setMessage('')} className="text-indigo-500 hover:text-indigo-800 text-xs">Dismiss</button>
        </div>
      )}

      {/* Superadmin Mode Tabs */}
      {isSuperadmin && (
        <div className="flex flex-wrap gap-2 p-1.5 bg-slate-100 dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700">
          {[
            { id: 'overview', label: 'Platform Metrics', icon: ShieldCheck },
            { id: 'orgs', label: `Organizations (${orgs?.length || 0})`, icon: Building2 },
            { id: 'users', label: `Global Users (${globalUsers?.length || 0})`, icon: Users },
            { id: 'calls', label: `Global Calls (${globalCalls?.total || 0})`, icon: Phone },
            { id: 'logs', label: 'Security Audit Logs', icon: FileText },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                  active
                    ? 'bg-white dark:bg-slate-900 text-[#7455f6] shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Platform Overview Metrics Cards */}
      {(!isSuperadmin || activeTab === 'overview') && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="border-indigo-100 shadow-sm">
            <CardContent className="p-5">
              <Building2 className="h-6 w-6 text-indigo-600" />
              <p className="mt-3 text-3xl font-extrabold text-slate-900">{platform?.organizations || 1}</p>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Tenant Organizations</p>
            </CardContent>
          </Card>
          <Card className="border-indigo-100 shadow-sm">
            <CardContent className="p-5">
              <Users className="h-6 w-6 text-indigo-600" />
              <p className="mt-3 text-3xl font-extrabold text-slate-900">{platform?.users || 0}</p>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Platform Users</p>
            </CardContent>
          </Card>
          <Card className="border-indigo-100 shadow-sm">
            <CardContent className="p-5">
              <Phone className="h-6 w-6 text-indigo-600" />
              <p className="mt-3 text-3xl font-extrabold text-slate-900">{platform?.calls || 0}</p>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Total AI Calls</p>
            </CardContent>
          </Card>
          <Card className="border-indigo-100 shadow-sm">
            <CardContent className="p-5">
              <ShieldCheck className="h-6 w-6 text-emerald-600" />
              <p className="mt-3 text-3xl font-extrabold text-slate-900">
                £{(platform?.usage_revenue || 0).toFixed(2)}
              </p>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Platform Revenue</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB: Organizations List (Superadmin) */}
      {isSuperadmin && activeTab === 'orgs' && (
        <div className="space-y-6">
          {/* Create New Tenant Form */}
          <Card className="border-indigo-100 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Plus className="h-5 w-5 text-[#7455f6]" />
                Provision New Tenant Organization
              </CardTitle>
              <CardDescription>Manually create an isolated company organization account.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateOrg} className="flex gap-3 max-w-md">
                <input
                  type="text"
                  placeholder="Company / Organization Name"
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                  required
                  className="h-10 flex-1 rounded-xl border border-slate-300 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#7455f6]"
                />
                <Button disabled={creatingOrg} className="bg-[#7455f6] hover:bg-[#6242e2] text-white font-bold">
                  {creatingOrg ? 'Creating…' : 'Create Tenant'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Organizations Table */}
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>All Platform Organizations</CardTitle>
              <CardDescription>Full list of active customer tenant environments on your platform.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Organization</TableHead>
                    <TableHead>Owner</TableHead>
                    <TableHead>Plan Status</TableHead>
                    <TableHead>Users</TableHead>
                    <TableHead>AI Agents</TableHead>
                    <TableHead>Calls</TableHead>
                    <TableHead>Usage</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orgs?.map((org) => (
                    <TableRow key={org.id}>
                      <TableCell className="font-bold text-slate-800">{org.name}</TableCell>
                      <TableCell>
                        <div className="font-medium text-xs text-slate-700">{org.owner_name}</div>
                        <div className="text-[11px] text-slate-400">{org.owner_email}</div>
                      </TableCell>
                      <TableCell>
                        <Badge className={org.plan === 'suspended' ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-800'}>
                          {org.plan.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-semibold">{org.users}</TableCell>
                      <TableCell className="font-semibold">{org.voice_agents}</TableCell>
                      <TableCell className="font-semibold">{org.calls}</TableCell>
                      <TableCell className="font-semibold text-emerald-600">£{org.usage.toFixed(2)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant={org.plan === 'suspended' ? 'default' : 'outline'}
                          onClick={() => toggleOrgStatus(org)}
                          className={org.plan === 'suspended' ? 'bg-emerald-600 hover:bg-emerald-700 text-white' : 'text-red-600 border-red-200 hover:bg-red-50'}
                        >
                          <Power className="h-3.5 w-3.5 mr-1" />
                          {org.plan === 'suspended' ? 'Activate' : 'Suspend'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB: Global Users (Superadmin) */}
      {isSuperadmin && activeTab === 'users' && (
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle>All Platform Users</CardTitle>
            <CardDescription>Cross-tenant view of every user account registered across companies.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User Name & Email</TableHead>
                  <TableHead>Organization</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {globalUsers?.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell>
                      <div className="font-bold text-slate-800">{u.full_name}</div>
                      <div className="text-xs text-slate-500">{u.email}</div>
                    </TableCell>
                    <TableCell className="font-semibold text-indigo-700">{u.organization_name || 'N/A'}</TableCell>
                    <TableCell>
                      <Badge className={u.role === 'superadmin' ? 'bg-amber-100 text-amber-900 font-bold' : 'bg-slate-100 text-slate-700'}>
                        {u.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={u.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* TAB: Global Calls (Superadmin) */}
      {isSuperadmin && activeTab === 'calls' && (
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle>Global AI Calls Stream</CardTitle>
            <CardDescription>Live call logs across all customer tenant organizations.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Company</TableHead>
                  <TableHead>Caller</TableHead>
                  <TableHead>Callee</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {globalCalls?.items.map((call) => (
                  <TableRow key={call.id}>
                    <TableCell className="font-bold text-indigo-700">{call.organization_name}</TableCell>
                    <TableCell className="font-mono text-xs">{call.caller_number || 'Inbound Stream'}</TableCell>
                    <TableCell className="font-mono text-xs">{call.callee_number || 'AI Agent'}</TableCell>
                    <TableCell>
                      <Badge className={call.status === 'completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'}>
                        {call.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-semibold">{call.duration_seconds}s</TableCell>
                    <TableCell className="text-xs text-slate-500">
                      {new Date(call.created_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* TAB: Security Audit Logs (Superadmin) */}
      {isSuperadmin && activeTab === 'logs' && (
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle>Global System Audit Trail</CardTitle>
            <CardDescription>Real-time security logs of admin actions and platform events.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Action</TableHead>
                  <TableHead>Actor Email</TableHead>
                  <TableHead>Organization</TableHead>
                  <TableHead>Entity Type</TableHead>
                  <TableHead>Timestamp</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {auditLogs?.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="font-mono text-xs font-bold text-indigo-700">{log.action}</TableCell>
                    <TableCell className="text-xs font-medium text-slate-800">{log.actor_email}</TableCell>
                    <TableCell className="text-xs text-slate-600">{log.organization_name}</TableCell>
                    <TableCell className="text-xs text-slate-500">{log.entity_type}</TableCell>
                    <TableCell className="text-xs text-slate-500">
                      {new Date(log.created_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Regular Workspace Admin View (Non-Superadmin) */}
      {!isSuperadmin && (
        <>
          <ProviderSettings />
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Workspace Users</CardTitle>
              <CardDescription>Manage user accounts within your organization.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Verified</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {workspaceUsers?.map((target) => (
                    <TableRow key={target.id}>
                      <TableCell>
                        <div className="font-medium text-slate-800">{target.full_name}</div>
                        <div className="text-xs text-slate-500">{target.email}</div>
                      </TableCell>
                      <TableCell className="capitalize font-semibold">{target.role}</TableCell>
                      <TableCell>{target.is_verified ? 'Yes' : 'No'}</TableCell>
                      <TableCell>
                        <Badge className={target.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}>
                          {target.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={target.id === user.id}
                          onClick={() => void toggleUser(target)}
                        >
                          {target.is_active ? 'Deactivate' : 'Activate'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
