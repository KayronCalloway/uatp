/**
 * UATP Browser Extension - Background Service Worker
 * Handles extension lifecycle, updates, and cross-tab communication
 */

class UATPBackground {
    constructor() {
        this.apiBase = 'http://localhost:8000';
        this.activeSessions = new Map();
        this.globalStats = {
            totalCaptures: 0,
            sessionsActive: 0,
            lastUpdate: Date.now()
        };
        
        this.init();
    }
    
    init() {
        // Handle extension startup
        chrome.runtime.onStartup.addListener(() => {
            this.onStartup();
        });
        
        // Handle extension installation
        chrome.runtime.onInstalled.addListener((details) => {
            this.onInstalled(details);
        });
        
        // Handle tab updates
        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            this.onTabUpdated(tabId, changeInfo, tab);
        });
        
        // Handle tab removal
        chrome.tabs.onRemoved.addListener((tabId) => {
            this.onTabRemoved(tabId);
        });
        
        // Handle messages from content scripts and popup
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
        });
        
        // Periodic stats update
        setInterval(() => {
            this.updateGlobalStats();
        }, 30000); // Every 30 seconds
        
        console.log('🚀 UATP Background Service Worker initialized');
    }
    
    onStartup() {
        console.log('UATP: Extension startup');
        this.initializeDefaultSettings();
    }
    
    onInstalled(details) {
        if (details.reason === 'install') {
            console.log('UATP: First time installation');
            this.showWelcomeNotification();
            this.openOnboardingPage();
        } else if (details.reason === 'update') {
            console.log('UATP: Extension updated');
            this.handleUpdate(details.previousVersion);
        }
        
        this.initializeDefaultSettings();
    }
    
    async initializeDefaultSettings() {
        const defaultSettings = {
            apiBase: 'http://localhost:8000',
            apiKey: 'dev-key-001',
            autoCapture: true,
            captureThreshold: 0.6,
            showNotifications: true,
            enableAnalytics: true,
            syncSettings: false
        };
        
        // Only set defaults if not already configured
        const existing = await chrome.storage.sync.get(Object.keys(defaultSettings));
        const toSet = {};
        
        for (const [key, value] of Object.entries(defaultSettings)) {
            if (existing[key] === undefined) {
                toSet[key] = value;
            }
        }
        
        if (Object.keys(toSet).length > 0) {
            await chrome.storage.sync.set(toSet);
            console.log('UATP: Initialized default settings:', toSet);
        }
    }
    
    onTabUpdated(tabId, changeInfo, tab) {
        if (changeInfo.status === 'complete' && tab.url) {
            // Check if this is a supported AI platform
            if (this.isSupportedPlatform(tab.url)) {
                // Inject content script if not already injected
                this.ensureContentScriptInjected(tabId);
            }
        }
    }
    
    onTabRemoved(tabId) {
        // Clean up session data for removed tab
        if (this.activeSessions.has(tabId)) {
            console.log(`UATP: Cleaning up session for closed tab ${tabId}`);
            this.activeSessions.delete(tabId);
            this.globalStats.sessionsActive = Math.max(0, this.globalStats.sessionsActive - 1);
        }
    }
    
    isSupportedPlatform(url) {
        const supportedDomains = [
            'chat.openai.com',
            'claude.ai',
            'perplexity.ai',
            'character.ai',
            'poe.com',
            'bard.google.com',
            'gemini.google.com',
            'copilot.microsoft.com',
            'huggingface.co'
        ];
        
        try {
            const urlObj = new URL(url);
            return supportedDomains.some(domain => urlObj.hostname.includes(domain));
        } catch {
            return false;
        }
    }
    
    async ensureContentScriptInjected(tabId) {
        try {
            // Try to ping existing content script
            await chrome.tabs.sendMessage(tabId, { action: 'ping' });
        } catch {
            // Content script not responding, inject it
            try {
                await chrome.scripting.executeScript({
                    target: { tabId: tabId },
                    files: ['content.js']
                });
                
                await chrome.scripting.insertCSS({
                    target: { tabId: tabId },
                    files: ['styles.css']
                });
                
                console.log(`UATP: Content script injected into tab ${tabId}`);
            } catch (error) {
                console.error(`UATP: Failed to inject content script into tab ${tabId}:`, error);
            }
        }
    }
    
    handleMessage(request, sender, sendResponse) {
        switch (request.action) {
            case 'ping':
                sendResponse({ pong: true });
                break;
                
            case 'registerSession':
                this.registerSession(sender.tab.id, request.sessionData);
                sendResponse({ success: true });
                break;
                
            case 'updateSessionStats':
                this.updateSessionStats(sender.tab.id, request.stats);
                sendResponse({ success: true });
                break;
                
            case 'getGlobalStats':
                sendResponse(this.globalStats);
                break;
                
            case 'captureCompleted':
                this.onCaptureCompleted(sender.tab.id, request.captureData);
                sendResponse({ success: true });
                break;
                
            default:
                console.log('UATP: Unknown message:', request);
                sendResponse({ error: 'Unknown action' });
        }
        
        return true; // Keep message channel open
    }
    
    registerSession(tabId, sessionData) {
        this.activeSessions.set(tabId, {
            ...sessionData,
            startTime: Date.now(),
            lastUpdate: Date.now()
        });
        
        this.globalStats.sessionsActive = this.activeSessions.size;
        console.log(`UATP: Registered session for tab ${tabId}:`, sessionData);
    }
    
    updateSessionStats(tabId, stats) {
        if (this.activeSessions.has(tabId)) {
            const session = this.activeSessions.get(tabId);
            this.activeSessions.set(tabId, {
                ...session,
                ...stats,
                lastUpdate: Date.now()
            });
        }
    }
    
    onCaptureCompleted(tabId, captureData) {
        this.globalStats.totalCaptures += captureData.messageCount || 1;
        this.globalStats.lastUpdate = Date.now();
        
        // Update badge with total captures
        this.updateBadge();
        
        // Send to analytics if enabled
        this.sendAnalytics('capture_completed', {
            tabId,
            platform: captureData.platform,
            messageCount: captureData.messageCount,
            significanceScore: captureData.significanceScore
        });
    }
    
    updateBadge() {
        const count = this.globalStats.totalCaptures;
        let badgeText = '';
        
        if (count > 0) {
            if (count < 1000) {
                badgeText = count.toString();
            } else if (count < 10000) {
                badgeText = Math.floor(count / 100) / 10 + 'k';
            } else {
                badgeText = Math.floor(count / 1000) + 'k';
            }
        }
        
        chrome.action.setBadgeText({ text: badgeText });
        chrome.action.setBadgeBackgroundColor({ color: '#10b981' });
    }
    
    async updateGlobalStats() {
        // Clean up stale sessions (no updates in 10 minutes)
        const now = Date.now();
        const staleThreshold = 10 * 60 * 1000; // 10 minutes
        
        for (const [tabId, session] of this.activeSessions.entries()) {
            if (now - session.lastUpdate > staleThreshold) {
                this.activeSessions.delete(tabId);
            }
        }
        
        this.globalStats.sessionsActive = this.activeSessions.size;
        
        // Sync stats with API if available
        try {
            const settings = await chrome.storage.sync.get(['apiBase', 'enableAnalytics']);
            if (settings.enableAnalytics) {
                await this.syncStatsWithAPI(settings.apiBase);
            }
        } catch (error) {
            // Silent fail - API sync is optional
        }
    }
    
    async syncStatsWithAPI(apiBase) {
        try {
            const response = await fetch(`${apiBase}/api/v1/auto-capture/stats`);
            if (response.ok) {
                const data = await response.json();
                // Update local stats with server data if available
                if (data.stats && data.stats.total_captured) {
                    this.globalStats.totalCaptures = Math.max(
                        this.globalStats.totalCaptures,
                        data.stats.total_captured
                    );
                    this.updateBadge();
                }
            }
        } catch (error) {
            // Silent fail - API sync is optional
        }
    }
    
    async sendAnalytics(event, data) {
        try {
            const settings = await chrome.storage.sync.get(['enableAnalytics', 'apiBase']);
            if (!settings.enableAnalytics) return;
            
            // Send anonymous analytics data
            await fetch(`${settings.apiBase}/api/v1/analytics/extension-event`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    event,
                    data: {
                        ...data,
                        timestamp: Date.now(),
                        version: '2.0.0'
                    }
                })
            });
        } catch (error) {
            // Silent fail - analytics are optional
        }
    }
    
    showWelcomeNotification() {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon128.png',
            title: 'UATP AI Capture Installed!',
            message: 'Universal AI accountability is now active. Visit any AI platform to start capturing conversations.'
        });
    }
    
    handleUpdate(previousVersion) {
        // Handle version-specific updates
        console.log(`UATP: Updated from ${previousVersion} to 2.0.0`);
        
        // Show update notification
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon128.png',
            title: 'UATP Extension Updated',
            message: 'New features: Enhanced significance detection, multi-platform support, and improved performance.'
        });
    }
    
    openOnboardingPage() {
        chrome.tabs.create({
            url: chrome.runtime.getURL('onboarding.html')
        });
    }
}

// Initialize the background service worker
new UATPBackground();