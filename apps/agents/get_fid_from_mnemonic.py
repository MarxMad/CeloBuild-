#!/usr/bin/env python3
"""
Script para obtener el FID de Farcaster desde un mnemonic.
Ejecuta: python get_fid_from_mnemonic.py
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

async def get_fid_from_mnemonic(mnemonic: str, neynar_api_key: str) -> int | None:
    """Obtiene el FID de Farcaster desde un mnemonic."""
    try:
        # Crear cuenta desde mnemonic
        account = Account.from_mnemonic(mnemonic)
        custody_address = account.address
        
        print(f"📍 Custody Address: {custody_address}")
        
        # Buscar usuario por custody address usando Neynar API
        url = "https://api.neynar.com/v2/farcaster/user/by_custody_address"
        params = {"custody_address": custody_address}
        headers = {
            "accept": "application/json",
            "x-api-key": neynar_api_key
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                fid = result.get("fid")
                
                if fid:
                    print(f"✅ FID encontrado: {fid}")
                    print(f"👤 Username: {result.get('username', 'N/A')}")
                    print(f"📛 Display Name: {result.get('display_name', 'N/A')}")
                    return fid
                else:
                    print("❌ No se encontró FID para esta dirección")
                    print("💡 Esto significa que esta wallet no tiene una cuenta Farcaster registrada")
                    return None
            elif response.status_code == 404:
                print("❌ No se encontró cuenta Farcaster para esta dirección")
                print("💡 Necesitas crear una cuenta Farcaster primero")
                return None
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def main():
    print("🔍 Obteniendo FID desde mnemonic...\n")
    
    # Obtener mnemonic de variables de entorno
    mnemonic = os.getenv("NEYNAR_APP_MNEMONIC")
    neynar_api_key = os.getenv("NEYNAR_API_KEY")
    
    if not mnemonic:
        print("❌ NEYNAR_APP_MNEMONIC no está configurado en las variables de entorno")
        print("💡 Configúralo en tu archivo .env o en Vercel")
        sys.exit(1)
    
    if not neynar_api_key or neynar_api_key == "NEYNAR_API_DOCS":
        print("❌ NEYNAR_API_KEY no está configurado o es inválido")
        print("💡 Configúralo en tu archivo .env o en Vercel")
        sys.exit(1)
    
    # Obtener FID
    fid = await get_fid_from_mnemonic(mnemonic, neynar_api_key)
    
    if fid:
        print(f"\n✅ Tu NEYNAR_APP_FID es: {fid}")
        print("\n💡 Puedes configurarlo en Vercel como:")
        print(f"   NEYNAR_APP_FID={fid}")
        print("\n   (Opcional: el sistema lo obtiene automáticamente si no lo configuras)")
    else:
        print("\n❌ No se pudo obtener el FID")
        print("💡 Asegúrate de que:")
        print("   1. El mnemonic corresponde a una wallet con cuenta Farcaster")
        print("   2. La cuenta Farcaster está registrada correctamente")
        print("   3. NEYNAR_API_KEY es válido y tiene créditos")

if __name__ == "__main__":
    asyncio.run(main())

