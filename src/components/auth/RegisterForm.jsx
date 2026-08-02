import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Mail, User, Lock, Phone, AlertCircle, Activity } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import Input from '../common/Input';
import Button from '../common/Button';

/**
 * Registration form component.
 * Validates matching password keys, phone numbers, and term requirements.
 * 
 * @returns {JSX.Element}
 */
export const RegisterForm = () => {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState(null);
  const [isSubmittingSimulated, setIsSubmittingSimulated] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors }
  } = useForm({
    defaultValues: {
      fullName: '',
      email: '',
      phone: '',
      password: '',
      confirmPassword: '',
      role: 'Patient',
      agreeToTerms: false
    }
  });

  const passwordValue = watch('password');
  const agreeToTermsValue = watch('agreeToTerms');

  const onSubmit = async (data) => {
    setSubmitError(null);
    setIsSubmittingSimulated(true);
    try {
      await registerUser(data);
      navigate('/dashboard');
    } catch (err) {
      setSubmitError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsSubmittingSimulated(false);
    }
  };

  return (
    <div className="w-full">
      {/* Header title */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-1 bg-teal-50 border border-teal-100 px-3 py-1 rounded-full text-xs font-semibold text-primary mb-3">
          <Activity className="w-4 h-4" />
          <span>NeuroCare Nexus</span>
        </div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Create Account</h2>
        <p className="text-sm text-slate-500 mt-1">Register to start AI-IoT home monitoring.</p>
      </div>

      {/* Global submit errors */}
      {submitError && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-lg text-sm font-medium text-status-emergency flex items-start gap-2.5">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{submitError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Full Name */}
        <Input
          label="Full Name"
          type="text"
          placeholder="John Doe"
          icon={<User className="w-5 h-5" />}
          error={errors.fullName?.message}
          {...register('fullName', {
            required: 'Please enter your full name'
          })}
        />

        {/* Email Address */}
        <Input
          label="Email Address"
          type="email"
          placeholder="patient@neurocare.com"
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

        {/* Phone Number */}
        <Input
          label="Phone Number"
          type="tel"
          placeholder="1234567890"
          icon={<Phone className="w-5 h-5" />}
          error={errors.phone?.message}
          {...register('phone', {
            required: 'Please enter your phone number',
            pattern: {
              value: /^[0-9+-\s()]{10,15}$/,
              message: 'Please enter a valid phone number (10+ digits)'
            }
          })}
        />

        {/* Role Select Dropdown */}
        <div className="w-full flex flex-col gap-1.5">
          <label htmlFor="role-select" className="text-sm font-semibold text-slate-700">
            Account Role
          </label>
          <select
            id="role-select"
            className="w-full py-2.5 px-3 border border-slate-300 rounded-lg bg-white focus:ring-1 focus:ring-primary focus:border-primary transition-smooth text-base"
            {...register('role', { required: 'Please select a system role' })}
          >
            <option value="Patient">Patient</option>
            <option value="Doctor">Doctor / Clinician</option>
            <option value="Caregiver">Caregiver</option>
          </select>
          {errors.role && (
            <span className="text-sm font-medium text-status-emergency">{errors.role.message}</span>
          )}
        </div>

        {/* Password */}
        <Input
          label="Password"
          type="password"
          placeholder="••••••••"
          showPasswordToggle={true}
          icon={<Lock className="w-5 h-5" />}
          error={errors.password?.message}
          {...register('password', {
            required: 'Please enter a password',
            minLength: {
              value: 6,
              message: 'Password must be at least 6 characters long'
            }
          })}
        />

        {/* Confirm Password */}
        <Input
          label="Confirm Password"
          type="password"
          placeholder="••••••••"
          showPasswordToggle={true}
          icon={<Lock className="w-5 h-5" />}
          error={errors.confirmPassword?.message}
          {...register('confirmPassword', {
            required: 'Please confirm your password',
            validate: (val) => val === passwordValue || 'Passwords do not match'
          })}
        />

        {/* Terms Agreement Checkbox */}
        <div className="flex flex-col gap-1 pt-1">
          <label className="flex items-start gap-2.5 font-medium text-slate-600 select-none cursor-pointer text-sm">
            <input
              type="checkbox"
              className="w-4 h-4 rounded border-slate-350 text-primary focus:ring-primary transition-smooth mt-0.5"
              {...register('agreeToTerms', {
                required: 'You must agree to the Terms & Conditions'
              })}
            />
            <span>
              I agree to the{' '}
              <a 
                href="#terms" 
                onClick={(e) => { e.preventDefault(); alert('Terms & Conditions agreement text placeholder.'); }} 
                className="text-primary hover:text-primary-dark font-bold underline"
              >
                Terms & Conditions
              </a>
            </span>
          </label>
          {errors.agreeToTerms && (
            <span className="text-sm font-medium text-status-emergency mt-1">
              {errors.agreeToTerms.message}
            </span>
          )}
        </div>

        {/* Submit action */}
        <div className="pt-2">
          <Button
            type="submit"
            isLoading={isSubmittingSimulated}
            disabled={!agreeToTermsValue}
            className="w-full text-base py-2.5 font-bold shadow-sm"
          >
            Create Account
          </Button>
        </div>
      </form>

      {/* Alternative prompt */}
      <div className="text-center mt-6 text-sm text-slate-500">
        Already have an account?{' '}
        <Link 
          to="/login" 
          className="font-bold text-primary hover:text-primary-dark transition-colors"
        >
          Login
        </Link>
      </div>
    </div>
  );
};

export default RegisterForm;
