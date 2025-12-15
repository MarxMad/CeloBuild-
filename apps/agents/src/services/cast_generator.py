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

    async def generate_cast(self, topic: str, user_context: dict[str, Any] | None = None, language: str = "es") -> dict[str, Any]:
        """Genera un cast usando Gemini basado en el tema.
        
        Args:
            topic: Tema del cast (tech, musica, motivacion, chistes, frases_celebres)
            user_context: Contexto opcional del usuario (username, fid, etc.)
            language: Idioma para generar el cast ('es' para español, 'en' para inglés)
        
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
            return self._generate_fallback_cast(topic, topic_info, language)
        
        # Generar prompt según el tema e idioma
        prompt_template = self._get_prompt_for_topic(topic, topic_info, language)
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
            
            # Remover emojis si los hay (por seguridad)
            import re
            # Patrón para emojis comunes
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F680-\U0001F6FF"  # transport & map symbols
                "\U0001F1E0-\U0001F1FF"  # flags (iOS)
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE
            )
            cast_text = emoji_pattern.sub('', cast_text).strip()
            
            # Validar y ajustar longitud (objetivo: ~100 caracteres)
            if len(cast_text) > 150:
                # Si excede, cortar en un punto lógico (espacio o punto)
                cast_text = cast_text[:150]
                # Intentar cortar en el último espacio antes de 100
                last_space = cast_text.rfind(' ')
                if last_space > 80:  # Si hay un espacio razonable cerca del final
                    cast_text = cast_text[:last_space]
                else:
                    cast_text = cast_text[:150] + "..."
            elif len(cast_text) < 80:
                # Si es muy corto, loguear pero aceptar
                logger.warning(f"⚠️ Cast generado muy corto ({len(cast_text)} caracteres), pero se acepta")
            
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
            return self._generate_fallback_cast(topic, topic_info, language)
        except Exception as e:
            logger.error(f"❌ Error generando cast con Gemini: {e}")
            return self._generate_fallback_cast(topic, topic_info, language)

    def _get_prompt_for_topic(self, topic: str, topic_info: dict[str, Any], language: str = "es") -> str:
        """Genera el prompt específico para cada tema en el idioma indicado."""
        
        if language == "en":
            base_prompt = """You are an expert at creating viral content for Farcaster.
Generate a unique, authentic, and engaging cast about the topic: {topic_name} ({topic_description}).

CRITICAL REQUIREMENTS:
- EXACTLY between 90-150 characters (target: ~150 characters)
- DO NOT use emojis of any kind
- DO NOT use hashtags
- The tone should be natural and conversational
- Must be concise but engaging
- Must invite interaction (likes, replies, recasts)
- Use all available space (90-150 characters)

Respond ONLY with the cast text, no additional explanations, no emojis, no hashtags.
The text must be exactly between 90-150 characters.
"""
            
            topic_prompts = {
                "tech": """Focus on technology, blockchain, Web3, AI, innovation.
