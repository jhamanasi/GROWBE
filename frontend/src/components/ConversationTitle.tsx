'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Edit2, Check, X, RefreshCw } from 'lucide-react';

interface ConversationTitleProps {
  conversationId: string;
  title: string;
  onTitleUpdate?: (newTitle: string) => void;
}

export default function ConversationTitle({
  conversationId,
  title,
  onTitleUpdate,
}: ConversationTitleProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(title);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSave = async () => {
    if (editValue.trim() && editValue !== title) {
      // Update title via API (you may need to add a PATCH endpoint)
      // For now, we'll use the summary endpoint to regenerate
      onTitleUpdate?.(editValue);
    }
    setIsEditing(false);
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/conversations/${conversationId}/summary`,
        { method: 'POST' }
      );
      if (response.ok) {
        const data = await response.json();
        setEditValue(data.title);
        onTitleUpdate?.(data.title);
      }
    } catch (error) {
      console.error('Failed to generate title:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-2">
        <Input
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          className="flex-1"
          autoFocus
        />
        <Button size="sm" onClick={handleSave} variant="default">
          <Check className="h-4 w-4" />
        </Button>
        <Button
          size="sm"
          onClick={() => {
            setEditValue(title);
            setIsEditing(false);
          }}
          variant="outline"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 flex-grow">
      {/* Edit and Regenerate buttons on the left */}
      {!isEditing && (
        <Button size="sm" onClick={() => setIsEditing(true)} variant="ghost" className="text-gray-600 hover:bg-gray-100">
        <Edit2 className="h-4 w-4" />
      </Button>
      )}
      <Button
        size="sm"
        onClick={handleGenerate}
        disabled={isGenerating}
        variant="ghost"
        title="Regenerate title with AI"
        className="text-gray-600 hover:bg-gray-100"
      >
        <RefreshCw className={`h-4 w-4 ${isGenerating ? 'animate-spin' : ''}`} />
      </Button>
      <h1 className="text-lg font-semibold text-gray-900 flex-1 ml-2 mr-auto">{title}</h1>
    </div>
  );
}

