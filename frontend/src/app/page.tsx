'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { User, ArrowRight } from 'lucide-react';
import { Poppins } from 'next/font/google';
import { InfiniteMovingCards } from '@/components/ui/infinite-moving-cards';
import { TextGenerateEffect } from '@/components/ui/text-generate-effect';

const poppins = Poppins({ subsets: ['latin'], weight: '400' });
const poppinsBold = Poppins({ subsets: ['latin'], weight: '700' });

export default function Home() {
  const router = useRouter();
  const [customerId, setCustomerId] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [guidanceType, setGuidanceType] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'login' | 'signup'>('login');

  // Helper to detect if input is a UUID (session_id) vs customer_id (C001 format)
  const isUUID = (str: string): boolean => {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(str);
  };

  const handleExistingUser = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!customerId.trim()) {
      setError('Please enter your customer ID or session ID');
      return;
    }

    setIsLoading(true);
    setError('');

    const input = customerId.trim();
    const isSessionId = isUUID(input);

    try {
      if (isSessionId) {
        const convsResp = await fetch(`http://localhost:8000/api/conversations?session_id=${input}`);
        if (convsResp.ok) {
              const params = new URLSearchParams();
              params.set('sessionId', input);
              router.push(`/conversations?${params.toString()}`);
        } else {
          setError('Session ID not found. Please check your ID or create a new profile.');
        }
      } else {
        const response = await fetch(`http://localhost:8000/customer/${input}/context`);
      if (response.ok) {
              const params = new URLSearchParams();
              params.set('customerId', input);
              router.push(`/conversations?${params.toString()}`);
      } else {
        setError('Customer ID not found. Please check your ID or create a new profile.');
        }
      }
    } catch (error) {
      console.error('Error checking customer/session:', error);
      setError('Unable to verify ID. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewUser = async () => {
    setIsLoading(true);
    setError('');
    try {
      const resp = await fetch('http://localhost:8000/api/conversations/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_type: 'new',
          initial_message: firstName
            ? `Hi ${firstName}, welcome to Growbe! Let’s get started with your goals.`
            : `Hello! Let’s get started with your goals.`,
        }),
      });
      if (!resp.ok) {
        throw new Error(`Failed to start conversation (${resp.status})`);
      }
      const data = await resp.json();
      const sessionId = data.session_id;
      // For new users, always redirect to the greeting page. The session_id is still passed.
      const params = new URLSearchParams();
      if (sessionId) params.set('sessionId', sessionId);
      router.push(`/conversations?${params.toString()}`);
    } catch (e: any) {
      console.error('Failed to start new user conversation:', e);
      setError('Something went wrong starting your chat. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div 
      className="min-h-screen relative overflow-hidden bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: "url('/bg-gradient.jpg')" }}
    >
      {/* Logo */}
      <div className="absolute text-white top-2 left-2 sm:top-4 sm:left-4 md:top-6 md:left-6">
        <h1 className={`${poppinsBold.className} logo-clarify text-3xl md:text-4xl lg:text-5xl xl:text-6xl`} style={{ margin: 0 }}>
          growbe.
        </h1>
      </div>

      <div className="relative min-h-screen flex flex-col items-center justify-center">
        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-2 text-white flex-1 flex flex-col items-center justify-center">
        {/* Hero Content */}
        <div className="text-center mb-4 sm:mb-6 md:mb-8 -mt-8 flex flex-col items-center justify-center w-full">
          <div className={`${poppinsBold.className} mb-1 sm:mb-2 sm:whitespace-nowrap`}>
            <TextGenerateEffect 
              words="Understand your financial life like never before."
              className="text-center text-white text-2xl sm:text-3xl md:text-4xl lg:text-5xl"
            />
          </div>
          <p className={`${poppins.className} text-white/90 text-base sm:text-lg md:text-xl sm:whitespace-nowrap`} style={{ lineHeight: '1.4' }}>
            You can now rely on growbe to get to grips with your financial life, thanks to expert level insights.
          </p>
          <p className={`${poppins.className} text-white/90 text-center text-base sm:text-lg md:text-xl sm:whitespace-nowrap`} style={{ lineHeight: '1.4' }}>
            See what you earn, what you owe and get ready for what's next.
          </p>
        </div>

        <div className="w-full flex justify-center mt-[10px]">
          <div className="w-full max-w-[240px] sm:max-w-[288px] md:max-w-[336px] lg:max-w-[384px]">
          <Card className="border-none bg-transparent transition-colors shadow-none">
            <CardHeader className="text-center pb-2">
              {/* Tab Buttons */}
              <div className="flex gap-4 mb-0 justify-center">
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('login');
                    setError('');
                  }}
                  className={`flex-1 px-4 py-2 text-black backdrop-blur-sm border border-black rounded-md hover:shadow-[0px_0px_4px_4px_rgba(0,0,0,0.1)] bg-white text-sm transition duration-200 ${
                    activeTab === 'login' ? 'opacity-100' : 'opacity-50'
                  }`}
                >
                  Login
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('signup');
                    setError('');
                  }}
                  className={`flex-1 px-4 py-2 text-black backdrop-blur-sm border border-black rounded-md hover:shadow-[0px_0px_4px_4px_rgba(0,0,0,0.1)] bg-white text-sm transition duration-200 ${
                    activeTab === 'signup' ? 'opacity-100' : 'opacity-50'
                  }`}
                >
                  Signup
                </button>
              </div>
            </CardHeader>
            <CardContent className="!pt-1 !pb-3 !px-6">
              {activeTab === 'login' && (
                <div className="mt-4 p-4 rounded-md border border-white/30 bg-white/10 backdrop-blur-sm animate-in fade-in slide-in-from-top-2 duration-200">
                  <form onSubmit={handleExistingUser} className="space-y-4">
                    <div>
                      <label htmlFor="customerId" className="block text-base font-medium text-white mb-2">
                        Customer ID or Session ID
                      </label>
                      <Input
                        id="customerId"
                        type="text"
                        value={customerId}
                        onChange={(e) => {
                          setCustomerId(e.target.value);
                          setError('');
                        }}
                        placeholder="Enter your Customer ID (e.g., C001) or Session ID"
                        className={`px-4 py-2 text-black backdrop-blur-sm border border-black rounded-md bg-white text-sm transition duration-200 ${error ? 'border-red-500' : ''}`}
                        disabled={isLoading}
                      />
                      {error && <p className="text-red-500 text-base mt-1">{error}</p>}
                    </div>
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full px-4 py-2 text-black backdrop-blur-sm border border-black rounded-md hover:shadow-[0px_0px_4px_4px_rgba(0,0,0,0.1)] bg-white text-sm transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      {isLoading ? (
                        <>
                          <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin mr-2" />
                          Verifying...
                        </>
                      ) : (
                        <>Access my profile</>
                      )}
                    </button>
                  </form>
                </div>
              )}
              {activeTab === 'signup' && (
                <div className="mt-4 p-4 rounded-md border border-white/30 bg-white/10 backdrop-blur-sm animate-in fade-in slide-in-from-top-2 duration-200">
                  <form onSubmit={(e) => { e.preventDefault(); handleNewUser(); }} className="space-y-4">
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <label htmlFor="firstName" className="block text-base font-medium text-white mb-2">
                          First Name
                        </label>
                        <Input
                          id="firstName"
                          type="text"
                          value={firstName}
                          onChange={(e) => {
                            setFirstName(e.target.value);
                            setError('');
                          }}
                          className="px-4 py-2 rounded-md border border-black bg-white text-black text-sm hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)] transition duration-200"
                          disabled={isLoading}
                        />
                      </div>
                      <div className="flex-1">
                        <label htmlFor="lastName" className="block text-base font-medium text-white mb-2">
                          Last Name
                        </label>
                        <Input
                          id="lastName"
                          type="text"
                          value={lastName}
                          onChange={(e) => {
                            setLastName(e.target.value);
                            setError('');
                          }}
                          className="px-4 py-2 rounded-md border border-black bg-white text-black text-sm hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)] transition duration-200"
                          disabled={isLoading}
                        />
                      </div>
                    </div>
                    <div>
                      <label htmlFor="guidanceType" className="block text-base font-medium text-white mb-2">
                        What guidance are you looking for?
                      </label>
                      <Select value={guidanceType} onValueChange={(value) => {
                        setGuidanceType(value);
                        setError('');
                      }} disabled={isLoading}>
                        <SelectTrigger className="w-full px-4 py-2 text-black backdrop-blur-sm border border-black rounded-md bg-white text-sm transition duration-200">
                          <SelectValue placeholder="Select a guidance type" />
                        </SelectTrigger>
                        <SelectContent className="bg-white border border-black">
                          <SelectItem value="debt">Guidance on any kind of debt</SelectItem>
                          <SelectItem value="financial-goals">Guidance on financial goal achievement</SelectItem>
                          <SelectItem value="home-affordability">Home affordability guidance</SelectItem>
                          <SelectItem value="general">General financial guidance</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full px-4 py-2 text-black backdrop-blur-sm border border-black rounded-md hover:shadow-[0px_0px_4px_4px_rgba(0,0,0,0.1)] bg-white text-sm transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      Get started
                    </button>
                  </form>
                </div>
              )}
            </CardContent>
          </Card>
          </div>
        </div>
        </div>

        {/* Infinite Moving Cards - 50px below login/signup section */}
        <div className="w-full relative mb-[60px] -mt-[126px]">
          <div className="text-center mb-[60px]">
            <h2 className={`${poppinsBold.className} text-white text-xl sm:text-2xl md:text-3xl lg:text-4xl`}>
              Get inspired by real prompts
            </h2>
          </div>
          <InfiniteMovingCards
            items={[
              {
                quote: "Given my income and existing debt, what is the maximum mortgage payment I can safely take on and still save $1,000 monthly?",
                name: "",
                title: ""
              },
              {
                quote: "If I save an extra $300/month, how much faster can I hit my $60,000 down payment goal?",
                name: "",
                title: ""
              },
              {
                quote: "How would raising my credit score by 40 points impact the interest rate I qualify for on a $400,000 mortgage?",
                name: "",
                title: ""
              },
              {
                quote: "Should I buy a home now or wait three years, assuming 5% home price appreciation and a 7% return on my investments?",
                name: "",
                title: ""
              },
              {
                quote: "Should I use the snowball or avalanche method to pay off my three student loans? Show me the total interest saved for each.",
                name: "",
                title: ""
              },
              {
                quote: "Is it worth refinancing my high-interest student loans if it means extending the loan term by five years?",
                name: "",
                title: ""
              },
              {
                quote: "Based on my expenses, what is the minimum emergency fund I should maintain before aggressively tackling my credit card debt?",
                name: "",
                title: ""
              }
            ]}
            direction="left"
            speed="slow"
            cardClassName="w-[300px] max-w-full px-3 py-3 md:w-[380px]"
            className="text-white w-full max-w-none"
          />
        </div>
      </div>
    </div>
  );
}