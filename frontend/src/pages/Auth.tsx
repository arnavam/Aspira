import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Sparkle, User, Lock, ArrowRight } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { api, setAuthToken } from '../services/api';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
  groqKey: z.string().optional(),
});

const registerSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  groqKey: z.string().min(4, 'Groq API Key is required').startsWith('gsk_', "Key must start with 'gsk_'"),
});

type AuthFormValues = {
  username: string;
  password: string;
  groqKey?: string;
};

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const errorParam = searchParams.get('error');

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
    clearErrors,
    reset
  } = useForm<AuthFormValues>({
    resolver: async (data, context, options) => {
      const schema = isLogin ? loginSchema : registerSchema;
      return zodResolver(schema)(data, context, options) as any;
    },
    defaultValues: { username: '', password: '', groqKey: '' }
  });

  useEffect(() => {
    if (errorParam === 'session_expired') {
      setError('root', { type: 'manual', message: 'Your session has expired. Please sign in again.' });
      setSearchParams({});
    }
  }, [errorParam, setSearchParams, setError]);

  const authMutation = useMutation({
    mutationFn: async (data: AuthFormValues) => {
      if (isLogin) {
        return api.login(data.username, data.password);
      } else {
        return api.register(data.username, data.password, data.groqKey!);
      }
    },
    onSuccess: (data) => {
      setAuthToken(data.access_token);
      navigate('/setup');
    },
    onError: (err: Error) => {
      setError('root', { type: 'manual', message: err.message || 'An error occurred' });
    }
  });

  const onSubmit = (data: AuthFormValues) => {
    clearErrors('root');
    authMutation.mutate(data);
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    reset();
    clearErrors();
  };

  return (
    <div className="app-container" style={{ alignItems: 'center', justifyContent: 'center' }}>
      <div className="glass animate-fade-in" style={{ width: '100%', maxWidth: '400px', padding: '2.5rem', borderRadius: '16px' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'inline-flex', padding: '12px', background: 'var(--accent-primary)', borderRadius: '50%', marginBottom: '1rem', boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)' }}>
            <Sparkle size={28} color="white" fill="white" />
          </div>
          <h2 style={{ marginBottom: '0.5rem' }}>Welcome to Aspira</h2>
          <p style={{ color: 'var(--text-secondary)' }}>
            {isLogin ? 'Sign in to continue your interviews' : 'Create an account to get started'}
          </p>
        </div>

        {errors.root && (
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid var(--danger)', padding: '0.75rem 1rem', borderRadius: '4px', marginBottom: '1.5rem', color: 'var(--danger)', fontSize: '0.875rem' }}>
            {errors.root.message}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label>Username</label>
            <div style={{ position: 'relative' }}>
              <User size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input 
                type="text" 
                placeholder="Enter your username" 
                {...register('username')}
                style={{ paddingLeft: '2.5rem', borderColor: errors.username ? 'var(--danger)' : undefined }}
              />
            </div>
            {errors.username && <p style={{ color: 'var(--danger)', fontSize: '0.75rem', marginTop: '0.25rem' }}>{errors.username.message}</p>}
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <label>Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input 
                type="password" 
                placeholder="••••••••" 
                {...register('password')}
                style={{ paddingLeft: '2.5rem', borderColor: errors.password ? 'var(--danger)' : undefined }}
              />
            </div>
            {errors.password && <p style={{ color: 'var(--danger)', fontSize: '0.75rem', marginTop: '0.25rem' }}>{errors.password.message}</p>}
          </div>

          {!isLogin && (
            <div style={{ marginBottom: '2rem' }}>
              <label>Groq API Key</label>
              <div style={{ position: 'relative' }}>
                <Lock size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input 
                  type="password" 
                  placeholder="gsk_..." 
                  {...register('groqKey')}
                  style={{ paddingLeft: '2.5rem', borderColor: errors.groqKey ? 'var(--danger)' : undefined }}
                />
              </div>
              {errors.groqKey && <p style={{ color: 'var(--danger)', fontSize: '0.75rem', marginTop: '0.25rem' }}>{errors.groqKey.message}</p>}
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                Required for the AI to function. It will be securely stored.
              </p>
            </div>
          )}

          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={authMutation.isPending}>
            {authMutation.isPending ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
            {!authMutation.isPending && <ArrowRight size={18} />}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            {isLogin ? "Don't have an account?" : "Already have an account?"}
            <button 
              type="button"
              onClick={toggleMode} 
              style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', marginLeft: '0.5rem', cursor: 'pointer', fontWeight: '500' }}
            >
              {isLogin ? 'Sign Up' : 'Sign In'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
