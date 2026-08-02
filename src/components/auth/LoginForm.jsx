import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Mail, Lock, AlertCircle, Activity } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import Input from '../common/Input';
import Button from '../common/Button';

/**
 * Authentication login form component.
 * Uses react-hook-form for inline validation and simulates response delays.
 * 
 * @returns {JSX.Element}
 */
export const LoginForm = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState(null);
  const [isSubmittingSimulated, setIsSubmittingSimulated] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm({
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false
    }
  });

  const onSubmit = async (data) => {
    setSubmitError(null);
    setIsSubmittingSimulated(true);
    try {
      await login(data.email, data.password);
      navigate('/dashboard');
    } catch (err) {
      setSubmitError(err.message || 'An unexpected authentication error occurred.');
    } finally {
      setIsSubmittingSimulated(false);
    }
  };

  return (
    <div className="w-full">
      {/* Brand Identity / Title */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-1 bg-teal-50 border border-teal-100 px-3 py-1 rounded-full text-xs font-semibold text-primary mb-3">
          <Activity className="w-4 h-4" />
          <span>NeuroCare Nexus</span>
        </div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Welcome Back</h2>
        <p className="text-sm text-slate-500 mt-1">Please sign in to access your platform portal.</p>
      </div>

      {/* Global submit errors */}
      {submitError && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-lg text-sm font-medium text-status-emergency flex items-start gap-2.5">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{submitError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Email Field */}
        <Input
          label="Email Address"
          type="email"
          placeholder="doctor@neurocare.com"
          icon={<Mail className="w-5 h-5" />}
          error={errors.email?.message}
          {...register('email', {
            required: 'Please enter your email address',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Please enter a valid email address'
            }
          })}
        />

        {/* Password Field */}
        <Input
          label="Password"
          type="password"
          placeholder="••••••••"
          showPasswordToggle={true}
          icon={<Lock className="w-5 h-5" />}
          error={errors.password?.message}
          {...register('password', {
            required: 'Please enter your password',
            minLength: {
              value: 6,
              message: 'Password must be at least 6 characters long'
            }
          })}
        />

        {/* Remembers & Forgot password links */}
        <div className="flex items-center justify-between text-sm py-1">
          <label className="flex items-center gap-2 font-medium text-slate-600 select-none cursor-pointer">
            <input
              type="checkbox"
              className="w-4 h-4 rounded border-slate-350 text-primary focus:ring-primary transition-smooth"
              {...register('rememberMe')}
            />
            <span>Remember Me</span>
          </label>
          <a
            href="#forgot-password"
            onClick={(e) => {
              e.preventDefault();
              alert('Password recovery link was dispatched to your email address (Simulated).');
            }}
            className="font-semibold text-primary hover:text-primary-dark transition-colors"
          >
            Forgot Password?
          </a>
        </div>

        {/* Submit action */}
        <div className="pt-2 flex flex-col gap-3">
          <Button
            type="submit"
            isLoading={isSubmittingSimulated}
            className="w-full text-base py-2.5 font-bold shadow-sm"
          >
            Login
          </Button>

          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/register')}
            className="w-full border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold"
          >
            Create Account
          </Button>
        </div>
      </form>

      {/* Alternative prompt */}
      <div className="text-center mt-6 text-sm text-slate-500">
        Don't have an account?{' '}
        <Link 
          to="/register" 
          className="font-bold text-primary hover:text-primary-dark transition-colors"
        >
          Register
        </Link>
      </div>
    </div>
  );
};

export default LoginForm;
