#!/usr/bin/env python3
"""Script de prueba para los endpoints de generación de casts."""
import asyncio
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.services.cast_generator import CastGeneratorService
from src.services.cast_scheduler import CastSchedulerService
from src.tools.farcaster import FarcasterToolbox
from src.tools.celo import CeloToolbox


async def test_cast_generator():
    """Prueba el servicio de generación de casts."""
    print("\n🧪 Probando CastGeneratorService...")
    
    try:
        generator = CastGeneratorService(settings)
        
        # Probar obtener temas
        topics = CastGeneratorService.get_available_topics()
        print(f"✅ Temas disponibles: {list(topics.keys())}")
        
        # Probar generar cast
        print("\n📝 Generando cast para tema 'tech'...")
        result = await generator.generate_cast("tech")
        print(f"✅ Cast generado:")
        print(f"   Texto: {result['cast_text']}")
        print(f"   Tema: {result['topic_name']} {result['emoji']}")
        print(f"   Generado con IA: {result['generated']}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_celo_toolbox():
    """Prueba el CeloToolbox para obtener dirección del agente."""
    print("\n🧪 Probando CeloToolbox...")
    
    try:
        celo_toolbox = CeloToolbox(
            rpc_url=settings.celo_rpc_url,
            private_key=settings.celo_private_key
        )
        
        # Obtener dirección del agente
        agent_address = celo_toolbox.get_agent_address()
        print(f"✅ Dirección del agente: {agent_address}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cast_scheduler():
    """Prueba el servicio de programación de casts."""
    print("\n🧪 Probando CastSchedulerService...")
    
    try:
        farcaster_toolbox = FarcasterToolbox(
            base_url=settings.farcaster_hub_api or "https://api.neynar.com/v2",
            neynar_key=settings.neynar_api_key
        )
        
        celo_toolbox = CeloToolbox(
            rpc_url=settings.celo_rpc_url,
            private_key=settings.celo_private_key
        )
        
        scheduler = CastSchedulerService(
            farcaster_toolbox=farcaster_toolbox,
            celo_toolbox=celo_toolbox,
            registry_address=settings.registry_address
        )
        
        print("✅ CastSchedulerService inicializado correctamente")
        
        # No iniciar el scheduler en la prueba (se iniciaría en producción)
        # scheduler.start()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Ejecuta todas las pruebas."""
    print("🚀 Iniciando pruebas del backend de generación de casts...\n")
    
    results = []
    
    # Prueba 1: CastGeneratorService
    results.append(await test_cast_generator())
    
    # Prueba 2: CeloToolbox
    results.append(await test_celo_toolbox())
    
    # Prueba 3: CastSchedulerService
    results.append(await test_cast_scheduler())
    
    # Resumen
    print("\n" + "="*50)
    print("📊 Resumen de Pruebas:")
    print("="*50)
    passed = sum(results)
    total = len(results)
    print(f"✅ Pasadas: {passed}/{total}")
    print(f"❌ Fallidas: {total - passed}/{total}")
    
    if all(results):
        print("\n🎉 ¡Todas las pruebas pasaron!")
        return 0
    else:
        print("\n⚠️ Algunas pruebas fallaron")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

