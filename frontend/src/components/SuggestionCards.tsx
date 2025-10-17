'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Send, Sparkles, DollarSign } from 'lucide-react';

interface Suggestion {
  title: string;
  description: string;
  question: string;
  icon: string;
}

interface CustomerContext {
  customer_id: string;
  first_name: string;
  last_name: string;
  base_salary_annual?: number;
  persona_type?: string;
  assessment?: {
    primary_goal?: string;
    debt_status?: string;
    employment_status?: string;
    timeline?: string;
    risk_tolerance?: string;
  };
}

interface SuggestionCardsProps {
  suggestions: Suggestion[];
  onSuggestionClick: (question: string) => void;
  isLoading?: boolean;
  userName?: string;
  customerContext?: CustomerContext | null;
}

export default function SuggestionCards({ 
  suggestions, 
  onSuggestionClick, 
  isLoading = false,
  userName,
  customerContext
}: SuggestionCardsProps) {

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="flex items-center space-x-3 mb-4">
          <motion.div
            className="w-8 h-8 bg-gradient-to-r from-green-500 to-blue-600 rounded-full flex items-center justify-center"
            animate={{ rotate: 360 }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "linear"
            }}
          >
            <span className="text-white text-lg">💰</span>
          </motion.div>
          <span className="text-lg font-medium text-gray-700">Growbe is loading suggestions...</span>
        </div>
        
        <div className="flex space-x-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 bg-green-500 rounded-full"
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.5, 1, 0.5]
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut"
              }}
            />
          ))}
        </div>
      </div>
    );
  }

  // Generate personalized greeting based on customer context
  const getPersonalizedGreeting = () => {
    if (!customerContext) {
      return {
        title: "Welcome to Growbe! 💰",
        subtitle: "Hi there! I'm Growbe, your AI financial advisor.",
        description: "I can help you with student loans, home buying, debt management, and financial planning. Let's get started with your financial journey!"
      };
    }

    const { first_name, persona_type, assessment } = customerContext;
    const name = first_name || 'there';
    
    let title = `Welcome back, ${name}! 💰`;
    let subtitle = "I'm Growbe, your AI financial advisor.";
    let description = "I'm here to help you achieve your financial goals. Let's continue working on your financial plan!";

    // Personalize based on persona type
    if (persona_type) {
      switch (persona_type) {
        case 'high_spending_student_debtor':
          title = `Let's tackle those student loans, ${name}! 🎓`;
          description = "I can help you optimize your student loan payments and create a strategy to pay them off faster.";
          break;
        case 'aspiring_homebuyer_moderate_savings':
          title = `Ready to buy your dream home, ${name}? 🏠`;
          description = "Let's analyze your home buying affordability and create a savings plan for your down payment.";
          break;
        case 'credit_card_juggler':
          title = `Let's get your debt under control, ${name}! 💳`;
          description = "I can help you create a debt payoff strategy and improve your credit score.";
          break;
        case 'consistent_saver_with_idle_cash':
          title = `Time to grow your wealth, ${name}! 📈`;
          description = "Let's explore investment opportunities and optimize your savings strategy.";
          break;
        case 'freelancer_with_income_volatility':
          title = `Let's stabilize your finances, ${name}! 💼`;
          description = "I can help you manage irregular income and build a robust financial foundation.";
          break;
      }
    }

    // Personalize based on primary goal
    if (assessment?.primary_goal) {
      switch (assessment.primary_goal) {
        case 'student_loans':
          description = "Let's focus on optimizing your student loan strategy and payment plan.";
          break;
        case 'home_buying':
          description = "Let's work on your home buying plan and affordability analysis.";
          break;
        case 'debt_consolidation':
          description = "Let's create a comprehensive debt consolidation and payoff strategy.";
          break;
        case 'emergency_fund':
          description = "Let's build a solid emergency fund and improve your financial security.";
          break;
        case 'investment':
          description = "Let's explore investment opportunities and grow your wealth.";
          break;
        case 'retirement':
          description = "Let's plan for your retirement and long-term financial security.";
          break;
      }
    }

    return { title, subtitle, description };
  };

  const greeting = getPersonalizedGreeting();

  return (
    <div className="py-4 flex flex-col items-center">
      {/* Greeting */}
      <div className="flex flex-col items-center text-center mb-6 max-w-2xl">
        <div className="flex items-center space-x-2 mb-3">
          <Sparkles className="h-5 w-5 text-green-500" />
          <h2 className="text-2xl font-bold text-gray-900">
            {greeting.title}
          </h2>
        </div>
        <p className="text-gray-600 text-base mb-4">
          {greeting.subtitle}
        </p>
        <p className="text-gray-500 text-sm leading-relaxed max-w-xl">
          {greeting.description}
        </p>
      </div>
      
      <div className="max-w-md w-full">
        <div className="grid grid-cols-2 gap-3">
          {suggestions.map((suggestion, index) => (
            <div
              key={index}
              className="cursor-pointer p-px bg-gradient-to-r from-green-300 via-blue-300 via-purple-300 to-yellow-300 hover:from-green-400 hover:via-blue-400 hover:via-purple-400 hover:to-yellow-400 transition-all duration-200 hover:shadow-md rounded-sm"
              onClick={() => onSuggestionClick(suggestion.question)}
            >
              <div className="bg-white h-full p-3 rounded-sm">
                <div className="text-center">
                  <div className="text-2xl mb-2">{suggestion.icon}</div>
                  <h4 className="font-medium text-gray-900 text-sm mb-1">
                    {suggestion.title}
                  </h4>
                  <p className="text-xs text-gray-600 leading-tight">
                    {suggestion.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Financial Tips */}
      {customerContext && (
        <div className="mt-8 max-w-2xl w-full">
          <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 border border-green-200">
            <div className="flex items-center space-x-2 mb-2">
              <DollarSign className="h-4 w-4 text-green-600" />
              <h4 className="font-medium text-gray-900 text-sm">Quick Financial Tip</h4>
            </div>
            <p className="text-xs text-gray-600">
              {getFinancialTip(customerContext)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// Generate personalized financial tips based on customer context
function getFinancialTip(customerContext: CustomerContext): string {
  const { persona_type, assessment } = customerContext;
  
  if (persona_type) {
    switch (persona_type) {
      case 'high_spending_student_debtor':
        return "Consider making extra payments on your highest interest rate student loans first to save money over time.";
      case 'aspiring_homebuyer_moderate_savings':
        return "Aim to save 20% of the home price for a down payment to avoid private mortgage insurance (PMI).";
      case 'credit_card_juggler':
        return "Pay more than the minimum payment on credit cards to reduce interest charges and pay off debt faster.";
      case 'consistent_saver_with_idle_cash':
        return "Consider investing excess cash in a diversified portfolio to beat inflation and grow your wealth.";
      case 'freelancer_with_income_volatility':
        return "Build an emergency fund with 6-12 months of expenses to handle income fluctuations.";
    }
  }
  
  if (assessment?.primary_goal) {
    switch (assessment.primary_goal) {
      case 'student_loans':
        return "Student loan interest may be tax-deductible. Keep track of your payments for tax season.";
      case 'home_buying':
        return "Check your credit score before applying for a mortgage. A higher score can save you thousands in interest.";
      case 'debt_consolidation':
        return "Compare debt consolidation options carefully. Lower monthly payments might mean longer repayment terms.";
      case 'emergency_fund':
        return "Start with a small emergency fund goal, like $1,000, then build up to 3-6 months of expenses.";
      case 'investment':
        return "Start investing early, even with small amounts. Compound interest works best over long periods.";
      case 'retirement':
        return "Take advantage of employer 401(k) matching - it's free money that can significantly boost your retirement savings.";
    }
  }
  
  return "Small, consistent financial actions add up over time. Start with one goal and build momentum!";
}