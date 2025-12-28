/**
 * KOMAS Trading Server - Export Buttons Component
 * ================================================
 * Export optimization results to CSV or JSON.
 * 
 * Features:
 * - Export to CSV (download file)
 * - Export to JSON (download file)
 * - Copy to clipboard
 * - Loading states
 * 
 * Chat #47: Preset Optimizer Results
 */

import React, { useState } from 'react';
import { optimizerApi } from '../../api';

/**
 * Download helper
 */
const downloadFile = (content, filename, contentType) => {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Format date for filename
 */
const formatDateForFilename = () => {
  const now = new Date();
  return now.toISOString().slice(0, 10).replace(/-/g, '');
};

/**
 * Export Buttons Component
 */
const ExportButtons = ({ runId, disabled = false }) => {
  const [loading, setLoading] = useState({ csv: false, json: false });
  const [success, setSuccess] = useState({ csv: false, json: false });
  const [error, setError] = useState(null);
  
  // Export to CSV
  const handleExportCSV = async () => {
    if (!runId || loading.csv) return;
    
    setLoading(l => ({ ...l, csv: true }));
    setError(null);
    
    try {
      // Use direct fetch for CSV download
      const response = await fetch(`/api/optimizer/results/${runId}/export/csv`);
      
      if (!response.ok) {
        throw new Error('Failed to export CSV');
      }
      
      const csvContent = await response.text();
      const filename = `optimization_${runId}_${formatDateForFilename()}.csv`;
      downloadFile(csvContent, filename, 'text/csv');
      
      setSuccess(s => ({ ...s, csv: true }));
      setTimeout(() => setSuccess(s => ({ ...s, csv: false })), 2000);
    } catch (err) {
      setError(`CSV export failed: ${err.message}`);
    } finally {
      setLoading(l => ({ ...l, csv: false }));
    }
  };
  
  // Export to JSON
  const handleExportJSON = async () => {
    if (!runId || loading.json) return;
    
    setLoading(l => ({ ...l, json: true }));
    setError(null);
    
    try {
      const response = await optimizerApi.exportResults(runId);
      const jsonContent = JSON.stringify(response.data, null, 2);
      const filename = `optimization_${runId}_${formatDateForFilename()}.json`;
      downloadFile(jsonContent, filename, 'application/json');
      
      setSuccess(s => ({ ...s, json: true }));
      setTimeout(() => setSuccess(s => ({ ...s, json: false })), 2000);
    } catch (err) {
      setError(`JSON export failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(l => ({ ...l, json: false }));
    }
  };
  
  // Copy to clipboard
  const handleCopyJSON = async () => {
    if (!runId) return;
    
    try {
      const response = await optimizerApi.exportResults(runId);
      const jsonContent = JSON.stringify(response.data, null, 2);
      await navigator.clipboard.writeText(jsonContent);
      
      setSuccess(s => ({ ...s, json: true }));
      setTimeout(() => setSuccess(s => ({ ...s, json: false })), 2000);
    } catch (err) {
      setError(`Copy failed: ${err.message}`);
    }
  };
  
  return (
    <div className="flex items-center gap-2">
      {/* Error message */}
      {error && (
        <span className="text-red-400 text-sm mr-2">{error}</span>
      )}
      
      {/* CSV Export */}
      <button
        onClick={handleExportCSV}
        disabled={disabled || !runId || loading.csv}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
          transition-all
          ${success.csv 
            ? 'bg-green-600 text-white' 
            : 'bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white border border-gray-700'
          }
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
      >
        {loading.csv ? (
          <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
        ) : success.csv ? (
          <span>✓</span>
        ) : (
          <span>📊</span>
        )}
        <span>{success.csv ? 'Downloaded!' : 'Export CSV'}</span>
      </button>
      
      {/* JSON Export Dropdown */}
      <div className="relative group">
        <button
          disabled={disabled || !runId || loading.json}
          className={`
            flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
            transition-all
            ${success.json 
              ? 'bg-green-600 text-white' 
              : 'bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white border border-gray-700'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          {loading.json ? (
            <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
          ) : success.json ? (
            <span>✓</span>
          ) : (
            <span>📄</span>
          )}
          <span>{success.json ? 'Done!' : 'Export JSON'}</span>
          <span className="text-xs">▼</span>
        </button>
        
        {/* Dropdown menu */}
        <div className="absolute right-0 mt-1 w-40 bg-gray-800 border border-gray-700 rounded-lg shadow-xl
          opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
          <button
            onClick={handleExportJSON}
            className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 hover:text-white
              rounded-t-lg"
          >
            💾 Download file
          </button>
          <button
            onClick={handleCopyJSON}
            className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 hover:text-white
              rounded-b-lg border-t border-gray-700"
          >
            📋 Copy to clipboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExportButtons;
