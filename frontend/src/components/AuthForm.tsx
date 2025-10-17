'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Sparkles, Shield, Mail } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const SECURITY_QUESTIONS_SET_1 = [
  "What city were you born in?",
  "What was the name of your first school?",
  "What street did you grow up on?",
  "What was your childhood nickname?",
  "What was the name of your first boss?"
];

const SECURITY_QUESTIONS_SET_2 = [
  "What was your first pet's name?",
  "What's your mother's maiden name?",
  "What was the make of your first car?",
  "What's your favorite movie?",
  "What was your first job title?"
];

interface AuthFormProps {
  onSuccess?: () => void;
}

export default function AuthForm({ onSuccess }: AuthFormProps) {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    question1: '',
    answer1: '',
    question2: '',
    answer2: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.question1) {
      newErrors.question1 = 'Please select a security question';
    }

    if (!formData.answer1.trim()) {
      newErrors.answer1 = 'Please provide an answer';
    }

    if (!formData.question2) {
      newErrors.question2 = 'Please select a security question';
    }

    if (!formData.answer2.trim()) {
      newErrors.answer2 = 'Please provide an answer';
    }

    if (formData.question1 === formData.question2 && formData.question1) {
      newErrors.question2 = 'Please select different security questions';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Create user auth data
      const userData = {
        email: formData.email.trim(),
        securityQuestions: {
          question1: {
            selectedQuestion: formData.question1,
            answer: formData.answer1.trim(),
          },
          question2: {
            selectedQuestion: formData.question2,
            answer: formData.answer2.trim(),
          },
        },
      };

      // Store in context and localStorage
      login(userData);
      
      // Call success callback
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      console.error('Error saving auth data:', error);
      setErrors({ submit: 'Something went wrong. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Sparkles className="h-8 w-8 text-yellow-400 mr-2" />
            <h1 className="text-2xl font-bold text-gray-900">Welcome to Ava</h1>
          </div>
          <p className="text-gray-600">
            Enter your details to get started with your personal real estate assistant
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Email */}
          <div className="space-y-2">
            <Label htmlFor="email" className="flex items-center text-sm font-medium text-gray-700">
              <Mail className="h-4 w-4 mr-2" />
              Email Address
            </Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              className={errors.email ? 'border-red-500' : ''}
              placeholder="your.email@example.com"
            />
            {errors.email && <p className="text-red-500 text-sm">{errors.email}</p>}
          </div>

          {/* Security Questions */}
          <div className="space-y-4">
            <div className="flex items-center text-sm font-medium text-gray-700 mb-4">
              <Shield className="h-4 w-4 mr-2" />
              Security Questions
            </div>

            {/* Question 1 */}
            <div className="space-y-2">
              <Label htmlFor="question1" className="text-sm font-medium text-gray-700">
                Security Question 1
              </Label>
              <select
                id="question1"
                value={formData.question1}
                onChange={(e) => handleInputChange('question1', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md ${errors.question1 ? 'border-red-500' : 'border-gray-300'} focus:outline-none focus:ring-2 focus:ring-blue-500`}
              >
                <option value="">Select a question...</option>
                {SECURITY_QUESTIONS_SET_1.map((question) => (
                  <option key={question} value={question}>
                    {question}
                  </option>
                ))}
              </select>
              {errors.question1 && <p className="text-red-500 text-sm">{errors.question1}</p>}
              
              {formData.question1 && (
                <Input
                  type="text"
                  value={formData.answer1}
                  onChange={(e) => handleInputChange('answer1', e.target.value)}
                  className={errors.answer1 ? 'border-red-500' : ''}
                  placeholder="Your answer..."
                />
              )}
              {errors.answer1 && <p className="text-red-500 text-sm">{errors.answer1}</p>}
            </div>

            {/* Question 2 */}
            <div className="space-y-2">
              <Label htmlFor="question2" className="text-sm font-medium text-gray-700">
                Security Question 2
              </Label>
              <select
                id="question2"
                value={formData.question2}
                onChange={(e) => handleInputChange('question2', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md ${errors.question2 ? 'border-red-500' : 'border-gray-300'} focus:outline-none focus:ring-2 focus:ring-blue-500`}
              >
                <option value="">Select a question...</option>
                {SECURITY_QUESTIONS_SET_2.map((question) => (
                  <option key={question} value={question}>
                    {question}
                  </option>
                ))}
              </select>
              {errors.question2 && <p className="text-red-500 text-sm">{errors.question2}</p>}
              
              {formData.question2 && (
                <Input
                  type="text"
                  value={formData.answer2}
                  onChange={(e) => handleInputChange('answer2', e.target.value)}
                  className={errors.answer2 ? 'border-red-500' : ''}
                  placeholder="Your answer..."
                />
              )}
              {errors.answer2 && <p className="text-red-500 text-sm">{errors.answer2}</p>}
            </div>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Setting up your account...
              </>
            ) : (
              'Get Started'
            )}
          </Button>

          {errors.submit && (
            <p className="text-red-500 text-sm text-center">{errors.submit}</p>
          )}
        </form>

        {/* Footer */}
        <div className="text-center mt-6 text-sm text-gray-500">
          <p>Your information is stored securely on your device.</p>
        </div>
      </div>
    </div>
  );
}