You can mention: Celo, MiniPay, DeFi, NFTs, smart contracts, but in a natural way.
Example tone: Blockchain technology is changing the world. What's your favorite Web3 project?""",
                
                "musica": """Focus on music, artists, songs, playlists.
You can mention: genres, artists, concerts, but in a natural way.
Example tone: Music is the universal language. What song inspires you today?""",
                
                "motivacion": """Focus on motivation, personal growth, self-improvement.
You can include inspiring but authentic phrases.
Example tone: Each day is a new opportunity to grow. What's your goal today?""",
                
                "chistes": """Focus on humor, memes, jokes, fun content.
Must be funny but appropriate for Farcaster.
Example tone: Why do programmers prefer dark mode? Because light attracts bugs.""",
                
                "frases_celebres": """Focus on inspiring quotes from famous people.
You can adapt or paraphrase famous quotes in a modern way.
Example tone: The only way to do great work is to love what you do - Steve Jobs. What quote do you identify with?"""
            }
        else:  # Spanish (default)
            base_prompt = """Eres un experto en crear contenido viral para Farcaster.
Genera un cast único, auténtico y engaging sobre el tema: {topic_name} ({topic_description}).

Requisitos CRÍTICOS:
- EXACTAMENTE entre 90-150 caracteres (objetivo: ~150 caracteres)
- NO uses emojis de ninguna clase
- NO uses hashtags
- El tono debe ser natural y conversacional
- Debe ser conciso pero engaging
- Debe invitar a la interacción (likes, replies, recasts)
- Aprovecha todo el espacio disponible (90-150 caracteres)

Responde SOLO con el texto del cast, sin explicaciones adicionales, sin emojis, sin hashtags.
El texto debe tener entre 90-150 caracteres exactamente.
"""
            
            topic_prompts = {
                "tech": """Enfócate en tecnología, blockchain, Web3, IA, innovación.
Puedes mencionar: Celo, MiniPay, DeFi, NFTs, smart contracts, pero de forma natural.
Ejemplo de tono: La tecnología blockchain está cambiando el mundo. ¿Cuál es tu proyecto Web3 favorito?""",
                
                "musica": """Enfócate en música, artistas, canciones, playlists.
Puedes mencionar: géneros, artistas, conciertos, pero de forma natural.
Ejemplo de tono: La música es el lenguaje universal. ¿Qué canción te inspira hoy?""",
                
                "motivacion": """Enfócate en motivación, superación personal, crecimiento.
Puedes incluir frases inspiradoras pero auténticas.
Ejemplo de tono: Cada día es una nueva oportunidad para crecer. ¿Cuál es tu meta de hoy?""",
                
                "chistes": """Enfócate en humor, memes, chistes, contenido divertido.
Debe ser gracioso pero apropiado para Farcaster.
Ejemplo de tono: ¿Por qué los programadores prefieren el modo oscuro? Porque la luz atrae bugs.""",
                
                "frases_celebres": """Enfócate en citas inspiradoras de personajes famosos.
Puedes adaptar o parafrasear frases célebres de forma moderna.
Ejemplo de tono: El único modo de hacer un gran trabajo es amar lo que haces - Steve Jobs. ¿Con qué frase te identificas?"""
            }
        
        specific_prompt = topic_prompts.get(topic, "")
        
        return base_prompt + "\n" + specific_prompt

    def _generate_fallback_cast(self, topic: str, topic_info: dict[str, Any], language: str = "es") -> dict[str, Any]:
        """Genera un cast de fallback cuando Gemini no está disponible."""
        
        if language == "en":
            fallback_casts = {
                "tech": "Blockchain technology is revolutionizing the world. What's your favorite Web3 project?",
                "musica": "Music is the language of the soul. What song inspires you today?",
                "motivacion": "Each day is a new opportunity to grow and improve. What's your goal?",
                "chistes": "Did you know programmers prefer dark mode? Because light attracts bugs.",
                "frases_celebres": "The only way to do great work is to love what you do. - Steve Jobs"
            }
        else:  # Spanish (default)
            fallback_casts = {
                "tech": "La tecnología blockchain está revolucionando el mundo. ¿Cuál es tu proyecto Web3 favorito?",
                "musica": "La música es el lenguaje del alma. ¿Qué canción te inspira hoy?",
                "motivacion": "Cada día es una nueva oportunidad para crecer y mejorar. ¿Cuál es tu meta?",
                "chistes": "¿Sabías que los programadores prefieren el modo oscuro? Porque la luz atrae bugs.",
                "frases_celebres": "El único modo de hacer un gran trabajo es amar lo que haces. - Steve Jobs"
            }
        
        cast_text = fallback_casts.get(topic, fallback_casts["tech"])
        
        # Asegurar que no exceda 100 caracteres
        if len(cast_text) > 150:
            cast_text = cast_text[:150] + "..."
        
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

