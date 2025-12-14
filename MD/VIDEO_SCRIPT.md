# 🎬 Script Comercial - Premio.xyz
## Duración: 60 segundos | Formato: Vertical (9:16) para Farcaster/Warpcast

---

## 📋 RESUMEN EJECUTIVO

**Título:** "Premio.xyz - Gana Recompensas Reales en Celo"
**Duración Total:** 60 segundos
**Formato:** Video vertical (1080x1920px) optimizado para Farcaster/Warpcast
**Estilo:** Dinámico, moderno, con animaciones y transiciones rápidas
**Música:** Upbeat, energética, sin copyright

---

## 🎭 ESTRUCTURA DEL VIDEO

### **ESCENA 1: HOOK (0-8s)**
**Objetivo:** Captar atención inmediata con un gancho visual impactante

**Visual:**
- Pantalla negra con texto animado apareciendo letra por letra
- Fondo con partículas doradas/púrpuras flotando
- Logo de Premio.xyz apareciendo con efecto de brillo

**Audio:**
- Música: Acorde dramático seguido de beat energético
- Voz: "¿Qué pasaría si cada post que haces pudiera ganarte recompensas reales?"

**Texto en pantalla:**
- "¿Cada post = Recompensas Reales?"

**JSON Prompt para VEED:**
```json
{
  "scene": 1,
  "duration": 8,
  "visual": {
    "background": "black",
    "effects": ["particle_gold_purple", "glow_logo"],
    "text_animation": "letter_by_letter",
    "text": "¿Cada post = Recompensas Reales?",
    "text_style": {
      "font": "bold sans-serif",
      "size": "large",
      "color": "#FCFF52",
      "position": "center",
      "animation": "fade_in_scale"
    },
    "logo": {
      "url": "https://celo-build-web-8rej.vercel.app/PremioxyzLogo.svg",
      "position": "top_center",
      "animation": "glow_pulse",
      "scale": 0.8
    }
  },
  "audio": {
    "music": "dramatic_chord_then_beat",
    "voiceover": "¿Qué pasaría si cada post que haces pudiera ganarte recompensas reales?",
    "voice_style": "energetic_male_spanish"
  },
  "transitions": {
    "in": "fade_from_black",
    "out": "zoom_to_next"
  }
}
```

---

