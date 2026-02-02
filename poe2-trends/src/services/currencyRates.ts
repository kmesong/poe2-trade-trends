// Currency rates service - fetches from backend and caches in localStorage
import toast from 'react-hot-toast';

const CURRENCY_RATES_KEY = 'poe_currency_rates';
const CURRENCY_RATES_VERSION = 'v1'; // Increment to force refresh

export interface CurrencyRates {
  [currency: string]: number;
}

const DEFAULT_RATES: CurrencyRates = {
  exalted: 1.0,
  divine: 320.0,
  chaos: 7.8,
  alch: 3.9,
  gcp: 15.6,
  regal: 7.8,
  vaal: 11.7,
  fusing: 7.8,
  chrom: 3.9,
  jewellers: 3.9,
  fossil_primitive: 78.0,
  fossil_pristine: 117.0,
  scouring: 3.9,
  regret: 7.8,
  blessed: 39.0,
  mirror: 1500000.0,
};

function getStoredRates(): CurrencyRates | null {
  try {
    const stored = localStorage.getItem(CURRENCY_RATES_KEY);
    if (stored) {
      const data = JSON.parse(stored);
      if (data.version === CURRENCY_RATES_VERSION && data.rates) {
        return data.rates;
      }
    }
  } catch (e) {
    console.error('Error reading stored rates:', e);
  }
  return null;
}

function saveRates(rates: CurrencyRates): void {
  try {
    const data = {
      version: CURRENCY_RATES_VERSION,
      rates,
      timestamp: Date.now(),
    };
    localStorage.setItem(CURRENCY_RATES_KEY, JSON.stringify(data));
  } catch (e) {
    console.error('Error saving rates:', e);
  }
}

export async function getRates(): Promise<CurrencyRates> {
  // Try localStorage first
  const stored = getStoredRates();
  if (stored) {
    return stored;
  }

  // Fallback to default rates
  saveRates(DEFAULT_RATES);
  return DEFAULT_RATES;
}

export async function fetchRatesFromBackend(): Promise<CurrencyRates> {
  try {
    const response = await fetch('/api/currency/rates');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    
    if (data && typeof data === 'object') {
      saveRates(data);
      return data;
    }
    throw new Error('Invalid response format');
  } catch (error) {
    console.error('Failed to fetch rates from backend:', error);
    throw error;
  }
}

export async function refreshRates(): Promise<CurrencyRates> {
  const loadingToast = toast.loading('Refreshing rates from poe.ninja...');
  
  try {
    const rates = await fetchRatesFromBackend();
    toast.success('Rates updated successfully!', { id: loadingToast });
    return rates;
  } catch {
    toast.error('Failed to refresh rates. Using cached values.', { id: loadingToast });
    // Return cached or default rates
    return getRates() || DEFAULT_RATES;
  }
}

export function formatCurrency(amount: number, currency: string = 'exalted'): string {
  const rates = getRates() || DEFAULT_RATES;
  const rate = rates[currency.toLowerCase()] || rates.exalted || 1;
  const exalts = amount * rate;
  
  if (exalts >= 1) {
    return `${exalts.toFixed(2)} Ex`;
  } else if (exalts >= 0.01) {
    return `${(exalts * 100).toFixed(1)}c`;
  } else {
    return `${(exalts * 10000).toFixed(0)} fragments`;
  }
}

export function chaosToExalted(chaosAmount: number): number {
  const rates = getRates() || DEFAULT_RATES;
  return chaosAmount * (rates.chaos || 0.00556);
}

export function exaltedToChaos(exAmount: number): number {
  const rates = getRates() || DEFAULT_RATES;
  const chaosRate = rates.chaos || 0.00556;
  return exAmount / chaosRate;
}

export { DEFAULT_RATES };
