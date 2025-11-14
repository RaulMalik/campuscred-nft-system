import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('📦 Exporting CampusCredNFT ABI...\n');

// Path to the compiled contract artifact
const artifactPath = join(__dirname, '../artifacts/contracts/CampusCredNFT.sol/CampusCredNFT.json');

// Check if artifact exists
if (!fs.existsSync(artifactPath)) {
    console.error('❌ Contract artifact not found!');
    console.error('   Please compile the contract first: npx hardhat compile');
    process.exit(1);
}

// Read the artifact
const artifact = JSON.parse(fs.readFileSync(artifactPath, 'utf8'));

// Create contracts directory in backend if it doesn't exist
const contractsDir = join(__dirname, '../contracts');
if (!fs.existsSync(contractsDir)) {
    fs.mkdirSync(contractsDir, { recursive: true });
}

// Write just the ABI to a JSON file
const abiOutputPath = join(contractsDir, 'CampusCredNFT_ABI.json');
fs.writeFileSync(abiOutputPath, JSON.stringify(artifact.abi, null, 2));

console.log('✅ ABI exported successfully!');
console.log(`   Location: ${abiOutputPath}`);
console.log('\n📝 ABI contains', artifact.abi.length, 'functions/events');
console.log('\n🎉 Ready to use in Python backend!');