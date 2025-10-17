'use client'

import { useState, useEffect } from 'react'
import { CheckCircle, Clock, Edit3, X } from 'lucide-react'

interface LeadProgressData {
  lead_id: number
  session_id: string
  completion_percentage: number
  completed_fields: number
  total_fields: number
  filled_fields: Array<{
    field: string
    value: any
    display_name: string
  }>
  missing_fields: Array<{
    field: string
    display_name: string
  }>
  engagement_score: number
  status: string
  last_updated: string
}

interface LeadProgressProps {
  sessionId: string
  className?: string
}

export default function LeadProgress({ sessionId, className = '' }: LeadProgressProps) {
  const [progressData, setProgressData] = useState<LeadProgressData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isExpanded, setIsExpanded] = useState(false)
  const [editingField, setEditingField] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')

  // Fetch progress data
  const fetchProgress = async () => {
    try {
      const response = await fetch(`http://localhost:9000/leads/session/${sessionId}/progress`)
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

  // Update field value
  const updateField = async (field: string, value: string) => {
    try {
      const response = await fetch(`http://localhost:9000/leads/session/${sessionId}/progress/update-field`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          field: field,
          value: value
        })
      })

      if (response.ok) {
        // Refresh progress data
        await fetchProgress()
        setEditingField(null)
        setEditValue('')
      }
    } catch (error) {
      console.error('Error updating field:', error)
    }
  }

  // Auto-refresh progress every 5 seconds
  useEffect(() => {
    if (sessionId) {
      fetchProgress()
      const interval = setInterval(fetchProgress, 5000)
      return () => clearInterval(interval)
    }
  }, [sessionId])

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm text-gray-600">Loading your progress...</span>
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

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      {/* Header */}
      <div 
        className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-blue-600 font-semibold text-sm">
                {progressData.completion_percentage}%
              </span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Your Progress</h3>
              <p className="text-sm text-gray-600">
                {progressData.completed_fields} of {progressData.total_fields} details captured
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(progressData.status)}`}>
              {progressData.status}
            </span>
            <span className={`text-sm font-medium ${getEngagementColor(progressData.engagement_score)}`}>
              {progressData.engagement_score}/100
            </span>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progressData.completion_percentage}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200 p-4 space-y-4">
          {/* Captured Information */}
          {progressData.filled_fields.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                Captured Information
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {progressData.filled_fields.map((field) => (
                  <div key={field.field} className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-green-800">{field.display_name}</p>
                        <p className="text-sm text-green-700">
                          {typeof field.value === 'boolean' 
                            ? (field.value ? 'Yes' : 'No')
                            : field.value
                          }
                        </p>
                      </div>
                      <button
                        onClick={() => {
                          setEditingField(field.field)
                          setEditValue(field.value?.toString() || '')
                        }}
                        className="text-green-600 hover:text-green-800 transition-colors"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Missing Information */}
          {progressData.missing_fields.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                <Clock className="w-4 h-4 text-amber-500 mr-2" />
                Still Need
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {progressData.missing_fields.map((field) => (
                  <div key={field.field} className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                    <p className="text-sm font-medium text-amber-800">{field.display_name}</p>
                    <p className="text-xs text-amber-600">Not specified yet</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Edit Modal */}
          {editingField && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
                <h3 className="font-semibold text-gray-900 mb-4">
                  Edit {progressData.filled_fields.find(f => f.field === editingField)?.display_name}
                </h3>
                <input
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter new value..."
                />
                <div className="flex justify-end space-x-3 mt-4">
                  <button
                    onClick={() => {
                      setEditingField(null)
                      setEditValue('')
                    }}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => updateField(editingField, editValue)}
                    className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
