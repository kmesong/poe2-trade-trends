import React, { useState, useEffect, useCallback } from 'react';
import { ItemTree } from '../components/ItemTree';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { startDistributionAnalysis, getAnalysisStatus, getDistributionResults } from '../services/analysis';
import type { Bucket as ApiBucket } from '../types';
import toast from 'react-hot-toast';

interface AnalysisResult {
  buckets: Bucket[];
  influence: InfluenceMetric[];
}

interface Bucket {
  range: string;
  count: number;
  avgPrice: number;
}

interface InfluenceMetric {
  attribute: string;
  diff: number; // Top 30% freq - Bottom 30% freq
  topFreq: number;
  bottomFreq: number;
}

export const ItemAnalysis: React.FC = () => {
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const processResults = useCallback((apiBuckets: ApiBucket[]) => {
    const sortedBuckets = [...apiBuckets].sort((a, b) => a.min_price - b.min_price);

    const buckets: Bucket[] = sortedBuckets.map(b => ({
      range: b.price_range,
      count: b.count,
      avgPrice: b.avg_price
    }));

    // Influence Calculation
    // Top 2 (expensive) vs Bottom 2 (cheap) for sharper contrast
    const topBuckets = sortedBuckets.slice(-2);
    const bottomBuckets = sortedBuckets.slice(0, 2);

    const getStats = (bucketList: ApiBucket[]) => {
      const total = bucketList.reduce((sum, b) => sum + b.count, 0);
      const attrs: Record<string, number> = {};
      bucketList.forEach(b => {
        Object.entries(b.attributes).forEach(([k, v]) => {
          attrs[k] = (attrs[k] || 0) + v;
        });
      });
      return { total, attrs };
    };

    const topStats = getStats(topBuckets);
    const bottomStats = getStats(bottomBuckets);

    const allKeys = new Set([...Object.keys(topStats.attrs), ...Object.keys(bottomStats.attrs)]);
    const influence: InfluenceMetric[] = [];

    allKeys.forEach(attr => {
      const topFreq = topStats.total > 0 ? (topStats.attrs[attr] || 0) / topStats.total : 0;
      const bottomFreq = bottomStats.total > 0 ? (bottomStats.attrs[attr] || 0) / bottomStats.total : 0;
      const diff = topFreq - bottomFreq;

    if (Math.abs(diff) > 0.05) {
              influence.push({
                attribute: attr,
                diff: Math.round(diff * 100),
                topFreq: Math.round(topFreq * 100),
                bottomFreq: Math.round(bottomFreq * 100)
              });
            }
    });

    influence.sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff));

    setResult({ buckets, influence });
    setAnalyzing(false);
  }, []);

  const fetchResults = useCallback(async () => {
    try {
      // Analyze the first selected item
      const itemToAnalyze = selectedItems[0];
      if (!itemToAnalyze) return;

      const results = await getDistributionResults(itemToAnalyze);
      if (results && results.length > 0) {
        processResults(results[0].buckets);
      } else {
        toast.error('No results found');
        setAnalyzing(false);
      }
    } catch (error) {
      console.error('Fetch results error:', error);
      toast.error('Failed to fetch analysis results');
      setAnalyzing(false);
    }
  }, [selectedItems, processResults]);

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval>;

    if (jobId) {
      intervalId = setInterval(async () => {
        try {
          const status = await getAnalysisStatus(jobId);
          
          if (status.status === 'completed') {
            clearInterval(intervalId);
            setJobId(null);
            // Fetch the results
            fetchResults();
          } else if (status.status === 'failed') {
            clearInterval(intervalId);
            setJobId(null);
            setAnalyzing(false);
            toast.error(status.error || 'Analysis failed');
          }
        } catch (error) {
          console.error('Polling error:', error);
          // Keep polling on error? Or stop?
          // For now, continue polling
        }
      }, 2000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [jobId, fetchResults]);

  const handleAnalyze = async () => {
    if (selectedItems.length === 0) return;
    
    setAnalyzing(true);
    setResult(null);

    try {
      const itemToAnalyze = selectedItems[0];
      const id = await startDistributionAnalysis(itemToAnalyze);
      setJobId(id);
      toast.success(`Analysis started for ${itemToAnalyze}`);
    } catch (error) {
      console.error(error);
      toast.error(error instanceof Error ? error.message : 'Failed to start analysis');
      setAnalyzing(false);
    }
  };

  return (
    <div className="p-6 h-screen flex flex-col overflow-hidden">
      <h1 className="text-2xl font-bold text-poe-gold mb-6 font-serif">Deep Item Analysis</h1>
      
      <div className="flex gap-6 flex-1 min-h-0">
        {/* Left Panel: Selection */}
        <div className="w-1/3 flex flex-col bg-poe-card border border-poe-border rounded-lg p-4">
          <h2 className="text-lg font-semibold text-poe-highlight mb-4">Select Items to Analyze</h2>
          <div className="flex-1 overflow-hidden">
             <ItemTree onSelectionChange={setSelectedItems} />
          </div>
          <div className="mt-4 pt-4 border-t border-poe-border">
            <button
              onClick={handleAnalyze}
              disabled={selectedItems.length === 0 || analyzing}
              className={`w-full py-3 px-4 rounded font-bold text-black transition-all ${
                selectedItems.length === 0 || analyzing
                  ? 'bg-gray-600 cursor-not-allowed opacity-50'
                  : 'bg-poe-gold hover:bg-poe-highlight shadow-lg hover:shadow-poe-gold/20'
              }`}
            >
              {analyzing ? 'Analyzing Market...' : `Analyze ${selectedItems.length} Items`}
            </button>
          </div>
        </div>

        {/* Right Panel: Results */}
        <div className="w-2/3 flex flex-col gap-6 overflow-y-auto pr-2">
          {/* Charts Section */}
          <div className="bg-poe-card border border-poe-border rounded-lg p-6">
            <h3 className="text-poe-golddim font-bold mb-4 flex items-center gap-2">
              <span>📊</span> Price Distribution
            </h3>
            
            {!result ? (
               <div className="h-64 flex items-center justify-center text-gray-500 italic border border-dashed border-gray-700 rounded">
                 {analyzing ? (
                   <div className="flex flex-col items-center gap-2">
                     <div className="w-8 h-8 border-2 border-poe-gold border-t-transparent rounded-full animate-spin"></div>
                     <span>Processing market data...</span>
                   </div>
                 ) : (
                   "Select items and click Analyze to see price distribution"
                 )}
               </div>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={result.buckets}>
                    <XAxis 
                      dataKey="range" 
                      stroke="#a38d6d" 
                      fontSize={12}
                      tick={{ fill: '#a38d6d' }}
                    />
                    <YAxis 
                      stroke="#a38d6d" 
                      fontSize={12}
                      tick={{ fill: '#a38d6d' }}
                    />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#2a2a2a', color: '#e0e0e0' }}
                  cursor={{ fill: 'rgba(200, 170, 109, 0.1)' }}
                  formatter={(value: number, name: string, props: any) => {
                    const bucket = props.payload;
                    return [
                      `Items reviewed: ${value}`,
                      `Price range: ${bucket.range}`,
                      `Avg price: ${bucket.avgPrice.toFixed(2)} ex`
                    ];
                  }}
                />
                    <Bar dataKey="count" fill="#c8aa6d" radius={[4, 4, 0, 0]}>
                      {result.buckets.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={index > result.buckets.length * 0.7 ? '#bd3333' : '#c8aa6d'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Influence Table Section */}
          <div className="bg-poe-card border border-poe-border rounded-lg p-6 flex-1">
            <h3 className="text-poe-golddim font-bold mb-4 flex items-center gap-2">
              <span>💎</span> Value Influencers
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              Attributes that appear frequently in high-value items (Top 30%) but rarely in low-value items.
            </p>

            {!result ? (
              <div className="h-48 flex items-center justify-center text-gray-500 italic border border-dashed border-gray-700 rounded">
                 No analysis data available
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-poe-border text-gray-400">
                      <th className="pb-2 font-medium">Attribute / Modifier</th>
                      <th className="pb-2 font-medium text-right">Influence Score</th>
                      <th className="pb-2 font-medium text-right">Top 30% Freq</th>
                      <th className="pb-2 font-medium text-right">Bottom 30% Freq</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-poe-border/30">
                    {result.influence.map((item, idx) => (
                      <tr key={idx} className="hover:bg-white/5 transition-colors">
                        <td className="py-3 text-poe-highlight">{item.attribute}</td>
                        <td className={`py-3 text-right font-bold ${item.diff > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {item.diff > 0 ? '+' : ''}{item.diff}%
                        </td>
                        <td className="py-3 text-right text-gray-400">{item.topFreq}%</td>
                        <td className="py-3 text-right text-gray-400">{item.bottomFreq}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
