import base64
import io
import logging
import random
from typing import Any, Optional

from PIL import Image, ImageDraw, ImageFont
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import Settings

logger = logging.getLogger(__name__)

class ArtGenerator:
    """Genera arte y metadatos para NFTs estilo Yu-Gi-Oh usando Gemini y PIL."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.google_api_key = settings.google_api_key
        self.llm = None
        if self.google_api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
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
                "prompt": f"Cyberpunk style digital art representing: {cast_text[:50]}..."
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
                "- type: Monster, Spell, Trap, Artifact\n"
                "- prompt: Un prompt detallado para generar la imagen de la carta con IA (en inglés, estilo cyberpunk/fantasy)"
            )
        )

        try:
            result = await self.llm.ainvoke({"text": cast_text, "author": author})
            # Limpiar markdown si Gemini lo incluye
            content = result.content.replace("```json", "").replace("```", "").strip()
            import json
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error generando metadata con AI: {e}")
            return {
                "title": f"Artifact of {author}",
                "description": "A mysterious artifact from the decentralized web.",
                "rarity": "Rare",
                "type": "Artifact",
                "prompt": "Abstract digital art, blockchain nodes connecting, glowing neon lines, dark background"
            }

    def generate_image(self, prompt: str) -> Image.Image:
        """
        Genera una imagen basada en el prompt.
        Nota: Como no tenemos acceso garantizado a Imagen API, generaremos
        una imagen abstracta procedural con PIL basada en el hash del prompt.
        """
        # En el futuro: Integrar llamada a DALL-E o Gemini Imagen aquí
        
        # Generar imagen abstracta procedural
        width, height = 400, 400
        image = Image.new('RGB', (width, height), color='black')
        draw = ImageDraw.Draw(image)
        
        # Seed basado en el prompt para consistencia
        random.seed(prompt)
        
        # Dibujar patrones abstractos
        for _ in range(50):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            color = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )
            width_line = random.randint(1, 5)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=width_line)
            
            if random.random() > 0.8:
                radius = random.randint(10, 50)
                draw.ellipse(
                    [(x1-radius, y1-radius), (x1+radius, y1+radius)],
                    outline=color,
                    width=2
                )

        return image

    def compose_card(self, art_image: Image.Image, metadata: dict[str, Any]) -> str:
        """
        Compone la carta final estilo Yu-Gi-Oh y retorna la imagen en base64.
        """
        # Dimensiones de carta estándar (proporción 59:86)
        card_w, card_h = 590, 860
        card = Image.new('RGB', (card_w, card_h), color='#1a1a1a')
        draw = ImageDraw.Draw(card)

        # Colores según rareza
        rarity_colors = {
            "Common": "#A0A0A0",
            "Rare": "#0070DD",
            "Epic": "#A335EE",
            "Legendary": "#FF8000"
        }
        border_color = rarity_colors.get(metadata.get("rarity", "Common"), "#A0A0A0")

        # Marco
        draw.rectangle([(20, 20), (card_w-20, card_h-20)], outline=border_color, width=10)
        
        # Título
        try:
            # Intentar cargar fuente default o usar básica
            font_title = ImageFont.truetype("Arial", 40)
        except:
            font_title = ImageFont.load_default()
            
        draw.text((40, 40), metadata.get("title", "Unknown Card"), fill=border_color, font=font_title)

        # Imagen de Arte (centrada)
        art_resized = art_image.resize((510, 510))
        card.paste(art_resized, (40, 100))

        # Caja de descripción
        draw.rectangle([(40, 630), (card_w-40, card_h-40)], outline=border_color, width=3)
        
        # Tipo y Rareza
        draw.text((50, 640), f"[{metadata.get('type', 'Monster')}] - {metadata.get('rarity', 'Common')}", fill="white")
        
        # Descripción (simple wrap manual)
        desc = metadata.get("description", "")
        words = desc.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 40: # Aprox chars per line
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        y_text = 680
        for line in lines:
            draw.text((50, y_text), line, fill="white")
            y_text += 25

        # Convertir a base64
        buffered = io.BytesIO()
        card.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
