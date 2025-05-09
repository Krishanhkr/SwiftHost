import hashlib
import json
import time
import os
import logging
import base64
from datetime import datetime
import hmac

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZKProof:
    """
    Simple mock implementation of Zero-Knowledge Proof for evidence verification
    In a real implementation, this would use a proper ZKP library
    """
    @staticmethod
    def generate(data, secret_key="honeypot_secret"):
        """Generate a simple ZK proof (mock implementation)"""
        if isinstance(data, bytes):
            data_bytes = data
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = json.dumps(data).encode('utf-8')
            
        # In a real implementation, this would be a proper ZKP
        # Here we just use HMAC as a simple demonstration
        h = hmac.new(secret_key.encode('utf-8'), data_bytes, hashlib.sha256)
        signature = h.hexdigest()
        
        # Create proof object
        proof = {
            "signature": signature,
            "timestamp": datetime.now().isoformat(),
            "method": "HMAC-SHA256"
        }
        
        return proof
    
    @staticmethod
    def verify(data, proof, secret_key="honeypot_secret"):
        """Verify a ZK proof (mock implementation)"""
        if isinstance(data, bytes):
            data_bytes = data
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = json.dumps(data).encode('utf-8')
            
        # Calculate expected signature
        h = hmac.new(secret_key.encode('utf-8'), data_bytes, hashlib.sha256)
        expected = h.hexdigest()
        
        # Check if signatures match
        if isinstance(proof, dict) and "signature" in proof:
            return proof["signature"] == expected
        else:
            return proof == expected

class ForensicEvidence:
    """Class to represent forensic evidence that is stored on the blockchain"""
    def __init__(self, attack_ip, evidence_type, content, metadata=None):
        self.timestamp = time.time()
        self.attack_ip = attack_ip
        self.evidence_type = evidence_type
        self.content = content
        self.metadata = metadata or {}
        self.evidence_id = None
        self.file_hash = None
        self.zkp_signature = None
        
    def hash_content(self):
        """Generate a hash of the evidence content"""
        if isinstance(self.content, bytes):
            content_bytes = self.content
        elif isinstance(self.content, str):
            content_bytes = self.content.encode('utf-8')
        else:
            content_bytes = json.dumps(self.content).encode('utf-8')
            
        # Generate SHA-256 hash of content
        hash_obj = hashlib.sha256(content_bytes)
        self.file_hash = hash_obj.hexdigest()
        return self.file_hash
    
    def generate_proof(self):
        """Generate a ZK proof for the evidence"""
        if isinstance(self.content, bytes):
            content_bytes = self.content
        elif isinstance(self.content, str):
            content_bytes = self.content.encode('utf-8')
        else:
            content_bytes = json.dumps(self.content).encode('utf-8')
            
        proof = ZKProof.generate(content_bytes)
        self.zkp_signature = proof["signature"]
        return proof
    
    def serialize(self):
        """Serialize evidence for blockchain storage"""
        # Ensure we have hash and proof
        if not self.file_hash:
            self.hash_content()
        if not self.zkp_signature:
            proof = self.generate_proof()
            self.zkp_signature = proof["signature"]
        
        # Base64 encode content if it's bytes
        if isinstance(self.content, bytes):
            content = base64.b64encode(self.content).decode('utf-8')
        else:
            content = self.content
        
        return {
            "timestamp": self.timestamp,
            "attack_ip": self.attack_ip,
            "evidence_type": self.evidence_type,
            "content": content,
            "metadata": self.metadata,
            "file_hash": self.file_hash,
            "zkp_signature": self.zkp_signature
        }
    
    @classmethod
    def deserialize(cls, data):
        """Create evidence object from serialized data"""
        evidence = cls(
            attack_ip=data["attack_ip"],
            evidence_type=data["evidence_type"],
            content=data["content"],
            metadata=data.get("metadata", {})
        )
        evidence.timestamp = data["timestamp"]
        evidence.file_hash = data["file_hash"]
        evidence.zkp_signature = data["zkp_signature"]
        
        # Decode base64 content if needed (based on evidence type)
        if evidence.evidence_type in ["packet_capture", "screenshot", "binary"]:
            evidence.content = base64.b64decode(evidence.content)
            
        return evidence

