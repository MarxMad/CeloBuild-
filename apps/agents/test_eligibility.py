#!/usr/bin/env python3
"""Script de prueba para verificar que el EligibilityAgent funcione correctamente."""

import asyncio
import logging
from src.config import Settings
from src.graph.eligibility import EligibilityAgent

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_eligibility_agent():
    """Prueba el EligibilityAgent con diferentes escenarios."""
    
    print("=" * 80)
    print("🧪 TEST: EligibilityAgent")
    print("=" * 80)
    
    settings = Settings()
    agent = EligibilityAgent(settings)
    
    # Test 1: Con target_address (usuario específico)
    print("\n📋 Test 1: Analizar usuario específico con target_address")
    print("-" * 80)
    
    context_with_target = {
        "frame_id": "cast-0x812abc",
        "cast_hash": "0x812abc123def456789",
        "trend_score": 0.85,
        "topic_tags": ["minipay", "celo", "farcaster"],
        "channel_id": "global",
        "target_address": "0x1234567890123456789012345678901234567890",  # Dirección de prueba
        "reward_type": "nft",
        "source_text": "¡MiniPay está cambiando el juego! 🚀",
        "ai_analysis": "Post relevante sobre adopción de MiniPay...",
    }
    
    try:
        result1 = await agent.handle(context_with_target)
        print(f"✅ Test 1 completado")
        print(f"   Campaign ID: {result1.get('campaign_id')}")
        print(f"   Recipients: {len(result1.get('recipients', []))}")
        print(f"   Rankings: {len(result1.get('rankings', []))}")
        if result1.get('rankings'):
            top_user = result1['rankings'][0]
            print(f"   Top User: {top_user.get('username')} - Score: {top_user.get('score')}")
    except Exception as e:
        print(f"❌ Test 1 falló: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Sin target_address (análisis de participantes del cast)
    print("\n📋 Test 2: Analizar participantes del cast (sin target_address)")
    print("-" * 80)
    
    context_without_target = {
        "frame_id": "cast-0x812abc",
        "cast_hash": "0x812abc123def456789",
        "trend_score": 0.85,
        "topic_tags": ["minipay", "celo"],
        "channel_id": "global",
        "reward_type": "nft",
    }
    
    try:
        result2 = await agent.handle(context_without_target)
        print(f"✅ Test 2 completado")
        print(f"   Campaign ID: {result2.get('campaign_id')}")
        print(f"   Recipients: {len(result2.get('recipients', []))}")
        print(f"   Rankings: {len(result2.get('rankings', []))}")
    except Exception as e:
        print(f"❌ Test 2 falló: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Sin cast_hash (solo análisis de perfil)
    print("\n📋 Test 3: Analizar usuario sin cast_hash (solo perfil)")
    print("-" * 80)
    
    context_no_cast = {
        "frame_id": "cast-0x812abc",
        "cast_hash": None,
        "trend_score": 0.5,
        "topic_tags": [],
        "channel_id": "global",
        "target_address": "0x1234567890123456789012345678901234567890",
        "reward_type": "nft",
    }
    
    try:
        result3 = await agent.handle(context_no_cast)
        print(f"✅ Test 3 completado")
        print(f"   Campaign ID: {result3.get('campaign_id')}")
        print(f"   Recipients: {len(result3.get('recipients', []))}")
        print(f"   Rankings: {len(result3.get('rankings', []))}")
        if result3.get('rankings'):
            top_user = result3['rankings'][0]
            print(f"   Top User: {top_user.get('username')} - Score: {top_user.get('score')}")
    except Exception as e:
        print(f"❌ Test 3 falló: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Verificar que campaign_id se genera correctamente
    print("\n📋 Test 4: Verificar generación de campaign_id")
    print("-" * 80)
    
    test_cases = [
        ("cast-0x812abc", "cast-0x812abc-loot"),
        ("global", "global-loot"),
        (None, "global-loot"),
        ("", "global-loot"),
    ]
    
    for frame_id, expected_campaign in test_cases:
        context_test = {
            "frame_id": frame_id,
            "cast_hash": "0x123",
            "trend_score": 0.5,
            "topic_tags": [],
            "channel_id": "global",
        }
        result = await agent.handle(context_test)
        actual_campaign = result.get('campaign_id')
        status = "✅" if actual_campaign == expected_campaign else "❌"
        print(f"   {status} frame_id='{frame_id}' -> campaign_id='{actual_campaign}' (esperado: '{expected_campaign}')")
    
    print("\n" + "=" * 80)
    print("✅ Tests completados")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_eligibility_agent())

