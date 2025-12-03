'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useOnboardingFlow } from '@/hooks/use-onboarding-flow';

interface RegistrationStepProps {
  onComplete: () => void;
  onSkip?: () => void;
}

export function RegistrationStep({ onComplete, onSkip }: RegistrationStepProps) {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    fullName: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { completeOnboarding } = useOnboardingFlow();

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
  };

  const validateForm = (): string | null => {
    if (!formData.email.trim()) return 'Email is required';
    if (!formData.username.trim()) return 'Username is required';
    if (!formData.password) return 'Password is required';
    if (formData.password !== formData.confirmPassword) return 'Passwords do not match';
    if (formData.password.length < 8) return 'Password must be at least 8 characters';
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) return 'Invalid email format';
    
    // Username validation
    if (formData.username.length < 3) return 'Username must be at least 3 characters';
    if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) return 'Username can only contain letters, numbers, and underscores';
    
    return null;
  };

  const handleSubmit = async () => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Complete onboarding with registration data
      await completeOnboarding({
        email: formData.email.trim(),
        username: formData.username.trim(),
        password: formData.password,
        full_name: formData.fullName.trim() || formData.username
      });

      onComplete();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Registration failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = async () => {
    if (onSkip) {
      // Complete onboarding without registration (anonymous mode)
      try {
        await completeOnboarding();
        onSkip();
      } catch (error) {
        console.error('Failed to complete onboarding:', error);
        onSkip(); // Still proceed even if backend fails
      }
    }
  };

  return (
    <Card className="p-6 max-w-md mx-auto">
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-2xl font-bold mb-2">Create Your Account</h3>
          <p className="text-gray-600">
            Create a UATP account to save your settings and track your usage
          </p>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-4">
          <div>
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              placeholder="your.email@example.com"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div>
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              type="text"
              placeholder="choose a username"
              value={formData.username}
              onChange={(e) => handleInputChange('username', e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div>
            <Label htmlFor="fullName">Full Name (Optional)</Label>
            <Input
              id="fullName"
              type="text"
              placeholder="Your full name"
              value={formData.fullName}
              onChange={(e) => handleInputChange('fullName', e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="create a secure password"
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div>
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="confirm your password"
              value={formData.confirmPassword}
              onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
              disabled={isSubmitting}
            />
          </div>
        </div>

        <div className="space-y-3">
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Creating Account...
              </>
            ) : (
              'Create Account & Complete Setup'
            )}
          </Button>

          {onSkip && (
            <Button
              onClick={handleSkip}
              variant="outline"
              className="w-full"
              disabled={isSubmitting}
            >
              Continue Without Account
            </Button>
          )}
        </div>

        <div className="text-xs text-gray-500 text-center space-y-2">
          <p>
            By creating an account, you agree to our Terms of Service and Privacy Policy.
          </p>
          <p>
            Your data is stored locally and encrypted. We never share your information.
          </p>
        </div>
      </div>
    </Card>
  );
}