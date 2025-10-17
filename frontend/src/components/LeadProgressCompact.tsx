'use client'

import { useState, useEffect } from 'react'
import { CheckCircle, Clock, ChevronDown, ChevronUp } from 'lucide-react'

interface LeadProgressSummary {
  lead_id: number
  name: string
  looking_for: string
  essential_progress: string
  engagement_score: number
  status: string
  captured_info: Record<string, any>
}

interface LeadProgressCompactProps {
  sessionId: string
  className?: string
}

export default function LeadProgressCompact({ sessionId, className = '' }: LeadProgressCompactProps) {
  const [progressData, setProgressData] = useState<LeadProgressSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isExpanded, setIsExpanded] = useState(false)

  // Fetch progress summary
  const fetchProgress = async () => {
    try {
      const response = await fetch(`http://localhost:9000/leads/session/${sessionId}/progress/summary`)
      if (response.ok) {
        const data = await response.json()
        setProgressData(data)
      }
    } catch (error) {
      console.error('Error fetching lead progress:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Auto-refresh progress every 3 seconds
  useEffect(() => {
    if (sessionId) {
      fetchProgress()
      const interval = setInterval(fetchProgress, 3000)
      return () => clearInterval(interval)
    }
  }, [sessionId])

  if (isLoading) {
    return (
      <div className={`bg-blue-50 border border-blue-200 rounded-lg p-3 ${className}`}>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm text-blue-700">Loading your progress...</span>
        </div>
      </div>
    )
  }

  if (!progressData) {
    return null
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new': return 'bg-gray-100 text-gray-800'
      case 'qualified': return 'bg-green-100 text-green-800'
      case 'contacted': return 'bg-blue-100 text-blue-800'
      case 'converted': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getEngagementColor = (score: number) => {
    if (score >= 70) return 'text-green-600'
    if (score >= 40) return 'text-yellow-600'
    return 'text-red-600'
  }

  const capturedCount = Object.keys(progressData.captured_info).length
  const totalEssential = 10 // location, budget_range, timeline, property_type, bedrooms, bathrooms, must_haves, motivation, pre_approved, current_situation

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg ${className}`}>
      {/* Compact Header */}
      <div 
        className="p-3 cursor-pointer hover:bg-blue-100 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h3 className="font-medium text-blue-900 text-sm">
                What we know so far {capturedCount > 0 && `(${capturedCount})`}
              </h3>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-blue-600" />
            ) : (
              <ChevronDown className="w-4 h-4 text-blue-600" />
            )}
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-blue-200 p-3 bg-white">
          <div className="space-y-3">
            {/* Progress Stats */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-600">
                  {capturedCount} of {totalEssential} details captured
                </span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(progressData.status)}`}>
                  {progressData.status}
                </span>
              </div>
              <span className={`text-xs font-medium ${getEngagementColor(progressData.engagement_score)}`}>
                Engagement: {progressData.engagement_score}/100
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-blue-200 rounded-full h-1.5 mb-3">
              <div 
                className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${(capturedCount / totalEssential) * 100}%` }}
              ></div>
            </div>
            
            <h4 className="font-medium text-gray-900 text-sm flex items-center">
              <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
              Captured Information
            </h4>
            
            {Object.keys(progressData.captured_info).length > 0 ? (
              <div className="grid grid-cols-1 gap-2">
                {Object.entries(progressData.captured_info).map(([field, value]) => {
                  // Format field names nicely
                  const fieldDisplay = field
                    .split('_')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ');
                  
                  // Format values
                  let displayValue = value;
                  if (typeof value === 'boolean') {
                    displayValue = value ? 'Yes' : 'No';
                  } else if (value === null) {
                    displayValue = 'Not specified';
                  }
                  
                  return (
                    <div key={field} className="bg-green-50 border border-green-200 rounded-md p-2">
                      <p className="text-xs text-gray-600">{fieldDisplay}</p>
                      <p className="text-xs font-medium text-green-800">{displayValue}</p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-600">No details captured yet. Keep chatting with Ava!</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
