"""
Help Chat Caching Service mit Supabase
Reduziert AI-API-Calls durch intelligentes Caching
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from config.database import supabase
import logging

logger = logging.getLogger(__name__)

# Cache TTL in Sekunden (5 Minuten)
CACHE_TTL = 300

async def get_cached_response(
    query: str,
    user_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Prüft Supabase cache-Tabelle für gecachte AI-Antwort.
    Cache-Key: SHA256 Hash von query + user_id + context
    """
    try:
        # Cache-Key generieren (inkl. context für präziseres Caching)
        cache_input = f"{query}:{user_id}"
        if context:
            # Nur relevante Context-Keys für Cache-Key verwenden
            relevant_context = {
                'route': context.get('route'),
                'userRole': context.get('userRole')
            }
            cache_input += f":{json.dumps(relevant_context, sort_keys=True)}"
        
        cache_key = hashlib.sha256(cache_input.encode()).hexdigest()
        
        # Query cache-Tabelle
        result = supabase.table('help_chat_cache') \
            .select('*') \
            .eq('cache_key', cache_key) \
            .gte('expires_at', datetime.utcnow().isoformat()) \
            .single() \
            .execute()
        
        if result.data:
            logger.info(f"Cache HIT for query: {query[:50]}...")
            return result.data['response']
    except Exception as e:
        # Cache Miss oder Fehler - kein Problem, AI-Call folgt
        logger.debug(f"Cache MISS: {e}")
    
    return None

async def set_cached_response(
    query: str,
    user_id: str,
    response: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    ttl: int = CACHE_TTL
):
    """
    Speichert AI-Antwort in Supabase cache-Tabelle mit TTL.
    """
    try:
        # Cache-Key generieren (gleiche Logik wie get_cached_response)
        cache_input = f"{query}:{user_id}"
        if context:
            relevant_context = {
                'route': context.get('route'),
                'userRole': context.get('userRole')
            }
            cache_input += f":{json.dumps(relevant_context, sort_keys=True)}"
        
        cache_key = hashlib.sha256(cache_input.encode()).hexdigest()
        
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        # Upsert in cache-Tabelle
        supabase.table('help_chat_cache').upsert({
            'cache_key': cache_key,
            'query': query[:500],  # Truncate für DB
            'user_id': user_id,
            'response': response,
            'expires_at': expires_at.isoformat(),
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        logger.info(f"Cached response for query: {query[:50]}... (TTL: {ttl}s)")
    except Exception as e:
        # Cache-Fehler nicht kritisch
        logger.error(f"Cache write error: {e}")

async def invalidate_cache(user_id: Optional[str] = None):
    """
    Invalidiert Cache-Einträge.
    Wenn user_id gegeben, nur für diesen User.
    """
    try:
        if user_id:
            supabase.table('help_chat_cache') \
                .delete() \
                .eq('user_id', user_id) \
                .execute()
            logger.info(f"Invalidated cache for user: {user_id}")
        else:
            # Alle abgelaufenen Einträge löschen
            supabase.table('help_chat_cache') \
                .delete() \
                .lt('expires_at', datetime.utcnow().isoformat()) \
                .execute()
            logger.info("Cleaned up expired cache entries")
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")

async def get_cache_stats() -> Dict[str, Any]:
    """
    Gibt Cache-Statistiken zurück.
    """
    try:
        # Anzahl aktiver Cache-Einträge
        active_count = supabase.table('help_chat_cache') \
            .select('id', count='exact') \
            .gte('expires_at', datetime.utcnow().isoformat()) \
            .execute()
        
        # Anzahl abgelaufener Einträge
        expired_count = supabase.table('help_chat_cache') \
            .select('id', count='exact') \
            .lt('expires_at', datetime.utcnow().isoformat()) \
            .execute()
        
        return {
            'active_entries': active_count.count or 0,
            'expired_entries': expired_count.count or 0,
            'total_entries': (active_count.count or 0) + (expired_count.count or 0)
        }
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return {
            'active_entries': 0,
            'expired_entries': 0,
            'total_entries': 0,
            'error': str(e)
        }
