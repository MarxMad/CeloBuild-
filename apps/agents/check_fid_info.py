#!/usr/bin/env python3
"""
Script para obtener información de un FID de Farcaster.
Uso: python check_fid_info.py <FID>
"""

import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def get_fid_info(fid: int, neynar_api_key: str):
    """Obtiene información de un FID."""
    try:
        # Usar el endpoint bulk que es el correcto según la implementación en farcaster.py
        url = "https://api.neynar.com/v2/farcaster/user/bulk"
        params = {"fids": str(fid)}  # Neynar espera fids como string separado por comas
        headers = {
            "accept": "application/json",
            "x-api-key": neynar_api_key
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # El endpoint bulk retorna {"users": [...]}
                users = data.get("users", [])
                
                if not users or len(users) == 0:
                    print(f"❌ FID {fid} no encontrado en la respuesta")
                    return None
                
                result = users[0]  # Tomar el primer usuario
                
                username = result.get("username", "N/A")
                display_name = result.get("display_name", "N/A")
                custody_address = result.get("custody_address", "N/A")
                pfp_url = result.get("pfp_url", "N/A")
                
                print(f"✅ FID {fid} encontrado:")
                print(f"   👤 Username: @{username}")
                print(f"   📛 Display Name: {display_name}")
                print(f"   📍 Custody Address: {custody_address}")
                if pfp_url and pfp_url != "N/A":
                    print(f"   🖼️  Profile Picture: {pfp_url}")
                
                print(f"\n💡 Para verificar si este FID corresponde a tu mnemonic:")
                print(f"   1. Obtén el custody address de tu mnemonic ejecutando:")
                print(f"      python get_fid_from_mnemonic.py")
                print(f"   2. Compara el custody address mostrado arriba con el de tu mnemonic")
                print(f"   3. Si coinciden, entonces FID {fid} es correcto ✅")
                
                return {
                    "fid": fid,
                    "username": username,
                    "display_name": display_name,
                    "custody_address": custody_address
                }
            elif response.status_code == 404:
                print(f"❌ FID {fid} no encontrado en Farcaster")
                return None
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def main():
    if len(sys.argv) < 2:
        print("Uso: python check_fid_info.py <FID>")
        print("Ejemplo: python check_fid_info.py 744296")
        sys.exit(1)
    
    try:
        fid = int(sys.argv[1])
    except ValueError:
        print("❌ El FID debe ser un número")
        sys.exit(1)
    
    print(f"🔍 Obteniendo información del FID {fid}...\n")
    
    # Obtener API key
    neynar_api_key = os.getenv("NEYNAR_API_KEY")
    
    if not neynar_api_key or neynar_api_key == "NEYNAR_API_DOCS":
        print("❌ NEYNAR_API_KEY no está configurado o es inválido")
        print("💡 Configúralo en tu archivo .env")
        sys.exit(1)
    
    # Obtener información
    result = await get_fid_info(fid, neynar_api_key)
    
    if result:
        print(f"\n✅ Información obtenida exitosamente")
    else:
        print(f"\n❌ No se pudo obtener información del FID")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

