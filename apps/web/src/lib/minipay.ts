/**
 * MiniPay Utilities
 * 
 * Funciones helper para interactuar con MiniPay wallet y verificar balances/transacciones.
 * Basado en la MiniPay Code Library de Celo.
 */

import { createPublicClient, http, formatEther, getContract, type Address } from "viem";
import { celo, celoSepolia } from "viem/chains";
import { stableTokenABI } from "@celo/abis";

// Direcciones de stablecoins en Celo Mainnet
export const STABLE_TOKEN_ADDRESSES = {
  cUSD: "0x765DE816845861e75A25fCA122bb6898B8B1282a",
  USDC: "0xcebA9300f2b948710d2653dD7B07f33A8B32118C",
  USDT: "0x48065fbbe25f71c9282ddf5e1cd6d6a887483d5e",
} as const;

// Direcciones de stablecoins en Celo Sepolia Testnet
export const STABLE_TOKEN_ADDRESSES_TESTNET = {
  cUSD: "0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1", // Sepolia cUSD
} as const;

/**
 * Detecta si el usuario está usando MiniPay wallet
 */
export function isMiniPay(): boolean {
  if (typeof window === "undefined") return false;
  return !!(window.ethereum && (window.ethereum as any).isMiniPay);
}

/**
 * Obtiene la dirección del usuario conectado sin usar librerías
 */
export async function getMiniPayAddress(): Promise<string | null> {
  if (typeof window === "undefined" || !window.ethereum) return null;
  
  if (isMiniPay()) {
    try {
      const accounts = await window.ethereum.request({
        method: "eth_requestAccounts",
        params: [],
      });
      return accounts[0] || null;
    } catch (error) {
      console.error("Error obteniendo cuenta de MiniPay:", error);
      return null;
    }
  }
  
  return null;
}

/**
 * Verifica el balance de cUSD de una dirección
 */
export async function checkCUSDBalance(
  address: Address,
  isTestnet: boolean = false
): Promise<string> {
  const chain = isTestnet ? celoSepolia : celo;
  const cUSDAddress = isTestnet 
    ? STABLE_TOKEN_ADDRESSES_TESTNET.cUSD 
    : STABLE_TOKEN_ADDRESSES.cUSD;

  const publicClient = createPublicClient({
    chain,
    transport: http(),
  });

  const stableTokenContract = getContract({
    abi: stableTokenABI,
    address: cUSDAddress as Address,
    client: publicClient,
  });

  const balanceInBigNumber = await stableTokenContract.read.balanceOf([address]);
  const balanceInEthers = formatEther(balanceInBigNumber);

  return balanceInEthers;
}

/**
 * Verifica si una transacción fue exitosa
 */
export async function checkTransactionStatus(
  transactionHash: `0x${string}`,
  isTestnet: boolean = false
): Promise<boolean> {
  const chain = isTestnet ? celoSepolia : celo;
  
  const publicClient = createPublicClient({
    chain,
    transport: http(),
  });

  try {
    const receipt = await publicClient.getTransactionReceipt({
      hash: transactionHash,
    });

    return receipt.status === "success";
  } catch (error) {
    console.error("Error verificando transacción:", error);
    return false;
  }
}

/**
 * Estima el gas para una transacción (en CELO)
 */
export async function estimateGasInCELO(
  transaction: {
    account: Address;
    to: Address;
    value?: bigint;
    data?: `0x${string}`;
  },
  isTestnet: boolean = false
): Promise<bigint> {
  const chain = isTestnet ? celoSepolia : celo;
  
  const publicClient = createPublicClient({
    chain,
    transport: http(),
  });

  return await publicClient.estimateGas({
    ...transaction,
    // feeCurrency no se especifica para usar CELO nativo
  });
}

/**
 * Estima el gas para una transacción (en cUSD)
 */
export async function estimateGasInCUSD(
  transaction: {
    account: Address;
    to: Address;
    value?: bigint;
    data?: `0x${string}`;
  },
  isTestnet: boolean = false
): Promise<bigint> {
  const chain = isTestnet ? celoSepolia : celo;
  const cUSDAddress = isTestnet 
    ? STABLE_TOKEN_ADDRESSES_TESTNET.cUSD 
    : STABLE_TOKEN_ADDRESSES.cUSD;

  const publicClient = createPublicClient({
    chain,
    transport: http(),
  });

  return await publicClient.estimateGas({
    ...transaction,
    feeCurrency: cUSDAddress as Address,
  });
}

/**
 * Estima el precio del gas (en CELO)
 */
export async function estimateGasPriceInCELO(
  isTestnet: boolean = false
): Promise<bigint> {
  const chain = isTestnet ? celoSepolia : celo;
  
  const publicClient = createPublicClient({
    chain,
    transport: http(),
  });

  const gasPrice = await publicClient.getGasPrice();

  return gasPrice;
}

/**
 * Estima el precio del gas (en cUSD)
 */
export async function estimateGasPriceInCUSD(
  isTestnet: boolean = false
): Promise<bigint> {
  const chain = isTestnet ? celoSepolia : celo;
  const cUSDAddress = isTestnet 
    ? STABLE_TOKEN_ADDRESSES_TESTNET.cUSD 
    : STABLE_TOKEN_ADDRESSES.cUSD;

  const publicClient = createPublicClient({
    chain,
    transport: http(),
  });

  // Para cUSD, usamos el método request con el tipo correcto
  const gasPrice = await publicClient.request({
    method: "eth_gasPrice",
    params: [cUSDAddress as `0x${string}`],
  } as any) as string; // Type assertion necesario para feeCurrency en Celo

  if (!gasPrice || typeof gasPrice !== "string") {
    throw new Error("Failed to get gas price");
  }

  return BigInt(gasPrice);
}

/**
 * Calcula el costo en cUSD para las fees de una transacción
 */
export async function calculateCUSDFees(
  transaction: {
    account: Address;
    to: Address;
    value?: bigint;
    data?: `0x${string}`;
  },
  isTestnet: boolean = false
): Promise<string> {
  const [gasLimit, gasPrice] = await Promise.all([
    estimateGasInCUSD(transaction, isTestnet),
    estimateGasPriceInCUSD(isTestnet),
  ]);

  const feesInWei = gasLimit * gasPrice;
  const feesInCUSD = formatEther(feesInWei);

  return feesInCUSD;
}

