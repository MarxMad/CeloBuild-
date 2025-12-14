#!/usr/bin/env python3
"""
Script para verificar si un FID corresponde al mnemonic configurado.
Uso: python verify_fid.py <FID>
"""

import os
import sys
import asyncio
import httpx
from eth_account import Account
from dotenv import load_dotenv

# Habilitar características de mnemonic
Account.enable_unaudited_hdwallet_features()

# Cargar variables de entorno
load_dotenv()

async def verify_fid(fid: int, mnemonic: str, neynar_api_key: str) -> bool:
    """Verifica si un FID corresponde al custody address del mnemonic."""
    try:
        # Obtener custody address desde mnemonic
        account = Account.from_mnemonic(mnemonic)
        custody_address = account.address.lower()
        
        print(f"📍 Custody Address del mnemonic: {custody_address}")
        print(f"🔍 Verificando FID: {fid}\n")
        
        # Obtener información del FID usando Neynar API
        url = f"https://api.neynar.com/v2/farcaster/user"
        params = {"fid": fid}
        headers = {
            "accept": "application/json",
            "x-api-key": neynar_api_key
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                
                user_custody_address = result.get("custody_address", "").lower()
                username = result.get("username", "N/A")
                display_name = result.get("display_name", "N/A")
                
                print(f"👤 Username: {username}")
                print(f"📛 Display Name: {display_name}")
                print(f"📍 Custody Address del FID: {user_custody_address}")
                print()
                
                if user_custody_address == custody_address:
                    print("✅ ¡CORRECTO! El FID corresponde al mnemonic configurado")
                    print(f"\n💡 Puedes configurar en Vercel:")
                    print(f"   NEYNAR_APP_FID={fid}")
                    return True
                else:
                    print("❌ El FID NO corresponde al mnemonic configurado")
                    print(f"   Custody address del FID: {user_custody_address}")
                    print(f"   Custody address del mnemonic: {custody_address}")
                    return False
            elif response.status_code == 404:
                print(f"❌ FID {fid} no encontrado en Farcaster")
                return False
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    if len(sys.argv) < 2:
        print("Uso: python verify_fid.py <FID>")
        print("Ejemplo: python verify_fid.py 744296")
        sys.exit(1)
    
    try:
        fid = int(sys.argv[1])
    except ValueError:
        print("❌ El FID debe ser un número")
        sys.exit(1)
    
    print("🔍 Verificando FID...\n")
    
    # Obtener variables de entorno
    mnemonic = os.getenv("NEYNAR_APP_MNEMONIC")
    neynar_api_key = os.getenv("NEYNAR_API_KEY")
    
    if not mnemonic:
        print("❌ NEYNAR_APP_MNEMONIC no está configurado")
        print("💡 Configúralo en tu archivo .env o pásalo como variable de entorno")
        print("\n   Ejemplo: NEYNAR_APP_MNEMONIC='tu mnemonic aquí' python verify_fid.py 744296")
        sys.exit(1)
    
    if not neynar_api_key or neynar_api_key == "NEYNAR_API_DOCS":
        print("❌ NEYNAR_API_KEY no está configurado o es inválido")
        sys.exit(1)
    
    # Verificar FID
    is_valid = await verify_fid(fid, mnemonic, neynar_api_key)
    
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    asyncio.run(main())

