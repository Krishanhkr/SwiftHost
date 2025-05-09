const { Gateway, Wallets } = require('fabric-network');
const fs = require('fs');
const path = require('path');
const FabricCAServices = require('fabric-ca-client');

// Configuration
const channelName = 'auditchannel';
const chaincodeName = 'auditcc';
const mspOrg = 'Org1MSP';
const walletPath = path.join(__dirname, 'wallet');
const org1UserId = 'appUser';

// Connection profile
const ccpPath = path.resolve(__dirname, 'connection-org1.json');
const ccpJSON = fs.readFileSync(ccpPath, 'utf8');
const ccp = JSON.parse(ccpJSON);

/**
 * Initialize the wallet
 * @returns {Promise<void>}
 */
async function initWallet() {
    try {
        // Create a new file system based wallet for managing identities
        const wallet = await Wallets.newFileSystemWallet(walletPath);
        console.log(`Wallet path: ${walletPath}`);

        // Check to see if we've already enrolled the user
        const identity = await wallet.get(org1UserId);
        if (identity) {
            console.log(`An identity for the user "${org1UserId}" already exists in the wallet`);
            return;
        }

        // Check to see if we've already enrolled the admin user
        const adminIdentity = await wallet.get('admin');
        if (!adminIdentity) {
            console.log('Admin identity can not be found in the wallet, please enroll admin first');
            return;
        }

        // Build a user object for authenticating with the CA
        const provider = wallet.getProviderRegistry().getProvider(adminIdentity.type);
        const adminUser = await provider.getUserContext(adminIdentity, 'admin');

        // Register the user, enroll the user, and import the new identity into the wallet
        const caURL = ccp.certificateAuthorities['ca.org1.example.com'].url;
        const ca = new FabricCAServices(caURL);

        const secret = await ca.register({
            affiliation: 'org1.department1',
            enrollmentID: org1UserId,
            role: 'client'
        }, adminUser);

        const enrollment = await ca.enroll({
            enrollmentID: org1UserId,
            enrollmentSecret: secret
        });

        const x509Identity = {
            credentials: {
                certificate: enrollment.certificate,
                privateKey: enrollment.key.toBytes(),
            },
            mspId: mspOrg,
            type: 'X.509',
        };

        await wallet.put(org1UserId, x509Identity);
        console.log(`Successfully registered and enrolled user "${org1UserId}" and imported it into the wallet`);
    } catch (error) {
        console.error(`Failed to enroll user: ${error}`);
        process.exit(1);
    }
}

/**
 * Log an admin action on the blockchain
 * @param {string} userId - The user ID performing the action
 * @param {string} resource - The resource being accessed
 * @returns {Promise<string>} - The transaction ID
 */
async function logAdminAction(userId, resource) {
    try {
        // Create a new gateway for connecting to the peer node
        const wallet = await Wallets.newFileSystemWallet(walletPath);
        const gateway = new Gateway();

        await gateway.connect(ccp, {
            wallet,
            identity: org1UserId,
            discovery: { enabled: true, asLocalhost: true }
        });

        // Get the network (channel) our contract is deployed to
        const network = await gateway.getNetwork(channelName);

        // Get the contract from the network
        const contract = network.getContract(chaincodeName);

        // Submit the transaction
        const result = await contract.submitTransaction('LogAccess', userId, resource);
        
        // Disconnect from the gateway
        await gateway.disconnect();

        return result.toString();
    } catch (error) {
        console.error(`Failed to submit transaction: ${error}`);
        throw new Error(`Failed to log admin action: ${error.message}`);
    }
}

/**
 * Get all audit logs from the blockchain
 * @returns {Promise<Array>} - The array of audit logs
 */
async function getAllLogs() {
    try {
        // Create a new gateway for connecting to the peer node
        const wallet = await Wallets.newFileSystemWallet(walletPath);
        const gateway = new Gateway();

        await gateway.connect(ccp, {
            wallet,
            identity: org1UserId,
            discovery: { enabled: true, asLocalhost: true }
        });

        // Get the network (channel) our contract is deployed to
        const network = await gateway.getNetwork(channelName);

        // Get the contract from the network
        const contract = network.getContract(chaincodeName);

        // Evaluate the transaction
        const result = await contract.evaluateTransaction('GetAllLogs');
        
        // Disconnect from the gateway
        await gateway.disconnect();

        return JSON.parse(result.toString());
    } catch (error) {
        console.error(`Failed to evaluate transaction: ${error}`);
        throw new Error(`Failed to get logs: ${error.message}`);
    }
}

// Export functions
module.exports = {
    initWallet,
    logAdminAction,
    getAllLogs
}; 