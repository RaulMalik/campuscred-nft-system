import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("CampusCredNFTModule", (m) => {
  const campusCred = m.contract("CampusCredNFT");
  return { campusCred };
});