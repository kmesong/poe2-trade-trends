"""
Database models and session management for PoE2 Trade Analysis.
Uses SQLAlchemy with SQLite for local development.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class AnalysisResult(db.Model):
    """
    Stores a complete analysis run for a specific base type.
    Links to all modifiers found during this analysis.
    """
    id = db.Column(db.Integer, primary_key=True)
    base_type = db.Column(db.String(255), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Price data
    normal_avg_chaos = db.Column(db.Float, nullable=False)
    crafting_avg_chaos = db.Column(db.Float, default=0.0)
    magic_avg_chaos = db.Column(db.Float, nullable=False)
    gap_chaos = db.Column(db.Float, nullable=False)

    # Search IDs for trade links
    search_id = db.Column(db.String(100))
    magic_search_id = db.Column(db.String(100))

    # Raw data snapshot (JSON)
    raw_data = db.Column(db.Text)

    # Relationships
    modifiers = db.relationship('Modifier', backref='analysis', lazy='dynamic',
                                  cascade='all, delete-orphan')

    def to_dict(self):
        """Convert to dictionary for API responses."""
        all_mods = [m.to_dict() for m in self.modifiers]
        return {
            'id': self.id,
            'base_type': self.base_type,
            'created_at': self.created_at.isoformat(),
            'normal_avg_chaos': self.normal_avg_chaos,
            'crafting_avg_chaos': self.crafting_avg_chaos,
            'magic_avg_chaos': self.magic_avg_chaos,
            'gap_chaos': self.gap_chaos,
            'search_id': self.search_id,
            'magic_search_id': self.magic_search_id,
            'modifiers': all_mods,
            'normal_modifiers': [m for m in all_mods if str(m['rarity']).lower() == 'normal' or str(m['rarity']).lower() == 'unknown'],
            'magic_modifiers': [m for m in all_mods if str(m['rarity']).lower() == 'magic']
        }


class Modifier(db.Model):
    """
    Stores individual modifier data from an analysis.
    Links to the parent AnalysisResult.
    """
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analysis_result.id'), nullable=False)

    # Modifier identification
    name = db.Column(db.String(255), nullable=False, index=True)
    tier = db.Column(db.String(20), nullable=False, index=True)  # e.g., "P1", "S1"
    mod_type = db.Column(db.String(50), nullable=False, index=True)  # explicit, implicit, etc.

    # Item context
    rarity = db.Column(db.String(20), nullable=False)  # normal, magic, rare
    item_name = db.Column(db.String(255))
    display_text = db.Column(db.String(500)) # The full text from the item

    # Price data (if available)
    price_chaos = db.Column(db.Float)

    # Magnitude values (min/max for the mod)
    magnitude_min = db.Column(db.Float)
    magnitude_max = db.Column(db.Float)

    # Additional metadata
    mod_group = db.Column(db.String(100))  # e.g., "Life", "Resistance"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
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


class ExcludedModifier(db.Model):
    """
    User preferences for modifiers to exclude from analysis.
    Can match by name pattern or tier.
    """
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Matching criteria (at least one must be set)
    mod_name_pattern = db.Column(db.String(255), index=True)  # SQL LIKE pattern
    mod_tier = db.Column(db.String(20), index=True)  # e.g., "P1", "S1"
    mod_type = db.Column(db.String(50), index=True)  # explicit, implicit, etc.

    # Reason/notes
    reason = db.Column(db.Text)

    # Active flag
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'mod_name_pattern': self.mod_name_pattern,
            'mod_tier': self.mod_tier,
            'mod_type': self.mod_type,
            'reason': self.reason,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

    def matches(self, modifier: Modifier) -> bool:
        """
        Check if this exclusion rule matches a modifier.
        """
        if not self.is_active:
            return False

        # Check mod_type match
        if self.mod_type and self.mod_type != modifier.mod_type:
            return False

        # Check tier match
        if self.mod_tier and self.mod_tier != modifier.tier:
            return False

        # Check name pattern match
        if self.mod_name_pattern:
            # Use SQL LIKE pattern matching
            if not modifier.name.lower().like(self.mod_name_pattern.lower()):
                return False

        return True


class CustomCategory(db.Model):
    """
    User-defined item categories for grouping items (e.g., "My Starter Build").
    Stores a name and a list of item base names.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    items = db.Column(db.Text, nullable=False)  # Comma-separated list of item base names

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'items': [i.strip() for i in self.items.split(',')] if self.items else []
        }


