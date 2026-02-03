"""
Database models and session management for PoE2 Trade Analysis.
Uses MongoDB with MongoEngine for flexible document storage.
"""
from datetime import datetime
from mongoengine import (
    connect, Document, EmbeddedDocument, StringField, FloatField, 
    DateTimeField, ListField, EmbeddedDocumentField, BooleanField,
    DictField
)
import json


class Modifier(EmbeddedDocument):
    """
    Stores individual modifier data from an analysis.
    Embedded inside AnalysisResult.
    """
    # Modifier identification
    name = StringField(required=True)
    tier = StringField(required=True)  # e.g., "P1", "S1"
    mod_type = StringField(required=True)  # explicit, implicit, etc.

    # Item context
    rarity = StringField(required=True)  # normal, magic, rare
    item_name = StringField()
    display_text = StringField() # The full text from the item

    # Price data (if available)
    price_chaos = FloatField()

    # Magnitude values (min/max for the mod)
    magnitude_min = FloatField()
    magnitude_max = FloatField()

    # Additional metadata
    mod_group = StringField()

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'name': self.name,
            'tier': self.tier,
            'mod_type': self.mod_type,
            'rarity': self.rarity,
            'item_name': self.item_name,
            'display_text': self.display_text,
            'price_chaos': self.price_chaos,
            'magnitude_min': self.magnitude_min,
            'magnitude_max': self.magnitude_max,
            'mod_group': self.mod_group
        }


class AnalysisResult(Document):
    """
    Stores a complete analysis run for a specific base type.
    Includes all modifiers found during this analysis as embedded documents.
    """
    base_type = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    # Price data
    normal_avg_chaos = FloatField(required=True)
    crafting_avg_chaos = FloatField(default=0.0)
    magic_avg_chaos = FloatField(required=True)
    gap_chaos = FloatField(required=True)

    # Search IDs for trade links
    search_id = StringField()
    magic_search_id = StringField()

    # Raw data snapshot
    raw_data = StringField()

    # Embedded modifiers
    modifiers = ListField(EmbeddedDocumentField(Modifier))

    meta = {
        'indexes': [
            'base_type',
            '-created_at'
        ]
    }

    def to_dict(self):
        """Convert to dictionary for API responses."""
        all_mods = [m.to_dict() for m in self.modifiers]
        return {
            'id': str(self.id),
            'base_type': self.base_type,
            'created_at': self.created_at.isoformat(),
            'normal_avg_chaos': self.normal_avg_chaos,
            'crafting_avg_chaos': self.crafting_avg_chaos,
            'magic_avg_chaos': self.magic_avg_chaos,
            'gap_chaos': self.gap_chaos,
            'search_id': self.search_id,
            'magic_search_id': self.magic_search_id,
            'modifiers': all_mods,
            'normal_modifiers': [m for m in all_mods if str(m['rarity']).lower() in ['normal', 'unknown']],
            'magic_modifiers': [m for m in all_mods if str(m['rarity']).lower() == 'magic']
        }


class ExcludedModifier(Document):
    """
    User preferences for modifiers to exclude from analysis.
    """
    created_at = DateTimeField(default=datetime.utcnow)

    # Matching criteria (at least one must be set)
    mod_name_pattern = StringField()  # Regex pattern for MongoDB
    mod_tier = StringField()  # e.g., "P1", "S1"
    mod_type = StringField()  # explicit, implicit, etc.

    # Reason/notes
    reason = StringField()

    # Active flag
    is_active = BooleanField(default=True)

    meta = {
        'indexes': [
            'mod_name_pattern',
            'mod_tier',
            'mod_type'
        ]
    }

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': str(self.id),
            'mod_name_pattern': self.mod_name_pattern,
            'mod_tier': self.mod_tier,
            'mod_type': self.mod_type,
            'reason': self.reason,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

    def matches(self, modifier_data: dict) -> bool:
        """
        Check if this exclusion rule matches a modifier.
        Works with both Modifier objects and raw dictionary data.
        """
        if not self.is_active:
            return False

        # Extract values from either object or dict
        m_type = modifier_data.get('mod_type')
        m_tier = modifier_data.get('tier')
        m_name = modifier_data.get('name', '')

        # Check mod_type match
        if self.mod_type and self.mod_type != m_type:
            return False

        # Check tier match
        if self.mod_tier and self.mod_tier != m_tier:
            return False

        # Check name pattern match (regex)
        if self.mod_name_pattern:
            import re
            try:
                if not re.search(self.mod_name_pattern, m_name, re.IGNORECASE):
                    return False
            except re.error:
                return False

        return True


