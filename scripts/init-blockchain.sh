#!/bin/bash

# Initialize Hyperledger Fabric blockchain for audit trails

echo "Initializing Hyperledger Fabric blockchain for audit trails..."

# Create required directories
mkdir -p blockchain/crypto-config
mkdir -p blockchain/data
mkdir -p audit-trail/data

# Download Hyperledger Fabric binaries if they don't exist
if [ ! -f bin/cryptogen ]; then
    echo "Downloading Hyperledger Fabric binaries..."
    curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.2.1 1.4.9
fi

# Generate crypto materials
echo "Generating crypto materials..."
bin/cryptogen generate --config=./crypto-config.yaml --output=blockchain/crypto-config

# Generate channel artifacts
echo "Generating channel artifacts..."
bin/configtxgen -profile TwoOrgsOrdererGenesis -channelID system-channel -outputBlock blockchain/system-genesis-block/genesis.block
bin/configtxgen -profile TwoOrgsChannel -outputCreateChannelTx blockchain/channel-artifacts/auditchannel.tx -channelID auditchannel
bin/configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate blockchain/channel-artifacts/Org1MSPanchors.tx -channelID auditchannel -asOrg Org1MSP
bin/configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate blockchain/channel-artifacts/Org2MSPanchors.tx -channelID auditchannel -asOrg Org2MSP

# Start the network
echo "Starting the blockchain network..."
docker-compose -f docker-compose-blockchain.yml up -d

# Wait for containers to start
echo "Waiting for containers to start..."
sleep 10

# Create channel
echo "Creating channel..."
docker exec -e CORE_PEER_LOCALMSPID=Org1MSP -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp cli peer channel create -o orderer.example.com:7050 -c auditchannel -f ./channel-artifacts/auditchannel.tx --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Join peers to channel
echo "Joining peers to channel..."
docker exec -e CORE_PEER_LOCALMSPID=Org1MSP -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp cli peer channel join -b auditchannel.block
docker exec -e CORE_PEER_LOCALMSPID=Org2MSP -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp -e CORE_PEER_ADDRESS=peer0.org2.example.com:9051 cli peer channel join -b auditchannel.block

# Install chaincode
echo "Installing audit chaincode..."
docker exec -e CORE_PEER_LOCALMSPID=Org1MSP -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp cli peer chaincode install -n auditcc -v 1.0 -p github.com/hyperledger/fabric-samples/chaincode/audit/go/
docker exec -e CORE_PEER_LOCALMSPID=Org2MSP -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp -e CORE_PEER_ADDRESS=peer0.org2.example.com:9051 cli peer chaincode install -n auditcc -v 1.0 -p github.com/hyperledger/fabric-samples/chaincode/audit/go/

# Instantiate chaincode
echo "Instantiating audit chaincode..."
docker exec -e CORE_PEER_LOCALMSPID=Org1MSP -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp cli peer chaincode instantiate -o orderer.example.com:7050 -C auditchannel -n auditcc -v 1.0 -c '{"Args":["init"]}' --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Wait for chaincode to instantiate
echo "Waiting for chaincode to instantiate..."
sleep 10

# Test the chaincode
echo "Testing the audit chaincode..."
docker exec -e CORE_PEER_LOCALMSPID=Org1MSP -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp cli peer chaincode invoke -o orderer.example.com:7050 -C auditchannel -n auditcc -c '{"function":"LogAccess","Args":["admin", "INIT"]}' --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

echo "Blockchain network initialized successfully!" 