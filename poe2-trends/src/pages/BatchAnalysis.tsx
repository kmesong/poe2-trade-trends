import React, { useState, useEffect, useRef } from 'react';
import { getSessionId, getBatchResults, saveBatchResults } from '../utils/storage';
import { Link } from 'react-router-dom';
import type { BatchResult } from '../types';
import toast from 'react-hot-toast';
import { ItemTree } from '../components/ItemTree';

export const BatchAnalysis: React.FC = () => {
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [results, setResults] = useState<BatchResult[]>(() => getBatchResults());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentBase, setCurrentBase] = useState<string | null>(null);
  const [totalBases, setTotalBases] = useState(0);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    saveBatchResults(results);
  }, [results]);

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
    abortControllerRef.current?.abort();
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
      const msg = 'Please select at least one item base type.';
      setError(msg);
      toast.error(msg);
      return;
    }

    setLoading(true);
    setError(null);
    setResults([]);
    setTotalBases(bases.length);
    setCurrentBase(null);
    
    abortControllerRef.current = new AbortController();

    try {
      for (let i = 0; i < bases.length; i++) {
        const base = bases[i];
        
        if (abortControllerRef.current?.signal.aborted) break;
        
        setCurrentBase(base);

        const response = await fetch('http://localhost:5000/analyze/batch-price', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-POESESSID': sessionId
          },
          body: JSON.stringify({ bases: [base] }),
          signal: abortControllerRef.current?.signal
        });

        if (!response.ok) {
          const data = await response.json();
          const errorMsg = data.error || `Analysis failed for ${base}`;
          
          // Check for specific error types
          if (errorMsg.includes('502') || errorMsg.includes('Bad Gateway')) {
            toast.error(`Server busy (502) for ${base} - retrying...`);
          } else if (errorMsg.includes('429') || errorMsg.includes('Rate limit')) {
            toast.error(`Rate limited - slowing down...`);
          } else {
            toast.error(errorMsg);
          }
          throw new Error(errorMsg);
        }

        const data = await response.json();
        if (data && data.length > 0) {
          setResults(prev => [...prev, data[0]]);
        }

        if (i < bases.length - 1) {
          if (abortControllerRef.current?.signal.aborted) break;
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }
      toast.success('Analysis complete!');
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('Analysis stopped by user');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
      setCurrentBase(null);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex h-screen bg-poe-bg text-gray-200 overflow-hidden">
      {/* Input Panel */}
      <div className="w-1/3 p-6 border-r border-poe-border flex flex-col bg-poe-card/50">
        <h2 className="text-xl font-serif text-poe-gold mb-4 font-bold tracking-wide">
          Batch Analysis
        </h2>
        
        <div className="flex-1 flex flex-col min-h-0">
          <label className="text-xs text-gray-400 uppercase font-bold mb-2">
            Select Item Bases
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

          {loading ? (
            <button
              onClick={handleStop}
              className="w-full py-3 rounded text-sm font-bold uppercase tracking-widest transition-all shadow-lg bg-gray-800 hover:bg-gray-700 text-red-400 border border-poe-border"
            >
              Stop Analysis
            </button>
          ) : (
            <button
              onClick={handleAnalyze}
              className="w-full py-3 rounded text-sm font-bold uppercase tracking-widest transition-all shadow-lg bg-gradient-to-r from-poe-red/80 to-poe-red hover:from-red-600 hover:to-red-500 text-white border border-red-900"
            >
              Analyze Bases
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
                {results.length} Results Found
              </div>
            </div>
          </div>

          {loading && (
            <div className="mb-8 p-4 bg-black/40 border border-poe-border/50 rounded-lg shadow-inner">
              <div className="flex justify-between items-end mb-3">
                <div className="flex flex-col">
                  <span className="text-[10px] text-gray-500 uppercase font-bold tracking-[0.2em] mb-1">Current Task</span>
                  <span className="text-sm text-poe-gold font-serif italic tracking-wide">
                    Analyzing {currentBase || 'Market'}...
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-gray-500 uppercase font-bold tracking-[0.2em] mb-1 block">Progress</span>
                  <span className="text-sm font-mono text-poe-highlight">
                    {results.length} <span className="text-gray-600">/</span> {totalBases}
                  </span>
                </div>
              </div>
              <div className="w-full h-1.5 bg-black/60 rounded-full overflow-hidden border border-poe-border/20 p-[1px]">
                <div 
                  className="h-full bg-gradient-to-r from-poe-gold/40 via-poe-gold to-poe-golddim rounded-full shadow-[0_0_12px_rgba(233,176,79,0.3)] transition-all duration-700 ease-out"
                  style={{ width: `${Math.min(100, (results.length / totalBases) * 100)}%` }}
                />
              </div>
            </div>
          )}

          {results.length === 0 && !loading && (
            <div className="text-center py-20 text-gray-600 italic">
              Select item bases on the left to analyze profit gaps.
            </div>
          )}

          {results.length > 0 && (
            <div className="border border-poe-border rounded overflow-hidden shadow-2xl">
              <table className="w-full text-left text-sm">
                <thead className="bg-black/60 text-poe-golddim uppercase text-xs tracking-wider font-bold">
                  <tr>
                    <th className="p-4 border-b border-poe-border">Base Type</th>
                    <th className="p-4 border-b border-poe-border text-right">Normal (Ex)</th>
                    <th className="p-4 border-b border-poe-border text-right">Magic (Ex)</th>
                    <th className="p-4 border-b border-poe-border text-right">Gap</th>
                    <th className="p-4 border-b border-poe-border text-right">ROI</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-poe-border/30 bg-poe-card/30">
                  {results.map((row, idx) => {
                    const roi = row.normal_avg_chaos > 0 
                      ? ((row.gap_chaos / row.normal_avg_chaos) * 100) 
                      : 0;
                    
                    const isPositive = row.gap_chaos > 0;
                    const isHighRoi = roi > 50;
                    
                    // Build trade URL for this base type
                    // PoE trade: https://www.pathofexile.com/trade2/search/poe2/LEAGUE/SEARCH_ID
                    const searchId = row.search_id || '';
                    const magicSearchId = row.magic_search_id || '';
                    const normalUrl = searchId
                        ? `https://www.pathofexile.com/trade2/search/poe2/Fate%20of%20the%20Vaal/${searchId}`
                        : `https://www.pathofexile.com/trade2/search/poe2/Fate%20of%20the%20Vaal`;
                    const magicUrl = magicSearchId
                        ? `https://www.pathofexile.com/trade2/search/poe2/Fate%20of%20the%20Vaal/${magicSearchId}`
                        : normalUrl;

                    return (
                      <React.Fragment key={idx}>
                        <tr
                          className="hover:bg-white/5 transition-colors cursor-pointer"
                          onClick={() => toggleRow(idx)}
                        >
                          <td className="p-4 font-medium text-poe-highlight">
                            <span className="mr-2">{expandedRows.has(idx) ? '▼' : '▶'}</span>
                            {row.base_type}
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
                              {row.normal_avg_chaos.toFixed(2)} Ex
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
                              {row.magic_avg_chaos.toFixed(2)} Ex
                            </a>
                          </td>
                          <td className={`p-4 text-right font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                            {row.gap_chaos > 0 ? '+' : ''}{row.gap_chaos.toFixed(2)} Ex
                          </td>
                          <td className={`p-4 text-right font-mono ${isHighRoi ? 'text-poe-gold' : 'text-gray-500'}`}>
                            {roi.toFixed(0)}%
                          </td>
                        </tr>
                        {expandedRows.has(idx) && (
                          <tr className="bg-black/30">
                            <td colSpan={5} className="p-4">
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
  );
};