def init_db(app):
    """
    Initialize the database with the Flask app.
    Call this once during app startup.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()


def get_db():
    """Get a database session."""
    return db.session


def save_analysis(analyzer, base_type: str, session_id: str = None,
                  excluded_mods: list = None) -> AnalysisResult:
    """
    Run a complete analysis for a base type and save all data to the database.

    Args:
        analyzer: PriceAnalyzer instance
        base_type: Item base type to analyze
        session_id: POESESSID for API access
        excluded_mods: List of modifier names/tiers to exclude

    Returns:
        AnalysisResult: The saved analysis record
    """
    from backend.price_analyzer import PriceAnalyzer
    from backend.currency_service import CurrencyService

    analyzer = analyzer or PriceAnalyzer(CurrencyService())

    # Run the analysis
    result = analyzer.analyze_gap(base_type, session_id, exclusions=excluded_mods)

    # Create the analysis record
    analysis = AnalysisResult(
        base_type=base_type,
        normal_avg_chaos=result['normal_avg_chaos'],
        crafting_avg_chaos=result.get('crafting_avg_chaos', 0.0),
        magic_avg_chaos=result['magic_avg_chaos'],
        gap_chaos=result['gap_chaos'],
        search_id=result.get('search_id'),
        magic_search_id=result.get('magic_search_id')
    )

    db.session.add(analysis)
    db.session.flush()  # Get the analysis ID

    # Store full modifier data
    all_mods = result.get('normal_modifiers', []) + result.get('magic_modifiers', [])
    
    for mod_data in all_mods:
        mod = Modifier(
            analysis_id=analysis.id,
            name=mod_data.get('name', 'Unknown'),
            tier=mod_data.get('tier', 'Unknown'),
            mod_type=mod_data.get('mod_type', 'unknown'),
            rarity=mod_data.get('rarity', 'unknown'),
            item_name=mod_data.get('item_name'),
            display_text=mod_data.get('display_text'),
            magnitude_min=mod_data.get('magnitude_min'),
            magnitude_max=mod_data.get('magnitude_max'),
            mod_group=None # extract_modifiers doesn't return group yet
        )
        db.session.add(mod)

    db.session.commit()

    return analysis


def get_analyses(base_type: str = None, limit: int = 100) -> list:
    """
    Get analysis results, optionally filtered by base type.

    Args:
        base_type: Optional filter for specific item type
        limit: Maximum number of results to return

    Returns:
        list: AnalysisResult objects
    """
    query = AnalysisResult.query

    if base_type:
        query = query.filter(AnalysisResult.base_type == base_type)

    return query.order_by(AnalysisResult.created_at.desc()).limit(limit).all()


def get_latest_analyses(limit: int = 100) -> list:
    """
    Get the LATEST analysis result for each base_type.
    This gives a snapshot of the current state for all tracked items.
    
    Args:
        limit: Maximum number of results to return (per base_type limit is 1)
        
    Returns:
        list: AnalysisResult objects (latest per base_type)
    """
    # Subquery to find the max ID for each base_type
    subquery = db.session.query(
        db.func.max(AnalysisResult.id).label('max_id')
    ).group_by(AnalysisResult.base_type).subquery()
    
    # Join with the main table to get full records
    query = AnalysisResult.query.join(
        subquery,
        AnalysisResult.id == subquery.c.max_id
    ).order_by(AnalysisResult.created_at.desc())
    
    if limit:
        query = query.limit(limit)
        
    return query.all()


def add_excluded_mod(name_pattern: str = None, tier: str = None,
                     mod_type: str = None, reason: str = None) -> ExcludedModifier:
    """
    Add a new excluded modifier rule.

    Args:
        name_pattern: SQL LIKE pattern for modifier name
        tier: Specific tier to exclude (e.g., "P1")
        mod_type: Modifier type (explicit, implicit, etc.)
        reason: Optional reason for exclusion

    Returns:
        ExcludedModifier: The created rule
    """
    exclusion = ExcludedModifier(
        mod_name_pattern=name_pattern,
        mod_tier=tier,
        mod_type=mod_type,
        reason=reason
    )

    db.session.add(exclusion)
    db.session.commit()

    return exclusion


def get_excluded_mods() -> list:
    """
    Get all active excluded modifier rules.

    Returns:
        list: ExcludedModifier objects
    """
    return ExcludedModifier.query.filter_by(is_active=True).all()


def remove_excluded_mod(exclusion_id: int) -> bool:
    """
    Remove (deactivate) an excluded modifier rule.

    Args:
        exclusion_id: ID of the rule to remove

    Returns:
        bool: True if found and deactivated, False otherwise
    """
    exclusion = ExcludedModifier.query.get(exclusion_id)
    if exclusion:
        exclusion.is_active = False
        db.session.commit()
        return True
    return False
