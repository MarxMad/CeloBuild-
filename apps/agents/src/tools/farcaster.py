from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _normalize_user(payload: dict[str, Any]) -> dict[str, Any]:
    """Asegura que siempre tenemos los campos mínimos de un perfil."""
    # En Neynar v2, fid/username están en el nivel superior.
    # En v1 o legacy, pueden estar en 'profile' o 'user'.
    
    # Si payload tiene 'fid' directamente, usar payload como fuente principal
    if "fid" in payload:
        source = payload
    else:
        # Fallback para estructuras anidadas
        source = payload.get("profile") or payload.get("user") or payload

    return {
        "fid": source.get("fid"),
        "username": source.get("username") or source.get("display_name") or "anon",
        "custody_address": (source.get("custody_address") or "").lower(),
        "pfp_url": source.get("pfp_url"),
        "follower_count": source.get("follower_count") or source.get("followers", {}).get("count", 0) or 0,
        "power_badge": bool(source.get("power_badge")),
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
        # FIDs de usuarios populares/activos en Farcaster para asegurar diversidad
        # 2: dwr.eth, 3: v, 5650: jesse.xyz, 1: fcast, 6: c
        # 1214: linda, 1689: oyealmond (approx/popular), 60: betashop
        popular_fids = [2, 3, 5650, 1, 6, 1214, 1689, 60, 10, 31]
        
        all_casts: list[dict[str, Any]] = []
        
        async with httpx.AsyncClient(timeout=10) as client:
            # Obtener casts de múltiples usuarios populares con rate limiting
            # Iterar sobre todos los FIDs definidos
            for idx, fid in enumerate(popular_fids):
                # Agregar delay entre requests para evitar rate limiting (429)
                if idx > 0:
                    await asyncio.sleep(2.0)  # Aumentado a 2 segundos entre requests
                
                # Retry loop para cada usuario
                for attempt in range(3):
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
                            wait_time = 2.0 * (2 ** attempt)
                            logger.warning(
                                "Rate limit alcanzado (429) para usuario %s. Esperando %.1fs...", fid, wait_time
                            )
                            await asyncio.sleep(wait_time)
                            continue  # Reintentar
                        
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
                        break # Success, move to next user
                        
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code == 429:
                            wait_time = 5 * (2 ** attempt) # 5s, 10s, 20s
                            logger.warning(f"Rate limit alcanzado (429) para usuario {fid}. Esperando {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.warning("Error HTTP obteniendo casts del usuario %s: %s", fid, exc)
                            break # No reintentar otros errores HTTP
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Error obteniendo casts del usuario %s: %s", fid, exc)
                        break
        
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

        # Retry logic for 429 Too Many Requests
        max_retries = 3
        base_delay = 2.0
        data = {} # Initialize to avoid UnboundLocalError
        
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=10) as client:
                try:
                    resp = await client.get(url, headers=headers, params=params)
                    
                    if resp.status_code == 429:
                        wait_time = base_delay * (2 ** attempt)
                        logger.warning("⚠️ Rate limit (429) en engagement. Esperando %.1fs...", wait_time)
                        await asyncio.sleep(wait_time)
                        continue

                    if resp.status_code == 402:
                        raise ValueError(
                            "Neynar API: Payment Required (402). Tu API key no tiene crédito o no es válida."
                        )
                    
                    resp.raise_for_status()
                    data = resp.json()
                    break # Success
                except Exception as exc:
                    if attempt == max_retries - 1:
                        logger.error("❌ Error final obteniendo engagement tras %d intentos: %s", max_retries, exc)
                        return [] # Return empty list on failure
                    logger.warning("Error temporal en engagement: %s. Reintentando...", exc)
                    await asyncio.sleep(1.0)

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

    async def fetch_user_best_cast(
        self, user_fid: int, topic_tags: list[str]
    ) -> dict[str, Any] | None:
        """Encuentra el cast con mayor engagement del usuario sobre un tema."""
        casts = await self.fetch_user_casts_by_topic(user_fid, topic_tags, limit=20)
        if not casts:
            return None
            
        # Calcular score de engagement para cada cast
        for cast in casts:
            reactions = cast.get("reactions", {})
            likes = reactions.get("likes", 0)
            recasts = reactions.get("recasts", 0)
            replies = reactions.get("replies", 0)
            cast["engagement_score"] = (likes * 1.0) + (recasts * 2.0) + (replies * 0.5)
            
        # Ordenar por score descendente
        casts.sort(key=lambda x: x["engagement_score"], reverse=True)
        return casts[0]

    async def fetch_relevant_followers(self, target_fid: int, viewer_fid: int = 3) -> list[dict[str, Any]]:
        """Obtiene seguidores relevantes (comunes con viewer_fid o de alto perfil)."""
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            return []
            
        url = "https://api.neynar.com/v2/farcaster/followers/relevant"
        params = {"target_fid": target_fid, "viewer_fid": viewer_fid}
        headers = {"accept": "application/json", "api_key": self.neynar_key}
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                # La respuesta suele ser { "relevant_followers": [...] } o lista directa
                return data.get("relevant_followers") or data.get("users") or []
            except Exception as exc:
                logger.warning("Error fetching relevant followers: %s", exc)
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

    async def fetch_user_by_address(self, custody_address: str) -> dict[str, Any] | None:
        """Obtiene información de un usuario de Farcaster por su custody_address (wallet).
        
        Retorna el perfil del usuario si existe, None si no se encuentra.
        """
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            logger.warning("NEYNAR_API_KEY no configurada, no se puede buscar usuario por address")
            return None
        
        headers = {"accept": "application/json", "api_key": self.neynar_key}
        # Endpoint de Neynar v2 para buscar usuario por custody address (bulk es más eficiente y disponible en plan free)
        # Documentación: https://docs.neynar.com/reference/user-bulk-by-address
        url = "https://api.neynar.com/v2/farcaster/user/bulk-by-address"
        
        # Verificar que tenemos API key válida
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            logger.warning("⚠️ NEYNAR_API_KEY no configurada o inválida")
            return None
        
        # Normalizar address: Neynar espera lowercase
        custody_address_lower = custody_address.lower().strip()
        
        # Validar que es una dirección Ethereum válida
        if not custody_address_lower.startswith("0x") or len(custody_address_lower) != 42:
            logger.warning("⚠️ Formato de dirección inválido: %s", custody_address)
            return None
        
        # Retry logic for 429 Too Many Requests
        max_retries = 3
        base_delay = 2.0
        
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=10) as client:
                try:
                    params = {"addresses": custody_address_lower}
                    logger.info("🔍 Buscando usuario en Farcaster por address: %s (Intento %d/%d)", 
                               custody_address_lower, attempt + 1, max_retries)
                    
                    resp = await client.get(url, headers=headers, params=params)
                    
                    if resp.status_code == 429:
                        wait_time = base_delay * (2 ** attempt)
                        logger.warning("⚠️ Rate limit (429) alcanzado. Esperando %.1fs...", wait_time)
                        await asyncio.sleep(wait_time)
                        continue
                    
                    if resp.status_code == 402:
                        raise ValueError("Neynar API: Payment Required (402).")
                    
                    resp.raise_for_status()
                    data = resp.json()
                    
                    # La respuesta es un mapa { "address": [user_obj, ...] }
                    # Puede devolver una lista vacía si no encuentra usuarios
                    users_list = data.get(custody_address_lower, [])
                    
                    if not users_list or len(users_list) == 0:
                        logger.warning("⚠️ Usuario no encontrado en Farcaster para address: %s", custody_address)
                        return None
                    
                    # Tomamos el primer usuario encontrado (usualmente el más relevante)
                    user_data = users_list[0]
                    
                    # Normalizar usando la función helper
                    normalized = _normalize_user(user_data)
                    logger.info("✅ Usuario encontrado: @%s (FID: %s)", 
                               normalized.get("username"), normalized.get("fid"))
                    return normalized
                    
                except Exception as exc:
                    if attempt == max_retries - 1:
                        logger.error("❌ Error obteniendo usuario por address %s tras %d intentos: %s", 
                                   custody_address, max_retries, exc)
                        return None
                    logger.warning("Error temporal obteniendo usuario: %s. Reintentando...", exc)
                    await asyncio.sleep(1.0)
        return None

    async def fetch_user_by_fid(self, fid: int) -> dict[str, Any] | None:
        """Obtiene información de un usuario de Farcaster por su FID.
        
        Retorna el perfil del usuario si existe, None si no se encuentra.
        """
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            logger.warning("NEYNAR_API_KEY no configurada, no se puede buscar usuario por FID")
            return None
        
        headers = {"accept": "application/json", "api_key": self.neynar_key}
        # Endpoint de Neynar v2 para buscar usuario por FID (usando bulk)
        # Documentación: https://docs.neynar.com/reference/user-bulk
        url = f"https://api.neynar.com/v2/farcaster/user/bulk?fids={fid}"
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                logger.info("🔍 Buscando usuario en Farcaster por FID: %d", fid)
                resp = await client.get(url, headers=headers)
                
                logger.info("📡 Respuesta de Neynar API: status=%d para FID: %d", resp.status_code, fid)
                
                if resp.status_code == 404:
                    logger.warning("⚠️ Usuario no encontrado (404) para FID: %d", fid)
                    return None
                
                if resp.status_code == 402:
                    raise ValueError(
                        "Neynar API: Payment Required (402). Tu API key no tiene crédito o no es válida."
                    )
                
                resp.raise_for_status()
                data = resp.json()
                
                logger.debug("📦 Datos recibidos de Neynar: %s", str(data)[:200])
                
                # La API v2 bulk retorna {"users": [...]}
                user_data = None
                if isinstance(data, dict):
                    users = data.get("users", [])
                    if users and len(users) > 0:
                        user_data = users[0]
                    if not user_data and "user" in data:
                        user_data = data["user"]
                    if not user_data and "fid" in data:
                        user_data = data
                
                if not user_data:
                    logger.warning("⚠️ No se pudo extraer datos del usuario de la respuesta: %s", str(data)[:200])
                    return None
                
                # Normalizar usando la función helper
                normalized = _normalize_user(user_data)
                logger.info("✅ Usuario encontrado: @%s (FID: %d)", normalized.get("username"), fid)
                return normalized
                
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                error_text = exc.response.text[:500] if exc.response.text else "sin respuesta"
                logger.error("❌ Error HTTP obteniendo usuario por FID %d: %s - %s", fid, status_code, error_text)
                return None
            except Exception as exc:  # noqa: BLE001
                logger.error("❌ Error obteniendo usuario por FID %d: %s", fid, exc, exc_info=True)
                return None

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

    async def fetch_trending_feed(
        self, 
        limit: int = 10, 
        time_window: str = "24h", 
        channel_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Obtiene el feed de tendencias de Farcaster usando Neynar API.
        
        Args:
            limit: Cantidad de casts a retornar (max 100)
            time_window: Ventana de tiempo ('1h', '24h', '7d')
            channel_id: (Opcional) Filtrar por canal específico
        """
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            raise ValueError("NEYNAR_API_KEY requerida para obtener tendencias.")
        
        headers = {"accept": "application/json", "api_key": self.neynar_key}
        url = "https://api.neynar.com/v2/farcaster/feed/trending"
        
        params = {
            "limit": limit,
            "time_window": time_window,
            "provider": "neynar" # Usar algoritmo de Neynar por defecto
        }
        
        if channel_id and channel_id != "global":
            params["channel_id"] = channel_id

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers, params=params)
            
            if resp.status_code == 402:
                raise ValueError("Neynar API: Payment Required (402). Verifica tu plan.")
            
            resp.raise_for_status()
            data = resp.json()
            
        casts = data.get("casts", [])
        
        # Normalizar estructura para que coincida con fetch_recent_casts
        normalized_casts = []
        for cast in casts:
            author = cast.get("author", {})
            normalized_casts.append({
                "hash": cast.get("hash"),
                "text": cast.get("text", ""),
                "author": {
                    "username": author.get("username"),
                    "fid": author.get("fid"),
                    "custody_address": author.get("custody_address"),
                    "pfp_url": author.get("pfp_url"),
                    "follower_count": author.get("follower_count"),
                },
                "reactions": {
                    "likes": cast.get("reactions", {}).get("likes_count", 0),
                    "recasts": cast.get("reactions", {}).get("recasts_count", 0),
                    "replies": cast.get("reactions", {}).get("replies_count", 0),
                },
                "timestamp": cast.get("timestamp"),
                "channel_id": cast.get("channel", {}).get("id") if cast.get("channel") else "global",
                "trend_score": cast.get("score", 0), # Neynar a veces devuelve un score
            })
            
        return normalized_casts

    async def publish_frame_notification(
        self,
        target_fids: list[int],
        title: str,
        body: str,
        target_url: str,
    ) -> dict[str, Any]:
        """Envía una notificación de Frame a usuarios específicos.
        
        Args:
            target_fids: Lista de FIDs de usuarios a notificar
            title: Título de la notificación (max 32 chars)
            body: Cuerpo de la notificación (max 128 chars)
            target_url: URL que se abre al hacer click (debe ser parte del dominio de la MiniApp)
        """
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            logger.warning("NEYNAR_API_KEY no configurada, no se pueden enviar notificaciones")
            return {"status": "skipped", "reason": "missing_api_key"}

        # Validaciones básicas
        if len(title) > 32:
            title = title[:32]
        if len(body) > 128:
            body = body[:128]
            
        headers = {
            "accept": "application/json", 
            "content-type": "application/json",
            "x-api-key": self.neynar_key # Endpoint de notificaciones suele requerir x-api-key
        }
        
        url = "https://api.neynar.com/v2/farcaster/frame/notifications"
        
        payload = {
            "notification": {
                "title": title,
                "body": body,
                "target_url": target_url,
                "target_fids": target_fids
            }
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                
                if resp.status_code == 402:
                    logger.error("Neynar API: Sin créditos para notificaciones (402)")
                    return {"status": "error", "code": 402, "message": "Payment Required"}
                
                resp.raise_for_status()
                return resp.json()
                
            except Exception as exc:
                logger.error("Error enviando notificación: %s", exc)
                return {"status": "error", "message": str(exc)}

    async def send_notification_custom(
        self,
        token: str,
        url: str,
        title: str,
        body: str,
        target_url: str,
        notification_id: str,
    ) -> dict[str, Any]:
        """Envía notificación usando un token específico (Self-hosted)."""
        
        # Validaciones
        if len(title) > 32: title = title[:32]
        if len(body) > 128: body = body[:128]
        
        payload = {
            "notificationId": notification_id,
            "title": title,
            "body": body,
            "targetUrl": target_url,
            "tokens": [token]
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                logger.info("📡 Enviando notificación custom a %s", url)
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.error("Error enviando notificación custom: %s", exc)
                return {"status": "error", "message": str(exc)}

