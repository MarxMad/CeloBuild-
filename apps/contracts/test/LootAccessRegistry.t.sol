// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {LootAccessRegistry} from "../src/LootAccessRegistry.sol";

contract LootAccessRegistryTest is Test {
    LootAccessRegistry internal registry;
    bytes32 internal campaignId = keccak256("frame-2");
    address internal reporter = address(0xBEEF);
    address internal participant = address(0xCAFE);

    function setUp() public {
        registry = new LootAccessRegistry(address(this));
        registry.configureCampaign(campaignId, 1 days);
        registry.setReporter(reporter, true);
    }

    function testRecordParticipation() public {
        vm.prank(reporter);
        registry.recordParticipation(campaignId, participant, 42);

        LootAccessRegistry.Participation memory info = registry.getParticipation(campaignId, participant);
        assertEq(info.weight, 42);
        assertEq(info.timestamp, block.timestamp);
    }

    function testCooldownLogic() public {
        vm.prank(reporter);
        registry.recordClaim(campaignId, participant);

        bool immediate = registry.canClaim(campaignId, participant);
        assertFalse(immediate, "Debe respetar cooldown");

        vm.warp(block.timestamp + 1 days + 1);
        assertTrue(registry.canClaim(campaignId, participant), "Cooldown expirado");
    }

    function testOnlyReporterGuard() public {
        vm.prank(address(0xDEAD)); // Random address
        vm.expectRevert(LootAccessRegistry.NotReporter.selector);
        registry.recordParticipation(campaignId, participant, 1);
    }
}

