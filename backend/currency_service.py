class CurrencyService:
    DEFAULT_RATES = {
        "exalted": 1.0,
        "divine": 320.0,        # 1 Divine = 320 Exalted
        "chaos": 7.8,           # 1 Chaos = 7.8 Exalted
        "alch": 3.9,            # 0.5 Chaos
        "gcp": 15.6,            # 2 Chaos
        "regal": 7.8,           # 1 Chaos
        "vaal": 11.7,           # 1.5 Chaos
        "fusing": 7.8,          # 1 Chaos
        "chrom": 3.9,           # 0.5 Chaos
        "jewellers": 3.9,       # 0.5 Chaos
        "fossil_primitive": 78.0,       # ~10 Chaos
        "fossil_pristine": 117.0,       # ~15 Chaos
        "scouring": 3.9,        # 0.5 Chaos
        "regret": 7.8,          # 1 Chaos
        "blessed": 39.0,        # ~5 Chaos
        "mirror": 1500000.0,    # Mirror shards
    }
    
    def __init__(self, custom_rates=None):
        # Use custom rates if provided (from poe.ninja fetch), otherwise defaults
        self.rates = custom_rates if custom_rates else self.DEFAULT_RATES.copy()

    def get_rates(self):
        """
        Returns a dictionary of currency rates normalized to Exalted.
        Rates can be updated via refresh_from_poe_ninja().
        """
        return self.rates

    def normalize_to_exalted(self, amount, currency_type):
        """
        Converts a given amount of a specific currency type into Exalted.
        Returns 0 if the currency type is unknown.
        """
        if not currency_type:
            return 0.0
            
        currency_type = currency_type.lower()
        rates = self.get_rates()
        
        if currency_type in rates:
            return amount * rates[currency_type]
        
        # Fallback/Unknown currency
        return 0.0

    def refresh_from_poe_ninja(self, fetched_rates):
        """
        Update rates from fetched poe.ninja data.
        Expects dict with currency -> rate (Exalted normalized).
        """
        if fetched_rates and isinstance(fetched_rates, dict):
            self.rates = fetched_rates
            return True
        return False

    def reset_to_defaults(self):
        """Reset rates to poe.ninja defaults."""
        self.rates = self.DEFAULT_RATES.copy()
