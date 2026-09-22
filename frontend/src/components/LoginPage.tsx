import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface LoginFormData {
  username: string;
  password: string;
}

export function LoginPage() {
  const [formData, setFormData] = useState<LoginFormData>({ username: '', password: '' });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await login(formData.username, formData.password);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='flex items-center justify-center min-h-screen bg-background'>
      <div className='w-full max-w-md p-8 space-y-8 bg-card rounded-lg shadow-md'>
        <div className='text-center'>
          <h1 className='text-2xl font-bold'>Login</h1>
          <p className='text-muted-foreground'>Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className='space-y-6'>
          <div className='space-y-2'>
            <Label htmlFor='username'>Username</Label>
            <Input
              id='username'
              name='username'
              type='text'
              value={formData.username}
              onChange={handleChange}
              required
              autoComplete='username'
            />
          </div>

          <div className='space-y-2'>
            <Label htmlFor='password'>Password</Label>
            <Input
              id='password'
              name='password'
              type='password'
              value={formData.password}
              onChange={handleChange}
              required
              autoComplete='current-password'
            />
          </div>

          {error && <p className='text-sm text-destructive'>{error}</p>}

          <Button type='submit' className='w-full' disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
      </div>
    </div>
  );
}