/**
 * UATP Browser Extension - Popup Script
 * Manages the extension popup interface and controls
 */

class UATPPopup {
    constructor() {
        this.apiBase = 'http://localhost:8000';
        this.currentTab = null;
        this.status = null;
        
        this.init();
    }
    
    async init() {
        try {
            // Get current tab
            this.currentTab = await this.getCurrentTab();
            
            // Load initial status
            await this.loadStatus();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Hide loading and show content
            document.getElementById('loading').style.display = 'none';
            document.getElementById('main-content').style.display = 'block';
            
        } catch (error) {
            console.error('UATP Popup initialization failed:', error);
            this.showError('Failed to initialize UATP extension');
        }
    }
    
    async getCurrentTab() {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        return tab;
    }
    
    async loadStatus() {
        try {
            // Get status from content script
            const response = await chrome.tabs.sendMessage(this.currentTab.id, { 
                action: 'getStatus' 
            });
            
            if (response) {
                this.status = response;
                this.updateUI();
            } else {
                throw new Error('No response from content script');
            }
            
        } catch (error) {
            console.error('Failed to load status:', error);
            this.showDisconnectedState();
        }
    }
    
    updateUI() {
        if (!this.status) return;
        
        // Update platform info
        document.getElementById('platform-name').textContent = 
            this.capitalizeFirst(this.status.platform || 'Unknown');
        
        // Update session ID (shortened)
        const sessionId = this.status.sessionId || 'Unknown';
        document.getElementById('session-id').textContent = 
            sessionId.length > 12 ? sessionId.substring(0, 12) + '...' : sessionId;
        
        // Update auto-capture status
        const isCapturing = this.status.autoCapture;
        const indicator = document.getElementById('capture-indicator');
        const statusText = document.getElementById('capture-status');
        const toggleButton = document.getElementById('toggle-capture');
        
        if (isCapturing) {
            indicator.className = 'status-indicator status-active';
            statusText.textContent = 'Active';
            toggleButton.textContent = 'Disable Auto-Capture';
            toggleButton.className = 'button button-danger';
        } else {
            indicator.className = 'status-indicator status-inactive';
            statusText.textContent = 'Inactive';
            toggleButton.textContent = 'Enable Auto-Capture';
            toggleButton.className = 'button button-primary';
        }
        
        // Update stats
        document.getElementById('messages-captured').textContent = 
            this.status.lastCaptured || '0';
        
        // Load additional stats from API
        this.loadAPIStats();
    }
    
    async loadAPIStats() {
        try {
            const response = await fetch(`${this.apiBase}/api/v1/auto-capture/stats`);
            if (response.ok) {
                const data = await response.json();
                const stats = data.stats;
                
                // Update significance score
                const avgScore = stats.significance_engine?.avg_significance || 0;
                document.getElementById('significance-score').textContent = 
                    Math.round(avgScore * 100) + '%';
                
                // Update message count with API data
                if (stats.auto_captured) {
                    document.getElementById('messages-captured').textContent = 
                        stats.auto_captured.toString();
                }
            }
        } catch (error) {
            console.log('Could not load API stats:', error);
        }
    }
    
    setupEventListeners() {
        // Toggle auto-capture
        document.getElementById('toggle-capture').addEventListener('click', async () => {
            try {
                await chrome.tabs.sendMessage(this.currentTab.id, { 
                    action: 'toggleAutoCapture' 
                });
                
                // Reload status
                setTimeout(() => this.loadStatus(), 500);
                
            } catch (error) {
                console.error('Failed to toggle auto-capture:', error);
                this.showNotification('Failed to toggle auto-capture', 'error');
            }
        });
        
        // Capture now button
        document.getElementById('capture-now').addEventListener('click', async () => {
            try {
                await chrome.tabs.sendMessage(this.currentTab.id, { 
                    action: 'captureNow' 
                });
                
                this.showNotification('Capturing current conversation...', 'success');
                
            } catch (error) {
                console.error('Failed to trigger capture:', error);
                this.showNotification('Failed to capture conversation', 'error');
            }
        });
        
        // View dashboard button
        document.getElementById('view-dashboard').addEventListener('click', () => {
            chrome.tabs.create({ url: 'http://localhost:3000' });
        });
        
        // Settings button
        document.getElementById('settings').addEventListener('click', () => {
            chrome.runtime.openOptionsPage();
        });
        
        // Toggle switches
        document.getElementById('notifications-toggle').addEventListener('change', (e) => {
            chrome.storage.sync.set({ showNotifications: e.target.checked });
        });
        
        document.getElementById('quality-toggle').addEventListener('change', (e) => {
            const threshold = e.target.checked ? 0.8 : 0.6;
            chrome.storage.sync.set({ captureThreshold: threshold });
        });
        
        // Footer links
        document.getElementById('help-link').addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: 'https://docs.uatp.app/browser-extension' });
        });
        
        document.getElementById('website-link').addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: 'https://uatp.app' });
        });
        
        // Load saved settings for toggles
        this.loadToggleSettings();
    }
    
    async loadToggleSettings() {
        try {
            const settings = await chrome.storage.sync.get({
                showNotifications: true,
                captureThreshold: 0.6
            });
            
            document.getElementById('notifications-toggle').checked = settings.showNotifications;
            document.getElementById('quality-toggle').checked = settings.captureThreshold > 0.7;
            
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }
    
    showDisconnectedState() {
        // Update UI to show disconnected state
        document.getElementById('platform-name').textContent = 'Not Supported';
        document.getElementById('capture-status').textContent = 'Unavailable';
        document.getElementById('session-id').textContent = 'N/A';
        
        const indicator = document.getElementById('capture-indicator');
        indicator.className = 'status-indicator status-inactive';
        
        const toggleButton = document.getElementById('toggle-capture');
        toggleButton.textContent = 'Platform Not Supported';
        toggleButton.disabled = true;
        toggleButton.style.opacity = '0.5';
        
        // Disable capture now button
        const captureButton = document.getElementById('capture-now');
        captureButton.disabled = true;
        captureButton.style.opacity = '0.5';
    }
    
    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelectorAll('.notification');
        existing.forEach(n => n.remove());
        
        // Create new notification
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        
        if (type === 'error') {
            notification.style.background = 'rgba(239, 68, 68, 0.9)';
        } else if (type === 'success') {
            notification.style.background = 'rgba(16, 185, 129, 0.9)';
        }
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }
    
    showError(message) {
        document.getElementById('loading').innerHTML = `
            <div style="color: #ef4444;">
                <div style="font-size: 24px; margin-bottom: 16px;">⚠️</div>
                <div style="font-weight: 500; margin-bottom: 8px;">Connection Failed</div>
                <div style="font-size: 14px; opacity: 0.8;">${message}</div>
            </div>
        `;
    }
    
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new UATPPopup();
});