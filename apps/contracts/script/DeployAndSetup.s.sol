// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import {LootBoxVault} from "../src/LootBoxVault.sol";
import {LootAccessRegistry} from "../src/LootAccessRegistry.sol";
import {LootBoxMinter} from "../src/LootBoxMinter.sol";

/**
 * @title DeployAndSetup
 * @notice Script completo que despliega los contratos y los configura automáticamente
 * 
 * IMPORTANTE: El usuario NO necesita firmar transacciones para recibir premios.
 * El backend (agente) distribuye automáticamente usando su private key.
 */
contract DeployAndSetup is Script {
    // Direcciones que se guardarán en .env
    address public deployedVault;
    address public deployedRegistry;
    address public deployedMinter;
    
    // Dirección del agente (backend) que distribuirá recompensas
    address public agentAddress;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        agentAddress = vm.envAddress("AGENT_ADDRESS");
        
        vm.startBroadcast(deployerPrivateKey);
        
        // 1. Desplegar contratos
        console.log("Desplegando contratos...");
        LootBoxVault vault = new LootBoxVault(msg.sender);
        LootAccessRegistry registry = new LootAccessRegistry(msg.sender);
        LootBoxMinter minter = new LootBoxMinter(msg.sender);
        
        deployedVault = address(vault);
        deployedRegistry = address(registry);
        deployedMinter = address(minter);
        
        console.log("LootBoxVault:", deployedVault);
        console.log("LootAccessRegistry:", deployedRegistry);
        console.log("LootBoxMinter:", deployedMinter);
        
        // 2. Configurar roles para el agente
        console.log("Configurando roles para el agente...");
        console.log("Agent address:", agentAddress);
        
        // LootBoxMinter: dar rol "agent" al backend
        minter.setAgent(agentAddress, true);
        console.log("[OK] Rol agent otorgado en LootBoxMinter");
        
        // LootAccessRegistry: dar rol "reporter" al backend
        registry.setReporter(agentAddress, true);
        console.log("[OK] Rol reporter otorgado en LootAccessRegistry");
        
        // LootBoxVault: dar rol "agent" al backend
        vault.setAgent(agentAddress, true);
        console.log("[OK] Rol agent otorgado en LootBoxVault");
        
        // 3. Configurar campaña demo (opcional, puedes crear más después)
        console.log("Configuring demo campaign...");
        bytes32 demoCampaignId = keccak256("demo-campaign");
        
        // LootAccessRegistry: configurar campaña con cooldown de 1 día (86400 segundos)
        registry.configureCampaign(demoCampaignId, 86400);
        console.log("[OK] Campaign demo configured in Registry");
        
        // LootBoxMinter: configurar campaña con metadata base
        minter.configureCampaign(demoCampaignId, "ipfs://QmExample/");
        console.log("[OK] Campaign demo configured in Minter");
        
        // LootBoxVault: inicializar campaña (requiere token address y reward amount)
        // Nota: Esto requiere que primero tengas fondos cUSD en el vault
        // address cusdAddress = 0x...; // Dirección de cUSD en Celo Sepolia
        // vault.initializeCampaign(demoCampaignId, cusdAddress, 0.15 * 1e18); // 0.15 cUSD
        
        vm.stopBroadcast();
        
        // 4. Mostrar resumen
        console.log("RESUMEN:");
        console.log("LOOTBOX_VAULT_ADDRESS=", deployedVault);
        console.log("REGISTRY_ADDRESS=", deployedRegistry);
        console.log("MINTER_ADDRESS=", deployedMinter);
        console.log("Agrega estas direcciones a tu archivo .env");
    }
}

