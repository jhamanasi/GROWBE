'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { DollarSign, User, ArrowRight, ArrowLeft, Target, TrendingUp } from 'lucide-react';

interface AssessmentData {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  annual_income: number | null;
  primary_goal: string;
  debt_status: string;
  employment_status: string;
  timeline: string;
  risk_tolerance: string;
}

const PRIMARY_GOALS = [
  { value: 'student_loans', label: 'Pay Off Student Loans', icon: '🎓' },
  { value: 'home_buying', label: 'Buy a Home', icon: '🏠' },
  { value: 'debt_consolidation', label: 'Consolidate Debt', icon: '💳' },
  { value: 'emergency_fund', label: 'Build Emergency Fund', icon: '💰' },
  { value: 'investment', label: 'Start Investing', icon: '📈' },
  { value: 'retirement', label: 'Plan for Retirement', icon: '🏖️' }
];

const DEBT_STATUS_OPTIONS = [
  { value: 'no_debt', label: 'No significant debt' },
  { value: 'student_loans', label: 'Student loans only' },
  { value: 'credit_cards', label: 'Credit card debt' },
  { value: 'multiple_debts', label: 'Multiple types of debt' },
  { value: 'high_debt', label: 'High debt burden' }
];

const EMPLOYMENT_STATUS_OPTIONS = [
  { value: 'full_time', label: 'Full-time employed' },
  { value: 'part_time', label: 'Part-time employed' },
  { value: 'self_employed', label: 'Self-employed' },
  { value: 'freelancer', label: 'Freelancer/Contractor' },
  { value: 'student', label: 'Student' },
  { value: 'unemployed', label: 'Currently unemployed' }
];

const TIMELINE_OPTIONS = [
  { value: 'asap', label: 'ASAP (within 6 months)' },
  { value: '1_year', label: 'Within 1 year' },
  { value: '2_5_years', label: '2-5 years' },
  { value: '5_plus_years', label: '5+ years' }
];

const RISK_TOLERANCE_OPTIONS = [
  { value: 'conservative', label: 'Conservative - Low risk, steady returns' },
  { value: 'moderate', label: 'Moderate - Balanced risk and return' },
  { value: 'aggressive', label: 'Aggressive - High risk, high potential return' }
];

