# 🤖 Mejoras con AI para EligibilityAgent

## 📋 Resumen

El `EligibilityAgent` actualmente usa solo datos estructurados y fórmulas matemáticas. Aquí proponemos **5 mejoras concretas** usando Gemini AI que agregarían valor real:

---

## 🎯 Mejora 1: Validación de Relevancia de Casts Relacionados

### Problema Actual
- Busca casts relacionados usando solo keywords simples (`topic_tags`)
- No entiende si los casts realmente están relacionados con el tema de la tendencia
- Puede incluir casts irrelevantes que solo mencionan las keywords

### Solución con AI
**Usar Gemini para validar si los casts relacionados realmente están relacionados con el tema**

```python
async def _validate_cast_relevance_with_ai(
    self, 
    cast_text: str, 
    trend_context: dict[str, Any]
) -> dict[str, Any]:
    """Valida si un cast está realmente relacionado con la tendencia usando AI."""
    
    llm = self._get_llm()
    if not llm:
        return {"relevant": True, "confidence": 0.5, "reason": "AI no disponible"}
    
    prompt = ChatPromptTemplate.from_template(
        """Eres un experto en análisis de contenido social.
        
        Tarea: Determina si este cast está realmente relacionado con la tendencia detectada.
        
        Tendencia detectada:
        - Texto: {trend_text}
        - Análisis: {trend_analysis}
        - Tags: {trend_tags}
        
        Cast del usuario a evaluar:
        - Texto: {cast_text}
        
        Responde en formato JSON:
        {{
            "relevant": true/false,
            "confidence": 0.0-1.0,
            "reason": "explicación breve"
        }}
        """
    )
    
    chain = prompt | llm
    try:
        result = await chain.ainvoke({
            "trend_text": trend_context.get("source_text", ""),
            "trend_analysis": trend_context.get("ai_analysis", ""),
            "trend_tags": ", ".join(trend_context.get("topic_tags", [])),
            "cast_text": cast_text,
        })
        
        # Parsear respuesta JSON
        import json
        analysis = json.loads(result.content)
        return analysis
    except Exception as exc:
        logger.warning("Error validando relevancia con AI: %s", exc)
        return {"relevant": True, "confidence": 0.5, "reason": "fallback"}
```

**Beneficio**: Solo cuenta casts realmente relevantes, mejorando la precisión del engagement.

---

## 🎯 Mejora 2: Análisis de Calidad de Participación

### Problema Actual
- Trata todos los likes/recasts/replies igual
- No distingue entre participación genuina y spam
- No detecta patrones sospechosos (bot behavior)

### Solución con AI
**Usar Gemini para analizar la calidad y autenticidad de la participación**

```python
async def _analyze_participation_quality_with_ai(
    self,
    user_participation: dict[str, Any],
    trend_context: dict[str, Any]
) -> dict[str, Any]:
    """Analiza la calidad de la participación del usuario usando AI."""
    
    llm = self._get_llm()
    if not llm:
        return {"quality_score": 0.5, "is_genuine": True, "flags": []}
    
    # Construir contexto de participación
    participation_summary = f"""
    Usuario: {user_participation.get('username', 'unknown')}
    - Participó directamente: {user_participation.get('directly_participated', False)}
    - Engagement total: {user_participation.get('total_engagement', 0)}
    - Casts relacionados: {len(user_participation.get('related_casts', []))}
    """
    
    prompt = ChatPromptTemplate.from_template(
        """Eres un experto en detección de engagement genuino vs spam en redes sociales.
        
        Tarea: Analiza la calidad de la participación de este usuario en la tendencia.
        
        Tendencia:
        {trend_context}
        
        Participación del usuario:
        {participation_summary}
        
        Evalúa:
        1. ¿La participación parece genuina o spam?
        2. ¿Hay patrones sospechosos (bot-like behavior)?
        3. ¿El usuario está realmente contribuyendo al tema?
        
        Responde en formato JSON:
        {{
            "quality_score": 0.0-1.0,
            "is_genuine": true/false,
            "flags": ["flag1", "flag2"],
            "reason": "explicación"
        }}
        """
    )
    
    chain = prompt | llm
    try:
        result = await chain.ainvoke({
            "trend_context": f"{trend_context.get('source_text', '')} - {trend_context.get('ai_analysis', '')}",
            "participation_summary": participation_summary,
        })
        
        import json
        analysis = json.loads(result.content)
        return analysis
    except Exception as exc:
        logger.warning("Error analizando calidad con AI: %s", exc)
        return {"quality_score": 0.5, "is_genuine": True, "flags": []}
```

