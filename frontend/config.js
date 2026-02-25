// Configuration - will be populated from CloudFormation outputs
const CONFIG = {
    // Set to false to disable quick login buttons in production
    ENABLE_QUICK_LOGIN: true,
    
    // These will be populated by deploy script from CloudFormation outputs
    COGNITO_USER_POOL_ID: '',
    COGNITO_CLIENT_ID: '',
    API_BASE_URL: '',
    AWS_REGION: 'us-east-1',
    
    // AgentCore endpoint
    AGENT_ENDPOINT: '',
    
    // Mock users for quick login
    MOCK_USERS: [
        { email: 'john.doe@acme.com', password: 'Password123', name: 'John Doe' },
        { email: 'jane.smith@acme.com', password: 'Password123', name: 'Jane Smith' },
        { email: 'bob.johnson@acme.com', password: 'Password123', name: 'Bob Johnson' }
    ]
};

// Load config from deployed config file if it exists
async function loadDeployedConfig() {
    try {
        // Add cache-busting parameter
        const response = await fetch(`config.json?t=${Date.now()}`);
        if (response.ok) {
            const deployedConfig = await response.json();
            Object.assign(CONFIG, deployedConfig);
            console.log('Loaded deployed config:', CONFIG);
        } else {
            console.log('No deployed config found, using defaults');
        }
    } catch (e) {
        console.log('Error loading config:', e);
    }
}

// Initialize config on load - must complete before app starts
window.configReady = loadDeployedConfig();

