/**
 * UATP Universal AI Capture - Content Script
 * Automatically detects and captures AI conversations across all major platforms
 */

class UniversalAICapture {
    constructor() {
        this.apiBase = 'http://localhost:8000';
        this.apiKey = 'dev-key-001';
        this.sessionId = `web-${Date.now()}`;
        this.platform = this.detectPlatform();
        this.lastCapturedContent = new Set();
        this.isCapturing = false;
        this.captureQueue = [];
        
        // Platform-specific configurations
        this.platformConfigs = {
            'chatgpt': {
                messageSelector: '[data-message-author-role]',
                contentSelector: '.markdown, .whitespace-pre-wrap, .prose',
                userRoleAttr: 'data-message-author-role',
                streaming: true
            },
            'claude': {
                messageSelector: '[data-is-streaming], .font-claude-message, [data-testid*="message"]',
                contentSelector: '.whitespace-pre-wrap, .prose, .markdown',
                userIndicator: '[data-testid="user-message"]',
                streaming: true
            },
            'perplexity': {
                messageSelector: '.prose, [role="article"]',
                contentSelector: '.prose, .markdown-prose',
                streaming: false
            },
            'character': {
                messageSelector: '[data-testid="message"]',
                contentSelector: '.text-sm, .prose',
                streaming: true
            },
            'poe': {
                messageSelector: '.Message_message__',
                contentSelector: '.Markdown_markdownContainer__',
                streaming: true
            },
            'gemini': {
                messageSelector: '[data-test-id*="conversation-turn"]',
                contentSelector: '.markdown, .response-content',
                streaming: true
            },
            'copilot': {
                messageSelector: '.message',
                contentSelector: '.message-content, .markdown',
                streaming: true
            }
        };
        
        this.init();
    }
    
    detectPlatform() {
        const hostname = window.location.hostname.toLowerCase();
        if (hostname.includes('openai.com')) return 'chatgpt';
        if (hostname.includes('claude.ai')) return 'claude';
        if (hostname.includes('perplexity.ai')) return 'perplexity';
        if (hostname.includes('character.ai')) return 'character';
        if (hostname.includes('poe.com')) return 'poe';
        if (hostname.includes('gemini.google.com') || hostname.includes('bard.google.com')) return 'gemini';
        if (hostname.includes('copilot.microsoft.com')) return 'copilot';
        return 'unknown';
    }
    
    async init() {
        console.log(`🚀 UATP Universal AI Capture initialized for ${this.platform}`);
        
        // Load settings from storage
        await this.loadSettings();
        
        // Start monitoring
        this.startMutationObserver();
        this.startPeriodicCapture();
        
        // Initial capture of existing conversation
        setTimeout(() => this.captureExistingConversation(), 2000);
        
        // Show initialization notification
        this.showNotification('UATP Auto-Capture Enabled', 'success');
    }
    
    async loadSettings() {
        try {
            const settings = await chrome.storage.sync.get({
                apiBase: 'http://localhost:8000',
                apiKey: 'dev-key-001',
                autoCapture: true,
                captureThreshold: 0.6,
                showNotifications: true
            });
            
            this.apiBase = settings.apiBase;
            this.apiKey = settings.apiKey;
            this.autoCapture = settings.autoCapture;
            this.captureThreshold = settings.captureThreshold;
            this.showNotifications = settings.showNotifications;
        } catch (error) {
            console.log('UATP: Using default settings');
        }
    }
    
