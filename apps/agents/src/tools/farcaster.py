from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _normalize_user(payload: dict[str, Any]) -> dict[str, Any]:
    """Asegura que siempre tenemos los campos mínimos de un perfil."""
    profile = payload.get("profile") or payload.get("user") or payload
    return {
        "fid": profile.get("fid"),
        "username": profile.get("username") or profile.get("display_name") or "anon",
        "custody_address": (profile.get("custody_address") or "").lower(),
        "pfp_url": profile.get("pfp_url"),
        "follower_count": profile.get("follower_count") or profile.get("followers", {}).get("count", 0) or 0,
        "power_badge": bool(profile.get("power_badge")),
    }


class FarcasterToolbox:
    """Cliente para consultar Neynar API. Requiere API key válida con créditos disponibles."""

    def __init__(
        self,
        base_url: str,
        api_token: str | None = None,
        neynar_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.neynar_key = neynar_key

    async def fetch_frame_stats(self, frame_id: str) -> dict[str, Any]:
        """Obtiene métricas de un frame. Requiere API token válido."""
        if not self.api_token:
            raise ValueError(
                "FARCASTER_API_TOKEN requerido para obtener stats de frames. "
                "Configura un token válido en tu archivo .env"
            )
        
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        async with httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=10) as client:
            resp = await client.get(f"/frames/{frame_id}")
            resp.raise_for_status()
            return resp.json()

    async def fetch_recent_casts(self, channel_id: str = "global", limit: int = 10) -> list[dict[str, Any]]:
        """Busca casts recientes usando Neynar API (Producción). Requiere API key válida."""
        
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            raise ValueError(
                "NEYNAR_API_KEY requerida. Obtén una API key válida en https://neynar.com "
                "y configúrala en tu archivo .env"
            )
        
        headers = {"accept": "application/json", "api_key": self.neynar_key}
        # Estrategia: Usar /feed/user/casts con usuarios populares conocidos de Farcaster
        # Este endpoint cuesta 4 créditos por usuario según: https://dev.neynar.com/pricing#product-api
        # FIDs de usuarios populares/activos en Farcaster (puedes ajustar estos)
        popular_fids = [2, 3, 1593, 5650]  # Ejemplos: dwr.eth, v, y otros usuarios activos
        
        all_casts: list[dict[str, Any]] = []
        
        async with httpx.AsyncClient(timeout=10) as client:
            # Obtener casts de múltiples usuarios populares con rate limiting
            # Limitar a 1 usuario para evitar rate limits (429) en plan gratuito
            for idx, fid in enumerate(popular_fids[:1]):  # Solo 1 usuario para evitar rate limits
                # Agregar delay entre requests para evitar rate limiting (429)
                if idx > 0:
                    await asyncio.sleep(1.0)  # Esperar 1 segundo entre requests
                
                try:
                    url = "https://api.neynar.com/v2/farcaster/feed/user/casts"
                    params = {"fid": fid, "limit": min(limit, 10)}
                    
                    resp = await client.get(url, headers=headers, params=params)
                    
                    if resp.status_code == 402:
                        raise ValueError(
                            "Neynar API: Payment Required (402). Tu API key no tiene crédito o no es válida. "
                            "Verifica tu API key en https://neynar.com o actualiza tu plan."
                        )
                    
                    if resp.status_code == 429:
                        logger.warning(
                            "Rate limit alcanzado (429) para usuario %s. Esperando antes de continuar...", fid
                        )
                        await asyncio.sleep(5.0)  # Esperar 5 segundos si hay rate limit
                        continue  # Saltar este usuario y continuar
                    
                    resp.raise_for_status()
                    data = resp.json()
                    
                    for cast in data.get("casts", []):
                        author = cast.get("author", {})
                        all_casts.append(
                        {
                                "hash": cast.get("hash"),
                                "text": cast.get("text", ""),
                            "author": {
                                    "username": author.get("username"),
                                    "fid": author.get("fid"),
                                    "custody_address": author.get("custody_address"),
                            },
                            "reactions": {
                                    "likes": cast.get("reactions", {}).get("likes_count", 0),
                                    "recasts": cast.get("reactions", {}).get("recasts_count", 0),
                                    "replies": cast.get("reactions", {}).get("replies_count", 0),
                                },
                                "timestamp": cast.get("timestamp"),
                                "channel_id": cast.get("thread", {}).get("channel", {}).get("id") or channel_id,
                            }
                        )
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 429:
                        logger.warning("Rate limit (429) para usuario %s. Saltando...", fid)
                        await asyncio.sleep(2.0)
                    else:
                        logger.warning("Error HTTP obteniendo casts del usuario %s: %s", fid, exc)
                    continue
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Error obteniendo casts del usuario %s: %s", fid, exc)
                    continue
        
        # Ordenar por timestamp y limitar resultados
        all_casts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_casts[:limit]

    async def fetch_cast_engagement(self, cast_hash: str, limit: int = 50) -> list[dict[str, Any]]:
        """Retorna usuarios que interactuaron con un cast específico. Requiere API key válida."""
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            raise ValueError(
                "NEYNAR_API_KEY requerida para obtener engagement. "
                "Configura una API key válida en tu archivo .env"
            )
        
        headers = {"accept": "application/json", "api_key": self.neynar_key}
        url = "https://api.neynar.com/v2/farcaster/cast"
        params = {"identifier": cast_hash, "type": "hash"}

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers, params=params)
            
            if resp.status_code == 402:
                raise ValueError(
                    "Neynar API: Payment Required (402). Tu API key no tiene crédito o no es válida."
                )
            
            resp.raise_for_status()
            data = resp.json()

        cast = data.get("cast") or data.get("result", {}).get("cast")
        if not cast:
            return []

        participants: dict[str, dict[str, Any]] = {}

        def upsert_participant(raw_user: dict[str, Any], weight: float, reason: str) -> None:
            user = _normalize_user(raw_user)
            if not user["custody_address"]:
                return
            record = participants.setdefault(
                user["custody_address"],
                {
                    "fid": user["fid"],
                    "username": user["username"],
                    "custody_address": user["custody_address"],
                    "follower_count": user["follower_count"],
                    "power_badge": user["power_badge"],
                    "engagement_weight": 0.0,
                    "reasons": set(),
                },
            )
            record["engagement_weight"] += weight
            record["reasons"].add(reason)

        upsert_participant(cast.get("author", {}), 2.0, "author")

        for reaction in cast.get("reactions", {}).get("likes", [])[:limit]:
            upsert_participant(reaction, 1.0, "like")

        for reaction in cast.get("reactions", {}).get("recasts", [])[:limit]:
            upsert_participant(reaction, 1.5, "recast")

        enriched = []
        for participant in participants.values():
            participant["reasons"] = list(participant["reasons"])
            enriched.append(participant)
        return enriched

    async def fetch_user_casts_by_topic(
        self, user_fid: int, topic_tags: list[str], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Busca casts de un usuario que mencionan los topic_tags de la tendencia."""
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            return []

        try:
            headers = {"accept": "application/json", "api_key": self.neynar_key}
            # Buscar casts del usuario que contengan los tags
            # Usar /feed/user/casts que cuesta 4 créditos según: https://dev.neynar.com/pricing#product-api
            url = "https://api.neynar.com/v2/farcaster/feed/user/casts"
            params = {"fid": user_fid, "limit": limit}

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()

            user_casts = []
            casts = data.get("casts", [])

            for cast in casts:
                text_lower = (cast.get("text", "") or "").lower()
                # Verificar si el cast menciona alguno de los topic_tags
                matches_any_tag = any(tag.lower() in text_lower for tag in topic_tags)

                if matches_any_tag:
                    reactions = cast.get("reactions", {})
                    user_casts.append({
                        "hash": cast.get("hash"),
                        "text": cast.get("text", ""),
                        "reactions": {
                            "likes": reactions.get("likes_count", 0),
                            "recasts": reactions.get("recasts_count", 0),
                            "replies": reactions.get("replies_count", 0),
                        },
                        "timestamp": cast.get("timestamp"),
                    })

            return user_casts
        except Exception as exc:  # noqa: BLE001
            logger.error("Error buscando casts del usuario por tema: %s", exc)
            return []

    async def analyze_user_participation_in_trend(
        self, user_fid: int, cast_hash: str, topic_tags: list[str]
    ) -> dict[str, Any]:
        """Analiza la participación de un usuario en una tendencia específica.
        
        Retorna:
        - Si participó directamente (like/recast/reply)
        - Sus casts relacionados con el tema
        - Ponderación basada en engagement
        """
        participation = {
            "directly_participated": False,
            "related_casts": [],
            "total_engagement": 0.0,
            "engagement_breakdown": {
                "likes_received": 0,
                "recasts_received": 0,
                "replies_received": 0,
            },
        }

        # 1. Verificar participación directa
        participants = await self.fetch_cast_engagement(cast_hash, limit=100)
        user_address = None
        for p in participants:
            if p.get("fid") == user_fid:
                participation["directly_participated"] = True
                participation["total_engagement"] += p.get("engagement_weight", 0.0)
                user_address = p.get("custody_address")
                break

        # 2. Buscar casts del usuario sobre el tema
        if user_fid:
            related_casts = await self.fetch_user_casts_by_topic(user_fid, topic_tags, limit=5)
            participation["related_casts"] = related_casts
            
            # Calcular engagement total de sus casts relacionados
            for cast in related_casts:
                reactions = cast.get("reactions", {})
                likes = reactions.get("likes", 0)
                recasts = reactions.get("recasts", 0)
                replies = reactions.get("replies", 0)
                
                # Ponderación: likes=1, recasts=2, replies=0.6
                cast_engagement = (likes * 1.0 + recasts * 2.0 + replies * 0.6)
                participation["total_engagement"] += cast_engagement
                participation["engagement_breakdown"]["likes_received"] += likes
                participation["engagement_breakdown"]["recasts_received"] += recasts
                participation["engagement_breakdown"]["replies_received"] += replies

        return participation

    @staticmethod
    def timestamp_age_hours(timestamp: str | None) -> float:
        if not timestamp:
            return 24.0
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return 24.0
        delta = datetime.now(timezone.utc) - dt
        return max(delta.total_seconds() / 3600, 0.0)

