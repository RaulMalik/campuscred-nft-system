import "@nomicfoundation/hardhat-toolbox-mocha-ethers";
import "dotenv/config";

export default {
  solidity: "0.8.28",
  networks: {
    sepolia: {
      url: process.env.ALCHEMY_URL,
      accounts: [process.env.PRIVATE_KEY]
    }
  }
};