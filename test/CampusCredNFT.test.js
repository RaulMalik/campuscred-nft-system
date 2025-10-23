import { expect } from "chai";
import { loadFixture } from "@nomicfoundation/hardhat-toolbox-mocha-ethers/network-helpers";
import hre from "hardhat";

describe("CampusCredNFT", function () {
  async function deployFixture() {
    const [owner, student] = await hre.ethers.getSigners();
    const CampusCredNFT = await hre.ethers.getContractFactory("CampusCredNFT");
    const campusCred = await CampusCredNFT.deploy();
    await campusCred.waitForDeployment();
    return { campusCred, owner, student };
  }

  it("Should mint a credential", async function () {
    const { campusCred, student } = await loadFixture(deployFixture);
    await campusCred.mint(student.address, "ipfs://test");
    expect(await campusCred.ownerOf(0)).to.equal(student.address);
  });

  it("Should prevent transfers", async function () {
    const { campusCred, owner, student } = await loadFixture(deployFixture);
    await campusCred.mint(student.address, "ipfs://test");
    await expect(
      campusCred.connect(student).transferFrom(student.address, owner.address, 0)
    ).to.be.revertedWith("Non-transferable");
  });

  it("Should revoke credential", async function () {
    const { campusCred, student } = await loadFixture(deployFixture);
    await campusCred.mint(student.address, "ipfs://test");
    await campusCred.revoke(0);
    expect(await campusCred.isRevoked(0)).to.be.true;
  });
});