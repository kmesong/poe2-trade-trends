import React, { useState } from 'react';
import { getSessionId } from '../utils/storage';
import { Link } from 'react-router-dom';

interface BatchResult {
  base_type: string;
  normal_avg_chaos: number;
  magic_avg_chaos: number;
  gap_chaos: number;
}

export const BatchAnalysis: React.FC = () => {
  const [input, setInput] = useState('');
  const [results, setResults] = useState<BatchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    const sessionId = getSessionId();
    if (!sessionId) {
      setError('Missing POESESSID. Please configure it in Settings.');
      return;
    }

    const bases = input.split('\n').map(s => s.trim()).filter(Boolean);
    if (bases.length === 0) {
      setError('Please enter at least one item base type.');
      return;
    }

    setLoading(true);
    setError(null);
    setResults([]);

    try {
      for (const base of bases) {
        const response = await fetch('http://localhost:5000/analyze/batch-price', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-POESESSID': sessionId
          },
          body: JSON.stringify({ bases: [base] }),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || `Analysis failed for ${base}`);
        }

        const data = await response.json();
        if (data && data.length > 0) {
          setResults(prev => [...prev, data[0]]);
        }

        if (bases.indexOf(base) < bases.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
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
            Item Bases (One per line)
          </label>
          <textarea
            className="flex-1 bg-black/40 border border-poe-border rounded p-3 text-sm text-poe-highlight focus:border-poe-gold focus:outline-none resize-none font-mono mb-4 custom-scrollbar"
            placeholder="Expert Laced Boots&#10;Solaris Circlet&#10;Primordial Staff"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          
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

          <button
            onClick={handleAnalyze}
            disabled={loading}
            className={`w-full py-3 rounded text-sm font-bold uppercase tracking-widest transition-all shadow-lg
              ${loading 
                ? 'bg-gray-800 text-gray-500 cursor-not-allowed' 
                : 'bg-gradient-to-r from-poe-red/80 to-poe-red hover:from-red-600 hover:to-red-500 text-white border border-red-900'
              }`}
          >
            {loading ? 'Analyzing Market...' : 'Analyze Bases'}
          </button>
        </div>
      </div>

      {/* Results Panel */}
      <div className="flex-1 p-6 overflow-y-auto custom-scrollbar bg-black/20">
        <div className="max-w-5xl mx-auto">
          <div className="flex justify-between items-center mb-6 border-b border-poe-border pb-2">
            <h3 className="text-lg text-poe-highlight font-serif">Market Gap Analysis</h3>
            <div className="flex items-center gap-4">
              {loading && (
                <div className="text-xs text-poe-gold animate-pulse font-bold uppercase tracking-widest">
                  Processing...
                </div>
              )}
              <div className="text-xs text-gray-500">
                {results.length} Results Found
              </div>
            </div>
          </div>

          {results.length === 0 && !loading && (
            <div className="text-center py-20 text-gray-600 italic">
              Enter base types on the left to analyze profit gaps.
            </div>
          )}

          {loading && results.length === 0 && (
             <div className="text-center py-20 text-poe-gold animate-pulse">
               Fetching live trade data... this may take a moment.
             </div>
          )}

          {results.length > 0 && (
            <div className="border border-poe-border rounded overflow-hidden shadow-2xl">
              <table className="w-full text-left text-sm">
                <thead className="bg-black/60 text-poe-golddim uppercase text-xs tracking-wider font-bold">
                  <tr>
                    <th className="p-4 border-b border-poe-border">Base Type</th>
                    <th className="p-4 border-b border-poe-border text-right">Normal (c)</th>
                    <th className="p-4 border-b border-poe-border text-right">Magic (c)</th>
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

                    return (
                      <tr key={idx} className="hover:bg-white/5 transition-colors">
                        <td className="p-4 font-medium text-poe-highlight">{row.base_type}</td>
                        <td className="p-4 text-right text-gray-400">{row.normal_avg_chaos.toFixed(1)}</td>
                        <td className="p-4 text-right text-blue-300">{row.magic_avg_chaos.toFixed(1)}</td>
                        <td className={`p-4 text-right font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                          {row.gap_chaos > 0 ? '+' : ''}{row.gap_chaos.toFixed(1)}
                        </td>
                        <td className={`p-4 text-right font-mono ${isHighRoi ? 'text-poe-gold' : 'text-gray-500'}`}>
                          {roi.toFixed(0)}%
                        </td>
                      </tr>
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