    startMutationObserver() {
        const observer = new MutationObserver((mutations) => {
            let shouldCapture = false;
            
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // Check if new content matches message patterns
                            if (this.isMessageNode(node)) {
                                shouldCapture = true;
                            }
                        }
                    });
                }
            });
            
            if (shouldCapture) {
                // Debounce rapid mutations
                clearTimeout(this.captureTimeout);
                this.captureTimeout = setTimeout(() => {
                    this.captureNewMessages();
                }, 1000);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: false
        });
        
        this.observer = observer;
    }
    
    isMessageNode(node) {
        const config = this.platformConfigs[this.platform];
        if (!config) return false;
        
        return node.matches && (
            node.matches(config.messageSelector) ||
            node.querySelector(config.messageSelector)
        );
    }
    
    startPeriodicCapture() {
        // Periodic backup capture in case mutations are missed
        setInterval(() => {
            if (!this.isCapturing) {
                this.captureNewMessages();
            }
        }, 10000); // Every 10 seconds
    }
    
    async captureExistingConversation() {
        console.log('UATP: Capturing existing conversation...');
        const messages = this.extractAllMessages();
        
        if (messages.length > 0) {
            await this.sendConversationToAPI(messages, 'existing_conversation');
            console.log(`UATP: Captured ${messages.length} existing messages`);
        }
    }
    
    async captureNewMessages() {
        if (this.isCapturing) return;
        
        this.isCapturing = true;
        try {
            const messages = this.extractAllMessages();
            const newMessages = this.filterNewMessages(messages);
            
            if (newMessages.length > 0) {
                await this.sendConversationToAPI(newMessages, 'new_messages');
                console.log(`UATP: Captured ${newMessages.length} new messages`);
                
                if (this.showNotifications && newMessages.length > 0) {
                    this.showNotification(`Captured ${newMessages.length} AI messages`, 'success');
                }
            }
        } catch (error) {
            console.error('UATP: Capture error:', error);
        } finally {
            this.isCapturing = false;
        }
    }
    
    extractAllMessages() {
        const config = this.platformConfigs[this.platform];
        if (!config) return [];
        
        const messages = [];
        const messageElements = document.querySelectorAll(config.messageSelector);
        
        messageElements.forEach((element, index) => {
            const content = this.extractMessageContent(element, config);
            const role = this.determineMessageRole(element, config);
            
            if (content && content.trim().length > 10) {
                const messageId = this.generateMessageId(content, role, index);
                messages.push({
                    role,
                    content: content.trim(),
                    messageId,
                    timestamp: Date.now(),
                    platform: this.platform,
                    url: window.location.href,
                    metadata: {
                        elementIndex: index,
                        hasCode: content.includes('```'),
                        hasLinks: /(https?:\/\/[^\s]+)/.test(content),
                        wordCount: content.split(/\s+/).length
                    }
                });
            }
        });
        
        return messages;
    }
    
    extractMessageContent(element, config) {
        let content = '';
        
        // Try content selector first
        const contentElement = element.querySelector(config.contentSelector);
        if (contentElement) {
            content = contentElement.textContent || contentElement.innerText || '';
        } else {
            content = element.textContent || element.innerText || '';
        }
        
        // Clean up content
        content = content.replace(/\s+/g, ' ').trim();
        
        return content;
    }
    
    determineMessageRole(element, config) {
        // Platform-specific role detection
        switch (this.platform) {
            case 'chatgpt':
                const role = element.getAttribute(config.userRoleAttr);
                return role === 'user' ? 'user' : 'assistant';
                
            case 'claude':
                return element.closest(config.userIndicator) ? 'user' : 'assistant';
                
            case 'perplexity':
                // Perplexity usually alternates, check for user indicators
                return element.textContent.includes('Pro Search') || 
                       element.previousElementSibling?.textContent.includes('You') ? 'user' : 'assistant';
                
            case 'character':
                return element.getAttribute('data-author') === 'user' ? 'user' : 'assistant';
                
            case 'poe':
                return element.classList.contains('Message_humanMessage__') ? 'user' : 'assistant';
                
            case 'gemini':
                return element.getAttribute('data-test-id')?.includes('user') ? 'user' : 'assistant';
                
            case 'copilot':
                return element.classList.contains('user-message') ? 'user' : 'assistant';
                
            default:
                // Fallback: alternate based on position or check for user indicators
                return this.guessMessageRole(element);
        }
    }
    
    guessMessageRole(element) {
        const text = element.textContent.toLowerCase();
        const userIndicators = ['you:', 'user:', 'human:', 'me:', 'question:'];
        const aiIndicators = ['assistant:', 'ai:', 'bot:', 'claude:', 'gpt:', 'response:'];
        
        for (const indicator of userIndicators) {
            if (text.includes(indicator)) return 'user';
        }
        
        for (const indicator of aiIndicators) {
            if (text.includes(indicator)) return 'assistant';
        }
        
        // Default to assistant if unsure
        return 'assistant';
    }
    
    generateMessageId(content, role, index) {
        const hash = this.simpleHash(content + role + index);
        return `${this.platform}-${hash}`;
    }
    
    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash).toString(36);
    }
    
    filterNewMessages(messages) {
        return messages.filter(msg => {
            const contentHash = this.simpleHash(msg.content + msg.role);
            if (this.lastCapturedContent.has(contentHash)) {
                return false;
            }
            this.lastCapturedContent.add(contentHash);
            return true;
        });
    }
    
    async sendConversationToAPI(messages, captureType) {
        if (!this.autoCapture || messages.length === 0) return;
        
        try {
            // Use enhanced significance analysis
            const response = await fetch(`${this.apiBase}/api/v1/auto-capture/analyze/conversation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.apiKey
                },
                body: JSON.stringify({
                    messages: messages,
                    source: 'browser_extension',
                    platform: this.platform,
                    metadata: {
                        url: window.location.href,
                        title: document.title,
                        captureType: captureType,
                        sessionId: this.sessionId,
                        timestamp: new Date().toISOString(),
                        userAgent: navigator.userAgent,
                        extensionVersion: '2.0.0'
                    }
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('UATP: Analysis result:', result);
                
                // Show significance feedback
                if (result.analysis && result.analysis.significance_score !== undefined) {
                    const score = result.analysis.significance_score;
                    const captured = result.analysis.capture;
                    const capsule = result.analysis.create_capsule;
                    
                    if (captured && this.showNotifications) {
                        let message = `Significance: ${(score * 100).toFixed(0)}%`;
                        if (capsule) message += ' • Capsule Created';
                        this.showNotification(message, 'info');
                    }
                }
            } else {
                console.error('UATP: API error:', response.status, response.statusText);
            }
        } catch (error) {
            console.error('UATP: Network error:', error);
        }
    }
    
    showNotification(message, type = 'info') {
        if (!this.showNotifications) return;
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `uatp-notification uatp-${type}`;
        notification.innerHTML = `
            <div class="uatp-notification-content">
                <div class="uatp-notification-icon">📦</div>
                <div class="uatp-notification-text">${message}</div>
                <div class="uatp-notification-close">×</div>
            </div>
        `;
        
        // Add styles if not already present
        if (!document.querySelector('#uatp-notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'uatp-notification-styles';
            styles.textContent = `
                .uatp-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 10000;
                    background: #1f2937;
                    color: white;
                    padding: 12px 16px;
                    border-radius: 8px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 14px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    animation: uatpSlideIn 0.3s ease-out;
                    max-width: 400px;
                }
                
                .uatp-notification-content {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .uatp-notification-icon {
                    flex-shrink: 0;
                }
                
                .uatp-notification-text {
                    flex: 1;
                }
                
                .uatp-notification-close {
                    cursor: pointer;
                    opacity: 0.7;
                    flex-shrink: 0;
                }
                
                .uatp-notification-close:hover {
                    opacity: 1;
                }
                
                .uatp-notification.uatp-success {
                    background: #059669;
                }
                
                .uatp-notification.uatp-error {
                    background: #dc2626;
                }
                
                .uatp-notification.uatp-info {
                    background: #2563eb;
                }
                
                @keyframes uatpSlideIn {
                    from {
                        opacity: 0;
                        transform: translateX(100%);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
                
                @keyframes uatpSlideOut {
                    from {
                        opacity: 1;
                        transform: translateX(0);
                    }
                    to {
                        opacity: 0;
                        transform: translateX(100%);
                    }
                }
            `;
            document.head.appendChild(styles);
        }
        
        // Add click handler for close button
        notification.querySelector('.uatp-notification-close').addEventListener('click', () => {
            notification.style.animation = 'uatpSlideOut 0.3s ease-in forwards';
            setTimeout(() => notification.remove(), 300);
        });
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'uatpSlideOut 0.3s ease-in forwards';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }
    
    // Public methods for extension popup/options
    getStatus() {
        return {
            platform: this.platform,
            sessionId: this.sessionId,
            isCapturing: this.isCapturing,
            lastCaptured: this.lastCapturedContent.size,
            autoCapture: this.autoCapture
        };
    }
    
    async toggleAutoCapture() {
        this.autoCapture = !this.autoCapture;
        await chrome.storage.sync.set({ autoCapture: this.autoCapture });
        
        this.showNotification(
            `Auto-capture ${this.autoCapture ? 'enabled' : 'disabled'}`,
            this.autoCapture ? 'success' : 'info'
        );
        
        return this.autoCapture;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.uatpCapture = new UniversalAICapture();
    });
} else {
    window.uatpCapture = new UniversalAICapture();
}

// Handle messages from popup/background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getStatus') {
        sendResponse(window.uatpCapture?.getStatus() || {});
    } else if (request.action === 'toggleAutoCapture') {
        window.uatpCapture?.toggleAutoCapture().then(sendResponse);
        return true; // Will respond asynchronously
    } else if (request.action === 'captureNow') {
        window.uatpCapture?.captureNewMessages();
        sendResponse({ success: true });
    }
});