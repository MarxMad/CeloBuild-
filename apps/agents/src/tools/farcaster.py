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
        
        # OPTIMIZATION: Seleccionar solo 3 usuarios aleatorios para no saturar la API
        # Esto reduce las llamadas de 10 a 3 por ejecución de fallback
        import random
        selected_fids = random.sample(popular_fids, min(3, len(popular_fids)))
        
        all_casts: list[dict[str, Any]] = []
        
        async with httpx.AsyncClient(timeout=10) as client:
            # Obtener casts de múltiples usuarios populares con rate limiting
            # Iterar sobre los FIDs seleccionados
            for idx, fid in enumerate(selected_fids):
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

    async def fetch_user_recent_casts(self, user_fid: int, limit: int = 10) -> list[dict[str, Any]]:
        """Obtiene los casts más recientes de un usuario."""
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            return []

        try:
            headers = {"accept": "application/json", "api_key": self.neynar_key}
            url = "https://api.neynar.com/v2/farcaster/feed/user/casts"
            params = {"fid": user_fid, "limit": limit}

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()

            casts = data.get("casts", [])
            
            # Normalizar estructura para asegurar que reactions sean números, no listas
            normalized_casts = []
            for cast in casts:
                reactions_raw = cast.get("reactions", {})
                # Neynar puede devolver likes/recasts/replies como listas o como objetos con count
                # Normalizar a números
                likes = reactions_raw.get("likes_count", 0) if isinstance(reactions_raw.get("likes_count"), (int, float)) else (
                    len(reactions_raw.get("likes", [])) if isinstance(reactions_raw.get("likes"), list) else 0
                )
                recasts = reactions_raw.get("recasts_count", 0) if isinstance(reactions_raw.get("recasts_count"), (int, float)) else (
                    len(reactions_raw.get("recasts", [])) if isinstance(reactions_raw.get("recasts"), list) else 0
                )
                replies = reactions_raw.get("replies_count", 0) if isinstance(reactions_raw.get("replies_count"), (int, float)) else (
                    len(reactions_raw.get("replies", [])) if isinstance(reactions_raw.get("replies"), list) else 0
                )
                
                normalized_casts.append({
                    **cast,  # Mantener todos los campos originales
                    "reactions": {
                        "likes": int(likes) if likes else 0,
                        "recasts": int(recasts) if recasts else 0,
                        "replies": int(replies) if replies else 0,
                    }
                })
            
            return normalized_casts
        except Exception as exc:
            logger.error("Error obteniendo casts recientes del fid %s: %s", user_fid, exc)
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
        # OPTIMIZATION: Reducir límite de 100 a 50 para ahorrar créditos API
        participants = await self.fetch_cast_engagement(cast_hash, limit=50)
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

    async def fetch_users_by_addresses(self, custody_addresses: list[str]) -> dict[str, dict[str, Any]]:
        """Obtiene información de múltiples usuarios de Farcaster por sus addresses (Bulk).
        
        Retorna mapa { address_lowercase: user_data }
        """
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            return {}
            
        headers = {"accept": "application/json", "api_key": self.neynar_key}
        url = "https://api.neynar.com/v2/farcaster/user/bulk-by-address"
        
        # Filtrar y normalizar addresses
        valid_addresses = [
            addr.lower().strip() for addr in custody_addresses 
            if addr and addr.lower().strip().startswith("0x") and len(addr.strip()) == 42
        ]
        
        if not valid_addresses:
            return {}
            
        # Chunking (Neynar suele permitir ~50-100 por call, usaremos 50 para seguridad)
        chunk_size = 50
        result_map = {}
        
        for i in range(0, len(valid_addresses), chunk_size):
            chunk = valid_addresses[i:i + chunk_size]
            addresses_str = ",".join(chunk)
            
            try:
                params = {"addresses": addresses_str}
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(url, headers=headers, params=params)
                    
                    if resp.status_code == 429:
                        logger.warning("⚠️ Rate limit (429) en bulk fetch. Esperando 2s y reintentando chunk...")
                        await asyncio.sleep(2.0)
                        # Simple retry once
                        resp = await client.get(url, headers=headers, params=params)
                        
                    if resp.status_code == 200:
                        data = resp.json()
                        # Data format: { "0x...": [user1, user2], "0x...": [] }
                        for addr, users in data.items():
                            if users and len(users) > 0:
                                result_map[addr.lower()] = _normalize_user(users[0])
                    else:
                        logger.warning("Error fetching bulk users: %s", resp.status_code)
                        
                await asyncio.sleep(0.2) # Rate limit kindness
                
            except Exception as e:
                logger.error("Error en batch fetch users: %s", e)
                
        return result_map

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
        
        url = "https://api.neynar.com/v2/farcaster/feed/trending"
        
        params = {
            "limit": limit,
            "time_window": time_window,
        }
        
        # Solo agregar provider si es necesario (puede causar 400 si no es válido)
        # params["provider"] = "neynar"  # Comentado: puede causar 400 Bad Request
        
        if channel_id and channel_id != "global":
            params["channel_id"] = channel_id

        async with httpx.AsyncClient(timeout=10) as client:
            # Intentar primero con api_key en header
            headers = {"accept": "application/json", "api_key": self.neynar_key}
            resp = await client.get(url, headers=headers, params=params)
            
            # Si falla con 400, probar con x-api-key
            if resp.status_code == 400:
                logger.warning("⚠️ Error 400 con api_key, probando con x-api-key...")
                headers_alt = {"accept": "application/json", "x-api-key": self.neynar_key}
                resp = await client.get(url, headers=headers_alt, params=params)
            
            if resp.status_code == 402:
                raise ValueError("Neynar API: Payment Required (402). Verifica tu plan.")
            
            if resp.status_code != 200:
                error_text = resp.text[:500] if resp.text else "sin respuesta"
                logger.error(f"❌ Error obteniendo trending feed: {resp.status_code} - {error_text}")
                # Retornar lista vacía en lugar de fallar completamente
                return []
            
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
            
        url = "https://api.neynar.com/v2/farcaster/frame/notifications"
        
        headers = {
            "accept": "application/json", 
            "content-type": "application/json",
            "api_key": self.neynar_key
        }
        
        # Formato correcto según documentación de Neynar: target_fids en nivel superior
        payload = {
            "target_fids": target_fids,
            "notification": {
                "title": title,
                "body": body,
                "target_url": target_url
            }
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                
                # Si falla con 400, probar con x-api-key como fallback
                if resp.status_code == 400:
                    logger.warning("Probando con header x-api-key...")
                    headers_alt = {
                        "accept": "application/json", 
                        "content-type": "application/json",
                        "x-api-key": self.neynar_key
                    }
                    resp = await client.post(url, headers=headers_alt, json=payload)
                
                if resp.status_code == 402:
                    logger.error("Neynar API: Sin créditos para notificaciones (402)")
                    return {"status": "error", "code": 402, "message": "Payment Required"}
                
                if resp.status_code == 400:
                    error_detail = resp.text
                    try:
                        error_json = resp.json()
                        error_detail = str(error_json)
                    except:
                        pass
                    logger.error("Neynar API: Bad Request (400). Payload: %s, Response: %s", payload, error_detail)
                    return {"status": "error", "code": 400, "message": f"Bad Request: {error_detail}"}
                
                resp.raise_for_status()
                result = resp.json()
                logger.info("✅ Notificación enviada exitosamente a %d FIDs", len(target_fids))
                return result
                
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

    async def fetch_user_by_username(self, username: str) -> dict[str, Any] | None:
        """Obtiene información de un usuario de Farcaster por su username."""
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            return None
        
        headers = {"accept": "application/json", "api_key": self.neynar_key}
        url = "https://api.neynar.com/v2/farcaster/user/search"
        params = {"q": username, "limit": 1}
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code != 200:
                    return None
                data = resp.json()
                users = data.get("result", {}).get("users", [])
                if not users:
                    return None
                
                # Verify exact match (case insensitive)
                found_user = users[0]
                if found_user.get("username", "").lower() != username.lower():
                    logger.warning("Username mismatch: searched %s, found %s", username, found_user.get("username"))
                    return None
                
                return _normalize_user(found_user)
            except Exception as exc:
                logger.error("Error fetching user %s: %s", username, exc)
                return None

    async def fetch_casts_from_users(self, usernames: list[str], limit_per_user: int = 5) -> list[dict[str, Any]]:
        """Obtiene casts recientes de una lista específica de usuarios."""
        all_casts = []
        
        for username in usernames:
            user = await self.fetch_user_by_username(username)
            if not user or not user.get("fid"):
                continue
                
            fid = user["fid"]
            try:
                # Reusing fetch_recent_casts logic but targeting specific FID
                headers = {"accept": "application/json", "api_key": self.neynar_key}
                url = "https://api.neynar.com/v2/farcaster/feed/user/casts"
                params = {"fid": fid, "limit": limit_per_user}
                
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(url, headers=headers, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        for cast in data.get("casts", []):
                            author = cast.get("author", {})
                            all_casts.append({
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
                                "channel_id": cast.get("thread", {}).get("channel", {}).get("id") or "global",
                                "trend_score": 0.0, # Will be calculated later but generally lower
                                "is_targeted": True, # Flag to identify these casts
                            })
                    await asyncio.sleep(0.5) # Gentle rate limit
            except Exception as exc:
                logger.warning("Error fetching casts for %s: %s", username, exc)
                
        return all_casts

    async def crawl_embed_metadata(self, url: str) -> dict[str, Any] | None:
        """Obtiene metadatos de embed para una URL usando Neynar API.
        
        Útil para validar que los metadatos Open Graph sean correctos antes de compartir un cast.
        
        Args:
            url: URL a validar/crawlear
            
        Returns:
            Dict con metadatos del embed o None si hay error
        """
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            logger.warning("NEYNAR_API_KEY no configurada, no se pueden validar metadatos de embed")
            return None
        
        headers = {
            "accept": "application/json",
            "api_key": self.neynar_key
        }
        
        url_endpoint = "https://api.neynar.com/v2/farcaster/cast/embed/crawl"
        params = {"url": url}
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(url_endpoint, headers=headers, params=params)
                
                if resp.status_code == 402:
                    logger.error("Neynar API: Sin créditos para crawl de embed (402)")
                    return None
                
                resp.raise_for_status()
                data = resp.json()
                return data.get("metadata")
                
            except Exception as exc:
                logger.warning("Error obteniendo metadatos de embed para %s: %s", url, exc)
                return None
    
    async def fetch_user_latest_cast(self, user_fid: int) -> dict[str, Any] | None:
        """Obtiene el ÚLTIMO cast (más reciente) de un usuario.
        
        Args:
            user_fid: FID del usuario
            
        Returns:
            Dict con los datos del cast o None si no tiene casts recientes.
        """
        # Reutilizamos fetch_user_recent_casts con el límite mínimo posible
        casts = await self.fetch_user_recent_casts(user_fid, limit=1)
        if casts and len(casts) > 0:
            return casts[0]
        return None

    async def create_signer(self) -> dict[str, Any]:
        """Crea un nuevo signer usando Neynar API v2.
        
        Returns:
            {
                "signer_uuid": str,
                "public_key": str,
                "status": "generated"
            }
        """
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            return {
                "status": "error",
                "message": "NEYNAR_API_KEY no configurada"
            }
        
        url = "https://api.neynar.com/v2/farcaster/signer"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.neynar_key
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(url, headers=headers)
                resp.raise_for_status()
                result = resp.json()
                
                return {
                    "status": "success",
                    "signer_uuid": result.get("signer_uuid"),
                    "public_key": result.get("public_key"),
                    "status": result.get("status", "generated")
                }
            except Exception as exc:
                logger.error(f"Error creando signer: {exc}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Error creando signer: {str(exc)}"
                }
    
    async def register_signed_key(
        self,
        signer_uuid: str,
        app_fid: int,
        deadline: int,
        signature: str
    ) -> dict[str, Any]:
        """Registra una signed key con Neynar API.
        
        Args:
            signer_uuid: UUID del signer creado
            app_fid: FID de la app (debe tener una cuenta Farcaster)
            deadline: UNIX timestamp en segundos
            signature: Firma creada con el mnemonic de la app
        
        Returns:
            {
                "status": "success" | "error",
                "approval_url": str | None,
                "message": str
            }
        """
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            return {
                "status": "error",
                "message": "NEYNAR_API_KEY no configurada"
            }
        
        url = "https://api.neynar.com/v2/farcaster/signer/signed_key"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.neynar_key
        }
        
        payload = {
            "signer_uuid": signer_uuid,
            "app_fid": app_fid,
            "deadline": deadline,
            "signature": signature
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                result = resp.json()
                
                return {
                    "status": "success",
                    "approval_url": result.get("approval_url"),
                    "status": result.get("status", "pending_approval")
                }
            except Exception as exc:
                logger.error(f"Error registrando signed key: {exc}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Error registrando signed key: {str(exc)}"
                }
    
    async def get_signer_status(self, signer_uuid: str) -> dict[str, Any]:
        """Obtiene el estado actual de un signer.
        
        Returns:
            {
                "signer_uuid": str,
                "status": "generated" | "pending_approval" | "approved" | "revoked",
                "public_key": str,
                "fid": int | None,
                "approval_url": str | None
            }
        """
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            return {
                "status": "error",
                "message": "NEYNAR_API_KEY no configurada"
            }
        
        url = f"https://api.neynar.com/v2/farcaster/signer?signer_uuid={signer_uuid}"
        headers = {
            "accept": "application/json",
            "x-api-key": self.neynar_key
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                result = resp.json()
                
                return {
                    "status": "success",
                    "signer_uuid": result.get("signer_uuid"),
                    "status": result.get("status"),
                    "public_key": result.get("public_key"),
                    "fid": result.get("fid"),
                    "approval_url": result.get("approval_url")
                }
            except Exception as exc:
                logger.error(f"Error obteniendo estado del signer: {exc}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Error obteniendo estado del signer: {str(exc)}"
                }

    async def publish_cast(
        self,
        user_fid: int,
        cast_text: str,
        parent_hash: str | None = None,
        signer_uuid: str | None = None
    ) -> dict[str, Any]:
        """Publica un cast en Farcaster usando Neynar API v2.
        
        Args:
            user_fid: FID del usuario que publica
            cast_text: Texto del cast (máximo 320 caracteres)
            parent_hash: Hash del cast padre si es una reply (opcional)
            signer_uuid: UUID del signer del usuario (requerido para publicar)
        
        Returns:
            {
                "status": "success" | "error",
                "cast_hash": str | None,
                "message": str
            }
        
        NOTA: Requiere signer_uuid del usuario. Si no se proporciona, intenta usar
        un signer compartido del backend (si está configurado en NEYNAR_SIGNER_UUID).
        """
        if not self.neynar_key or self.neynar_key == "NEYNAR_API_DOCS":
            logger.warning("NEYNAR_API_KEY no configurada, no se pueden publicar casts")
            return {
                "status": "error",
                "cast_hash": None,
                "message": "NEYNAR_API_KEY no configurada"
            }
        
        # Validar longitud
        if len(cast_text) > 320:
            return {
                "status": "error",
                "cast_hash": None,
                "message": "Cast demasiado largo (máximo 320 caracteres)"
            }
        
        # Si no hay signer_uuid, buscar en el store de signers
        if not signer_uuid:
            from ..stores.signers import get_signer_store
            signer_store = get_signer_store()
            # Intentar buscar por FID primero
            signer_data = signer_store.get_signer(str(user_fid))
            if signer_data and signer_data.get("status") == "approved":
                signer_uuid = signer_data.get("signer_uuid")
                logger.info(f"Usando signer aprobado del store para FID {user_fid}")
            else:
                # Fallback: intentar usar signer compartido del backend (para desarrollo)
                import os
                signer_uuid = os.getenv("NEYNAR_SIGNER_UUID")
                if signer_uuid:
                    logger.info(f"Usando signer compartido del backend para FID {user_fid}")
                else:
                    logger.warning(
                        f"⚠️ No se encontró signer aprobado para FID {user_fid}. "
                        "El usuario necesita crear y aprobar un signer primero."
                    )
                    return {
                        "status": "error",
                        "cast_hash": None,
                        "message": "Se requiere un signer aprobado para publicar casts. Por favor, crea y aprueba un signer primero."
                    }
        
        # Publicar usando Neynar API v2
        # Documentación: https://docs.neynar.com/reference/post-cast
        url = "https://api.neynar.com/v2/farcaster/cast"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.neynar_key  # Neynar usa x-api-key en el header (no api_key)
        }
        
        payload: dict[str, Any] = {
            "signer_uuid": signer_uuid,
            "text": cast_text
        }
        
        # Si es una reply, agregar parent (puede ser hash del cast o parent_url del canal)
        if parent_hash:
            payload["parent"] = parent_hash  # Neynar acepta string directamente (hash o parent_url)
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                logger.info(f"📤 Publicando cast para FID {user_fid} usando signer {signer_uuid[:8]}...")
                resp = await client.post(url, headers=headers, json=payload)
                
                if resp.status_code == 402:
                    logger.error("Neynar API: Sin créditos para publicar casts (402)")
                    return {
                        "status": "error",
                        "cast_hash": None,
                        "message": "Sin créditos en Neynar API. Se requieren 150 créditos por cast."
                    }
                
                if resp.status_code == 400:
                    error_detail = resp.text
                    try:
                        error_json = resp.json()
                        error_detail = str(error_json)
                    except:
                        pass
                    logger.error(f"Neynar API: Bad Request (400). Response: {error_detail}")
                    return {
                        "status": "error",
                        "cast_hash": None,
                        "message": f"Error de Neynar API: {error_detail}"
                    }
                
                resp.raise_for_status()
                result = resp.json()
                
                # Extraer el hash del cast publicado
                cast_hash = None
                if isinstance(result, dict):
                    cast_hash = result.get("cast", {}).get("hash") or result.get("hash")
                
                if cast_hash:
                    logger.info(f"✅ Cast publicado exitosamente: {cast_hash}")
                    return {
                        "status": "success",
                        "cast_hash": cast_hash,
                        "message": "Cast publicado exitosamente"
                    }
                else:
                    logger.warning(f"⚠️ Respuesta de Neynar no contiene cast_hash: {result}")
                    return {
                        "status": "success",
                        "cast_hash": None,
                        "message": "Cast publicado pero no se pudo obtener el hash"
                    }
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Error HTTP publicando cast: {e.response.status_code} - {e.response.text}")
                return {
                    "status": "error",
                    "cast_hash": None,
                    "message": f"Error HTTP {e.response.status_code}: {e.response.text[:200]}"
                }
            except Exception as exc:
                logger.error(f"Error publicando cast: {exc}", exc_info=True)
                return {
                    "status": "error",
                    "cast_hash": None,
                    "message": f"Error publicando cast: {str(exc)}"
                }
