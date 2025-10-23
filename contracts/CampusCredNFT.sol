// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract CampusCredNFT is ERC721, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    
    uint256 private _tokenIdCounter;
    mapping(uint256 => string) private _tokenURIs;
    mapping(uint256 => bool) private _revoked;
    
    event CredentialMinted(uint256 indexed tokenId, address indexed recipient, string uri);
    event CredentialRevoked(uint256 indexed tokenId);
    
    constructor() ERC721("CampusCred", "CCRED") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
    }
    
    function _update(address to, uint256 tokenId, address auth)
        internal override returns (address)
    {
        address from = _ownerOf(tokenId);
        require(from == address(0) || to == address(0), "Non-transferable");
        return super._update(to, tokenId, auth);
    }
    
    function mint(address recipient, string memory uri) 
        public onlyRole(MINTER_ROLE) returns (uint256) 
    {
        uint256 tokenId = _tokenIdCounter++;
        _safeMint(recipient, tokenId);
        _tokenURIs[tokenId] = uri;
        emit CredentialMinted(tokenId, recipient, uri);
        return tokenId;
    }
    
    function tokenURI(uint256 tokenId) 
        public view override returns (string memory) 
    {
        require(_ownerOf(tokenId) != address(0), "Nonexistent token");
        return _tokenURIs[tokenId];
    }
    
    function revoke(uint256 tokenId) public onlyRole(DEFAULT_ADMIN_ROLE) {
        _revoked[tokenId] = true;
        emit CredentialRevoked(tokenId);
    }
    
    function isRevoked(uint256 tokenId) public view returns (bool) {
        return _revoked[tokenId];
    }
    
    function supportsInterface(bytes4 interfaceId)
        public view override(ERC721, AccessControl) returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}