export default function FinancialAssessmentPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Partial<AssessmentData>>({});
  
  const [formData, setFormData] = useState<AssessmentData>({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    annual_income: null,
    primary_goal: '',
    debt_status: '',
    employment_status: '',
    timeline: '',
    risk_tolerance: ''
  });

  const totalSteps = 4;

  const validateStep = (step: number): boolean => {
    const newErrors: Partial<AssessmentData> = {};
    
    switch (step) {
      case 1:
        if (!formData.first_name.trim()) newErrors.first_name = 'First name is required';
        if (!formData.last_name.trim()) newErrors.last_name = 'Last name is required';
        if (!formData.email.trim()) {
          newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
          newErrors.email = 'Please enter a valid email';
        }
        if (!formData.phone.trim()) newErrors.phone = 'Phone number is required';
        break;
      case 2:
        if (!formData.annual_income || formData.annual_income <= 0) {
          newErrors.annual_income = 'Please enter a valid annual income';
        }
        if (!formData.employment_status) newErrors.employment_status = 'Please select your employment status';
        break;
      case 3:
        if (!formData.primary_goal) newErrors.primary_goal = 'Please select your primary financial goal';
        if (!formData.debt_status) newErrors.debt_status = 'Please select your debt status';
        break;
      case 4:
        if (!formData.timeline) newErrors.timeline = 'Please select your timeline';
        if (!formData.risk_tolerance) newErrors.risk_tolerance = 'Please select your risk tolerance';
        break;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, totalSteps));
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;
    
    setIsSubmitting(true);
    
    try {
      const response = await fetch('http://localhost:8000/assess', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      if (response.ok) {
        const result = await response.json();
        // Redirect to chat with customer ID
        router.push(`/chat?customerId=${result.customer_id}&userType=new`);
      } else {
        const error = await response.json();
        console.error('Error creating assessment:', error);
        alert('Something went wrong. Please try again.');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof AssessmentData, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Personal Information</h3>
              <p className="text-gray-600">Let's start with some basic information about you.</p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name *
                </label>
                <Input
                  value={formData.first_name}
                  onChange={(e) => handleInputChange('first_name', e.target.value)}
                  className={errors.first_name ? 'border-red-500' : ''}
                  placeholder="Enter your first name"
                />
                {errors.first_name && <p className="text-red-500 text-sm mt-1">{errors.first_name}</p>}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name *
                </label>
                <Input
                  value={formData.last_name}
                  onChange={(e) => handleInputChange('last_name', e.target.value)}
                  className={errors.last_name ? 'border-red-500' : ''}
                  placeholder="Enter your last name"
                />
                {errors.last_name && <p className="text-red-500 text-sm mt-1">{errors.last_name}</p>}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address *
              </label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className={errors.email ? 'border-red-500' : ''}
                placeholder="your.email@example.com"
              />
              {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Phone Number *
              </label>
              <Input
                type="tel"
                value={formData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
                className={errors.phone ? 'border-red-500' : ''}
                placeholder="(555) 123-4567"
              />
              {errors.phone && <p className="text-red-500 text-sm mt-1">{errors.phone}</p>}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Income & Employment</h3>
              <p className="text-gray-600">Help us understand your financial situation.</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Annual Income *
              </label>
              <Input
                type="number"
                value={formData.annual_income || ''}
                onChange={(e) => handleInputChange('annual_income', parseInt(e.target.value) || 0)}
                className={errors.annual_income ? 'border-red-500' : ''}
                placeholder="Enter your annual income"
              />
              {errors.annual_income && <p className="text-red-500 text-sm mt-1">{errors.annual_income}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Employment Status *
              </label>
              <div className="space-y-2">
                {EMPLOYMENT_STATUS_OPTIONS.map((option) => (
                  <label
                    key={option.value}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-all ${
                      formData.employment_status === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="employment_status"
                      value={option.value}
                      checked={formData.employment_status === option.value}
                      onChange={(e) => handleInputChange('employment_status', e.target.value)}
                      className="sr-only"
                    />
                    <span className="text-sm font-medium text-gray-900">{option.label}</span>
                  </label>
                ))}
              </div>
              {errors.employment_status && <p className="text-red-500 text-sm mt-1">{errors.employment_status}</p>}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Financial Goals & Debt</h3>
              <p className="text-gray-600">What are your primary financial objectives?</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Primary Financial Goal *
              </label>
              <div className="grid grid-cols-2 gap-3">
                {PRIMARY_GOALS.map((goal) => (
                  <label
                    key={goal.value}
                    className={`flex items-center p-4 border rounded-lg cursor-pointer transition-all ${
                      formData.primary_goal === goal.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="primary_goal"
                      value={goal.value}
                      checked={formData.primary_goal === goal.value}
                      onChange={(e) => handleInputChange('primary_goal', e.target.value)}
                      className="sr-only"
                    />
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{goal.icon}</span>
                      <span className="text-sm font-medium text-gray-900">{goal.label}</span>
                    </div>
                  </label>
                ))}
              </div>
              {errors.primary_goal && <p className="text-red-500 text-sm mt-1">{errors.primary_goal}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Current Debt Status *
              </label>
              <div className="space-y-2">
                {DEBT_STATUS_OPTIONS.map((option) => (
                  <label
                    key={option.value}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-all ${
                      formData.debt_status === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="debt_status"
                      value={option.value}
                      checked={formData.debt_status === option.value}
                      onChange={(e) => handleInputChange('debt_status', e.target.value)}
                      className="sr-only"
                    />
                    <span className="text-sm font-medium text-gray-900">{option.label}</span>
                  </label>
                ))}
              </div>
              {errors.debt_status && <p className="text-red-500 text-sm mt-1">{errors.debt_status}</p>}
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Timeline & Risk Preferences</h3>
              <p className="text-gray-600">Help us tailor our advice to your preferences.</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timeline for Achieving Your Goal *
              </label>
              <div className="space-y-2">
                {TIMELINE_OPTIONS.map((option) => (
                  <label
                    key={option.value}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-all ${
                      formData.timeline === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="timeline"
                      value={option.value}
                      checked={formData.timeline === option.value}
                      onChange={(e) => handleInputChange('timeline', e.target.value)}
                      className="sr-only"
                    />
                    <span className="text-sm font-medium text-gray-900">{option.label}</span>
                  </label>
                ))}
              </div>
              {errors.timeline && <p className="text-red-500 text-sm mt-1">{errors.timeline}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Risk Tolerance *
              </label>
              <div className="space-y-2">
                {RISK_TOLERANCE_OPTIONS.map((option) => (
                  <label
                    key={option.value}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-all ${
                      formData.risk_tolerance === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="risk_tolerance"
                      value={option.value}
                      checked={formData.risk_tolerance === option.value}
                      onChange={(e) => handleInputChange('risk_tolerance', e.target.value)}
                      className="sr-only"
                    />
                    <span className="text-sm font-medium text-gray-900">{option.label}</span>
                  </label>
                ))}
              </div>
              {errors.risk_tolerance && <p className="text-red-500 text-sm mt-1">{errors.risk_tolerance}</p>}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-blue-600 rounded-lg flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">Growbe</h1>
            </div>
            <Button
              variant="outline"
              onClick={() => router.push('/')}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Home</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white border-b">
        <div className="max-w-2xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Step {currentStep} of {totalSteps}</span>
            <span className="text-sm text-gray-500">{Math.round((currentStep / totalSteps) * 100)}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-green-500 to-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentStep / totalSteps) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card className="shadow-xl">
          <CardContent className="p-8">
            {renderStep()}
            
            {/* Navigation Buttons */}
            <div className="flex justify-between mt-8 pt-6 border-t">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentStep === 1}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Previous</span>
              </Button>
              
              {currentStep < totalSteps ? (
                <Button
                  onClick={handleNext}
                  className="bg-blue-600 hover:bg-blue-700 text-white flex items-center space-x-2"
                >
                  <span>Next</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="bg-green-600 hover:bg-green-700 text-white flex items-center space-x-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Creating Profile...</span>
                    </>
                  ) : (
                    <>
                      <span>Complete Assessment</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