class BlockchainLogger:
    """
    Mock implementation of blockchain evidence logging
    In a real implementation, this would interact with Hyperledger or another blockchain
    """
    def __init__(self):
        self.evidence_dir = "forensics/evidence"
        self.chain_file = "forensics/evidence_chain.json"
        
        # Create directories if they don't exist
        os.makedirs(self.evidence_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.chain_file), exist_ok=True)
        
        # Initialize the chain if it doesn't exist
        if not os.path.exists(self.chain_file):
            self._initialize_chain()
        
        # Load the chain
        self.chain = self._load_chain()
    
    def _initialize_chain(self):
        """Initialize a new blockchain"""
        # Create genesis block
        genesis = {
            "index": 0,
            "timestamp": time.time(),
            "evidence_id": "genesis",
            "previous_hash": "0" * 64,
            "hash": hashlib.sha256("genesis".encode('utf-8')).hexdigest()
        }
        
        # Write chain with genesis block
        with open(self.chain_file, 'w') as f:
            json.dump([genesis], f, indent=2)
        
        logger.info("Initialized new evidence blockchain")
    
    def _load_chain(self):
        """Load the blockchain from file"""
        with open(self.chain_file, 'r') as f:
            chain = json.load(f)
        
        logger.info(f"Loaded evidence blockchain with {len(chain)} blocks")
        return chain
    
    def _save_chain(self):
        """Save the blockchain to file"""
        with open(self.chain_file, 'w') as f:
            json.dump(self.chain, f, indent=2)
        
        logger.info(f"Saved evidence blockchain with {len(self.chain)} blocks")
    
    def log_evidence(self, evidence):
        """
        Log evidence to the blockchain
        
        Args:
            evidence: ForensicEvidence object
            
        Returns:
            block: The created blockchain block
        """
        # Ensure evidence has hash and proof
        if not evidence.file_hash:
            evidence.hash_content()
        if not evidence.zkp_signature:
            evidence.generate_proof()
        
        # Generate unique evidence ID
        timestamp_str = datetime.fromtimestamp(evidence.timestamp).strftime("%Y%m%d%H%M%S")
        evidence_id = f"evidence_{timestamp_str}_{evidence.attack_ip.replace('.', '_')}"
        evidence.evidence_id = evidence_id
        
        # Create a new block
        previous_block = self.chain[-1]
        block = {
            "index": len(self.chain),
            "timestamp": time.time(),
            "evidence_id": evidence_id,
            "evidence_hash": evidence.file_hash,
            "zkp_signature": evidence.zkp_signature,
            "attack_ip": evidence.attack_ip,
            "evidence_type": evidence.evidence_type,
            "previous_hash": previous_block["hash"]
        }
        
        # Calculate block hash
        block_string = json.dumps(block, sort_keys=True)
        block["hash"] = hashlib.sha256(block_string.encode('utf-8')).hexdigest()
        
        # Save evidence file
        with open(f"{self.evidence_dir}/{evidence_id}.json", 'w') as f:
            json.dump(evidence.serialize(), f, indent=2)
            
        # Add block to chain
        self.chain.append(block)
        self._save_chain()
        
        logger.info(f"Added evidence {evidence_id} to blockchain at block {block['index']}")
        return block
    
    def verify_evidence(self, evidence_id):
        """
        Verify the integrity of evidence
        
        Args:
            evidence_id: ID of the evidence to verify
            
        Returns:
            result: Dictionary with verification results
        """
        # Find the block for this evidence
        block = None
        for b in self.chain:
            if b.get("evidence_id") == evidence_id:
                block = b
                break
        
        if block is None:
            return {
                "verified": False,
                "error": f"Evidence {evidence_id} not found in blockchain"
            }
        
        # Load the evidence file
        try:
            with open(f"{self.evidence_dir}/{evidence_id}.json", 'r') as f:
                evidence_data = json.load(f)
                
            evidence = ForensicEvidence.deserialize(evidence_data)
        except Exception as e:
            return {
                "verified": False,
                "error": f"Failed to load evidence file: {str(e)}"
            }
        
        # Verify evidence hash
        current_hash = evidence.hash_content()
        if current_hash != block["evidence_hash"]:
            return {
                "verified": False,
                "error": "Evidence hash mismatch - evidence may have been modified"
            }
        
        # Verify ZKP
        if not ZKProof.verify(evidence.content, evidence.zkp_signature):
            return {
                "verified": False,
                "error": "Zero-Knowledge Proof verification failed"
            }
        
        # Verify blockchain integrity
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Verify previous hash reference
            if current["previous_hash"] != previous["hash"]:
                return {
                    "verified": False,
                    "error": f"Blockchain integrity error at block {i}"
                }
            
            # Verify block hash
            block_data = current.copy()
            current_hash = block_data.pop("hash")
            block_string = json.dumps(block_data, sort_keys=True)
            calculated_hash = hashlib.sha256(block_string.encode('utf-8')).hexdigest()
            
            if calculated_hash != current_hash:
                return {
                    "verified": False,
                    "error": f"Block hash mismatch at block {i}"
                }
        
        return {
            "verified": True,
            "evidence_id": evidence_id,
            "block_index": block["index"],
            "timestamp": datetime.fromtimestamp(block["timestamp"]).isoformat(),
            "attack_ip": evidence.attack_ip,
            "evidence_type": evidence.evidence_type
        }
    
    def list_evidence(self):
        """
        List all evidence in the blockchain
        
        Returns:
            evidence_list: List of evidence summaries
        """
        evidence_list = []
        
        for block in self.chain[1:]:  # Skip genesis block
            evidence_list.append({
                "evidence_id": block["evidence_id"],
                "attack_ip": block["attack_ip"],
                "evidence_type": block["evidence_type"],
                "timestamp": datetime.fromtimestamp(block["timestamp"]).isoformat(),
                "block_index": block["index"]
            })
        
        return evidence_list

# Helper function to create and log evidence from attack data
def log_attack_evidence(attack_data, blockchain_logger=None):
    """
    Create and log evidence from attack data
    
    Args:
        attack_data: Dictionary containing attack information
        blockchain_logger: Optional BlockchainLogger instance
        
    Returns:
        evidence_id: ID of the created evidence
    """
    if blockchain_logger is None:
        blockchain_logger = BlockchainLogger()
    
    # Create forensic evidence object
    evidence = ForensicEvidence(
        attack_ip=attack_data["ip"],
        evidence_type="attack_log",
        content=attack_data,
        metadata={
            "threat_score": attack_data.get("threat_score", 0),
            "attack_types": attack_data.get("attack_types", []),
            "user_agent": attack_data.get("user_agent", "")
        }
    )
    
    # Log to blockchain
    block = blockchain_logger.log_evidence(evidence)
    
    return evidence.evidence_id 