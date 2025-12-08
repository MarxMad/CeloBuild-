// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import {LootBoxVault} from "../src/LootBoxVault.sol";
import {LootAccessRegistry} from "../src/LootAccessRegistry.sol";
import {LootBoxMinter} from "../src/LootBoxMinter.sol";

/**
 * @title DeployProduction
 * @notice Script completo de deployment para PRODUCCION
 * 
 * Este script:
 * 1. Despliega los 3 contratos con mejoras de seguridad
 * 2. Configura roles para el agente
 * 3. Transfiere ownership al agente (para campanas dinamicas)
 * 4. Configura campana demo (opcional)
 * 
 * IMPORTANTE: El usuario NO necesita firmar transacciones para recibir premios.
 * El backend (agente) distribuye automaticamente usando su private key.
 */
contract DeployProduction is Script {
    // Direcciones que se guardaran en .env
    address public deployedVault;
    address public deployedRegistry;
    address public deployedMinter;
    
    // Direccion del agente (backend) que distribuira recompensas
    address public agentAddress;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        agentAddress = vm.envAddress("AGENT_ADDRESS");
        // CUSD_ADDRESS es opcional
        address cusdAddress;
        try vm.envAddress("CUSD_ADDRESS") returns (address addr) {
            cusdAddress = addr;
        } catch {
            cusdAddress = address(0);
        }
        
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("========================================");
        console.log("DEPLOYMENT PARA PRODUCCION");
        console.log("========================================");
        console.log("Agent address:", agentAddress);
        console.log("cUSD address:", cusdAddress);
        console.log("");
        
        // 1. Desplegar contratos
        console.log("1. Desplegando contratos...");
        LootBoxVault vault = new LootBoxVault(msg.sender);
        LootAccessRegistry registry = new LootAccessRegistry(msg.sender);
        LootBoxMinter minter = new LootBoxMinter(msg.sender);
        
        deployedVault = address(vault);
        deployedRegistry = address(registry);
        deployedMinter = address(minter);
        
        console.log("   LootBoxVault:", deployedVault);
        console.log("   LootAccessRegistry:", deployedRegistry);
        console.log("   LootBoxMinter:", deployedMinter);
        console.log("");
        
        // 2. Configurar roles para el agente (antes de transferir ownership)
        console.log("2. Configurando roles para el agente...");
        
        // LootBoxMinter: dar rol "agent" al backend
        minter.setAgent(agentAddress, true);
        console.log("   [OK] Rol agent otorgado en LootBoxMinter");
        
        // LootAccessRegistry: dar rol "reporter" al backend
        registry.setReporter(agentAddress, true);
        console.log("   [OK] Rol reporter otorgado en LootAccessRegistry");
        
        // LootBoxVault: dar rol "agent" al backend
        vault.setAgent(agentAddress, true);
        console.log("   [OK] Rol agent otorgado en LootBoxVault");
        console.log("");
        
        // 3. Transferir ownership al agente (para campanas dinamicas)
        console.log("3. Transfiriendo ownership al agente...");
        console.log("   ADVERTENCIA: El agente tendra control completo de los contratos");
        
        vault.transferOwnership(agentAddress);
        console.log("   [OK] Ownership de LootBoxVault transferido");
        
        registry.transferOwnership(agentAddress);
        console.log("   [OK] Ownership de LootAccessRegistry transferido");
        
        minter.transferOwnership(agentAddress);
        console.log("   [OK] Ownership de LootBoxMinter transferido");
        console.log("");
        
        // 4. Configurar campana demo (opcional, para testing)
        console.log("4. Configurando campana demo (opcional)...");
        bytes32 demoCampaignId = keccak256("demo-campaign");
        
        // LootAccessRegistry: configurar campana con cooldown de 1 dia
        registry.configureCampaign(demoCampaignId, 86400);
        console.log("   [OK] Campaign demo configured in Registry");
        
        // LootBoxMinter: configurar campana con metadata base
        minter.configureCampaign(demoCampaignId, "ipfs://QmExample/");
        console.log("   [OK] Campaign demo configured in Minter");
        
        // LootBoxVault: inicializar campana demo (requiere cUSD address)
        if (cusdAddress != address(0)) {
            vault.initializeCampaign(demoCampaignId, cusdAddress, 0.15 * 1e18); // 0.15 cUSD
            console.log("   [OK] Campaign demo initialized in Vault");
        } else {
            console.log("   [SKIP] cUSD address no configurada, saltando inicializacion de Vault");
        }
        
        vm.stopBroadcast();
        
        // 5. Mostrar resumen
        console.log("");
        console.log("========================================");
        console.log("DEPLOYMENT COMPLETADO");
        console.log("========================================");
        console.log("LOOTBOX_VAULT_ADDRESS=", deployedVault);
        console.log("REGISTRY_ADDRESS=", deployedRegistry);
        console.log("MINTER_ADDRESS=", deployedMinter);
        console.log("");
        console.log("Agrega estas direcciones a tu archivo .env");
        console.log("El agente ahora puede crear campanas dinamicas automaticamente");
    }
}

