'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Database, Plus, Settings, Download, Trash2, RefreshCw } from 'lucide-react';
import Link from 'next/link';
import SchemaCanvas from './components/SchemaCanvas';
import SchemaChatbot from './components/SchemaChatbot';
import SchemaToolbar from './components/SchemaToolbar';

// Types
interface Schema {
  id: string;
  name: string;
  description?: string;
  tables: Table[];
  relationships: Relationship[];
  created_at: string;
  updated_at: string;
}

interface Table {
  name: string;
  columns: Column[];
}

interface Column {
  name: string;
  type: 'TEXT' | 'INTEGER' | 'REAL' | 'BLOB' | 'DATETIME';
  primary_key: boolean;
  not_null: boolean;
  default?: string;
}

interface Relationship {
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
}

export default function SchemaBuilderPage() {
  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [currentSchema, setCurrentSchema] = useState<Schema | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newSchemaName, setNewSchemaName] = useState('');
  const [newSchemaDescription, setNewSchemaDescription] = useState('');

  // Load schemas on component mount
  useEffect(() => {
    loadSchemas();
  }, []);

  const loadSchemas = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('http://localhost:9000/schemas');
      if (!response.ok) throw new Error('Failed to load schemas');
      
      const schemaList = await response.json();
      setSchemas(schemaList);
      
      // Auto-select first schema if available
      if (schemaList.length > 0 && !currentSchema) {
        setCurrentSchema(schemaList[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load schemas');
    } finally {
      setIsLoading(false);
    }
  };

  const createSchema = async () => {
    if (!newSchemaName.trim()) return;

    try {
      const response = await fetch('http://localhost:9000/schemas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newSchemaName.trim(),
          description: newSchemaDescription.trim() || undefined
        })
      });

      if (!response.ok) throw new Error('Failed to create schema');
      
      const newSchema = await response.json();
      setSchemas(prev => [newSchema, ...prev]);
      setCurrentSchema(newSchema);
      setShowCreateDialog(false);
      setNewSchemaName('');
      setNewSchemaDescription('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create schema');
    }
  };

  const deleteSchema = async (schemaId: string) => {
    if (!confirm('Are you sure you want to delete this schema?')) return;

    try {
      const response = await fetch(`http://localhost:9000/schemas/${schemaId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete schema');
      
      setSchemas(prev => prev.filter(s => s.id !== schemaId));
      if (currentSchema?.id === schemaId) {
        const remaining = schemas.filter(s => s.id !== schemaId);
        setCurrentSchema(remaining.length > 0 ? remaining[0] : null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete schema');
    }
  };

  const refreshCurrentSchema = async () => {
    if (!currentSchema) return;

    try {
      const response = await fetch(`http://localhost:9000/schemas/${currentSchema.id}`);
      if (!response.ok) throw new Error('Failed to refresh schema');
      
      const updatedSchema = await response.json();
      console.log('Refreshed schema data:', updatedSchema);
      setCurrentSchema(updatedSchema);
      
      // Update in schemas list
      setSchemas(prev => prev.map(s => s.id === updatedSchema.id ? updatedSchema : s));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh schema');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Database className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-pulse" />
          <p className="text-gray-600">Loading schemas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mx-6 mt-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
              <button
                onClick={() => setError(null)}
                className="text-red-500 hover:text-red-700 text-sm underline mt-1"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

             {/* Main Content */}
             {currentSchema ? (
               <div className="flex h-screen">
                 {/* Full Width Schema Visualization */}
                 <div className="flex-1 flex flex-col">
                   {/* Header */}
                   <div className="bg-gray-800 text-white px-6 py-3 flex items-center justify-between">
                     <div className="flex items-center space-x-3">
                       <Link href="/" className="flex items-center text-gray-300 hover:text-white">
                         <ArrowLeft className="h-4 w-4" />
                       </Link>
                       <Database className="h-5 w-5 text-blue-400" />
                       <select
                         value={currentSchema?.id || ''}
                         onChange={(e) => {
                           const schema = schemas.find(s => s.id === e.target.value);
                           setCurrentSchema(schema || null);
                         }}
                         className="bg-gray-700 text-white border border-gray-600 rounded px-3 py-1.5 text-sm font-medium"
                       >
                         {schemas.map(schema => (
                           <option key={schema.id} value={schema.id}>
                             {schema.name}
                           </option>
                         ))}
                       </select>
                       <div className="text-xs text-gray-400">
                         {currentSchema.tables.length} tables • {currentSchema.relationships.length} relationships
                       </div>
                     </div>
                     
                     {/* Action Buttons */}
                     <div className="flex items-center space-x-2">
                       <button
                         onClick={() => setShowCreateDialog(true)}
                         className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center space-x-1"
                       >
                         <Plus className="h-4 w-4" />
                         <span>New Schema</span>
                       </button>
                       <button
                         onClick={refreshCurrentSchema}
                         className="px-3 py-1.5 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded flex items-center space-x-1"
                         title="Refresh"
                       >
                         <RefreshCw className="h-4 w-4" />
                       </button>
                       <button
                         onClick={() => {
                           // Validate schema logic will be in SchemaToolbar
                         }}
                         className="px-3 py-1.5 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded flex items-center space-x-1"
                         title="Validate"
                       >
                         <Settings className="h-4 w-4" />
                       </button>
                       <button
                         onClick={() => deleteSchema(currentSchema.id)}
                         className="px-3 py-1.5 text-sm text-red-400 hover:text-red-300 hover:bg-gray-700 rounded flex items-center space-x-1"
                         title="Delete"
                       >
                         <Trash2 className="h-4 w-4" />
                       </button>
                     </div>
                   </div>
                   
                   <SchemaToolbar 
                     schema={currentSchema}
                     onRefresh={refreshCurrentSchema}
                     onDelete={() => {}}
                   />
                   
                   <SchemaCanvas 
                     schema={currentSchema}
                     onSchemaUpdate={refreshCurrentSchema}
                   />
                 </div>

                 {/* Floating Chatbot */}
                 <SchemaChatbot 
                   schema={currentSchema}
                   onSchemaUpdate={refreshCurrentSchema}
                 />
               </div>
      ) : (
        /* No Schema Selected State */
        <div className="flex h-screen items-center justify-center">
          <div className="text-center">
            <Database className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-600 mb-2">No Schema Selected</h2>
            <p className="text-gray-500 mb-6">Create a new schema or select an existing one to get started</p>
            <button
              onClick={() => setShowCreateDialog(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded flex items-center space-x-2 mx-auto"
            >
              <Plus className="h-5 w-5" />
              <span>Create New Schema</span>
            </button>
          </div>
        </div>
      )}

      {/* Create Schema Dialog */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Create New Schema</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Schema Name *
                </label>
                <input
                  type="text"
                  value={newSchemaName}
                  onChange={(e) => setNewSchemaName(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., E-commerce Database"
                  autoFocus
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={newSchemaDescription}
                  onChange={(e) => setNewSchemaDescription(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Optional description..."
                  rows={3}
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateDialog(false);
                  setNewSchemaName('');
                  setNewSchemaDescription('');
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={createSchema}
                disabled={!newSchemaName.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded"
              >
                Create Schema
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
