import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { PaperNestLogoFull } from '@/components/SideNav';

export function LoginPage() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const { login, register, isLoading, error, clearError } = useAuthStore();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!isLogin) {
      // Register
      if (password !== confirmPassword) {
        toast({
          title: 'Password mismatch',
          description: 'Passwords do not match.',
          variant: 'destructive',
        });
        return;
      }

      if (password.length < 8) {
        toast({
          title: 'Password too short',
          description: 'Password must be at least 8 characters.',
          variant: 'destructive',
        });
        return;
      }

      try {
        await register({ email, password, full_name: fullName || undefined });
        toast({
          title: 'Account created!',
          description: 'Welcome to PaperNest.',
        });
        navigate('/');
      } catch (err) {
        toast({
          title: 'Registration failed',
          description: error || 'Please try again.',
          variant: 'destructive',
        });
      }
    } else {
      // Login
      try {
        await login({ email, password });
        toast({
          title: 'Welcome back!',
          description: 'You have successfully logged in.',
        });
        navigate('/');
      } catch (err) {
        toast({
          title: 'Login failed',
          description: error || 'Please check your credentials and try again.',
          variant: 'destructive',
        });
      }
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 flex justify-center">
          <PaperNestLogoFull className="h-8" />
        </div>

        {/* Card */}
        <div className="rounded-xl border border-border bg-white p-8 shadow-sm">
          <div className="mb-6 text-center">
            <h1 className="text-2xl font-bold text-foreground">
              {isLogin ? 'Welcome back' : 'Create account'}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {isLogin
                ? 'Login to access your saved papers and alerts'
                : 'Register to start saving papers and creating alerts'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name (Optional)</Label>
                <Input
                  id="fullName"
                  type="text"
                  placeholder="John Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={isLoading}
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                minLength={8}
              />
              {!isLogin && (
                <p className="text-xs text-muted-foreground">
                  Must be at least 8 characters
                </p>
              )}
            </div>

            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
            )}

            {error && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading
                ? isLogin
                  ? 'Logging in...'
                  : 'Creating account...'
                : isLogin
                ? 'Login'
                : 'Register'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                clearError();
              }}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              {isLogin ? (
                <>
                  Don't have an account?{' '}
                  <span className="font-medium text-primary">Register</span>
                </>
              ) : (
                <>
                  Already have an account?{' '}
                  <span className="font-medium text-primary">Login</span>
                </>
              )}
            </button>
          </div>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              ← Back to home
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
