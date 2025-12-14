"""Servicio para programar y publicar casts en Farcaster."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger(__name__)


class ScheduledCast:
    """Representa un cast programado."""
    
    def __init__(
        self,
        cast_id: str,
        user_address: str,
        user_fid: int,
        topic: str,
        cast_text: str,
        scheduled_time: datetime,
        payment_tx_hash: str,
        status: str = "scheduled"
    ):
        self.cast_id = cast_id
        self.user_address = user_address
        self.user_fid = user_fid
        self.topic = topic
        self.cast_text = cast_text
        self.scheduled_time = scheduled_time
        self.payment_tx_hash = payment_tx_hash
        self.status = status  # scheduled, published, cancelled, failed
        self.published_cast_hash: str | None = None
        self.xp_granted: int = 0
        self.created_at = datetime.now(timezone.utc)
        self.error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "cast_id": self.cast_id,
            "user_address": self.user_address,
            "user_fid": self.user_fid,
            "topic": self.topic,
            "cast_text": self.cast_text,
            "scheduled_time": self.scheduled_time.isoformat(),
            "payment_tx_hash": self.payment_tx_hash,
            "status": self.status,
            "published_cast_hash": self.published_cast_hash,
            "xp_granted": self.xp_granted,
            "created_at": self.created_at.isoformat(),
            "error_message": self.error_message
        }


class CastSchedulerService:
    """Maneja la programación y publicación de casts."""
    
    def __init__(self, farcaster_toolbox: Any, celo_toolbox: Any, registry_address: str) -> None:
        self.scheduler = AsyncIOScheduler()
        self.scheduled_casts: dict[str, ScheduledCast] = {}
        self.farcaster_toolbox = farcaster_toolbox
        self.celo_toolbox = celo_toolbox
        self.registry_address = registry_address
        self.campaign_id = "cast-generation"  # ID de campaña para XP
        
    def start(self):
        """Inicia el scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ CastSchedulerService iniciado")
    
    def shutdown(self):
        """Detiene el scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("✅ CastSchedulerService detenido")
    
    def schedule_cast(
        self,
        user_address: str,
        user_fid: int,
        topic: str,
        cast_text: str,
        scheduled_time: datetime | None,
        payment_tx_hash: str
    ) -> str:
        """Programa un cast para publicarse.
        
        Args:
            user_address: Dirección del usuario
            user_fid: FID del usuario en Farcaster
            topic: Tema del cast
            cast_text: Texto del cast a publicar
            scheduled_time: Fecha/hora programada (None = publicar ahora)
            payment_tx_hash: Hash de la transacción de pago
        
        Returns:
            cast_id: ID único del cast programado
        """
        cast_id = str(uuid.uuid4())
        
        # Si no hay scheduled_time, publicar ahora
        if scheduled_time is None:
            scheduled_time = datetime.now(timezone.utc)
        
        # Validar que no sea en el pasado
        if scheduled_time < datetime.now(timezone.utc):
            raise ValueError("No se puede programar un cast en el pasado")
        
        scheduled_cast = ScheduledCast(
            cast_id=cast_id,
            user_address=user_address,
            user_fid=user_fid,
            topic=topic,
            cast_text=cast_text,
            scheduled_time=scheduled_time,
            payment_tx_hash=payment_tx_hash
        )
        
        self.scheduled_casts[cast_id] = scheduled_cast
        
        # Programar publicación
        self.scheduler.add_job(
            self._publish_scheduled_cast,
            trigger=DateTrigger(run_date=scheduled_time),
            args=[cast_id],
            id=cast_id,
            replace_existing=True
        )
        
        logger.info(f"📅 Cast programado: {cast_id} para {scheduled_time}")
        
        return cast_id
    
    async def _publish_scheduled_cast(self, cast_id: str):
        """Publica un cast programado."""
        cast = self.scheduled_casts.get(cast_id)
        if not cast:
            logger.error(f"❌ Cast {cast_id} no encontrado")
            return
        
        if cast.status != "scheduled":
            logger.warning(f"⚠️ Cast {cast_id} ya no está en estado 'scheduled': {cast.status}")
            return
        
        try:
            # Publicar cast en Farcaster
            logger.info(f"📤 Publicando cast {cast_id} para FID {cast.user_fid}")
            
            # TODO: Implementar publicación real cuando tengamos la API
            # Por ahora, simulamos
            published_hash = await self._publish_cast_to_farcaster(
                user_fid=cast.user_fid,
                cast_text=cast.cast_text
            )
            
            if published_hash:
                cast.published_cast_hash = published_hash
                cast.status = "published"
                
                # Otorgar XP
                try:
                    self.celo_toolbox.grant_xp(
                        registry_address=self.registry_address,
                        campaign_id=self.campaign_id,
                        participant=cast.user_address,
                        amount=100  # XP por publicar
                    )
                    cast.xp_granted = 100
                    logger.info(f"✅ XP otorgado a {cast.user_address}")
                except Exception as e:
                    logger.error(f"❌ Error otorgando XP: {e}")
                
                logger.info(f"✅ Cast {cast_id} publicado exitosamente: {published_hash}")
            else:
                cast.status = "failed"
                cast.error_message = "No se pudo publicar el cast"
                logger.error(f"❌ Error publicando cast {cast_id}")
                
        except Exception as e:
            cast.status = "failed"
            cast.error_message = str(e)
            logger.error(f"❌ Error publicando cast {cast_id}: {e}", exc_info=True)
    
    async def _publish_cast_to_farcaster(self, user_fid: int, cast_text: str) -> str | None:
        """Publica un cast en Farcaster usando Neynar API.
        
        Returns:
            cast_hash: Hash del cast publicado, o None si falla
        """
        try:
            result = await self.farcaster_toolbox.publish_cast(
                user_fid=user_fid,
                cast_text=cast_text,
                parent_hash=None,
                signer_uuid=None  # Usará NEYNAR_SIGNER_UUID del backend si está configurado
            )
            
            if result.get("status") == "success":
                return result.get("cast_hash")
            else:
                logger.error(f"Error publicando cast: {result.get('message')}")
                return None
        except Exception as e:
            logger.error(f"Excepción publicando cast: {e}", exc_info=True)
            return None
    
    async def publish_now(
        self,
        user_address: str,
        user_fid: int,
        topic: str,
        cast_text: str,
        payment_tx_hash: str
    ) -> dict[str, Any]:
        """Publica un cast inmediatamente (sin programar).
        
        Returns:
            {
                "cast_id": str,
                "published_cast_hash": str | None,
                "xp_granted": int,
                "status": str
            }
        """
        cast_id = str(uuid.uuid4())
        
        try:
            # Publicar cast en Farcaster directamente (sin usar scheduler)
            logger.info(f"📤 Publicando cast {cast_id} inmediatamente para FID {user_fid}")
            
            published_hash = await self._publish_cast_to_farcaster(
                user_fid=user_fid,
                cast_text=cast_text
            )
            
            if published_hash:
                # Solo guardar el cast si se publicó exitosamente
                scheduled_cast = ScheduledCast(
                    cast_id=cast_id,
                    user_address=user_address,
                    user_fid=user_fid,
                    topic=topic,
                    cast_text=cast_text,
                    scheduled_time=datetime.now(timezone.utc),
                    payment_tx_hash=payment_tx_hash,
                    status="published"
                )
                scheduled_cast.published_cast_hash = published_hash
                
                self.scheduled_casts[cast_id] = scheduled_cast
                
                # Otorgar XP después de publicar exitosamente
                try:
                    tx_hash = self.celo_toolbox.grant_xp(
                        registry_address=self.registry_address,
                        campaign_id=self.campaign_id,
                        participant=user_address,
                        amount=100  # XP por publicar
                    )
                    scheduled_cast.xp_granted = 100
                    logger.info(f"✅ XP otorgado a {user_address} (tx: {tx_hash})")
                except Exception as e:
                    logger.error(f"❌ Error otorgando XP: {e}", exc_info=True)
                    # No fallar la publicación si el XP falla, pero registrar el error
                
                logger.info(f"✅ Cast {cast_id} publicado exitosamente: {published_hash}")
                
                return {
                    "cast_id": cast_id,
                    "published_cast_hash": published_hash,
                    "xp_granted": scheduled_cast.xp_granted,
                    "status": "published"
                }
            else:
                # No guardar el cast si falló la publicación
                error_message = "No se pudo publicar el cast en Farcaster"
                logger.error(f"❌ Error publicando cast {cast_id}: {error_message}")
                
                return {
                    "cast_id": cast_id,
                    "published_cast_hash": None,
                    "xp_granted": 0,
                    "status": "failed",
                    "error_message": error_message
                }
                
        except Exception as e:
            # No guardar el cast si falló la publicación
            error_message = str(e)
            logger.error(f"❌ Error publicando cast {cast_id}: {e}", exc_info=True)
            
            return {
                "cast_id": cast_id,
                "published_cast_hash": None,
                "xp_granted": 0,
                "status": "failed",
                "error_message": error_message
            }
    
    def cancel_cast(self, cast_id: str, user_address: str) -> bool:
        """Cancela un cast programado."""
        cast = self.scheduled_casts.get(cast_id)
        if not cast:
            return False
        
        if cast.user_address.lower() != user_address.lower():
            return False  # No es del usuario
        
        if cast.status != "scheduled":
            return False  # Ya no se puede cancelar
        
        # Remover del scheduler
        try:
            self.scheduler.remove_job(cast_id)
        except Exception:
            pass
        
        cast.status = "cancelled"
        logger.info(f"❌ Cast {cast_id} cancelado por usuario {user_address}")
        
        return True
    
    def get_user_scheduled_casts(self, user_address: str) -> list[dict[str, Any]]:
        """Obtiene todos los casts programados de un usuario."""
        user_casts = [
            cast.to_dict()
            for cast in self.scheduled_casts.values()
            if cast.user_address.lower() == user_address.lower()
        ]
        return sorted(user_casts, key=lambda x: x["scheduled_time"], reverse=True)
    
    def get_cast(self, cast_id: str) -> dict[str, Any] | None:
        """Obtiene un cast por su ID."""
        cast = self.scheduled_casts.get(cast_id)
        return cast.to_dict() if cast else None