**Beneficio**: Filtra spam y bots, recompensando solo participación genuina.

---

## 🎯 Mejora 3: Análisis de Intención y Contribución

### Problema Actual
- No distingue entre usuarios que contribuyen vs usuarios que solo buscan recompensas
- No entiende el valor real de la participación

### Solución con AI
**Usar Gemini para entender la intención y valor de la contribución**

```python
async def _analyze_contribution_value_with_ai(
    self,
    user_casts: list[dict[str, Any]],
    trend_context: dict[str, Any]
) -> dict[str, Any]:
    """Analiza el valor de la contribución del usuario usando AI."""
    
    llm = self._get_llm()
    if not llm:
        return {"contribution_score": 0.5, "value_type": "neutral"}
    
    # Resumir casts del usuario
    casts_text = "\n".join([
        f"- {cast.get('text', '')[:100]}..." 
        for cast in user_casts[:5]
    ])
    
    prompt = ChatPromptTemplate.from_template(
        """Eres un experto en evaluación de contribuciones en comunidades Web3.
        
        Tarea: Evalúa el valor de la contribución de este usuario a la tendencia.
        
        Tendencia:
        {trend_context}
        
        Casts del usuario relacionados:
        {casts_text}
        
        Evalúa:
        1. ¿El usuario está realmente contribuyendo al tema o solo mencionándolo?
        2. ¿Agrega valor (insights, preguntas, recursos) o solo repite información?
        3. ¿Su participación fomenta más engagement genuino?
        
        Responde en formato JSON:
        {{
            "contribution_score": 0.0-1.0,
            "value_type": "high_value" | "medium_value" | "low_value" | "spam",
            "reason": "explicación"
        }}
        """
    )
    
    chain = prompt | llm
    try:
        result = await chain.ainvoke({
            "trend_context": f"{trend_context.get('source_text', '')} - {trend_context.get('ai_analysis', '')}",
            "casts_text": casts_text,
        })
        
        import json
        analysis = json.loads(result.content)
        return analysis
    except Exception as exc:
        logger.warning("Error analizando contribución con AI: %s", exc)
        return {"contribution_score": 0.5, "value_type": "neutral"}
```

**Beneficio**: Prioriza usuarios que realmente aportan valor a la comunidad.

---

## 🎯 Mejora 4: Scoring Dinámico con Contexto

### Problema Actual
- Usa pesos fijos (40% trend, 20% followers, 15% badge, 25% engagement)
- No ajusta los pesos según el contexto de la tendencia

### Solución con AI
**Usar Gemini para ajustar dinámicamente los pesos del score según el contexto**

```python
async def _calculate_dynamic_weights_with_ai(
    self,
    trend_context: dict[str, Any],
    user_profile: dict[str, Any]
) -> dict[str, float]:
    """Calcula pesos dinámicos para el scoring usando AI."""
    
    llm = self._get_llm()
    if not llm:
        # Usar pesos por defecto
        return {
            "trend_weight": 0.4,
            "follower_weight": 0.2,
            "badge_weight": 0.15,
            "engagement_weight": 0.25,
        }
    
    prompt = ChatPromptTemplate.from_template(
        """Eres un experto en algoritmos de scoring para sistemas de recompensas.
        
        Tarea: Determina los pesos óptimos para calcular el score de elegibilidad.
        
        Contexto de la tendencia:
        - Tipo: {trend_type}
        - Análisis: {trend_analysis}
        - Engagement esperado: {expected_engagement}
        
        Perfil del usuario:
        - Followers: {follower_count}
        - Power Badge: {power_badge}
        - Engagement histórico: {historical_engagement}
        
        Para esta tendencia específica, ¿qué factores deberían pesar más?
        - ¿Es más importante el engagement reciente o la reputación?
        - ¿El power badge es relevante para este tipo de tendencia?
        
        Responde en formato JSON con pesos (deben sumar 1.0):
        {{
            "trend_weight": 0.0-1.0,
            "follower_weight": 0.0-1.0,
            "badge_weight": 0.0-1.0,
            "engagement_weight": 0.0-1.0,
            "reason": "explicación"
        }}
        """
    )
    
    chain = prompt | llm
    try:
        result = await chain.ainvoke({
            "trend_type": "viral" if trend_context.get("trend_score", 0) > 0.7 else "moderate",
            "trend_analysis": trend_context.get("ai_analysis", ""),
            "expected_engagement": "high" if trend_context.get("trend_score", 0) > 0.7 else "medium",
            "follower_count": user_profile.get("follower_count", 0),
            "power_badge": user_profile.get("power_badge", False),
            "historical_engagement": "high" if user_profile.get("follower_count", 0) > 1000 else "medium",
        })
        
        import json
        weights = json.loads(result.content)
        
        # Normalizar para que sumen 1.0
        total = sum([weights.get("trend_weight", 0.4), weights.get("follower_weight", 0.2), 
                     weights.get("badge_weight", 0.15), weights.get("engagement_weight", 0.25)])
        if total > 0:
            for key in weights:
                if key.endswith("_weight"):
                    weights[key] = weights[key] / total
        
        return weights
    except Exception as exc:
        logger.warning("Error calculando pesos dinámicos con AI: %s", exc)
        return {
            "trend_weight": 0.4,
            "follower_weight": 0.2,
            "badge_weight": 0.15,
            "engagement_weight": 0.25,
        }
```

