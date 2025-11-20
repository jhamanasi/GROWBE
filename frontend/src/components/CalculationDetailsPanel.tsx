'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Calculator } from 'lucide-react';
import MathDisplay from './MathDisplay';

interface CalculationStep {
  title: string;
  description: string;
  latex: string;
  display: boolean;
}

interface CalculationDetails {
  scenario_type: string;
  calculation_steps?: CalculationStep[];
  latex_formulas?: string[];
}

interface CalculationDetailsPanelProps {
  calculationDetails: CalculationDetails;
  className?: string;
  defaultCollapsed?: boolean;
}

export default function CalculationDetailsPanel({
  calculationDetails,
  className = '',
  defaultCollapsed = true
}: CalculationDetailsPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  // Determine the panel title based on scenario type
  const getPanelTitle = () => {
    const scenarioTypeMap: Record<string, string> = {
      'current': 'Current Payment Calculation',
      'extra_payment': 'Extra Payment Scenario',
      'target_payoff': 'Target Payoff Calculation',
      'consolidate': 'Consolidation Analysis',
      'refinance': 'Refinancing Analysis',
      'avalanche': 'Avalanche Strategy',
      'snowball': 'Snowball Strategy'
    };
    
    return scenarioTypeMap[calculationDetails.scenario_type] || 'Calculation Details';
  };

  const steps = calculationDetails.calculation_steps || [];
  const hasSteps = steps.length > 0;

  return (
    <div className={`border border-blue-100 bg-blue-50/30 overflow-hidden rounded-lg ${className}`}>
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-blue-50 border-b border-blue-100 transition-colors"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div className="flex items-center space-x-2">
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4 text-blue-600" />
          ) : (
            <ChevronDown className="h-4 w-4 text-blue-600" />
          )}
          <Calculator className="h-4 w-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-blue-900">{getPanelTitle()}</h3>
          {hasSteps && (
            <span className="text-xs text-blue-600 bg-blue-100 px-2 py-0.5 rounded-full">
              {steps.length} {steps.length === 1 ? 'step' : 'steps'}
            </span>
          )}
        </div>

        <div className="text-xs text-blue-400">
          {isCollapsed ? 'Click to view calculations' : 'Click to hide'}
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <div className="p-6 space-y-6 bg-white">
          {!hasSteps ? (
            <div className="text-center py-8 text-gray-500">
              <p className="text-sm">No calculation details available</p>
            </div>
          ) : (
            <>
              {steps.map((step, index) => (
                <div key={index} className="space-y-2">
                  {/* Step Title */}
                  <div className="flex items-start space-x-2">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold flex-shrink-0 mt-0.5">
                      {index + 1}
                    </span>
                    <h4 className="text-sm font-semibold text-gray-900 pt-0.5">{step.title}</h4>
                  </div>

                  {/* Step Description */}
                  {step.description && (
                    <p className="text-sm text-gray-600 ml-8">{step.description}</p>
                  )}

                  {/* Step Formula (if display=true) */}
                  {step.display && step.latex && (
                    <div className="ml-8 my-3 p-4 bg-gray-50 border border-gray-200 rounded-md overflow-x-auto">
                      <MathDisplay formula={step.latex} displayMode />
                    </div>
                  )}

                  {/* Divider (except for last step) */}
                  {index < steps.length - 1 && (
                    <div className="ml-8 border-b border-gray-100 pt-2"></div>
                  )}
                </div>
              ))}

              {/* Optional: Display latex_formulas if calculation_steps is not available */}
              {!hasSteps && calculationDetails.latex_formulas && calculationDetails.latex_formulas.length > 0 && (
                <div className="space-y-4">
                  {calculationDetails.latex_formulas.map((formula, index) => {
                    // Remove $$ wrappers if present
                    const cleanFormula = formula.replace(/^\$\$|\$\$$/g, '').trim();
                    return (
                      <div key={index} className="p-4 bg-gray-50 border border-gray-200 rounded-md overflow-x-auto">
                        <MathDisplay formula={cleanFormula} displayMode />
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

