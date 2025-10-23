const hre = require("hardhat");

async function main() {
  console.log("Deploying CampusCredNFT to Sepolia...");
  
  const CampusCredNFT = await hre.ethers.getContractFactory("CampusCredNFT");
  const campusCred = await CampusCredNFT.deploy();
  
  await campusCred.waitForDeployment();
  const address = await campusCred.getAddress();
  
  console.log(`✅ CampusCredNFT deployed to: ${address}`);
  console.log(`View on Etherscan: https://sepolia.etherscan.io/address/${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});