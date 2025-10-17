'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { DollarSign, User, ArrowRight, Sparkles } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const [customerId, setCustomerId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleExistingUser = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!customerId.trim()) {
      setError('Please enter your customer ID');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Check if customer exists by trying to get their context
      const response = await fetch(`http://localhost:8000/customer/${customerId.trim()}/context`);
      
      if (response.ok) {
        // Customer exists, redirect to chat
        router.push(`/chat?customerId=${customerId.trim()}&userType=existing`);
      } else {
        setError('Customer ID not found. Please check your ID or create a new profile.');
      }
    } catch (error) {
      console.error('Error checking customer:', error);
      setError('Unable to verify customer ID. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewUser = () => {
    router.push('/financial-assessment');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-blue-600 rounded-lg flex items-center justify-center">
              <DollarSign className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Growbe</h1>
              <p className="text-sm text-gray-600">Your AI Financial Advisor</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Sparkles className="h-8 w-8 text-blue-600" />
            <h2 className="text-4xl font-bold text-gray-900">
              Welcome to Your Financial Future! 💰
            </h2>
          </div>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Get personalized financial advice from Growbe, your AI financial advisor. 
            Whether you're managing student loans, planning to buy a home, or building wealth, 
            I'm here to help you make smart financial decisions.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Existing User Card */}
          <Card className="border-2 border-blue-200 hover:border-blue-300 transition-colors">
            <CardHeader className="text-center pb-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <User className="h-8 w-8 text-blue-600" />
              </div>
              <CardTitle className="text-2xl text-gray-900">Existing Customer</CardTitle>
              <CardDescription className="text-gray-600">
                Already have a customer profile? Enter your customer ID to access your personalized financial dashboard.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleExistingUser} className="space-y-4">
                <div>
                  <label htmlFor="customerId" className="block text-sm font-medium text-gray-700 mb-2">
                    Customer ID
                  </label>
                  <Input
                    id="customerId"
                    type="text"
                    value={customerId}
                    onChange={(e) => {
                      setCustomerId(e.target.value);
                      setError('');
                    }}
                    placeholder="Enter your customer ID (e.g., C001)"
                    className={error ? 'border-red-500' : ''}
                    disabled={isLoading}
                  />
                  {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
                </div>
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center"
                >
                  {isLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      Verifying...
                    </>
                  ) : (
                    <>
                      Access My Profile
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* New User Card */}
          <Card className="border-2 border-green-200 hover:border-green-300 transition-colors">
            <CardHeader className="text-center pb-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles className="h-8 w-8 text-green-600" />
              </div>
              <CardTitle className="text-2xl text-gray-900">New Customer</CardTitle>
              <CardDescription className="text-gray-600">
                New to Growbe? Complete a quick financial assessment to get personalized advice tailored to your goals.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-sm text-gray-600 space-y-2">
                  <p>• Get personalized financial advice</p>
                  <p>• Student loan optimization strategies</p>
                  <p>• Home buying affordability analysis</p>
                  <p>• Debt payoff planning</p>
                  <p>• Investment and savings guidance</p>
                </div>
                <Button
                  onClick={handleNewUser}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center"
                >
                  Start Financial Assessment
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Features Section */}
        <div className="mt-16">
          <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">
            How Growbe Can Help You
          </h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center p-6 bg-white rounded-lg shadow-sm">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🎓</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Student Loan Management</h4>
              <p className="text-gray-600 text-sm">
                Optimize your student loan payments, explore refinancing options, and create payoff strategies.
              </p>
            </div>
            <div className="text-center p-6 bg-white rounded-lg shadow-sm">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🏠</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Home Buying Planning</h4>
              <p className="text-gray-600 text-sm">
                Calculate affordability, plan for down payments, and understand mortgage options.
              </p>
            </div>
            <div className="text-center p-6 bg-white rounded-lg shadow-sm">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📊</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Financial Planning</h4>
              <p className="text-gray-600 text-sm">
                Build budgets, manage debt, plan for emergencies, and grow your wealth.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-gray-500">
          <p>Secure • Confidential • Personalized Financial Guidance</p>
        </div>
      </div>
    </div>
  );
}