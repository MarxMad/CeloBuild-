// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {LootBoxVault} from "../src/LootBoxVault.sol";
import {MockERC20} from "../src/mocks/MockERC20.sol";

contract LootBoxVaultTest is Test {
    LootBoxVault internal vault;
    MockERC20 internal token;
    bytes32 internal campaignId = keccak256("frame-1");
    address internal agent = address(0xA11CE);

    function setUp() public {
        vault = new LootBoxVault(address(this));
        token = new MockERC20("cUSD", "cUSD", 1_000_000 ether);

        vault.setAgent(agent, true);
        vault.initializeCampaign(campaignId, address(token), 10 ether);

        token.approve(address(vault), type(uint256).max);
        vault.fundCampaign(campaignId, 1000 ether);
    }

    function testDistributeRewards() public {
        address[] memory recipients = new address[](3);
        recipients[0] = address(0x1);
        recipients[1] = address(0x2);
        recipients[2] = address(0x3);

        vm.prank(agent);
        vault.distributeERC20(campaignId, recipients);

        assertEq(token.balanceOf(recipients[0]), 10 ether);
        assertEq(token.balanceOf(recipients[1]), 10 ether);
        assertEq(token.balanceOf(recipients[2]), 10 ether);

        LootBoxVault.Campaign memory campaign = vault.getCampaign(campaignId);
        assertEq(campaign.remainingBudget, 970 ether);
    }

    function testRevertIfNotAgent() public {
        address[] memory recipients = new address[](1);
        recipients[0] = address(0x4);

        vm.expectRevert(LootBoxVault.NotAgent.selector);
        vault.distributeERC20(campaignId, recipients);
    }

    function testSweepBudget() public {
        vault.sweepBudget(campaignId, address(0x9), 100 ether);
        assertEq(token.balanceOf(address(0x9)), 100 ether);
        LootBoxVault.Campaign memory campaign = vault.getCampaign(campaignId);
        assertEq(campaign.remainingBudget, 900 ether);
    }

    function testInsufficientBudget() public {
        address[] memory recipients = new address[](200);
        for (uint256 i = 0; i < recipients.length; i++) {
            recipients[i] = address(uint160(i + 10));
        }

        vm.prank(agent);
        vm.expectRevert(LootBoxVault.InsufficientBudget.selector);
        vault.distributeERC20(campaignId, recipients);
    }
}
