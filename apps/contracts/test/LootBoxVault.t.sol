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
    address internal owner = address(this);

    // Events to check
    event RewardsDistributed(bytes32 indexed campaignId, uint256 recipients, uint256 totalAmount);
    event CampaignInitialized(bytes32 indexed campaignId, address token, uint96 rewardPerRecipient);
    event CampaignStatusChanged(bytes32 indexed campaignId, bool active);

    function setUp() public {
        vault = new LootBoxVault(owner);
        token = new MockERC20("cUSD", "cUSD", 1_000_000 ether);

        vault.setAgent(agent, true);
        // Setup basic campaign
        vault.initializeCampaign(campaignId, address(token), 10 ether);
        
        token.approve(address(vault), type(uint256).max);
        vault.fundCampaign(campaignId, 1000 ether);
    }

    function testDistributeRewards() public {
        address[] memory recipients = new address[](3);
        recipients[0] = address(0x1);
        recipients[1] = address(0x2);
        recipients[2] = address(0x3);

        vm.expectEmit(true, false, false, true);
        emit RewardsDistributed(campaignId, 3, 30 ether);

        vm.prank(agent);
        vault.distributeERC20(campaignId, recipients);

        assertEq(token.balanceOf(recipients[0]), 10 ether);
        assertEq(token.balanceOf(recipients[1]), 10 ether);
        assertEq(token.balanceOf(recipients[2]), 10 ether);

        LootBoxVault.Campaign memory campaign = vault.getCampaign(campaignId);
        assertEq(campaign.remainingBudget, 970 ether);
    }

    function testFuzzDistribute(uint8 recipientCount) public {
        // Fuzz test with 1 to 50 recipients
        vm.assume(recipientCount > 0 && recipientCount <= 50);

        address[] memory recipients = new address[](recipientCount);
        for (uint256 i = 0; i < recipientCount; i++) {
            recipients[i] = address(uint160(i + 100));
        }

        uint256 totalRequired = uint256(recipientCount) * 10 ether;
        
        vm.prank(agent);
        vault.distributeERC20(campaignId, recipients);

        assertEq(token.balanceOf(recipients[0]), 10 ether);
        LootBoxVault.Campaign memory campaign = vault.getCampaign(campaignId);
        assertEq(campaign.remainingBudget, 1000 ether - totalRequired);
    }

    function testRevertIfNotAgent() public {
        address[] memory recipients = new address[](1);
        recipients[0] = address(0x4);

        vm.prank(address(0xDEAD)); // Random address, not agent, not owner
        vm.expectRevert(LootBoxVault.NotAgent.selector);
        vault.distributeERC20(campaignId, recipients);
    }

    function testRevertIfInactive() public {
        vault.setCampaignStatus(campaignId, false);
        
        address[] memory recipients = new address[](1);
        recipients[0] = address(0x5);

        vm.prank(agent);
        vm.expectRevert(LootBoxVault.CampaignInactive.selector);
        vault.distributeERC20(campaignId, recipients);
    }

    function testSweepBudget() public {
        vault.sweepBudget(campaignId, address(0x9), 100 ether);
        assertEq(token.balanceOf(address(0x9)), 100 ether);
        LootBoxVault.Campaign memory campaign = vault.getCampaign(campaignId);
        assertEq(campaign.remainingBudget, 900 ether);
    }

    function testInsufficientBudget() public {
        address[] memory recipients = new address[](101); // 101 * 10 = 1010 > 1000
        for (uint256 i = 0; i < recipients.length; i++) {
            recipients[i] = address(uint160(i + 10));
        }

        vm.prank(agent);
        vm.expectRevert(LootBoxVault.InsufficientBudget.selector);
        vault.distributeERC20(campaignId, recipients);
    }

    function testMultipleCampaigns() public {
        bytes32 campaign2 = keccak256("frame-2");
        vault.initializeCampaign(campaign2, address(token), 5 ether);
        vault.fundCampaign(campaign2, 500 ether);

        address[] memory recipients = new address[](1);
        recipients[0] = address(0x20);

        vm.prank(agent);
        vault.distributeERC20(campaign2, recipients);

        assertEq(token.balanceOf(address(0x20)), 5 ether);
        
        LootBoxVault.Campaign memory c1 = vault.getCampaign(campaignId);
        LootBoxVault.Campaign memory c2 = vault.getCampaign(campaign2);
        
        assertEq(c1.remainingBudget, 1000 ether); // Unchanged
        assertEq(c2.remainingBudget, 495 ether);
    }
}
