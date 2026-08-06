import { useState, type FormEvent } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/AuthContext';
import { errorMessage } from '@/services/api';

export function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState('admin@nova.example.com');
  const [password, setPassword] = useState('NovaAdmin123!');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

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
    <div 
      className="grid min-h-screen place-items-center p-4 bg-cover bg-center bg-no-repeat relative before:absolute before:inset-0 before:bg-black/40 before:z-0"
      style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop")' }}
    >
      <Card className="w-full max-w-md relative z-10 backdrop-blur-xl bg-background/30 border-white/10 shadow-[0_0_40px_rgba(0,0,0,0.5)]">
        <CardHeader className="space-y-4">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-primary shadow-lg shadow-primary/20 text-primary-foreground mx-auto">
            <Activity className="h-7 w-7" />
          </div>
          <div className="text-center">
            <CardTitle className="text-3xl font-bold tracking-tight text-white">Nova AI</CardTitle>
            <CardDescription className="text-slate-300 mt-2 text-base">Sign in to manage AI voice operations.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-200">Email</label>
              <Input 
                className="mt-1.5 bg-background/50 border-white/20 text-white placeholder:text-slate-400 focus-visible:ring-primary/50" 
                type="email" 
                value={email} 
                onChange={e => setEmail(e.target.value)} 
                required 
                autoComplete="email" 
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-200">Password</label>
              <Input 
                className="mt-1.5 bg-background/50 border-white/20 text-white placeholder:text-slate-400 focus-visible:ring-primary/50" 
                type="password" 
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                required 
                autoComplete="current-password" 
              />
            </div>
            {error && (
              <p className="rounded-md bg-destructive/80 backdrop-blur-md p-3 text-sm text-white font-medium border border-destructive">
                {error}
              </p>
            )}
            <Button className="w-full h-11 text-base font-semibold shadow-xl" disabled={busy}>
              {busy ? 'Signing in…' : 'Sign in'}
            </Button>
            <div className="flex justify-between text-sm mt-4">
              <Link className="text-slate-300 hover:text-white hover:underline transition-colors" to="/register">Create account</Link>
              <Link className="text-slate-400 hover:text-white transition-colors" to="/forgot-password">Forgot password?</Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