**Beneficio**: Scoring más preciso y contextualizado para cada tendencia.

---

## 🎯 Mejora 5: Detección de Patrones Sospechosos

### Problema Actual
- No detecta bots o cuentas fake
- No identifica patrones de abuso (farmers de recompensas)

### Solución con AI
**Usar Gemini para detectar patrones sospechosos en el comportamiento**

```python
async def _detect_suspicious_patterns_with_ai(
    self,
    user_data: dict[str, Any],
    participation_history: list[dict[str, Any]]
) -> dict[str, Any]:
    """Detecta patrones sospechosos usando AI."""
    
    llm = self._get_llm()
    if not llm:
        return {"is_suspicious": False, "risk_score": 0.0, "flags": []}
    
    # Construir historial de participación
    history_summary = f"""
    Participaciones recientes: {len(participation_history)}
    Engagement promedio: {sum([p.get('total_engagement', 0) for p in participation_history]) / max(len(participation_history), 1)}
    Patrón temporal: {'frecuente' if len(participation_history) > 5 else 'esporádico'}
    """
    
    prompt = ChatPromptTemplate.from_template(
        """Eres un experto en detección de fraude y comportamiento sospechoso en redes sociales.
        
        Tarea: Analiza si este usuario muestra patrones sospechosos.
        
        Datos del usuario:
        - Followers: {follower_count}
        - Power Badge: {power_badge}
        - Edad de la cuenta: {account_age}
        
        Historial de participación:
        {history_summary}
        
        Evalúa:
        1. ¿Muestra patrones de bot (timing perfecto, engagement artificial)?
        2. ¿Es un farmer de recompensas (solo participa cuando hay rewards)?
        3. ¿Su engagement es orgánico o manipulado?
        
        Responde en formato JSON:
        {{
            "is_suspicious": true/false,
            "risk_score": 0.0-1.0,
            "flags": ["flag1", "flag2"],
            "reason": "explicación"
        }}
        """
    )
    
    chain = prompt | llm
    try:
        result = await chain.ainvoke({
            "follower_count": user_data.get("follower_count", 0),
            "power_badge": user_data.get("power_badge", False),
            "account_age": "new" if user_data.get("follower_count", 0) < 100 else "established",
            "history_summary": history_summary,
        })
        
        import json
        analysis = json.loads(result.content)
        return analysis
    except Exception as exc:
        logger.warning("Error detectando patrones sospechosos con AI: %s", exc)
        return {"is_suspicious": False, "risk_score": 0.0, "flags": []}
```

**Beneficio**: Protege el sistema de abusos y farmers de recompensas.

---

## 🔧 Implementación Práctica

### Paso 1: Agregar LLM al EligibilityAgent

