import React, { useState, useEffect } from 'react';
import { getSessionId } from '../utils/storage';
import { Link } from 'react-router-dom';
import type { BatchResult, JobResponse } from '../types';
import { ErrorBoundary } from '../components/ErrorBoundary';
import toast from 'react-hot-toast';
import { ItemTree } from '../components/ItemTree';

export const BatchAnalysis: React.FC = () => {
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  // allResults stores the full list of latest analyses from the DB
  const [allResults, setAllResults] = useState<BatchResult[]>([]);
  // displayedResults is what the user sees (filtered by selection)
  const [displayedResults, setDisplayedResults] = useState<BatchResult[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [isAnalysing, setIsAnalysing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentBase, setCurrentBase] = useState<string | null>(null);
  const [totalBases, setTotalBases] = useState(0);
  const [processedCount, setProcessedCount] = useState(0);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  // Sorting state
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' }>({
    key: 'gap_ex',
    direction: 'desc'
  });

  const handleSort = (key: string) => {
    setSortConfig(current => ({
      key,
      direction: current.key === key && current.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  const sortedResults = React.useMemo(() => {
    const sorted = [...displayedResults];
    sorted.sort((a, b) => {
      let aValue: number | string = 0;
      let bValue: number | string = 0;

      switch (sortConfig.key) {
        case 'base_type':
          aValue = a.base_type || '';
          bValue = b.base_type || '';
          break;
        case 'normal_avg_ex':
          aValue = a.normal_avg_ex || 0;
          bValue = b.normal_avg_ex || 0;
          break;
        case 'crafting_avg_ex':
          aValue = a.crafting_avg_ex || 0;
          bValue = b.crafting_avg_ex || 0;
          break;
        case 'magic_avg_ex':
          aValue = a.magic_avg_ex || 0;
          bValue = b.magic_avg_ex || 0;
          break;
        case 'gap_ex':
          aValue = a.gap_ex || 0;
          bValue = b.gap_ex || 0;
          break;
        case 'roi':
          const aNormal = a.normal_avg_ex || 0;
          const aGap = a.gap_ex || 0;
          aValue = aNormal > 0 ? (aGap / aNormal) : 0;
          
          const bNormal = b.normal_avg_ex || 0;
          const bGap = b.gap_ex || 0;
          bValue = bNormal > 0 ? (bGap / bNormal) : 0;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [displayedResults, sortConfig]);
  
  // Initial load of latest data
  useEffect(() => {
    loadLatestAnalyses();
  }, []);

  // Filter displayed results whenever selection or allResults changes
  useEffect(() => {
    if (selectedItems.length === 0) {
      // If nothing selected, show everything (or could show nothing, but everything is better for "overview")
      setDisplayedResults(allResults);
    } else {
      // Filter results to only show selected base types
      const filtered = allResults.filter(r => selectedItems.includes(r.base_type));
      setDisplayedResults(filtered);
    }
  }, [selectedItems, allResults]);

  // Polling for active job
  useEffect(() => {
    if (!activeJobId) return;

    const pollJob = async () => {
      try {
        const response = await fetch(`/api/jobs/${activeJobId}`);
        if (!response.ok) {
           if (response.status === 404) {
             throw new Error("Job not found");
           }
           return;
        }
        
        const data: JobResponse = await response.json();
        
        setProcessedCount(data.progress);
        setTotalBases(data.total);
        if (data.current_item) setCurrentBase(data.current_item);
        
        if (data.results && data.results.length > 0) {
           setAllResults(prev => {
             const updated = [...prev];
             
              for (const newResult of data.results) {
                if ('gap_ex' in newResult) {
                  const index = updated.findIndex(r => r.base_type === newResult.base_type);
                  if (index >= 0) {
                    updated[index] = newResult;
                  } else {
                    updated.unshift(newResult);
                  }
                }
              }
             return updated;
           });
        }

        if (data.status === 'completed') {
          setIsAnalysing(false);
          setActiveJobId(null);
          toast.success('Analysis complete!');
        } else if (data.status === 'failed') {
          setIsAnalysing(false);
          setActiveJobId(null);
          setError(data.error || 'Job failed');
          toast.error(`Job failed: ${data.error}`);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    };

    const intervalId = setInterval(pollJob, 2000);
    pollJob();

    return () => clearInterval(intervalId);
  }, [activeJobId]);

  const loadLatestAnalyses = async () => {
    try {
      setLoading(true);
      // Fetch latest only, high limit
      // Note: We need to cast the response to BatchResult[] because the DB shape matches but isn't strictly typed the same in frontend yet
      const response = await fetch('/api/db/analyses?latest_only=true&limit=500');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch history (${response.status})`);
      }
      
      const text = await response.text();
      try {
        const data = JSON.parse(text);
        if (data.success) {
          setAllResults(data.data);
        } else {
          console.error('API returned success: false', data);
        }
      } catch (e) {
        console.error('Failed to parse API response:', e, text.substring(0, 100));
        throw new Error('Invalid API response format');
      }
    } catch (err) {
      console.error('Failed to load history', err);
      toast.error('Failed to load current data');
    } finally {
      setLoading(false);
    }
  };

  const toggleRow = (idx: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(idx)) {
      newExpanded.delete(idx);
    } else {
      newExpanded.add(idx);
    }
    setExpandedRows(newExpanded);
  };

  const addExclusion = async (modifierName: string, tier: string) => {
    try {
      const response = await fetch('/api/db/exclusions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mod_name_pattern: `%${modifierName}%`,
          mod_tier: tier,
          reason: `Excluded from Batch Analysis`
        })
      });
      if (response.ok) {
        toast.success(`Excluded "${modifierName}" (${tier})`);
      } else {
        toast.error('Failed to add exclusion');
      }
    } catch {
      toast.error('Failed to add exclusion');
    }
  };

  const handleStop = () => {
    // Currently we just stop polling on frontend, but ideally we should cancel the job
    // For now, just reset frontend state
    setIsAnalysing(false);
    setActiveJobId(null);
    toast('Analysis monitoring stopped (Background job may continue)', { icon: '⚠️' });
  };

  const handleAnalyze = async () => {
    const sessionId = getSessionId();
    if (!sessionId) {
      const msg = 'Missing POESESSID. Please configure it in Settings.';
      setError(msg);
      toast.error(msg);
      return;
    }

    const bases = selectedItems;
    if (bases.length === 0) {
      const msg = 'Please select at least one item base type to analyze/refresh.';
      setError(msg);
      toast.error(msg);
      return;
    }

    setIsAnalysing(true);
    setError(null);
    setTotalBases(bases.length);
    setProcessedCount(0);
    setCurrentBase('Initializing...');
    
    try {
      const response = await fetch('/api/jobs/batch-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-POESESSID': sessionId
        },
        body: JSON.stringify({ bases })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to start analysis job');
      }

      const data = await response.json();
      if (data.success && data.job_id) {
        setActiveJobId(data.job_id);
        toast.success('Analysis job started');
      } else {
        throw new Error('Invalid server response');
      }

    } catch (err: unknown) {
      setIsAnalysing(false);
      if (err instanceof Error) {
        setError(err.message);
        toast.error(err.message);
      } else {
        setError('An unexpected error occurred');
        toast.error('An unexpected error occurred');
      }
    }
  };

  return (
    <ErrorBoundary>
      <div className="flex h-screen bg-poe-bg text-gray-200 overflow-hidden">
      {/* Input Panel */}
      <div className="w-1/3 p-6 border-r border-poe-border flex flex-col bg-poe-card/50">
        <h2 className="text-xl font-serif text-poe-gold mb-4 font-bold tracking-wide">
          Batch Analysis
        </h2>
        
        <div className="flex-1 flex flex-col min-h-0">
          <label className="text-xs text-gray-400 uppercase font-bold mb-2">
            Select Item Bases (Filter / Refresh)
          </label>
          <div className="flex-1 min-h-0 mb-4 overflow-hidden">
            <ItemTree
              onSelectionChange={(items) => {
                setSelectedItems(items);
                if (items.length > 0) {
                  setError(null);
                }
              }}
            />
          </div>
          
          {error && (
            <div className="mb-4 p-3 bg-red-950/40 border border-red-900/50 rounded text-red-400 text-xs">
              {error} 
              {error.includes('Settings') && (
                <Link to="/settings" className="underline ml-1 text-red-300 hover:text-white">
                  Go to Settings
                </Link>
              )}
            </div>
          )}

          {isAnalysing ? (
            <button
              onClick={handleStop}
              className="w-full py-3 rounded text-sm font-bold uppercase tracking-widest transition-all shadow-lg bg-gray-800 hover:bg-gray-700 text-red-400 border border-poe-border"
            >
              Stop Analysis
            </button>
          ) : (
            <button
              onClick={handleAnalyze}
              disabled={selectedItems.length === 0}
              className={`w-full py-3 rounded text-sm font-bold uppercase tracking-widest transition-all shadow-lg border ${
                selectedItems.length === 0 
                  ? 'bg-gray-800 text-gray-500 border-gray-700 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-poe-red/80 to-poe-red hover:from-red-600 hover:to-red-500 text-white border-red-900'
              }`}
            >
              {selectedItems.length > 0 ? `Analyze Selected (${selectedItems.length})` : 'Select items to analyze'}
            </button>
          )}
        </div>
      </div>

      {/* Results Panel */}
      <div className="flex-1 p-6 overflow-y-auto custom-scrollbar bg-black/20">
        <div className="max-w-5xl mx-auto">
          <div className="flex justify-between items-center mb-6 border-b border-poe-border pb-2">
            <h3 className="text-lg text-poe-highlight font-serif">Market Gap Analysis</h3>
            <div className="flex items-center gap-4">
              <div className="text-xs text-gray-500">
                {displayedResults.length} Results Found
                {selectedItems.length > 0 && ` (Filtered from ${allResults.length})`}
              </div>
            </div>
          </div>

          {isAnalysing && (
            <div className="mb-8 p-4 bg-black/40 border border-poe-border/50 rounded-lg shadow-inner">
              <div className="flex justify-between items-end mb-3">
                <div className="flex flex-col">
                  <span className="text-[10px] text-gray-500 uppercase font-bold tracking-[0.2em] mb-1">Current Task</span>
                  <span className="text-sm font-serif italic tracking-wide text-poe-gold">
                    Analyzing {currentBase || 'Market'}...
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-gray-500 uppercase font-bold tracking-[0.2em] mb-1 block">Progress</span>
                  <span className="text-sm font-mono text-poe-highlight">
                    {processedCount} <span className="text-gray-600">/</span> {totalBases}
                  </span>
                </div>
              </div>
              <div className="w-full h-1.5 bg-black/60 rounded-full overflow-hidden border border-poe-border/20 p-[1px]">
                <div 
                  className="h-full rounded-full shadow-[0_0_12px_rgba(233,176,79,0.3)] transition-all duration-700 ease-out bg-gradient-to-r from-poe-gold/40 via-poe-gold to-poe-golddim"
                  style={{ width: `${Math.min(100, (processedCount / totalBases) * 100)}%` }}
                />
              </div>
            </div>
          )}

          {displayedResults.length === 0 && !loading && !isAnalysing && (
            <div className="text-center py-20 text-gray-600 italic">
              {selectedItems.length > 0 
                ? "No previous data for selected items. Click 'Analyze Selected' to fetch data." 
                : "Select items on the left to filter results."}
            </div>
          )}

          {displayedResults.length > 0 && (
            <div className="border border-poe-border rounded overflow-hidden shadow-2xl">
              <table className="w-full text-left text-sm">
                <thead className="bg-black/60 text-poe-golddim uppercase text-xs tracking-wider font-bold">
                  <tr>
                    <th 
                      className="p-4 border-b border-poe-border cursor-pointer hover:text-poe-highlight transition-colors select-none"
                      onClick={() => handleSort('base_type')}
                    >
                      <div className="flex items-center gap-1">
                        Base Type
                        {sortConfig.key === 'base_type' && (
                          <span className="text-poe-gold">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </div>
                    </th>
                    <th 
                      className="p-4 border-b border-poe-border text-right cursor-pointer hover:text-poe-highlight transition-colors select-none"
                      onClick={() => handleSort('normal_avg_ex')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        Normal (Ex)
                        {sortConfig.key === 'normal_avg_ex' && (
                          <span className="text-poe-gold">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </div>
                    </th>
                    <th 
                      className="p-4 border-b border-poe-border text-right cursor-pointer hover:text-poe-highlight transition-colors select-none"
                      title="ilvl 82+, Min 2 Rune Sockets"
                      onClick={() => handleSort('crafting_avg_ex')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        Crafting (Ex)
                        {sortConfig.key === 'crafting_avg_ex' && (
                          <span className="text-poe-gold">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </div>
                    </th>
                    <th 
                      className="p-4 border-b border-poe-border text-right cursor-pointer hover:text-poe-highlight transition-colors select-none"
                      onClick={() => handleSort('magic_avg_ex')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        Magic (Ex)
                        {sortConfig.key === 'magic_avg_ex' && (
                          <span className="text-poe-gold">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </div>
                    </th>
                    <th 
                      className="p-4 border-b border-poe-border text-right cursor-pointer hover:text-poe-highlight transition-colors select-none"
                      onClick={() => handleSort('gap_ex')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        Gap
                        {sortConfig.key === 'gap_ex' && (
                          <span className="text-poe-gold">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </div>
                    </th>
                    <th 
                      className="p-4 border-b border-poe-border text-right cursor-pointer hover:text-poe-highlight transition-colors select-none"
                      onClick={() => handleSort('roi')}
                    >
                      <div className="flex items-center justify-end gap-1">
                        ROI
                        {sortConfig.key === 'roi' && (
                          <span className="text-poe-gold">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-poe-border/30 bg-poe-card/30">
                  {sortedResults.map((row, idx) => {
                    const normalPrice = row.normal_avg_ex || 0;
                    const craftingPrice = row.crafting_avg_ex || 0;
                    const magicPrice = row.magic_avg_ex || 0;
                    const gap = row.gap_ex || 0;
                    
                    const roi = normalPrice > 0 
                      ? ((gap / normalPrice) * 100) 
                      : 0;
                    
                    const isPositive = gap > 0;
                    const isHighRoi = roi > 50;
                    
                    // Build trade URL for this base type
                    // PoE trade: https://www.pathofexile.com/trade2/search/poe2/LEAGUE/SEARCH_ID
                    const searchId = row.search_id || '';
                    const magicSearchId = row.magic_search_id || '';
                    const craftingSearchId = row.crafting_search_id || '';
                    const normalUrl = searchId
                        ? `https://www.pathofexile.com/trade2/search/poe2/Fate%20of%20the%20Vaal/${searchId}`
                        : `https://www.pathofexile.com/trade2/search/poe2/Fate%20of%20the%20Vaal`;
                    const magicUrl = magicSearchId
                        ? `https://www.pathofexile.com/trade2/search/poe2/Fate%20of%20the%20Vaal/${magicSearchId}`
                        : normalUrl;
                    const craftingUrl = craftingSearchId
                        ? `https://www.pathofexile.com/trade2/search/poe2/Fate%20of%20the%20Vaal/${craftingSearchId}`
                        : normalUrl;

                    return (
                      <React.Fragment key={idx}>
                        <tr
                          className="hover:bg-white/5 transition-colors cursor-pointer"
                          onClick={() => toggleRow(idx)}
                        >
                          <td className="p-4 font-medium text-poe-highlight">
                            <span className="mr-2">{expandedRows.has(idx) ? '▼' : '▶'}</span>
                            {row.base_type || 'Unknown Base'}
                          </td>
                          <td className="p-4 text-right text-gray-400">
                            <a
                              href={normalUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hover:text-poe-gold hover:underline cursor-pointer"
                              title="View Normal items on PoE Trade"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {normalPrice.toFixed(2)} Ex
                            </a>
                          </td>
                          <td className="p-4 text-right text-gray-400" title="ilvl 82+, Min 2 Rune Sockets">
                            <a
                              href={craftingUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hover:text-poe-gold hover:underline cursor-pointer"
                              title="View Crafting items on PoE Trade"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {craftingPrice.toFixed(2)} Ex
                            </a>
                          </td>
                          <td className="p-4 text-right text-blue-300">
                            <a
                              href={magicUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hover:text-poe-gold hover:underline cursor-pointer"
                              title="View Magic items on PoE Trade"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {magicPrice.toFixed(2)} Ex
                            </a>
                          </td>
                          <td className={`p-4 text-right font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                            {gap > 0 ? '+' : ''}{gap.toFixed(2)} Ex
                          </td>
                          <td className={`p-4 text-right font-mono ${isHighRoi ? 'text-poe-gold' : 'text-gray-500'}`}>
                            {roi.toFixed(0)}%
                          </td>
                        </tr>
                        {expandedRows.has(idx) && (
                          <tr className="bg-black/30">
                            <td colSpan={6} className="p-4">
                              <div className="grid grid-cols-1 gap-6">
                                {/* Magic Modifiers */}
                                <div>
                                  <h4 className="text-poe-gold text-xs font-bold uppercase mb-2">Magic Modifiers (T1)</h4>
                                  <div className="max-h-48 overflow-y-auto custom-scrollbar">
                                          {row.magic_modifiers && row.magic_modifiers.length > 0 ? (
                                      <div className="space-y-1">
                                        {row.magic_modifiers.map((mod, mIdx) => (
                                          <div key={mIdx} className="flex items-center justify-between text-xs py-1 px-2 bg-poe-card/50 rounded">
                                            <span className="text-gray-300">
                                              <span className="text-poe-golddim mr-1">[{mod.tier}]</span>
                                              {mod.display_text || mod.name}
                                            </span>
                                            <button
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                addExclusion(mod.name, mod.tier);
                                              }}
                                              className="text-red-400 hover:text-red-300 ml-2 px-2 py-0.5 rounded hover:bg-red-900/30"
                                              title="Exclude this modifier"
                                            >
                                              ✕
                                            </button>
                                          </div>
                                        ))}
                                      </div>
                                    ) : (
                                      <div className="text-gray-500 text-xs italic">No modifiers found</div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      </div>
    </ErrorBoundary>
  );
};
