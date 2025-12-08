// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import {LootBoxVault} from "../src/LootBoxVault.sol";

/**
 * @title FundCampaign
 * @notice Script para depositar fondos cUSD en una campaña del LootBoxVault
 * 
 * IMPORTANTE: Este script requiere:
 * 1. Que el LootBoxVault este desplegado
 * 2. Que la campaña este inicializada
 * 3. Que tengas fondos cUSD en tu wallet
 * 4. Que hayas aprobado el vault para transferir tus cUSD
 */
contract FundCampaign is Script {
    function run() external {
        // Usar CELO_PRIVATE_KEY (del agente) o DEPLOYER_PRIVATE_KEY como fallback
        uint256 deployerPrivateKey = vm.envOr("CELO_PRIVATE_KEY", vm.envUint("DEPLOYER_PRIVATE_KEY"));
        address vaultAddress = vm.envAddress("LOOTBOX_VAULT_ADDRESS");
        address cusdAddress = vm.envAddress("CUSD_ADDRESS");
        
        // Obtener campaign_id desde variable de entorno o usar demo-campaign
        string memory campaignName = vm.envOr("CAMPAIGN_ID", string("demo-campaign"));
        bytes32 campaignId = keccak256(bytes(campaignName));
        
        // Cantidad a depositar (por defecto 100 cUSD)
        uint256 amount = vm.envOr("FUND_AMOUNT", uint256(100 * 1e18));
        
        vm.startBroadcast(deployerPrivateKey);
        
        LootBoxVault vault = LootBoxVault(vaultAddress);
        
        console.log("========================================");
        console.log("DEPOSITANDO FONDOS EN CAMPAÑA");
        console.log("========================================");
        console.log("Vault:", vaultAddress);
        console.log("cUSD Token:", cusdAddress);
        console.log("Campaign ID:", vm.toString(campaignId));
        console.log("Campaign Name:", campaignName);
        console.log("Amount:", amount / 1e18, "cUSD");
        console.log("");
        
        // Paso 1: Aprobar el vault para transferir cUSD
        console.log("Paso 1: Aprobando vault para transferir cUSD...");
        // Usar cast para aprobar (más simple que hacerlo desde el script)
        console.log("Ejecuta este comando primero:");
        console.log("cast send", cusdAddress, "approve(address,uint256)", vaultAddress, vm.toString(amount), "--private-key $DEPLOYER_PRIVATE_KEY --rpc-url $CELO_RPC_URL");
        console.log("");
        
        // Paso 2: Depositar fondos
        console.log("Paso 2: Depositando fondos en la campaña...");
        vault.fundCampaign(campaignId, amount);
        console.log("[OK] Fondos depositados:", amount / 1e18, "cUSD");
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("========================================");
        console.log("FONDOS DEPOSITADOS EXITOSAMENTE");
        console.log("========================================");
        console.log("La campaña ahora tiene fondos para distribuir recompensas");
    }
}