{
  "scene": 1,
  "duration": 8,
  "visual": {
    "background": "black",
    "effects": ["particle_gold_purple", "glow_logo"],
    "text_animation": "letter_by_letter",
    "text": "¿Cada post = Recompensas Reales?",
    "text_style": {
      "font": "bold sans-serif",
      "size": "large",
      "color": "#FCFF52",
      "position": "center",
      "animation": "fade_in_scale"
    },
    "logo": {
      "url": "https://celo-build-web-8rej.vercel.app/PremioxyzLogo.svg",
      "position": "top_center",
      "animation": "glow_pulse",
      "scale": 0.8
    }
  },
  "audio": {
    "music": "dramatic_chord_then_beat",
    "voiceover": "¿Qué pasaría si cada post que haces pudiera ganarte recompensas reales?",
    "voice_style": "energetic_male_spanish"
  },
  "transitions": {
    "in": "fade_from_black",
    "out": "zoom_to_next"
  }
}
```

---

### **ESCENA 3: SOLUCIÓN (16-24s)**
**Objetivo:** Presentar Premio.xyz como la solución

**Visual:**
- Logo de Premio.xyz centrado con efecto de explosión de partículas
- Iconos flotando alrededor: NFT, cUSD, XP, Trophy
- Fondo con gradiente púrpura (#855DCD) a amarillo (#FCFF52)

**Audio:**
- Música: Aumenta la intensidad
- Voz: "Premio.xyz detecta tendencias virales y recompensa a los mejores creadores con NFT, cUSD y XP en Celo."

**Texto en pantalla:**
- "Premio.xyz"
- "Recompensas Reales en Celo"

**JSON Prompt para VEED:**
```json
{
  "scene": 3,
  "duration": 8,
  "visual": {
    "background": {
      "type": "gradient",
      "colors": ["#855DCD", "#FCFF52"],
      "direction": "diagonal"
    },
    "center_element": {
      "type": "logo",
      "url": "https://celo-build-web-8rej.vercel.app/PremioxyzLogo.svg",
      "animation": "explosion_particles",
      "scale": 1.2
    },
    "floating_icons": [
      {"icon": "nft", "position": "top_left", "animation": "float"},
      {"icon": "cusd", "position": "top_right", "animation": "float"},
      {"icon": "xp", "position": "bottom_left", "animation": "float"},
      {"icon": "trophy", "position": "bottom_right", "animation": "float"}
    ],
    "text": {
      "primary": "Premio.xyz",
      "secondary": "Recompensas Reales en Celo",
      "style": {
        "font": "bold",
        "size": "xlarge",
        "color": "#FFFFFF",
        "shadow": "glow_yellow"
      }
    }
  },
  "audio": {
    "music": "intensity_increases",
    "voiceover": "Premio.xyz detecta tendencias virales y recompensa a los mejores creadores con NFT, cUSD y XP en Celo.",
    "voice_style": "energetic_male_spanish"
  },
  "transitions": {
    "in": "slide_from_previous",
    "out": "zoom_out"
  }
}
```

---

### **ESCENA 4: CÓMO FUNCIONA - PARTE 1 (24-32s)**
**Objetivo:** Explicar el proceso de forma visual y rápida

**Visual:**
- Animación de 3 pasos en pantalla:
  1. Usuario postea en Farcaster (ícono de mensaje)
  2. Sistema detecta tendencia (ícono de radar/gráfico)
  3. Recompensa cae del cielo (NFT/cUSD/XP)

**Audio:**
- Música: Mantiene el ritmo
- Voz: "Es simple: postea contenido de calidad, el sistema detecta si es viral, y automáticamente recibes tu recompensa."

**Texto en pantalla:**
- "1. Postea"
- "2. Detecta"
- "3. Gana"

**JSON Prompt para VEED:**
```json
{
  "scene": 4,
  "duration": 8,
  "visual": {
    "layout": "three_steps_horizontal",
    "step_1": {
      "icon": "message_post",
      "label": "1. Postea",
      "animation": "pulse",
      "color": "#855DCD",
      "duration": 2.5
    },
    "step_2": {
      "icon": "radar_trend",
      "label": "2. Detecta",
      "animation": "scanning",
      "color": "#FCFF52",
      "duration": 2.5
    },
    "step_3": {
      "icon": "reward_falling",
      "label": "3. Gana",
      "animation": "falling_coins",
      "color": "#4ade80",
      "duration": 3
    },
    "connector": {
      "type": "arrow",
      "animation": "flow"
    },
    "background": "dark_purple"
  },
  "audio": {
    "music": "maintains_rhythm",
    "voiceover": "Es simple: postea contenido de calidad, el sistema detecta si es viral, y automáticamente recibes tu recompensa.",
    "voice_style": "energetic_male_spanish"
  },
  "transitions": {
    "in": "zoom_out_from_previous",
    "out": "slide_left"
  }
}
```

---

### **ESCENA 5: SISTEMA DE ENERGÍA (32-40s)**
**Objetivo:** Mostrar el sistema único de energía/rayos

**Visual:**
- 3 rayos de energía (⚡) apareciendo uno por uno
- Cada rayo se "consume" visualmente con efecto de chispa
- Contador mostrando "3/3" → "2/3" → "1/3"
- Texto explicando la recarga automática

**Audio:**
- Música: Continúa
- Voz: "Tienes 3 rayos de energía. Úsalos para reclamar recompensas. Se recargan automáticamente cada hora."

**Texto en pantalla:**
- "3 Rayos de Energía"
- "Se recargan cada hora"

**JSON Prompt para VEED:**
```json
{
  "scene": 5,
  "duration": 8,
  "visual": {
    "background": "dark_with_particles",
    "energy_bolts": {
      "count": 3,
      "layout": "horizontal_center",
      "animation": "appear_one_by_one",
      "bolt_style": {
        "icon": "lightning_bolt",
        "color_active": "#FCFF52",
        "color_consumed": "#666666",
        "glow": true
      },
      "counter": {
        "position": "below_bolts",
        "format": "X/3",
        "animation": "countdown",
        "color": "#FCFF52"
      }
    },
    "text": {
      "primary": "3 Rayos de Energía",
      "secondary": "Se recargan cada hora",
      "position": "top_center",
      "style": {
        "font": "bold",
        "size": "large",
        "color": "#FFFFFF"
      }
    },
    "effects": ["spark_on_consume", "glow_pulse"]
  },
  "audio": {
    "music": "continues",
    "voiceover": "Tienes 3 rayos de energía. Úsalos para reclamar recompensas. Se recargan automáticamente cada hora.",
    "voice_style": "energetic_male_spanish"
  },
  "transitions": {
    "in": "slide_left_from_previous",
    "out": "fade_to_next"
  }
}
```

---

### **ESCENA 6: TIPOS DE RECOMPENSAS (40-48s)**
**Objetivo:** Mostrar los diferentes tipos de recompensas disponibles

**Visual:**
- 3 cards apareciendo en secuencia:
  1. NFT (con imagen de NFT brillante)
  2. cUSD (con símbolo de dólar y número animado)
  3. XP (con barra de progreso llenándose)
- Cada card tiene un efecto de "shine" al aparecer

**Audio:**
- Música: Pico de intensidad
- Voz: "Gana NFT exclusivos, cUSD reales, o XP para subir en el leaderboard. Todo en la blockchain de Celo."

**Texto en pantalla:**
- "NFT Exclusivos"
- "cUSD Reales"
- "XP y Ranking"

**JSON Prompt para VEED:**
```json
{
  "scene": 6,
  "duration": 8,
  "visual": {
    "layout": "three_cards_vertical",
    "card_1": {
      "type": "nft",
      "title": "NFT Exclusivos",
      "icon": "nft_glowing",
      "color": "#855DCD",
      "animation": "slide_in_from_left",
      "effect": "shine",
      "duration": 2.5
    },
    "card_2": {
      "type": "cusd",
      "title": "cUSD Reales",
      "icon": "dollar_animated",
      "color": "#4ade80",
      "animation": "slide_in_from_bottom",
      "effect": "shine",
      "duration": 2.5
    },
    "card_3": {
      "type": "xp",
      "title": "XP y Ranking",
      "icon": "progress_bar",
      "color": "#FCFF52",
      "animation": "slide_in_from_right",
      "effect": "shine",
      "duration": 3
    },
    "background": "gradient_purple_to_yellow"
  },
  "audio": {
    "music": "intensity_peak",
    "voiceover": "Gana NFT exclusivos, cUSD reales, o XP para subir en el leaderboard. Todo en la blockchain de Celo.",
    "voice_style": "energetic_male_spanish"
  },
  "transitions": {
    "in": "fade_from_previous",
    "out": "zoom_in"
  }
}
```

---

### **ESCENA 7: CALL TO ACTION (48-56s)**
**Objetivo:** Motivar a la acción con un CTA claro y urgente

**Visual:**
- Botón grande pulsante con texto "Únete Ahora"
- QR code apareciendo a la derecha (opcional)
- Logo de Premio.xyz y Celo apareciendo en la parte inferior
- Efectos de partículas doradas cayendo

**Audio:**
- Música: Mantiene energía pero prepara para cierre
- Voz: "No esperes más. Conecta tu wallet de Celo y comienza a ganar recompensas reales por tu contenido."

**Texto en pantalla:**
- "Únete Ahora"
- "Gana Recompensas Reales"
- "premio.xyz"

**JSON Prompt para VEED:**
```json
{
  "scene": 7,
  "duration": 8,
  "visual": {
    "background": "dark_with_golden_particles",
    "cta_button": {
      "text": "Únete Ahora",
      "position": "center",
      "style": {
        "background": "gradient_purple_to_yellow",
        "border": "glow_yellow",
        "size": "xlarge",
        "animation": "pulse_glow"
      }
    },
    "secondary_text": {
      "text": "Gana Recompensas Reales",
      "position": "above_button",
      "style": {
        "font": "bold",
        "size": "large",
        "color": "#FCFF52"
      }
    },
    "logo": {
      "url": "https://celo-build-web-8rej.vercel.app/PremioxyzLogo.svg",
      "position": "bottom_center",
      "scale": 0.6
    },
    "url": {
      "text": "premio.xyz",
      "position": "below_logo",
      "style": {
        "font": "monospace",
        "color": "#FFFFFF"
      }
    },
    "qr_code": {
      "position": "bottom_right",
      "scale": 0.3,
      "animation": "fade_in"
    },
    "effects": ["golden_particles_falling", "glow_ambient"]
  },
  "audio": {
    "music": "maintains_energy_closing",
    "voiceover": "No esperes más. Conecta tu wallet de Celo y comienza a ganar recompensas reales por tu contenido.",
    "voice_style": "energetic_male_spanish"
  },
  "transitions": {
    "in": "zoom_in_from_previous",
    "out": "fade_to_final"
  }
}
```

---

### **ESCENA 8: CIERRE Y BRANDING (56-60s)**
**Objetivo:** Reforzar la marca y dejar el mensaje final

**Visual:**
- Logo de Premio.xyz centrado con efecto de zoom final
- Tagline apareciendo debajo
- Fondo con gradiente púrpura brillante
- Efecto de "explosión de estrellas" al final

**Audio:**
- Música: Cierre dramático con acorde final
- Voz: "Premio.xyz. Donde tu contenido vale."

**Texto en pantalla:**
- "Premio.xyz"
- "Donde tu contenido vale"
- "Built on Celo"

**JSON Prompt para VEED:**
```json
{
  "scene": 8,
  "duration": 4,
  "visual": {
    "background": {
      "type": "gradient",
      "colors": ["#855DCD", "#1a0b2e"],
      "animation": "pulse"
    },
    "logo": {
      "url": "https://celo-build-web-8rej.vercel.app/PremioxyzLogo.svg",
      "position": "center",
      "animation": "zoom_final",
      "scale": 1.5,
      "effect": "glow_intense"
    },
    "tagline": {
      "text": "Donde tu contenido vale",
      "position": "below_logo",
      "style": {
        "font": "elegant",
        "size": "large",
        "color": "#FCFF52",
        "animation": "fade_in_up"
      }
    },
    "subtitle": {
      "text": "Built on Celo",
      "position": "bottom",
      "style": {
        "font": "small",
        "color": "#94a3b8"
      }
    },
    "effects": ["star_explosion", "glow_ambient_intense"]
  },
  "audio": {
    "music": "dramatic_close_chord",
    "voiceover": "Premio.xyz. Donde tu contenido vale.",
    "voice_style": "energetic_male_spanish",
    "echo": true
  },
  "transitions": {
    "in": "fade_from_previous",
    "out": "fade_to_black"
  }
}
```

---

## 🎨 ESPECIFICACIONES TÉCNICAS

### **Resolución y Formato:**
- **Resolución:** 1080x1920px (9:16 vertical)
- **Frame Rate:** 30fps
- **Formato:** MP4 (H.264)
- **Bitrate:** 8-10 Mbps

### **Paleta de Colores:**
- **Primario:** Púrpura #855DCD
- **Secundario:** Amarillo #FCFF52
- **Acento:** Verde #4ade80
- **Fondo:** Negro #0f172a / Púrpura oscuro #1a0b2e
- **Texto:** Blanco #FFFFFF

### **Tipografía:**
- **Títulos:** Bold Sans-serif (Inter Bold / Montserrat Bold)
- **Cuerpo:** Regular Sans-serif (Inter / Roboto)
- **Monospace:** Para URLs y números (JetBrains Mono)

### **Efectos Visuales:**
- Partículas doradas/púrpuras
- Glows y brillos
- Transiciones suaves (fade, slide, zoom)
- Animaciones de pulso
- Efectos de "shine" en elementos importantes

### **Música:**
- **Estilo:** Upbeat, energético, moderno
- **Duración:** 60 segundos exactos
- **Sin copyright:** Usar librería de música libre (Epidemic Sound, Artlist, etc.)
- **Sugerencia:** "Upbeat Corporate" o "Tech Startup" genre

### **Voz en Off:**
- **Idioma:** Español (latinoamericano neutro)
- **Género:** Masculino o Femenino (preferencia: masculino energético)
- **Tono:** Entusiasta, claro, profesional
- **Velocidad:** Moderada (no muy rápida, para que se entienda)

---

## 📝 NOTAS ADICIONALES PARA PRODUCCIÓN

### **Elementos Visuales Necesarios:**
1. Logo de Premio.xyz: https://celo-build-web-8rej.vercel.app/PremioxyzLogo.svg (SVG vectorial)
2. Iconos: NFT, cUSD, XP, Trophy, Lightning Bolt, Message, Radar
3. Screenshots de la app (opcional pero recomendado)
4. Animaciones de partículas
5. Gradientes de fondo

### **Textos Alternativos (si se necesita variación):**
- "Crea. Gana. Repite."
- "Tu contenido, tus recompensas."
- "La primera plataforma que paga por contenido viral en Farcaster."

### **Optimización para Redes Sociales:**
- **Farcaster/Warpcast:** Formato vertical 9:16
- **Twitter/X:** Puede usarse el mismo formato o crear versión horizontal
- **Instagram Reels/TikTok:** Mismo formato vertical
- **YouTube Shorts:** Mismo formato vertical

### **Call to Action Final:**
- URL: `premio.xyz` o `celo-build-web-8rej.vercel.app`
- QR Code: Apuntando a la URL de la app
- Texto: "Conecta tu wallet y comienza ahora"

---

## 🎯 OBJETIVOS DEL VIDEO

1. **Awareness:** Dar a conocer Premio.xyz a la comunidad de Farcaster
2. **Educación:** Explicar cómo funciona el sistema de recompensas
3. **Conversión:** Motivar a usuarios a conectar su wallet y usar la app
4. **Retención:** Mostrar el sistema de energía para que vuelvan cada hora

---

## 📊 MÉTRICAS DE ÉXITO ESPERADAS

- **Vistas:** Objetivo 10K+ en primera semana
- **Engagement:** 5%+ tasa de clics en CTA
- **Conversiones:** 2-3% de usuarios que conectan wallet
- **Shares:** Alto número de compartidos en Farcaster

---

## 🔄 VARIACIONES SUGERIDAS

### **Versión Corta (30s):**
- Escenas 1, 3, 6, 7, 8 (solo las más impactantes)

### **Versión Larga (90s):**
- Agregar escena de testimonios/ejemplos reales
- Mostrar leaderboard
- Explicar más detalles del sistema de scoring

---

**Creado para:** Premio.xyz / Celo Build  
**Fecha:** Diciembre 2024  
**Versión:** 1.0

