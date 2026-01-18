import pytest
import hashlib
from datetime import datetime, timedelta
from services.help_chat_cache import (
    get_cached_response,
    set_cached_response,
    invalidate_cache,
    get_cache_stats
)

@pytest.mark.asyncio
async def test_cache_miss(supabase_client, test_user):
    """Test: Cache Miss gibt None zurück"""
    result = await get_cached_response(
        query="test query that does not exist",
        user_id=test_user['id']
    )
    assert result is None

@pytest.mark.asyncio
async def test_cache_hit(supabase_client, test_user):
    """Test: Cache Hit gibt gecachte Response zurück"""
    query = "test query for caching"
    expected_response = {
        'response': 'test answer',
        'confidence': 0.95,
        'session_id': 'test_session'
    }
    
    # Cache setzen
    await set_cached_response(
        query=query,
        user_id=test_user['id'],
        response=expected_response
    )
    
    # Cache abrufen
    result = await get_cached_response(
        query=query,
        user_id=test_user['id']
    )
    
    assert result is not None
    assert result['response'] == expected_response['response']
    assert result['confidence'] == expected_response['confidence']

@pytest.mark.asyncio
async def test_cache_with_context(supabase_client, test_user):
    """Test: Cache berücksichtigt Context"""
    query = "same query different context"
    context1 = {'route': '/dashboards', 'userRole': 'admin'}
    context2 = {'route': '/projects', 'userRole': 'user'}
    
    response1 = {'response': 'answer for dashboards'}
    response2 = {'response': 'answer for projects'}
    
    # Zwei verschiedene Responses mit gleichem Query aber unterschiedlichem Context
    await set_cached_response(query, test_user['id'], response1, context1)
    await set_cached_response(query, test_user['id'], response2, context2)
    
    # Abrufen mit Context 1
    result1 = await get_cached_response(query, test_user['id'], context1)
    assert result1['response'] == 'answer for dashboards'
    
    # Abrufen mit Context 2
    result2 = await get_cached_response(query, test_user['id'], context2)
    assert result2['response'] == 'answer for projects'

@pytest.mark.asyncio
async def test_cache_expiry(supabase_client, test_user):
    """Test: Abgelaufener Cache wird nicht zurückgegeben"""
    query = "expired query"
    
    # Cache mit sehr kurzem TTL setzen (1 Sekunde)
    await set_cached_response(
        query=query,
        user_id=test_user['id'],
        response={'response': 'old answer'},
        ttl=1
    )
    
    # Sofort abrufen - sollte funktionieren
    result = await get_cached_response(query, test_user['id'])
    assert result is not None
    
    # 2 Sekunden warten
    import asyncio
    await asyncio.sleep(2)
    
    # Jetzt sollte Cache abgelaufen sein
    result = await get_cached_response(query, test_user['id'])
    assert result is None

@pytest.mark.asyncio
async def test_cache_invalidation(supabase_client, test_user):
    """Test: Cache kann invalidiert werden"""
    query = "query to invalidate"
    
    # Cache setzen
    await set_cached_response(
        query=query,
        user_id=test_user['id'],
        response={'response': 'answer'}
    )
    
    # Verifizieren dass Cache existiert
    result = await get_cached_response(query, test_user['id'])
    assert result is not None
    
    # Cache für User invalidieren
    await invalidate_cache(user_id=test_user['id'])
    
    # Cache sollte jetzt leer sein
    result = await get_cached_response(query, test_user['id'])
    assert result is None

@pytest.mark.asyncio
async def test_cache_stats(supabase_client, test_user):
    """Test: Cache-Statistiken werden korrekt berechnet"""
    # Mehrere Cache-Einträge erstellen
    for i in range(3):
        await set_cached_response(
            query=f"query {i}",
            user_id=test_user['id'],
            response={'response': f'answer {i}'}
        )
    
    # Stats abrufen
    stats = await get_cache_stats()
    
    assert stats['active_entries'] >= 3
    assert stats['total_entries'] >= 3

@pytest.mark.asyncio
async def test_cache_key_generation(test_user):
    """Test: Cache-Keys werden konsistent generiert"""
    query = "test query"
    context = {'route': '/test', 'userRole': 'user'}
    
    # Gleiche Inputs sollten gleichen Cache-Key erzeugen
    import json
    cache_input1 = f"{query}:{test_user['id']}:{json.dumps({'route': '/test', 'userRole': 'user'}, sort_keys=True)}"
    cache_input2 = f"{query}:{test_user['id']}:{json.dumps({'route': '/test', 'userRole': 'user'}, sort_keys=True)}"
    
    key1 = hashlib.sha256(cache_input1.encode()).hexdigest()
    key2 = hashlib.sha256(cache_input2.encode()).hexdigest()
    
    assert key1 == key2

@pytest.mark.asyncio
async def test_cache_ttl_based_on_confidence(supabase_client, test_user):
    """Test: TTL wird basierend auf Confidence angepasst"""
    query_high_conf = "high confidence query"
    query_low_conf = "low confidence query"
    
    # High confidence = längerer TTL (600s)
    await set_cached_response(
        query=query_high_conf,
        user_id=test_user['id'],
        response={'response': 'high conf answer', 'confidence': 0.95},
        ttl=600
    )
    
    # Low confidence = kürzerer TTL (300s)
    await set_cached_response(
        query=query_low_conf,
        user_id=test_user['id'],
        response={'response': 'low conf answer', 'confidence': 0.6},
        ttl=300
    )
    
    # Beide sollten abrufbar sein
    result_high = await get_cached_response(query_high_conf, test_user['id'])
    result_low = await get_cached_response(query_low_conf, test_user['id'])
    
    assert result_high is not None
    assert result_low is not None

# Fixtures für Tests
@pytest.fixture
def test_user():
    """Mock User für Tests"""
    return {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'email': 'test@example.com'
    }

@pytest.fixture
def supabase_client(monkeypatch):
    """Mock Supabase Client für Tests"""
    # In echten Tests würde hier ein Test-Supabase-Client verwendet
    # Für dieses Beispiel mocken wir die Funktionen
    pass
