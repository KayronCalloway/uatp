
// UATP Automatic Conversation Capture
(function() {
    const UATP_API = 'http://192.168.1.79:9090';
    const API_KEY = 'dev-key-001';
    
    let lastCapturedConversation = '';
    let sessionId = 'web-' + Date.now();
    
    function detectPlatform() {
        if (window.location.hostname.includes('openai.com')) return 'chatgpt';
        if (window.location.hostname.includes('claude.ai')) return 'claude';
        return 'unknown';
    }
    
    function extractConversations() {
        const platform = detectPlatform();
        let conversations = [];
        
        if (platform === 'chatgpt') {
            // ChatGPT conversation extraction
            const messages = document.querySelectorAll('[data-message-author-role]');
            messages.forEach(msg => {
                const role = msg.getAttribute('data-message-author-role');
                const content = msg.querySelector('.markdown, .whitespace-pre-wrap')?.textContent?.trim();
                if (content && content !== lastCapturedConversation) {
                    conversations.push({ role, content });
                }
            });
        } else if (platform === 'claude') {
            // Claude conversation extraction
            const messages = document.querySelectorAll('[data-is-streaming], .font-claude-message');
            messages.forEach(msg => {
                const isUser = msg.closest('[data-testid="user-message"]') !== null;
                const role = isUser ? 'user' : 'assistant';
                const content = msg.textContent?.trim();
                if (content && content !== lastCapturedConversation) {
                    conversations.push({ role, content });
                }
            });
        }
        
        return conversations;
    }
    
    async function captureMessage(role, content, platform) {
        try {
            const response = await fetch(`${UATP_API}/api/v1/live/capture/message`, {
                method: 'POST',
                headers: {
                    'X-API-Key': API_KEY,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    user_id: role === 'user' ? 'web-user' : 'ai-assistant',
                    platform: platform,
                    role: role,
                    content: content,
                    metadata: { 
                        source: 'safari_extension', 
                        url: window.location.href,
                        automatic: true 
                    }
                })
            });
            
            if (response.ok) {
                console.log('✅ UATP: Captured', role, 'message');
                showCaptureNotification();
            }
        } catch (error) {
            console.log('❌ UATP: Capture failed', error);
        }
    }
    
    function showCaptureNotification() {
        // Create subtle notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 10000;
            background: #10b981; color: white; padding: 8px 16px;
            border-radius: 8px; font-size: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: fadeInOut 3s ease-in-out forwards;
        `;
        notification.textContent = '📦 UATP Captured';
        
        // Add fade animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInOut {
                0% { opacity: 0; transform: translateY(-10px); }
                20% { opacity: 1; transform: translateY(0); }
                80% { opacity: 1; transform: translateY(0); }
                100% { opacity: 0; transform: translateY(-10px); }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }
    
    function monitorConversations() {
        const conversations = extractConversations();
        const platform = detectPlatform();
        
        conversations.forEach(async (conv, index) => {
            if (conv.content && conv.content.length > 10) {
                // Add small delay to avoid overwhelming the API
                setTimeout(() => {
                    captureMessage(conv.role, conv.content, platform);
                    lastCapturedConversation = conv.content;
                }, index * 500);
            }
        });
    }
    
    // Monitor for new messages
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length > 0) {
                // Debounce to avoid excessive calls
                clearTimeout(window.uatpTimeout);
                window.uatpTimeout = setTimeout(monitorConversations, 1000);
            }
        });
    });
    
    // Start monitoring
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Initial capture of existing conversation
    setTimeout(monitorConversations, 2000);
    
    console.log('🚀 UATP Auto-Capture enabled for', detectPlatform());
})();
