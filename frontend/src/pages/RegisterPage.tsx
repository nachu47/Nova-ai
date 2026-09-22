import { useState, type FormEvent } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { Activity, Building2, User as UserIcon, Mail, Lock, Globe, ArrowRight } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { errorMessage } from '@/services/api';

export function RegisterPage() {
  const { user, register } = useAuth();
  const [form, setForm] = useState({
    organization_name: '',
    full_name: '',
    email: '',
    password: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await register(form);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative min-h-screen w-full bg-[#f0eaff] overflow-hidden">
      {/* Background Shapes */}
      <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full border border-white/40 shadow-[inset_0_0_100px_rgba(255,255,255,0.5)] bg-gradient-to-br from-white/20 to-transparent backdrop-blur-3xl" />
      <div className="absolute -bottom-40 -right-40 w-[800px] h-[800px] rounded-full border border-white/20 shadow-[inset_0_0_100px_rgba(255,255,255,0.3)] bg-gradient-to-tl from-[#e3d5ff]/40 to-transparent backdrop-blur-2xl" />

      {/* Scrollable container */}
      <div className="relative z-10 min-h-screen w-full flex items-center justify-center p-4 sm:p-8 overflow-y-auto">
        <div className="w-full max-w-[480px] p-6 sm:p-10 rounded-3xl sm:rounded-[32px] bg-white/30 backdrop-blur-xl border border-white/60 shadow-[0_8px_32px_0_rgba(31,38,135,0.05)] my-auto">
          {/* Header */}
          <div className="mb-6">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#7455f6] to-[#9b7aff] text-white shadow-lg shadow-indigo-500/30 mb-6">
              <Activity className="h-7 w-7" />
            </div>
            <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Create Workspace</h1>
            <p className="text-sm text-slate-500 mt-1">Start your isolated AI voice tenant account.</p>
          </div>

          {/* Mode Switcher Tabs */}
          <div className="flex p-1.5 bg-slate-900/5 backdrop-blur-md rounded-2xl mb-6 border border-white/60">
            <Link
              to="/login"
              className="flex-1 text-center py-2 text-xs sm:text-sm font-medium rounded-xl text-slate-600 hover:text-slate-900 transition-all"
            >
              Sign In
            </Link>
            <span className="flex-1 text-center py-2 text-xs sm:text-sm font-bold rounded-xl bg-white text-[#7455f6] shadow-sm transition-all">
              Create Account
            </span>
          </div>

          {/* Form */}
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-[13px] font-bold text-slate-700 ml-1">Organization Name</label>
              <div className="relative flex items-center">
                <Building2 className="absolute left-4 h-4 w-4 text-[#8b6dff]" />
                <input
                  type="text"
                  placeholder="Acme Corp"
                  value={form.organization_name}
                  onChange={(e) => setForm({ ...form, organization_name: e.target.value })}
                  required
                  className="h-12 w-full rounded-xl border border-white/80 bg-white/40 pl-11 pr-4 text-sm text-slate-800 placeholder:text-slate-400 focus:border-[#8b6dff] focus:outline-none focus:ring-1 focus:ring-[#8b6dff] transition-all"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[13px] font-bold text-slate-700 ml-1">Full Name</label>
              <div className="relative flex items-center">
                <UserIcon className="absolute left-4 h-4 w-4 text-[#8b6dff]" />
                <input
                  type="text"
                  placeholder="Jane Doe"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  required
                  className="h-12 w-full rounded-xl border border-white/80 bg-white/40 pl-11 pr-4 text-sm text-slate-800 placeholder:text-slate-400 focus:border-[#8b6dff] focus:outline-none focus:ring-1 focus:ring-[#8b6dff] transition-all"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[13px] font-bold text-slate-700 ml-1">Work Email</label>
              <div className="relative flex items-center">
                <Mail className="absolute left-4 h-4 w-4 text-[#8b6dff]" />
                <input
                  type="email"
                  placeholder="jane@acme.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                  className="h-12 w-full rounded-xl border border-white/80 bg-white/40 pl-11 pr-4 text-sm text-slate-800 placeholder:text-slate-400 focus:border-[#8b6dff] focus:outline-none focus:ring-1 focus:ring-[#8b6dff] transition-all"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[13px] font-bold text-slate-700 ml-1">Password</label>
              <div className="relative flex items-center">
                <Lock className="absolute left-4 h-4 w-4 text-[#8b6dff]" />
                <input
                  type="password"
                  placeholder="••••••••••••"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  minLength={12}
                  required
                  className="h-12 w-full rounded-xl border border-white/80 bg-white/40 pl-11 pr-4 text-sm text-slate-800 placeholder:text-slate-400 focus:border-[#8b6dff] focus:outline-none focus:ring-1 focus:ring-[#8b6dff] transition-all"
                />
              </div>
              <p className="text-[11px] text-slate-500 ml-1">Must be at least 12 characters.</p>
            </div>

            <div className="space-y-1.5">
              <label className="text-[13px] font-bold text-slate-700 ml-1">Timezone</label>
              <div className="relative flex items-center">
                <Globe className="absolute left-4 h-4 w-4 text-[#8b6dff]" />
                <input
                  type="text"
                  value={form.timezone}
                  onChange={(e) => setForm({ ...form, timezone: e.target.value })}
                  required
                  className="h-12 w-full rounded-xl border border-white/80 bg-white/40 pl-11 pr-4 text-sm text-slate-800 placeholder:text-slate-400 focus:border-[#8b6dff] focus:outline-none focus:ring-1 focus:ring-[#8b6dff] transition-all"
                />
              </div>
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-100/50 backdrop-blur-md p-3 rounded-xl border border-red-200">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="group relative flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#7455f6] to-[#9b7aff] text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:opacity-90 disabled:opacity-50 mt-4"
            >
              {busy ? 'Creating Workspace…' : 'Create Organization Workspace'}
              {!busy && <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
