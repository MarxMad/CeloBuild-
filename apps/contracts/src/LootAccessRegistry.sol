// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title LootAccessRegistry
 * @notice Registra participaciones on-chain/off-chain para campañas de loot boxes y aplica cooldowns.
 */
contract LootAccessRegistry {
    struct ClaimData {
        uint64 lastClaimAt;
        uint32 totalClaims;
    }

    struct Participation {
        uint64 timestamp;
        uint64 weight;
    }

    struct Rule {
        uint64 cooldownSeconds;
        bool exists;
    }

    address public owner;
    mapping(address => bool) public reporters;
    mapping(bytes32 => Rule) public campaignRules;
    mapping(bytes32 => mapping(address => ClaimData)) private claims;
    mapping(bytes32 => mapping(address => Participation)) private participations;

    event OwnershipTransferred(address indexed oldOwner, address indexed newOwner);
    event ReporterUpdated(address indexed reporter, bool allowed);
    event CampaignRuleConfigured(bytes32 indexed campaignId, uint64 cooldownSeconds);
    event ParticipationRecorded(bytes32 indexed campaignId, address indexed participant, uint64 weight);
    event ClaimRecorded(bytes32 indexed campaignId, address indexed participant, uint64 timestamp);

    error NotOwner();
    error NotReporter();
    error CampaignNotConfigured();

    constructor(address initialOwner) {
        owner = initialOwner == address(0) ? msg.sender : initialOwner;
        emit OwnershipTransferred(address(0), owner);
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier onlyReporter() {
        if (!reporters[msg.sender] && msg.sender != owner) revert NotReporter();
        _;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "owner zero");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function setReporter(address reporter, bool allowed) external onlyOwner {
        reporters[reporter] = allowed;
        emit ReporterUpdated(reporter, allowed);
    }

    function configureCampaign(bytes32 campaignId, uint64 cooldownSeconds) external onlyOwner {
        campaignRules[campaignId] = Rule({cooldownSeconds: cooldownSeconds, exists: true});
        emit CampaignRuleConfigured(campaignId, cooldownSeconds);
    }

    function recordParticipation(bytes32 campaignId, address participant, uint64 weight) external onlyReporter {
        Participation storage data = participations[campaignId][participant];
        data.timestamp = uint64(block.timestamp);
        data.weight = weight;
        emit ParticipationRecorded(campaignId, participant, weight);
    }

    function recordClaim(bytes32 campaignId, address participant) external onlyReporter {
        if (!campaignRules[campaignId].exists) revert CampaignNotConfigured();
        ClaimData storage data = claims[campaignId][participant];
        data.lastClaimAt = uint64(block.timestamp);
        data.totalClaims += 1;
        emit ClaimRecorded(campaignId, participant, data.lastClaimAt);
    }

    function canClaim(bytes32 campaignId, address participant) public view returns (bool) {
        Rule memory rule = campaignRules[campaignId];
        if (!rule.exists) revert CampaignNotConfigured();
        ClaimData memory data = claims[campaignId][participant];
        return block.timestamp >= data.lastClaimAt + rule.cooldownSeconds;
    }

    function getParticipation(bytes32 campaignId, address participant) external view returns (Participation memory) {
        return participations[campaignId][participant];
    }

    function getClaimData(bytes32 campaignId, address participant) external view returns (ClaimData memory) {
        return claims[campaignId][participant];
    }
}
