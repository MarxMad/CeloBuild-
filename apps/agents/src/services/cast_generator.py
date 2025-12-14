"""Servicio para generar casts usando IA (Gemini API)."""
import logging
import json
from typing import Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import Settings

logger = logging.getLogger(__name__)

# Temas disponibles
TOPICS = {
    "tech": {
        "name": "Tech",
        "description": "Tecnología, blockchain, Web3, IA, innovación",
        "emoji": "💻"
    },
    "musica": {
        "name": "Música",
        "description": "Música, artistas, canciones, playlists",
        "emoji": "🎵"
    },
    "motivacion": {
        "name": "Motivación",
        "description": "Frases motivacionales, superación personal, crecimiento",
        "emoji": "🚀"
    },
    "chistes": {
        "name": "Chistes",
        "description": "Humor, memes, chistes, contenido divertido",
        "emoji": "😂"
    },
    "frases_celebres": {
        "name": "Frases Célebres",
        "description": "Citas inspiradoras de personajes famosos",
        "emoji": "💬"
    }
}


class CastGeneratorService:
    """Genera casts usando Gemini API basado en temas."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.google_api_key = settings.google_api_key
        self.llm = None
        
        if self.google_api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-lite",
                    google_api_key=self.google_api_key,
                    temperature=0.8,  # Más creativo para casts
                )
                logger.info("✅ CastGeneratorService inicializado con Gemini")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo inicializar Gemini para CastGenerator: {e}")
        else:
            logger.warning("⚠️ GOOGLE_API_KEY no configurada, CastGenerator funcionará en modo fallback")

    async def generate_cast(self, topic: str, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Genera un cast usando Gemini basado en el tema.
        
        Args:
            topic: Tema del cast (tech, musica, motivacion, chistes, frases_celebres)
            user_context: Contexto opcional del usuario (username, fid, etc.)
        
        Returns:
            {
                "cast_text": str,  # Texto del cast generado
                "topic": str,
                "topic_name": str,
                "emoji": str,
                "generated": bool  # True si se generó con IA, False si es fallback
            }
        """
        # Validar tema
        if topic not in TOPICS:
            logger.warning(f"⚠️ Tema '{topic}' no válido, usando 'tech' por defecto")
            topic = "tech"
        
        topic_info = TOPICS[topic]
        
        # Si no hay LLM, retornar fallback
        if not self.llm:
            return self._generate_fallback_cast(topic, topic_info)
        
        # Generar prompt según el tema
        prompt_template = self._get_prompt_for_topic(topic, topic_info)
        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Contexto del usuario (opcional)
        user_name = user_context.get("username", "usuario") if user_context else "usuario"
        
        chain = prompt | self.llm
        
        try:
            import asyncio
            result = await asyncio.wait_for(
                chain.ainvoke({
                    "topic_name": topic_info["name"],
                    "topic_description": topic_info["description"],
                    "emoji": topic_info["emoji"],
                    "user_name": user_name
                }),
                timeout=10.0
            )
            
            # Limpiar markdown si Gemini lo incluye
            content = result.content.strip()
            content = content.replace("```", "").strip()
            
            # Si el contenido está en JSON, extraer el campo "cast"
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "cast" in parsed:
                    cast_text = parsed["cast"]
                elif isinstance(parsed, str):
                    cast_text = parsed
                else:
                    cast_text = content
            except json.JSONDecodeError:
                cast_text = content
            
            # Validar longitud (Farcaster tiene límite de 320 caracteres)
            if len(cast_text) > 320:
                cast_text = cast_text[:317] + "..."
            
            logger.info(f"✅ Cast generado para tema '{topic}': {cast_text[:50]}...")
            
            return {
                "cast_text": cast_text,
                "topic": topic,
                "topic_name": topic_info["name"],
                "emoji": topic_info["emoji"],
                "generated": True
            }
            
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Timeout generando cast para tema '{topic}', usando fallback")
            return self._generate_fallback_cast(topic, topic_info)
        except Exception as e:
            logger.error(f"❌ Error generando cast con Gemini: {e}")
            return self._generate_fallback_cast(topic, topic_info)

    def _get_prompt_for_topic(self, topic: str, topic_info: dict[str, Any]) -> str:
        """Genera el prompt específico para cada tema."""
        
        base_prompt = """Eres un experto en crear contenido viral para Farcaster.
Genera un cast único, auténtico y engaging sobre el tema: {topic_name} ({topic_description}).

Requisitos:
- Máximo 280 caracteres (Farcaster tiene límite de 320, pero 280 es ideal)
- Debe ser engaging y auténtico
- Incluye emojis relevantes ({emoji})
- NO uses hashtags a menos que sea absolutamente necesario
- El tono debe ser natural y conversacional
- Debe invitar a la interacción (likes, replies, recasts)

Responde SOLO con el texto del cast, sin explicaciones adicionales.
"""
        
        # Prompts específicos por tema
        topic_prompts = {
            "tech": """Enfócate en tecnología, blockchain, Web3, IA, innovación.
Puedes mencionar: Celo, MiniPay, DeFi, NFTs, smart contracts, pero de forma natural.
Ejemplo de tono: La tecnología blockchain está cambiando el mundo 🌍 ¿Cuál es tu proyecto Web3 favorito?""",
            
            "musica": """Enfócate en música, artistas, canciones, playlists.
Puedes mencionar: géneros, artistas, conciertos, pero de forma natural.
Ejemplo de tono: La música es el lenguaje universal 🎵 ¿Qué canción te inspira hoy?""",
            
            "motivacion": """Enfócate en motivación, superación personal, crecimiento.
Puedes incluir frases inspiradoras pero auténticas.
Ejemplo de tono: Cada día es una nueva oportunidad para crecer 🚀 ¿Cuál es tu meta de hoy?""",
            
            "chistes": """Enfócate en humor, memes, chistes, contenido divertido.
Debe ser gracioso pero apropiado para Farcaster.
Ejemplo de tono: ¿Por qué los programadores prefieren el modo oscuro? Porque la luz atrae bugs 🐛😂""",
            
            "frases_celebres": """Enfócate en citas inspiradoras de personajes famosos.
Puedes adaptar o parafrasear frases célebres de forma moderna.
Ejemplo de tono: El único modo de hacer un gran trabajo es amar lo que haces - Steve Jobs 💬 ¿Con qué frase te identificas?"""
        }
        
        specific_prompt = topic_prompts.get(topic, "")
        
        return base_prompt + "\n" + specific_prompt

    def _generate_fallback_cast(self, topic: str, topic_info: dict[str, Any]) -> dict[str, Any]:
        """Genera un cast de fallback cuando Gemini no está disponible."""
        
        fallback_casts = {
            "tech": "🚀 La tecnología blockchain está revolucionando el mundo. ¿Cuál es tu proyecto Web3 favorito? #Web3 #Blockchain",
            "musica": "🎵 La música es el lenguaje del alma. ¿Qué canción te inspira hoy? #Música",
            "motivacion": "💪 Cada día es una nueva oportunidad para crecer y mejorar. ¿Cuál es tu meta de hoy? #Motivación",
            "chistes": "😂 ¿Sabías que los programadores prefieren el modo oscuro? ¡Porque la luz atrae bugs! #Humor #Tech",
            "frases_celebres": "💬 El único modo de hacer un gran trabajo es amar lo que haces. - Steve Jobs #Inspiración"
        }
        
        cast_text = fallback_casts.get(topic, fallback_casts["tech"])
        
        return {
            "cast_text": cast_text,
            "topic": topic,
            "topic_name": topic_info["name"],
            "emoji": topic_info["emoji"],
            "generated": False
        }

    @staticmethod
    def get_available_topics() -> dict[str, dict[str, Any]]:
        """Retorna todos los temas disponibles."""
        return TOPICS

