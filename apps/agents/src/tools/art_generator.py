import logging
import urllib.parse
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import Settings

logger = logging.getLogger(__name__)

class ArtGenerator:
    """Genera metadatos para NFTs y construye la URL de la imagen dinámica."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.google_api_key = settings.google_api_key
        self.llm = None
        if self.google_api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-lite", # Use specific version requested by user
                    google_api_key=self.google_api_key,
                    temperature=0.7,
                )
            except Exception as e:
                logger.warning(f"No se pudo inicializar Gemini para ArtGenerator: {e}")

    async def generate_card_metadata(self, cast_text: str, author: str) -> dict[str, Any]:
        """Genera título, descripción, rareza y tipo para la carta."""
        if not self.llm:
            return {
                "title": f"Loot of {author}",
                "description": f"A legendary moment captured from {author}'s cast.",
                "rarity": "Common",
                "type": "Spell Caster",
            }

        prompt = ChatPromptTemplate.from_template(
            (
                "Eres un diseñador de juegos de cartas estilo Yu-Gi-Oh / Magic. "
                "Genera los metadatos para una carta basada en este cast de Farcaster.\n\n"
                "Cast: {text}\nAutor: {author}\n\n"
                "Responde SOLO con un JSON válido con estos campos:\n"
                "- title: Título épico y corto (max 25 chars)\n"
                "- description: Lore de la carta (max 100 chars)\n"
                "- rarity: Common, Rare, Epic, Legendary (basado en el texto)\n"
                "- type: Monster, Spell, Trap, Artifact"
            )
        )

        # Chain the prompt and the LLM
        chain = prompt | self.llm

        import asyncio
        # OPTIMIZATION: Fail fast if Gemini is overloaded to keep UX fast
        max_retries = 1 
        
        for attempt in range(max_retries):
            try:
                # Timeout corto para no bloquear
                result = await asyncio.wait_for(chain.ainvoke({"text": cast_text, "author": author}), timeout=5.0)
                
                # Limpiar markdown si Gemini lo incluye
                content = result.content.replace("```json", "").replace("```", "").strip()
                import json
                return json.loads(content)
            except Exception as e:
                logger.warning(f"Gemini AI falló o tardó mucho (intento {attempt+1}): {e}")
                # Fallback inmediato a metadata estática
                return {
                    "title": f"Loot of {author}",
                    "description": f"A legendary moment captured from {author}'s cast.",
                    "rarity": "Common",
                    "type": "Spell Caster",
                }

    def generate_image(self, prompt: str) -> Any:
        """
        Deprecado: Ya no generamos imágenes en el backend.
        Retorna None para mantener compatibilidad si es necesario.
        """
        return None

    def compose_card(self, art_image: Any, metadata: dict[str, Any]) -> str:
        """
        Construye la URL de la imagen dinámica servida por el frontend.
        """
        # Base URL del frontend (debería venir de settings, pero usamos fallback)
        # En producción, esto debe ser la URL real de la app
        frontend_url = "https://celo-build-web-8rej.vercel.app"
        
        title = metadata.get("title", "Unknown Artifact")
        rarity = metadata.get("rarity", "Common")
        card_type = metadata.get("type", "Item")
        
        # Codificar parámetros
        params = urllib.parse.urlencode({
            "title": title,
            "rarity": rarity,
            "type": card_type,
            "description": metadata.get("description", "A mysterious artifact."),
            "v": "3" # Force cache bust for new assets
        })
        
        return f"{frontend_url}/api/nft-image?{params}"