class SearchHistory(Document):
    """
    Stores generic search history and analysis results.
    Replaces the local JSON file storage.
    """
    name = StringField(required=True)
    query = DictField()
    results = DictField()
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            '-created_at',
            'name'
        ]
    }

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'query': self.query,
            'results': self.results,
            'created_at': self.created_at.isoformat(),
            'timestamp': int(self.created_at.timestamp())
        }


class CustomCategory(Document):
    """
    User-defined item categories for grouping items.
    """
    name = StringField(unique=True, required=True)
    items = ListField(StringField())  # List of item base names

    meta = {
        'indexes': [
            'name'
        ]
    }

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': str(self.id),
            'name': self.name,
            'items': self.items
        }


def init_db(app):
    """
    Initialize the database connection.
    """
    mongodb_uri = app.config.get('MONGODB_URI') or app.config.get('MONGODB_SETTINGS', {}).get('host')
    if mongodb_uri:
        connect(host=mongodb_uri)
    else:
        # Default to localhost if no config found
        connect(host='mongodb://localhost:27017/poe2_trade')


def get_db():
    """Get the database connection."""
    import mongoengine
    return mongoengine.connection.get_db()



def save_analysis(analyzer, base_type: str, session_id: str = None,
                  excluded_mods: list = None) -> AnalysisResult:
    """
    Run a complete analysis for a base type and save all data to MongoDB.
    """
    from backend.price_analyzer import PriceAnalyzer
    from backend.currency_service import CurrencyService

    analyzer = analyzer or PriceAnalyzer(CurrencyService())

    # Run the analysis
    result = analyzer.analyze_gap(base_type, session_id, exclusions=excluded_mods)

    # Create embedded modifiers
    all_mods_data = result.get('normal_modifiers', []) + result.get('magic_modifiers', [])
    modifiers = []
    
    for mod_data in all_mods_data:
        mod = Modifier(
            name=mod_data.get('name', 'Unknown'),
            tier=mod_data.get('tier', 'Unknown'),
            mod_type=mod_data.get('mod_type', 'unknown'),
            rarity=mod_data.get('rarity', 'unknown'),
            item_name=mod_data.get('item_name'),
            display_text=mod_data.get('display_text'),
            magnitude_min=mod_data.get('magnitude_min'),
            magnitude_max=mod_data.get('magnitude_max'),
            mod_group=None
        )
        modifiers.append(mod)

    # Create and save the analysis document
    analysis = AnalysisResult(
        base_type=base_type,
        normal_avg_chaos=result['normal_avg_chaos'],
        crafting_avg_chaos=result.get('crafting_avg_chaos', 0.0),
        magic_avg_chaos=result['magic_avg_chaos'],
        gap_chaos=result['gap_chaos'],
        search_id=result.get('search_id'),
        magic_search_id=result.get('magic_search_id'),
        modifiers=modifiers
    )

    analysis.save()
    return analysis


def get_analyses(base_type: str = None, limit: int = 100) -> list:
    """
    Get analysis results from MongoDB.
    """
    query = AnalysisResult.objects
    if base_type:
        query = query.filter(base_type=base_type)

    return query.order_by('-created_at').limit(limit)


def get_latest_analyses(limit: int = 100) -> list:
    """
    Get the LATEST analysis result for each base_type.
    """
    # MongoDB aggregation to find latest per base_type
    pipeline = [
        {'$sort': {'created_at': -1}},
        {'$group': {
            '_id': '$base_type',
            'latest_id': {'$first': '$_id'}
        }},
        {'$limit': limit}
    ]
    
    latest_ids = [res['latest_id'] for res in AnalysisResult.objects.aggregate(pipeline)]
    return AnalysisResult.objects.filter(id__in=latest_ids).order_by('-created_at')


def add_excluded_mod(name_pattern: str = None, tier: str = None,
                     mod_type: str = None, reason: str = None) -> ExcludedModifier:
    """
    Add a new excluded modifier rule.
    """
    exclusion = ExcludedModifier(
        mod_name_pattern=name_pattern,
        mod_tier=tier,
        mod_type=mod_type,
        reason=reason
    )
    exclusion.save()
    return exclusion


def get_excluded_mods() -> list:
    """
    Get all active excluded modifier rules.
    """
    return ExcludedModifier.objects.filter(is_active=True)


def remove_excluded_mod(exclusion_id: str) -> bool:
    """
    Remove (deactivate) an excluded modifier rule.
    """
    exclusion = ExcludedModifier.objects.filter(id=exclusion_id).first()
    if exclusion:
        exclusion.is_active = False
        exclusion.save()
        return True
    return False
