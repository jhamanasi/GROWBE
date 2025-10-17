'use client';

import { useState } from 'react';
import { RefreshCw, Download, Trash2, Eye, FileText, CheckCircle, AlertCircle } from 'lucide-react';

interface Schema {
  id: string;
  name: string;
  description?: string;
  tables: any[];
  relationships: any[];
  created_at: string;
  updated_at: string;
}

interface SchemaToolbarProps {
  schema: Schema;
  onRefresh: () => void;
  onDelete: () => void;
}

export default function SchemaToolbar({ schema, onRefresh, onDelete }: SchemaToolbarProps) {
  const [showSqlDialog, setShowSqlDialog] = useState(false);
  const [showValidationDialog, setShowValidationDialog] = useState(false);
  const [sqlContent, setSqlContent] = useState('');
  const [validationResult, setValidationResult] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isValidating, setIsValidating] = useState(false);

  const generateSql = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch('http://localhost:9000/schema-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schema_id: schema.id,
          message: 'Generate SQL for this schema'
        })
      });

      if (!response.ok) throw new Error('Failed to generate SQL');
      
      const result = await response.json();
      setSqlContent(result.response);
      setShowSqlDialog(true);
    } catch (err) {
      console.error('Failed to generate SQL:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const validateSchema = async () => {
    setIsValidating(true);
    try {
      const response = await fetch('http://localhost:9000/schema-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schema_id: schema.id,
          message: 'Validate this schema'
        })
      });

      if (!response.ok) throw new Error('Failed to validate schema');
      
      const result = await response.json();
      setValidationResult(result.response);
      setShowValidationDialog(true);
    } catch (err) {
      console.error('Failed to validate schema:', err);
    } finally {
      setIsValidating(false);
    }
  };

  const downloadSql = () => {
    const blob = new Blob([sqlContent], { type: 'text/sql' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${schema.name.replace(/\s+/g, '_').toLowerCase()}_schema.sql`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <div className="bg-white border-b border-gray-200 px-4 py-2">
        <div className="flex items-center justify-center space-x-2">
          <button
            onClick={validateSchema}
            disabled={isValidating}
            className="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded disabled:opacity-50 flex items-center space-x-1"
            title="Validate Schema"
          >
            {isValidating ? (
              <RefreshCw className="h-3 w-3 animate-spin" />
            ) : (
              <CheckCircle className="h-3 w-3" />
            )}
            <span>Validate</span>
          </button>

          <button
            onClick={generateSql}
            disabled={isGenerating}
            className="px-3 py-1.5 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded disabled:opacity-50 flex items-center space-x-1"
            title="Generate SQL"
          >
            {isGenerating ? (
              <RefreshCw className="h-3 w-3 animate-spin" />
            ) : (
              <FileText className="h-3 w-3" />
            )}
            <span>Generate SQL</span>
          </button>
        </div>
      </div>

      {/* SQL Generation Dialog */}
      {showSqlDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-3/4 max-w-4xl max-h-3/4 flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Generated SQL</h3>
              <div className="flex space-x-2">
                <button
                  onClick={downloadSql}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm flex items-center space-x-1"
                >
                  <Download className="h-4 w-4" />
                  <span>Download</span>
                </button>
                <button
                  onClick={() => setShowSqlDialog(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="flex-1 overflow-auto">
              <pre className="bg-gray-900 text-gray-100 p-4 rounded text-sm overflow-auto">
                {sqlContent}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Validation Dialog */}
      {showValidationDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-2/3 max-w-2xl max-h-3/4 flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span>Schema Validation</span>
              </h3>
              <button
                onClick={() => setShowValidationDialog(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="flex-1 overflow-auto">
              <div className="prose prose-sm max-w-none">
                <pre className="whitespace-pre-wrap text-sm">{validationResult}</pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
