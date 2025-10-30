'use client';

import React, { useEffect, useRef } from 'react';

interface MathDisplayProps {
  formula: string;
  displayMode?: boolean; // true for block display, false for inline
  className?: string;
}

/**
 * MathDisplay component for rendering LaTeX math formulas using KaTeX
 * 
 * Usage:
 * - Inline: <MathDisplay formula="E = mc^2" />
 * - Block: <MathDisplay formula="E = mc^2" displayMode={true} />
 */
export default function MathDisplay({ formula, displayMode = false, className = '' }: MathDisplayProps) {
  const containerRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const renderMath = async () => {
      if (typeof window !== 'undefined' && containerRef.current) {
        try {
          // Dynamically import katex only on client side
          const katex = (await import('katex')).default;
          await import('katex/dist/katex.min.css');
          
          katex.render(formula, containerRef.current, {
            throwOnError: false,
            displayMode,
            output: 'html',
            trust: false, // Security: don't allow \href or arbitrary HTML
            strict: 'warn'
          });
        } catch (error) {
          console.error('Error rendering math:', error);
          // Fallback: show the raw formula
          if (containerRef.current) {
            containerRef.current.textContent = formula;
          }
        }
      }
    };

    renderMath();
  }, [formula, displayMode]);

  return (
    <span 
      ref={containerRef} 
      className={`math-display ${displayMode ? 'block my-4' : 'inline'} ${className}`}
      style={{
        fontSize: displayMode ? '1.1em' : '1em',
        overflowX: displayMode ? 'auto' : 'visible',
        overflowY: 'hidden'
      }}
    />
  );
}

/**
 * Helper function to detect and extract LaTeX from markdown-style delimiters
 * Supports: $inline$, $$block$$, \(inline\), \[block\]
 */
export function extractLatexFromText(text: string): Array<{ type: 'text' | 'math', content: string, displayMode: boolean }> {
  const parts: Array<{ type: 'text' | 'math', content: string, displayMode: boolean }> = [];
  
  // Regex to match LaTeX delimiters
  const regex = /(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$|\\[\[\(][\s\S]+?\\[\]\)])/g;
  
  let lastIndex = 0;
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    // Add text before the math
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex, match.index),
        displayMode: false
      });
    }
    
    // Add the math part
    const fullMatch = match[0];
    let formula = fullMatch;
    let displayMode = false;
    
    // Determine display mode and extract formula
    if (fullMatch.startsWith('$$') && fullMatch.endsWith('$$')) {
      formula = fullMatch.slice(2, -2);
      displayMode = true;
    } else if (fullMatch.startsWith('$') && fullMatch.endsWith('$')) {
      formula = fullMatch.slice(1, -1);
      displayMode = false;
    } else if (fullMatch.startsWith('\\[') && fullMatch.endsWith('\\]')) {
      formula = fullMatch.slice(2, -2);
      displayMode = true;
    } else if (fullMatch.startsWith('\\(') && fullMatch.endsWith('\\)')) {
      formula = fullMatch.slice(2, -2);
      displayMode = false;
    }
    
    parts.push({
      type: 'math',
      content: formula.trim(),
      displayMode
    });
    
    lastIndex = match.index + fullMatch.length;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push({
      type: 'text',
      content: text.substring(lastIndex),
      displayMode: false
    });
  }
  
  return parts;
}

/**
 * Component to render text with embedded LaTeX formulas
 */
interface TextWithMathProps {
  text: string;
  className?: string;
}

export function TextWithMath({ text, className = '' }: TextWithMathProps) {
  const parts = extractLatexFromText(text);
  
  return (
    <span className={className}>
      {parts.map((part, index) => {
        if (part.type === 'math') {
          return (
            <MathDisplay 
              key={index} 
              formula={part.content} 
              displayMode={part.displayMode}
            />
          );
        } else {
          return <span key={index}>{part.content}</span>;
        }
      })}
    </span>
  );
}
