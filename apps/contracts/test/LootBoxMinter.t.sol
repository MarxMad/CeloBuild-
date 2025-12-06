// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {LootBoxMinter} from "../src/LootBoxMinter.sol";

contract LootBoxMinterTest is Test {
    LootBoxMinter internal minter;
    bytes32 internal campaignId = keccak256("frame-3");
    address internal agent = address(0x123);

    function setUp() public {
        minter = new LootBoxMinter(address(this));
        minter.setAgent(agent, true);
        minter.configureCampaign(campaignId, "ipfs://base/");
    }

    function testMintBatchStoresMetadata() public {
        address[] memory recipients = new address[](2);
        recipients[0] = address(0xA);
        recipients[1] = address(0xB);

        string[] memory metadata = new string[](2);
        metadata[0] = "ipfs://custom/loot1";
        metadata[1] = "";

        bool[] memory soulboundFlags = new bool[](2);
        soulboundFlags[0] = false;
        soulboundFlags[1] = true;

        vm.prank(agent);
        minter.mintBatch(campaignId, recipients, metadata, soulboundFlags);

        assertEq(minter.ownerOf(1), recipients[0]);
        assertEq(minter.ownerOf(2), recipients[1]);
        assertEq(minter.tokenURI(1), "ipfs://custom/loot1");
        assertEq(minter.tokenURI(2), "ipfs://base/2");
        assertFalse(minter.soulboundToken(1));
        assertTrue(minter.soulboundToken(2));
    }

    function testSoulboundPreventsTransfer() public {
        address[] memory recipients = new address[](1);
        recipients[0] = address(0xAA);
        string[] memory metadata = new string[](1);
        metadata[0] = "";
        bool[] memory flags = new bool[](1);
        flags[0] = true;

        vm.prank(agent);
        minter.mintBatch(campaignId, recipients, metadata, flags);

        vm.prank(recipients[0]);
        vm.expectRevert(LootBoxMinter.SoulboundTransfer.selector);
        minter.transferFrom(recipients[0], address(0xBB), 1);
    }

    function testSetSoulboundByOwner() public {
        address[] memory recipients = new address[](1);
        recipients[0] = address(0xCC);
        string[] memory metadata = new string[](1);
        metadata[0] = "";
        bool[] memory flags = new bool[](1);
        flags[0] = false;

        vm.prank(agent);
        minter.mintBatch(campaignId, recipients, metadata, flags);

        minter.setSoulbound(1, true);
        assertTrue(minter.soulboundToken(1));
    }
}