```python
# En eligibility.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

class EligibilityAgent:
    def __init__(self, settings: Settings) -> None:
        # ... código existente ...
        self.llm = None
        self.llm_initialized = False
        self.google_api_key = settings.google_api_key
    
    def _get_llm(self) -> ChatGoogleGenerativeAI | None:
        """Inicializa LLM de forma lazy (similar a TrendWatcher)."""
        if self.llm_initialized:
            return self.llm
        
        if not self.google_api_key or self.google_api_key == "GOOGLE_API_DOCS":
            logger.warning("GOOGLE_API_KEY no configurada, AI deshabilitado")
            self.llm_initialized = True
            return None
        
        # Intentar modelos en orden de preferencia
        models = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
        ]
        
        for model_name in models:
            try:
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=self.google_api_key,
                    temperature=0.3,  # Más determinístico para análisis
                )
                self.llm = llm
                self.llm_initialized = True
                logger.info("✅ Gemini LLM inicializado para EligibilityAgent: %s", model_name)
                return llm
            except Exception as exc:
                logger.debug("Modelo %s no disponible: %s", model_name, exc)
                continue
        
        logger.warning("⚠️ No se pudo inicializar ningún modelo de Gemini para EligibilityAgent")
        self.llm_initialized = True
        return None
```

### Paso 2: Integrar en el Flujo de Análisis

```python
# En el método handle() del EligibilityAgent

# Después de obtener participation_data
participation_data = await self.farcaster.analyze_user_participation_in_trend(...)

# NUEVO: Validar relevancia de casts relacionados con AI
if participation_data.get("related_casts"):
    validated_casts = []
    for cast in participation_data["related_casts"]:
        relevance = await self._validate_cast_relevance_with_ai(
            cast_text=cast.get("text", ""),
            trend_context=context
        )
        if relevance.get("relevant", True) and relevance.get("confidence", 0) > 0.5:
            validated_casts.append(cast)
            # Ajustar engagement basado en confianza
            cast["ai_confidence"] = relevance.get("confidence", 1.0)
    
    participation_data["related_casts"] = validated_casts
    participation_data["ai_validated"] = True

# NUEVO: Analizar calidad de participación
quality_analysis = await self._analyze_participation_quality_with_ai(
    user_participation=participation_data,
    trend_context=context
)
participation_data["quality_score"] = quality_analysis.get("quality_score", 0.5)
participation_data["is_genuine"] = quality_analysis.get("is_genuine", True)

# NUEVO: Detectar patrones sospechosos
suspicious_check = await self._detect_suspicious_patterns_with_ai(
    user_data=user_info,
    participation_history=[]  # TODO: obtener historial
)
if suspicious_check.get("is_suspicious", False):
    # Reducir score o marcar para revisión
    logger.warning("⚠️ Patrones sospechosos detectados para @%s: %s", 
                   username, suspicious_check.get("flags", []))
```

### Paso 3: Ajustar Scoring con AI

```python
# En _score_user_advanced()

# NUEVO: Obtener pesos dinámicos con AI
dynamic_weights = await self._calculate_dynamic_weights_with_ai(
    trend_context=context,
    user_profile=participant
)

# Usar pesos dinámicos en lugar de fijos
trend_component = trend_score * 100 * dynamic_weights.get("trend_weight", 0.4)
follower_component = follower_score_raw * dynamic_weights.get("follower_weight", 0.2) * 5
badge_component = 15.0 * dynamic_weights.get("badge_weight", 0.15) if participant.get("power_badge") else 0
engagement_component = engagement_normalized * dynamic_weights.get("engagement_weight", 0.25)

# NUEVO: Aplicar multiplicador de calidad si está disponible
quality_multiplier = participation_data.get("quality_score", 1.0)
total = (trend_component + follower_component + badge_component + engagement_component) * quality_multiplier
```

---

## 📊 Beneficios Esperados

1. **Mayor Precisión**: Solo cuenta participación realmente relevante
2. **Protección contra Abusos**: Detecta bots y farmers
3. **Mejor Distribución**: Prioriza usuarios que realmente aportan valor
4. **Scoring Contextualizado**: Ajusta pesos según el tipo de tendencia
5. **Transparencia**: Proporciona razones para las decisiones

---

## ⚠️ Consideraciones

1. **Costo**: Cada análisis con AI tiene costo (Gemini API)
2. **Latencia**: Agregar AI aumenta el tiempo de respuesta
3. **Fallback**: Siempre tener fallback sin AI si falla
4. **Rate Limiting**: Respetar límites de la API de Gemini
5. **Caching**: Cachear resultados de análisis similares

---

## 🚀 Próximos Pasos

1. Implementar Mejora 1 (Validación de Relevancia) - Más impacto, menor costo
2. Implementar Mejora 2 (Calidad de Participación) - Alto impacto
3. Implementar Mejora 5 (Detección de Patrones) - Protección crítica
4. Implementar Mejora 4 (Scoring Dinámico) - Optimización avanzada
5. Implementar Mejora 3 (Análisis de Contribución) - Valor agregado

