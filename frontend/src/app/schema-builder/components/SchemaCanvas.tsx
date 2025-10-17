'use client';

import { useState } from 'react';
import { Table, Key, ChevronDown, ChevronRight, Type, Hash, Calendar, Binary, ArrowRight } from 'lucide-react';

interface Schema {
  id: string;
  name: string;
  tables: TableType[];
  relationships: Relationship[];
}

interface TableType {
  name: string;
  columns: Column[];
  record_count?: number;
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

interface SchemaCanvasProps {
  schema: Schema;
  onSchemaUpdate: () => void;
}

export default function SchemaCanvas({ schema, onSchemaUpdate }: SchemaCanvasProps) {
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  const [showRelationships, setShowRelationships] = useState(true);

  const toggleTable = (tableName: string) => {
    const newExpanded = new Set(expandedTables);
    if (newExpanded.has(tableName)) {
      newExpanded.delete(tableName);
    } else {
      newExpanded.add(tableName);
    }
    setExpandedTables(newExpanded);
  };

  const expandAll = () => {
    setExpandedTables(new Set(schema.tables?.map(t => t.name) || []));
  };

  const collapseAll = () => {
    setExpandedTables(new Set());
  };

  const getColumnIcon = (type: Column['type']) => {
    switch (type) {
      case 'TEXT': return <Type className="h-4 w-4 text-blue-500" />;
      case 'INTEGER': return <Hash className="h-4 w-4 text-green-500" />;
      case 'REAL': return <Hash className="h-4 w-4 text-orange-500" />;
      case 'DATETIME': return <Calendar className="h-4 w-4 text-purple-500" />;
      case 'BLOB': return <Binary className="h-4 w-4 text-gray-500" />;
      default: return <Type className="h-4 w-4 text-gray-500" />;
    }
  };

  const getConstraintBadges = (column: Column) => {
    const badges = [];
    if (column.primary_key) {
      badges.push(<span key="pk" className="px-1 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded">PK</span>);
    }
    if (column.not_null && !column.primary_key) {
      badges.push(<span key="nn" className="px-1 py-0.5 bg-red-100 text-red-800 text-xs rounded">NOT NULL</span>);
    }
    if (column.default) {
      badges.push(<span key="def" className="px-1 py-0.5 bg-blue-100 text-blue-800 text-xs rounded">DEFAULT</span>);
    }
    return badges;
  };

  if (!schema.tables || schema.tables.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Table className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">No Tables Yet</h3>
          <p className="text-gray-500">Use the chatbot to create your first table</p>
          <div className="mt-4 text-sm text-gray-400">
            <p>Try saying: "Create a users table with id, email, and name columns"</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-gray-50 p-4 overflow-auto">
      {/* Controls */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex space-x-3">
          <button
            onClick={expandAll}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Collapse All
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={showRelationships}
              onChange={(e) => setShowRelationships(e.target.checked)}
              className="rounded"
            />
            <span>Show Relationships</span>
          </label>
        </div>
      </div>

      {/* Tables */}
      <div className="space-y-4">
        {schema.tables.map((table) => {
          const isExpanded = expandedTables.has(table.name);
          
          return (
            <div key={table.name} className="bg-white rounded-lg border border-gray-200 shadow-sm">
              {/* Table Header */}
              <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
                onClick={() => toggleTable(table.name)}
              >
                <div className="flex items-center space-x-3">
                  {isExpanded ? (
                    <ChevronDown className="h-5 w-5 text-gray-500" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-gray-500" />
                  )}
                  <Table className="h-5 w-5 text-gray-700" />
                  <h3 className="text-lg font-medium text-gray-900">{table.name}</h3>
                </div>
                
                <div className="text-sm text-gray-500">
                  {table.columns?.length || 0} columns
                  {table.record_count !== undefined && (
                    <span className="ml-2 text-blue-600">• {table.record_count} records</span>
                  )}
                </div>
              </div>

              {/* Table Content */}
              {isExpanded && (
                <div className="border-t border-gray-200">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Column
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Type
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Constraints
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Default
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {table.columns && table.columns.map((column) => (
                          <tr key={column.name} className="hover:bg-gray-50">
                            <td className="px-4 py-2 whitespace-nowrap">
                              <div className="flex items-center space-x-2">
                                {getColumnIcon(column.type)}
                                <span className="text-sm font-medium text-gray-900">
                                  {column.name}
                                </span>
                                {column.primary_key && (
                                  <Key className="h-4 w-4 text-yellow-600" />
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap">
                              <span className="text-sm text-gray-900">{column.type}</span>
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap">
                              <div className="flex space-x-1">
                                {getConstraintBadges(column)}
                              </div>
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                              {column.default || '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Relationships Section */}
      {showRelationships && schema.relationships && schema.relationships.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Relationships</h3>
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      From
                    </th>
                    <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Relationship
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      To
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {schema.relationships.map((rel, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-4 py-2 whitespace-nowrap">
                        <div className="text-sm">
                          <div className="font-medium text-gray-900">{rel.from_table}</div>
                          <div className="text-gray-500">{rel.from_column}</div>
                        </div>
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-center">
                        <ArrowRight className="h-4 w-4 text-gray-400 mx-auto" />
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap">
                        <div className="text-sm">
                          <div className="font-medium text-gray-900">{rel.to_table}</div>
                          <div className="text-gray-500">{rel.to_column}</div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-3 gap-3">
        <div className="bg-white p-3 rounded-lg border border-gray-200 text-center">
          <div className="text-xl font-bold text-blue-600">{schema.tables?.length || 0}</div>
          <div className="text-xs text-gray-500">Tables</div>
        </div>
        <div className="bg-white p-3 rounded-lg border border-gray-200 text-center">
          <div className="text-xl font-bold text-green-600">
            {schema.tables?.reduce((sum, t) => sum + (t.columns?.length || 0), 0) || 0}
          </div>
          <div className="text-xs text-gray-500">Columns</div>
        </div>
        <div className="bg-white p-3 rounded-lg border border-gray-200 text-center">
          <div className="text-xl font-bold text-purple-600">{schema.relationships?.length || 0}</div>
          <div className="text-xs text-gray-500">Relationships</div>
        </div>
      </div>
    </div>
  );
}
