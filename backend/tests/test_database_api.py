import pytest
from backend.server import app, db, init_db
from backend.database import ExcludedModifier, AnalysisResult

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            # db is already initialized in server.py, just create tables
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_add_get_exclusion(client):
    """Test adding and retrieving an excluded modifier."""
    # 1. Add exclusion
    response = client.post('/api/db/exclusions', json={
        'mod_name_pattern': 'Life',
        'mod_tier': 'P1',
        'mod_type': 'explicit',
        'reason': 'Too common'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['mod_name_pattern'] == 'Life'
    
    # 2. Get exclusions
    response = client.get('/api/db/exclusions')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']) == 1
    assert data['data'][0]['mod_name_pattern'] == 'Life'

def test_remove_exclusion(client):
    """Test removing an exclusion."""
    # Add one first
    client.post('/api/db/exclusions', json={
        'mod_name_pattern': 'Mana',
        'reason': 'Ignore'
    })
    
    # Get ID
    response = client.get('/api/db/exclusions')
    exclusion_id = response.get_json()['data'][0]['id']
    
    # Remove
    response = client.delete(f'/api/db/exclusions/{exclusion_id}')
    assert response.status_code == 200
    
    # Verify it's gone (or inactive)
    response = client.get('/api/db/exclusions')
    assert len(response.get_json()['data']) == 0

def test_save_and_get_analysis(client):
    """Test saving (simulated) and retrieving an analysis."""
    # Create analysis manually since the endpoint just reads
    with app.app_context():
        analysis = AnalysisResult(
            base_type="Test Bow",
            normal_avg_chaos=10.0,
            magic_avg_chaos=50.0,
            gap_chaos=40.0,
            search_id="abc",
            magic_search_id="def"
        )
        db.session.add(analysis)
        db.session.commit()
    
    # Get analyses
    response = client.get('/api/db/analyses')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']) == 1
    assert data['data'][0]['base_type'] == "Test Bow"

def test_save_analysis_function(client):
    """Test the save_analysis function logic with exclusions."""
    from backend.database import save_analysis
    from unittest.mock import MagicMock
    
    # Mock analyzer
    mock_analyzer = MagicMock()
    mock_analyzer.analyze_gap.return_value = {
        "base_type": "Test Item",
        "normal_avg_chaos": 10.0,
        "magic_avg_chaos": 20.0,
        "gap_chaos": 10.0,
        "search_id": "123",
        "magic_search_id": "456",
        "normal_modifiers": [{"name": "Mod 1", "tier": "P1", "mod_type": "explicit", "rarity": "normal"}],
        "magic_modifiers": [{"name": "Mod 2", "tier": "S1", "mod_type": "explicit", "rarity": "magic"}]
    }
    
    with app.app_context():
        # Run save_analysis
        result = save_analysis(mock_analyzer, "Test Item", "sessid", excluded_mods=[])
        
        # Verify result
        assert result.base_type == "Test Item"
        assert result.gap_chaos == 10.0
        
        # Verify modifiers were saved
        assert result.modifiers.count() == 2
        
        # Verify analyzer was called
        mock_analyzer.analyze_gap.assert_called_once()

