import React, { useState, useEffect } from 'react';
import { getSessionId, saveSessionId } from '../utils/storage';
import { refreshRates, getRates, type CurrencyRates } from '../services/currencyRates';
import { getExclusions, addExclusion, removeExclusion } from '../services/database';
import type { ExcludedModifier } from '../types';
import toast from 'react-hot-toast';

export const Settings: React.FC = () => {
  const [sessionId, setSessionId] = useState(getSessionId() || '');
  const [isVisible, setIsVisible] = useState(false);
  const [status, setStatus] = useState<'idle' | 'saved' | 'cleared'>('idle');
  const [rates, setRates] = useState<CurrencyRates | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const [exclusions, setExclusions] = useState<ExcludedModifier[]>([]);
  const [newExclusion, setNewExclusion] = useState<Partial<ExcludedModifier>>({
    mod_name_pattern: '',
    mod_tier: '',
    mod_type: 'explicit',
    reason: ''
  });
  const [isLoadingExclusions, setIsLoadingExclusions] = useState(false);

  useEffect(() => {
    getRates().then(setRates).catch(console.error);
    loadExclusions();
  }, []);

  const loadExclusions = async () => {
    setIsLoadingExclusions(true);
    try {
      const data = await getExclusions();
      setExclusions(data);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load excluded modifiers');
    } finally {
      setIsLoadingExclusions(false);
    }
  };

  const handleAddExclusion = async () => {
    if (!newExclusion.mod_name_pattern && !newExclusion.mod_tier) {
      toast.error('Must provide Name Pattern or Tier');
      return;
    }
    
    try {
      await addExclusion(newExclusion);
      toast.success('Exclusion added');
      setNewExclusion({ mod_name_pattern: '', mod_tier: '', mod_type: 'explicit', reason: '' });
      loadExclusions();
    } catch (err) {
      console.error(err);
      toast.error('Failed to add exclusion');
    }
  };

  const handleRemoveExclusion = async (id: number) => {
    try {
      await removeExclusion(id);
      toast.success('Exclusion removed');
      loadExclusions();
    } catch (err) {
      console.error(err);
      toast.error('Failed to remove exclusion');
    }
  };

  const handleSave = () => {
    saveSessionId(sessionId.trim());
    setStatus('saved');
    setTimeout(() => setStatus('idle'), 2000);
  };

  const handleClear = () => {
    setSessionId('');
    saveSessionId('');
    setStatus('cleared');
    setTimeout(() => setStatus('idle'), 2000);
  };

  const handleRefreshRates = async () => {
    setIsRefreshing(true);
    try {
      await refreshRates();
      const newRates = await getRates();
      setRates(newRates);
      toast.success('Currency rates updated from poe.ninja');
    } catch {
      toast.error('Failed to refresh rates');
    } finally {
      setIsRefreshing(false);
    }
  };

  const formatRate = (rate: number) => {
    if (rate >= 1) {
      return rate.toFixed(2);
    } else if (rate >= 0.01) {
      return rate.toFixed(4);
    }
    return rate.toExponential(2);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto text-gray-200">
      <h1 className="text-3xl font-serif text-poe-gold mb-8 border-b border-poe-border pb-4">
        Settings
      </h1>

      <div className="bg-poe-card border border-poe-border p-6 rounded-lg shadow-lg">
        <h2 className="text-xl font-bold text-poe-highlight mb-4">API Configuration</h2>
        
        <div className="mb-6">
          <label className="block text-sm font-bold text-poe-golddim mb-2 uppercase tracking-wide">
            POESESSID
          </label>
          <p className="text-xs text-gray-500 mb-3">
            Required for batch analysis to fetch trade data. 
            Found in your browser cookies on pathofexile.com.
          </p>
          
          <div className="relative">
            <input
              type={isVisible ? "text" : "password"}
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="Enter your POESESSID..."
              className="w-full bg-black/40 border border-poe-border rounded p-3 text-sm text-poe-highlight focus:border-poe-gold focus:outline-none transition-colors pr-10"
            />
            <button
              onClick={() => setIsVisible(!isVisible)}
              className="absolute right-3 top-3 text-gray-500 hover:text-gray-300"
            >
              {isVisible ? '🙈' : '👁️'}
            </button>
          </div>
        </div>

        <div className="flex gap-4 items-center">
          <button
            onClick={handleSave}
            className="bg-poe-gold/20 text-poe-gold border border-poe-gold/50 px-6 py-2 rounded hover:bg-poe-gold hover:text-black font-bold transition-all uppercase text-sm tracking-wide"
          >
            Save Configuration
          </button>
          
          <button
            onClick={handleClear}
            className="text-gray-500 hover:text-red-400 text-sm underline transition-colors"
          >
            Clear Session
          </button>

          {status === 'saved' && (
            <span className="text-green-500 text-sm animate-pulse ml-auto">
              ✓ Settings saved successfully
            </span>
          )}
          {status === 'cleared' && (
            <span className="text-yellow-500 text-sm animate-pulse ml-auto">
              ✓ Session cleared
            </span>
          )}
        </div>
      </div>

      {/* Currency Rates Section */}
      <div className="bg-poe-card border border-poe-border p-6 rounded-lg shadow-lg mt-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-poe-highlight">Currency Rates</h2>
          <button
            onClick={handleRefreshRates}
            disabled={isRefreshing}
            className={`bg-poe-gold/20 text-poe-gold border border-poe-gold/50 px-4 py-2 rounded hover:bg-poe-gold hover:text-black font-bold transition-all uppercase text-sm tracking-wide disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {isRefreshing ? 'Refreshing...' : 'Refresh from poe.ninja'}
          </button>
        </div>
        
        <p className="text-xs text-gray-500 mb-4">
          Current exchange rates normalized to Exalted Orbs. 
          Rates are approximate and may vary. Click refresh to update from poe.ninja.
        </p>

        {rates && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(rates)
              .sort((a, b) => b[1] - a[1])
              .map(([currency, rate]) => (
                <div 
                  key={currency} 
                  className="bg-black/30 border border-poe-border/50 rounded p-2 text-center"
                >
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                    {currency}
                  </div>
                  <div className="text-sm text-poe-highlight font-mono">
                    {formatRate(rate)} Ex
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      <div className="bg-poe-card border border-poe-border p-6 rounded-lg shadow-lg mt-6">
        <h2 className="text-xl font-bold text-poe-highlight mb-4">Excluded Modifiers</h2>
        <p className="text-xs text-gray-500 mb-6">
          Define modifiers to ignore during price analysis. Useful for removing outliers or irrelevant mods.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6 items-end bg-black/20 p-4 rounded border border-poe-border/30">
          <div>
            <label className="block text-xs text-poe-golddim mb-1">Name Pattern (SQL LIKE)</label>
            <input 
              type="text" 
              placeholder="%Life%" 
              value={newExclusion.mod_name_pattern || ''}
              onChange={e => setNewExclusion({...newExclusion, mod_name_pattern: e.target.value})}
              className="w-full bg-black/40 border border-poe-border rounded p-2 text-sm text-poe-highlight"
            />
          </div>
          <div>
            <label className="block text-xs text-poe-golddim mb-1">Tier (e.g. P1)</label>
            <input 
              type="text" 
              placeholder="P1" 
              value={newExclusion.mod_tier || ''}
              onChange={e => setNewExclusion({...newExclusion, mod_tier: e.target.value})}
              className="w-full bg-black/40 border border-poe-border rounded p-2 text-sm text-poe-highlight"
            />
          </div>
          <div>
            <label className="block text-xs text-poe-golddim mb-1">Type</label>
            <select 
              value={newExclusion.mod_type || 'explicit'}
              onChange={e => setNewExclusion({...newExclusion, mod_type: e.target.value})}
              className="w-full bg-black/40 border border-poe-border rounded p-2 text-sm text-poe-highlight"
            >
              <option value="explicit">Explicit</option>
              <option value="implicit">Implicit</option>
              <option value="fractured">Fractured</option>
              <option value="rune">Rune</option>
            </select>
          </div>
          <button 
            onClick={handleAddExclusion}
            className="bg-poe-gold/20 text-poe-gold border border-poe-gold/50 px-4 py-2 rounded hover:bg-poe-gold hover:text-black font-bold transition-all uppercase text-sm tracking-wide h-10"
          >
            Add Rule
          </button>
        </div>

        <div className="space-y-2">
          {exclusions.map(ex => (
            <div key={ex.id} className="flex items-center justify-between bg-black/30 p-3 rounded border border-poe-border/30 hover:border-poe-gold/30 transition-colors">
              <div className="flex gap-4 items-center">
                <span className={`px-2 py-0.5 rounded text-xs uppercase font-bold ${
                  ex.mod_type === 'explicit' ? 'bg-blue-900/30 text-blue-300' : 
                  ex.mod_type === 'fractured' ? 'bg-yellow-900/30 text-yellow-300' : 'bg-gray-800 text-gray-300'
                }`}>
                  {ex.mod_type}
                </span>
                {ex.mod_name_pattern && (
                  <span className="text-poe-highlight font-mono text-sm">
                    {ex.mod_name_pattern}
                  </span>
                )}
                {ex.mod_tier && (
                  <span className="text-gray-400 text-xs border border-gray-700 px-1 rounded">
                    {ex.mod_tier}
                  </span>
                )}
                {ex.reason && (
                  <span className="text-gray-500 text-xs italic">
                    — {ex.reason}
                  </span>
                )}
              </div>
              <button 
                onClick={() => handleRemoveExclusion(ex.id)}
                className="text-red-500 hover:text-red-300 text-xs uppercase font-bold"
              >
                Remove
              </button>
            </div>
          ))}
          {exclusions.length === 0 && !isLoadingExclusions && (
            <p className="text-center text-gray-500 italic py-4">No exclusion rules defined.</p>
          )}
        </div>
      </div>
    </div>
  );
};
