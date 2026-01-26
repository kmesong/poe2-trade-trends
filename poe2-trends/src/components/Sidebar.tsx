import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import type { Data } from '../types';

interface Props {
  data: Data | null;
  activeType: string;
  onSelect: (type: string) => void;
  onDataRefresh?: (newData: any) => void;
}

interface SavedSearch {
  filename: string;
  name: string;
  date: string;
  timestamp: number;
}

export const Sidebar: React.FC<Props> = ({ data, activeType, onSelect, onDataRefresh }) => {
  const [queryInput, setQueryInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [saveName, setSaveName] = useState('');
  const [showSaveInput, setShowSaveInput] = useState(false);

  const types = data ? Object.keys(data).sort() : [];

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch('http://localhost:5000/history');
      if (res.ok) {
        setSavedSearches(await res.json());
      }
    } catch (e) {
      console.error("Failed to load history", e);
    }
  };

  const handleAnalyze = async () => {
    if (!queryInput.trim()) return;
    
    setLoading(true);
    setError(null);
    setShowSaveInput(false);
    
    try {
      // Validate JSON locally if possible
      try { JSON.parse(queryInput); } catch (e) {}

      const response = await fetch('http://localhost:5000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_text: queryInput }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Analysis failed');
      }

      const newData = await response.json();
      if (onDataRefresh) {
        onDataRefresh(newData);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!saveName.trim() || !data) return;
    
    try {
      const response = await fetch('http://localhost:5000/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: saveName,
          query: queryInput, // Save the query too if we have it
          results: data
        }),
      });
      
      if (response.ok) {
        setSaveName('');
        setShowSaveInput(false);
        fetchHistory(); // Refresh list
      } else {
        alert('Failed to save');
      }
    } catch (e) {
      console.error(e);
      alert('Error saving');
    }
  };

  const loadHistoryItem = async (filename: string) => {
    try {
      const res = await fetch(`http://localhost:5000/history/${filename}`);
      if (res.ok) {
        const historyData = await res.json();
        if (onDataRefresh) onDataRefresh(historyData);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="w-64 bg-poe-card border-r border-poe-border h-screen flex flex-col fixed left-0 top-0">
      <div className="p-6 border-b border-poe-border bg-gradient-to-b from-poe-card to-black shrink-0">
        <h1 className="font-serif text-2xl text-poe-gold font-bold tracking-wider">
          POE2 <span className="text-poe-red">META</span>
        </h1>
        <p className="text-xs text-gray-500 mt-1 uppercase tracking-widest">Mirror Tier Stats</p>
      </div>
      
      <div className="p-4 border-b border-poe-border bg-black/20 shrink-0">
        <label className="text-[10px] text-gray-400 uppercase font-bold mb-2 block">
          Paste Trade Query JSON
        </label>
        <textarea 
          className="w-full h-16 bg-black/40 border border-poe-border/30 rounded p-2 text-xs text-gray-300 focus:border-poe-gold focus:outline-none resize-none mb-2"
          placeholder='{"query": { ... }}'
          value={queryInput}
          onChange={(e) => setQueryInput(e.target.value)}
        />
        <button 
          onClick={handleAnalyze}
          disabled={loading || !queryInput}
          className={`w-full py-1.5 rounded text-xs font-bold uppercase tracking-wide transition-all mb-2
            ${loading 
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed' 
              : 'bg-poe-red/20 text-poe-red hover:bg-poe-red hover:text-white border border-poe-red/30'
            }`}
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
        
        {/* Save Button */}
        {data && !showSaveInput && (
            <button 
                onClick={() => setShowSaveInput(true)}
                className="w-full py-1.5 rounded text-xs font-bold uppercase tracking-wide bg-blue-900/30 text-blue-400 hover:bg-blue-800/50 border border-blue-800/50"
            >
                Save Results
            </button>
        )}

        {showSaveInput && (
            <div className="mt-2 animate-in fade-in slide-in-from-top-1">
                <input 
                    type="text" 
                    placeholder="Enter name..." 
                    className="w-full bg-black/40 border border-poe-border/30 rounded p-1.5 text-xs text-white mb-2 focus:border-blue-500 outline-none"
                    value={saveName}
                    onChange={e => setSaveName(e.target.value)}
                />
                <div className="flex gap-2">
                    <button 
                        onClick={handleSave}
                        className="flex-1 bg-blue-600 text-white text-[10px] py-1 rounded hover:bg-blue-500"
                    >
                        Confirm
                    </button>
                    <button 
                        onClick={() => setShowSaveInput(false)}
                        className="flex-1 bg-gray-700 text-gray-300 text-[10px] py-1 rounded hover:bg-gray-600"
                    >
                        Cancel
                    </button>
                </div>
            </div>
        )}

        {error && (
          <p className="text-red-500 text-[10px] mt-2 leading-tight bg-red-950/30 p-1 rounded border border-red-900/50">
            {error}
          </p>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {/* Saved Searches List */}
        {savedSearches.length > 0 && (
            <div className="border-b border-poe-border/30 bg-black/10">
                <h3 className="px-4 py-2 text-[10px] uppercase font-bold text-gray-500 tracking-wider">History</h3>
                <div className="max-h-40 overflow-y-auto custom-scrollbar">
                    {savedSearches.map((item) => (
                        <button
                            key={item.filename}
                            onClick={() => loadHistoryItem(item.filename)}
                            className="w-full text-left px-4 py-2 hover:bg-white/5 group border-l-2 border-transparent hover:border-gray-600 transition-all"
                        >
                            <div className="text-xs text-gray-300 font-medium truncate group-hover:text-white">
                                {item.name}
                            </div>
                            <div className="text-[10px] text-gray-600 group-hover:text-gray-500">
                                {item.date}
                            </div>
                        </button>
                    ))}
                </div>
            </div>
        )}

        <div className="py-4">
          {types.length === 0 ? (
             <p className="text-gray-500 text-xs px-6">No data loaded.</p>
          ) : (
              types.map(type => (
                <button
                  key={type}
                  onClick={() => onSelect(type)}
                  className={`w-full text-left px-6 py-3 text-sm transition-all relative
                    ${activeType === type 
                      ? 'text-poe-highlight bg-white/5 border-l-2 border-poe-gold' 
                      : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border-l-2 border-transparent'
                    }`}
                >
                  {type}
                </button>
              ))
          )}
        </div>
      </div>
      
      <div className="p-4 border-t border-poe-border text-xs text-gray-600 text-center flex flex-col gap-2 shrink-0 bg-poe-card">
        <Link 
          to="/tablet-modifiers" 
          className="text-poe-gold hover:text-poe-highlight transition-colors underline"
        >
          📜 Tablet Crafting Guide
        </Link>
        <span>Data from Trade Site</span>
      </div>
    </div>
  );
};
