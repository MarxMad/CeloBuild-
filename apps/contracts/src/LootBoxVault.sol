// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);

    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

/**
 * @title LootBoxVault
 * @notice Custodia fondos ERC20 destinados a campañas de loot boxes y permite
 *         distribuir recompensas de forma batched por un conjunto de agentes autorizados.
 */
contract LootBoxVault {
    struct Campaign {
        address token;
        uint96 rewardPerRecipient;
        uint256 remainingBudget;
        bool active;
    }

    address public owner;
    mapping(address => bool) public agents;
    mapping(bytes32 => Campaign) private campaigns;

    event OwnershipTransferred(address indexed oldOwner, address indexed newOwner);
    event AgentUpdated(address indexed agent, bool allowed);
    event CampaignInitialized(bytes32 indexed campaignId, address token, uint96 rewardPerRecipient);
    event CampaignStatusChanged(bytes32 indexed campaignId, bool active);
    event CampaignFunded(bytes32 indexed campaignId, uint256 amount, uint256 newBudget);
    event RewardsDistributed(bytes32 indexed campaignId, uint256 recipients, uint256 totalAmount);
    event BudgetSwept(bytes32 indexed campaignId, address indexed to, uint256 amount);

    error NotOwner();
    error NotAgent();
    error InvalidCampaign();
    error CampaignInactive();
    error InsufficientBudget();
    error InvalidInput();

    constructor(address initialOwner) {
        owner = initialOwner == address(0) ? msg.sender : initialOwner;
        emit OwnershipTransferred(address(0), owner);
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier onlyAgent() {
        if (!agents[msg.sender] && msg.sender != owner) revert NotAgent();
        _;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "owner zero");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function setAgent(address agent, bool allowed) external onlyOwner {
        agents[agent] = allowed;
        emit AgentUpdated(agent, allowed);
    }

    function initializeCampaign(bytes32 campaignId, address token, uint96 rewardPerRecipient) external onlyOwner {
        if (token == address(0) || rewardPerRecipient == 0) revert InvalidInput();
        Campaign storage campaign = campaigns[campaignId];
        if (campaign.token != address(0)) revert InvalidInput(); // ya inicializada
        campaign.token = token;
        campaign.rewardPerRecipient = rewardPerRecipient;
        campaign.active = true;
        emit CampaignInitialized(campaignId, token, rewardPerRecipient);
    }

    function setCampaignStatus(bytes32 campaignId, bool active) external onlyOwner {
        Campaign storage campaign = campaigns[campaignId];
        if (campaign.token == address(0)) revert InvalidCampaign();
        campaign.active = active;
        emit CampaignStatusChanged(campaignId, active);
    }

    function fundCampaign(bytes32 campaignId, uint256 amount) external onlyOwner {
        if (amount == 0) revert InvalidInput();
        Campaign storage campaign = campaigns[campaignId];
        if (campaign.token == address(0)) revert InvalidCampaign();
        IERC20(campaign.token).transferFrom(msg.sender, address(this), amount);
        campaign.remainingBudget += amount;
        emit CampaignFunded(campaignId, amount, campaign.remainingBudget);
    }

    function distributeERC20(bytes32 campaignId, address[] calldata recipients) external onlyAgent {
        Campaign storage campaign = campaigns[campaignId];
        if (campaign.token == address(0)) revert InvalidCampaign();
        if (!campaign.active) revert CampaignInactive();
        uint256 count = recipients.length;
        if (count == 0) revert InvalidInput();

        uint256 total = uint256(campaign.rewardPerRecipient) * count;
        if (campaign.remainingBudget < total) revert InsufficientBudget();

        campaign.remainingBudget -= total;
        IERC20 token = IERC20(campaign.token);
        for (uint256 i = 0; i < count; i++) {
            require(recipients[i] != address(0), "recipient zero");
            token.transfer(recipients[i], campaign.rewardPerRecipient);
        }

        emit RewardsDistributed(campaignId, count, total);
    }

    function sweepBudget(bytes32 campaignId, address to, uint256 amount) external onlyOwner {
        if (to == address(0) || amount == 0) revert InvalidInput();
        Campaign storage campaign = campaigns[campaignId];
        if (campaign.token == address(0)) revert InvalidCampaign();
        if (amount > campaign.remainingBudget) revert InsufficientBudget();

        campaign.remainingBudget -= amount;
        IERC20(campaign.token).transfer(to, amount);
        emit BudgetSwept(campaignId, to, amount);
    }

    function getCampaign(bytes32 campaignId) external view returns (Campaign memory) {
        Campaign memory campaign = campaigns[campaignId];
        if (campaign.token == address(0)) revert InvalidCampaign();
        return campaign;
    }
}
