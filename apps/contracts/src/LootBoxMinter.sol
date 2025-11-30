// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ERC721} from "openzeppelin-contracts/token/ERC721/ERC721.sol";
import {Ownable} from "openzeppelin-contracts/access/Ownable.sol";
import {Strings} from "openzeppelin-contracts/utils/Strings.sol";

/**
 * @title LootBoxMinter
 * @notice Minter ERC721 para loot boxes sociales. Permite configurar campañas
 *         con metadata base y acuñar NFTs (incluyendo soulbound) hacia los ganadores.
 */
contract LootBoxMinter is ERC721, Ownable {
    using Strings for uint256;

    struct CampaignConfig {
        string baseURI;
        bool active;
    }

    uint256 public nextTokenId = 1;
    mapping(bytes32 => CampaignConfig) public campaigns;
    mapping(address => bool) public agents;
    mapping(uint256 => string) private tokenURIs;
    mapping(uint256 => bool) public soulboundToken;

    event CampaignConfigured(bytes32 indexed campaignId, string baseURI);
    event CampaignStatusChanged(bytes32 indexed campaignId, bool active);
    event AgentUpdated(address indexed agent, bool allowed);
    event LootMinted(bytes32 indexed campaignId, address indexed to, uint256 tokenId, bool soulbound);
    event SoulboundUpdated(uint256 indexed tokenId, bool enabled);

    error InvalidCampaign();
    error NotAgent();
    error SoulboundTransfer();

    constructor(address initialOwner) ERC721("LootBoxSBT", "LOOT") Ownable(initialOwner) {}

    modifier onlyAgent() {
        if (!agents[msg.sender] && msg.sender != owner()) revert NotAgent();
        _;
    }

    function setAgent(address agent, bool allowed) external onlyOwner {
        agents[agent] = allowed;
        emit AgentUpdated(agent, allowed);
    }

    function configureCampaign(bytes32 campaignId, string calldata baseURI) external onlyOwner {
        require(bytes(baseURI).length > 0, "baseURI required");
        campaigns[campaignId] = CampaignConfig({baseURI: baseURI, active: true});
        emit CampaignConfigured(campaignId, baseURI);
    }

    function setCampaignStatus(bytes32 campaignId, bool active) external onlyOwner {
        CampaignConfig storage config = campaigns[campaignId];
        if (bytes(config.baseURI).length == 0) revert InvalidCampaign();
        config.active = active;
        emit CampaignStatusChanged(campaignId, active);
    }

    function mintBatch(
        bytes32 campaignId,
        address[] calldata recipients,
        string[] calldata metadataURIs,
        bool[] calldata soulboundFlags
    ) external onlyAgent {
        CampaignConfig memory config = campaigns[campaignId];
        if (bytes(config.baseURI).length == 0 || !config.active) revert InvalidCampaign();
        uint256 count = recipients.length;
        require(count > 0, "recipients empty");
        require(metadataURIs.length == count, "metadata length mismatch");
        require(soulboundFlags.length == count, "soulbound length mismatch");

        for (uint256 i = 0; i < count; i++) {
            uint256 tokenId = nextTokenId++;
            _safeMint(recipients[i], tokenId);
            string memory storedURI =
                bytes(metadataURIs[i]).length > 0 ? metadataURIs[i] : string.concat(config.baseURI, tokenId.toString());
            tokenURIs[tokenId] = storedURI;
            soulboundToken[tokenId] = soulboundFlags[i];
            emit LootMinted(campaignId, recipients[i], tokenId, soulboundFlags[i]);
        }
    }

    function setSoulbound(uint256 tokenId, bool enabled) external onlyOwner {
        require(_ownerOf(tokenId) != address(0), "token not minted");
        soulboundToken[tokenId] = enabled;
        emit SoulboundUpdated(tokenId, enabled);
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        _requireOwned(tokenId);
        string memory uri = tokenURIs[tokenId];
        if (bytes(uri).length == 0) {
            return "";
        }
        return uri;
    }

    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        if (soulboundToken[tokenId] && to != address(0) && auth != address(0)) revert SoulboundTransfer();
        return super._update(to, tokenId, auth);
    }
}

