// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import {LootBoxVault} from "../src/LootBoxVault.sol";

/**
 * @title InitializeCampaign
 * @notice Script para inicializar la campana demo en LootBoxVault
 * 
 * IMPORTANTE: Este script requiere:
 * 1. Que el LootBoxVault este desplegado
 * 2. Que tengas fondos cUSD para depositar en el vault
 * 3. Que apruebes el vault para transferir tus cUSD
 */
contract InitializeCampaign is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address vaultAddress = vm.envAddress("LOOTBOX_VAULT_ADDRESS");
        address cusdAddress = vm.envAddress("CUSD_ADDRESS"); // Direccion de cUSD en Celo Sepolia
        
        vm.startBroadcast(deployerPrivateKey);
        
        LootBoxVault vault = LootBoxVault(vaultAddress);
        bytes32 demoCampaignId = keccak256("demo-campaign");
        
        // Inicializar campana: 0.15 cUSD por recipient
        uint96 rewardPerRecipient = uint96(0.15 * 1e18); // 0.15 cUSD con 18 decimales
        
        console.log("Inicializando campana demo en LootBoxVault...");
        console.log("Vault:", vaultAddress);
        console.log("cUSD Token:", cusdAddress);
        console.log("Reward per recipient:", rewardPerRecipient);
        
        vault.initializeCampaign(demoCampaignId, cusdAddress, rewardPerRecipient);
        console.log("[OK] Campana demo inicializada en LootBoxVault");
        
        // Opcional: Depositar fondos iniciales (requiere que hayas aprobado el vault primero)
        // uint256 initialFunding = 10 * 1e18; // 10 cUSD
        // vault.fundCampaign(demoCampaignId, initialFunding);
        // console.log("[OK] Fondos depositados:", initialFunding);
        
        vm.stopBroadcast();
        
        console.log("NOTA: Para depositar fondos, primero aprueba el vault");
        console.log("Luego deposita usando cast send");
    }
}

