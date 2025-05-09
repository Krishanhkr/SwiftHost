const { logAdminAction } = require('./blockchain-connector');

/**
 * Middleware for logging admin actions to blockchain
 * @param {Object} options - Configuration options
 * @param {Array<string>} options.adminRoutes - List of routes to audit
 * @param {Function} options.getUserId - Function to extract user ID from request
 * @returns {Function} Express middleware
 */
function auditMiddleware(options = {}) {
    const {
        adminRoutes = ['/api/users', '/api/admin'],
        getUserId = (req) => req.user && req.user.id
    } = options;
    
    return async (req, res, next) => {
        // Store original end function
        const originalEnd = res.end;
        
        // Check if this is an admin route
        const isAdminRoute = adminRoutes.some(route => req.path.startsWith(route));
        
        if (isAdminRoute) {
            // Replace res.end with our function
            res.end = async function(chunk, encoding) {
                // Call original end function
                originalEnd.call(res, chunk, encoding);
                
                // Extract user ID
                const userId = getUserId(req) || 'anonymous';
                
                // Log to blockchain
                try {
                    const resource = `${req.method} ${req.originalUrl}`;
                    await logAdminAction(userId, resource);
                    console.log(`Logged admin action to blockchain: ${userId} - ${resource}`);
                } catch (error) {
                    console.error('Failed to log admin action to blockchain:', error);
                }
            };
        }
        
        next();
    };
}

/**
 * Express route handler for admin actions
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 */
const adminActionHandler = async (req, res) => {
    try {
        // Extract user ID from request
        const userId = req.user && req.user.id || 'anonymous';
        
        // Log admin action to blockchain
        const resource = `${req.method} ${req.originalUrl}`;
        await logAdminAction(userId, resource);
        
        // Return success
        res.status(200).json({ success: true, message: 'Admin action logged to blockchain' });
    } catch (error) {
        console.error('Failed to log admin action:', error);
        res.status(500).json({ success: false, message: 'Failed to log admin action' });
    }
};

module.exports = {
    auditMiddleware,
    adminActionHandler
}; 