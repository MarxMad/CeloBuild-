// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import {LootBoxVault} from "../src/LootBoxVault.sol";
import {LootAccessRegistry} from "../src/LootAccessRegistry.sol";

contract LootBoxDeployer is Script {
    function run() external returns (LootBoxVault vault, LootAccessRegistry registry) {
        vm.startBroadcast();
        vault = new LootBoxVault(msg.sender);
        registry = new LootAccessRegistry(msg.sender);
        vm.stopBroadcast();
    }
}
