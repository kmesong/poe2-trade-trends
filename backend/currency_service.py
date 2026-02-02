class CurrencyService:
    def __init__(self):
        # Initial hardcoded rates for V1
        self.rates = {
            "chaos": 1.0,
            "divine": 90.0,
            "exalted": 5.0,
            "alch": 0.5,
            "gcp": 2.0,
            "regal": 1.0,
            "vaal": 1.5
        }

    def get_rates(self):
        """
        Returns a dictionary of currency rates normalized to Chaos.
        In V1, these are hardcoded. In V2, this will fetch from an API or scraper.
        """
        return self.rates

    def normalize_to_chaos(self, amount, currency_type):
        """
        Converts a given amount of a specific currency type into Chaos.
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
