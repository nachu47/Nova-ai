import { useState, type FormEvent } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { Activity, Mail, Lock, Eye, ArrowRight } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { errorMessage } from '@/services/api';

export function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState('admin@nova.example.com');
  const [password, setPassword] = useState('NovaAdmin123!');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await login(email, password);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-[#f0eaff]">
      {/* Background Shapes */}
      <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full border border-white/40 shadow-[inset_0_0_100px_rgba(255,255,255,0.5)] bg-gradient-to-br from-white/20 to-transparent backdrop-blur-3xl" />
      <div className="absolute -bottom-40 -right-40 w-[800px] h-[800px] rounded-full border border-white/20 shadow-[inset_0_0_100px_rgba(255,255,255,0.3)] bg-gradient-to-tl from-[#e3d5ff]/40 to-transparent backdrop-blur-2xl" />
      
      {/* Login Card */}
      <div className="relative z-10 w-full max-w-[420px] mx-4 sm:mx-auto p-6 sm:p-10 rounded-3xl sm:rounded-[32px] bg-white/30 backdrop-blur-xl border border-white/60 shadow-[0_8px_32px_0_rgba(31,38,135,0.05)]">
        
        {/* Header */}
        <div className="mb-6 sm:mb-8">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#7455f6] to-[#9b7aff] text-white shadow-lg shadow-indigo-500/30 mb-6">
            <Activity className="h-7 w-7" />
          </div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Welcome to Nova</h1>
          <p className="text-sm text-slate-500 mt-1">Sign in to manage AI voice operations.</p>
        </div>

        {/* Form */}
        <form onSubmit={submit} className="space-y-6">
          
          <div className="space-y-1.5">
            <label className="text-[13px] font-bold text-slate-700 ml-1">Email</label>
            <div className="relative flex items-center">
              <Mail className="absolute left-4 h-4 w-4 text-[#8b6dff]" />
              <input 
                type="email" 
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="h-12 w-full rounded-xl border border-white/80 bg-white/40 pl-11 pr-4 text-sm text-slate-800 placeholder:text-slate-500 focus:border-[#8b6dff] focus:outline-none focus:ring-1 focus:ring-[#8b6dff] transition-all"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[13px] font-bold text-slate-700 ml-1">Password</label>
            <div className="relative flex items-center">
              <Lock className="absolute left-4 h-4 w-4 text-[#8b6dff]" />
              <input 
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="h-12 w-full rounded-xl border border-white/80 bg-white/40 pl-11 pr-11 text-sm text-slate-800 placeholder:text-slate-500 focus:border-[#8b6dff] focus:outline-none focus:ring-1 focus:ring-[#8b6dff] transition-all"
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 text-slate-500 hover:text-slate-700 transition-colors"
              >
                <Eye className="h-4 w-4" />
              </button>
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
            className="group relative flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#7455f6] to-[#9b7aff] text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:opacity-90 disabled:opacity-50"
          >
            {busy ? 'Signing in…' : 'Sign in'}
            {!busy && <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />}
          </button>

          <div className="flex items-center justify-between pt-2">
            <Link to="/register" className="text-[13px] font-bold text-[#7455f6] hover:underline">
              Create account
            </Link>
            <Link to="/forgot-password" className="text-[13px] font-medium text-slate-500 hover:text-slate-700 transition-colors">
              Forgot password?
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
