import Foundation
import Network
import Combine

/// Main API client for UATP backend communication
/// Follows Steve Jobs philosophy: It just works.
@MainActor
class UATPAPIClient: ObservableObject {
    static let shared = UATPAPIClient()
    
    // MARK: - Published Properties
    @Published var isConnected = false
    @Published var captureCount = 0
    @Published var lastCaptureTime: Date?
    @Published var connectionStatus = "Checking connection..."
    
    // MARK: - Private Properties
    private var baseURL: String = ""
    private let apiKey = "dev-key-001" // Default development key
    private let monitor = NWPathMonitor()
    private let monitorQueue = DispatchQueue(label: "NetworkMonitor")
    private var session: URLSession
    
    private init() {
        // Configure URLSession for optimal performance
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10
        config.timeoutIntervalForResource = 30
        config.waitsForConnectivity = true
        self.session = URLSession(configuration: config)
        
        // Start network monitoring
        startNetworkMonitoring()
    }
    
    // MARK: - Initialization
    func initialize() {
        Task {
            await discoverUATPBackend()
        }
    }
    
    // MARK: - Network Discovery
    /// Automatically discovers UATP backend on local network
    /// True Steve Jobs magic - zero configuration
    private func discoverUATPBackend() async {
        connectionStatus = "Discovering UATP backend..."
        
        let candidates = [
            "http://localhost:9090",
            "http://127.0.0.1:9090",
            "http://192.168.1.79:9090", // From setup instructions
            getLocalNetworkIP() + ":9090"
        ].compactMap { $0 }
        
        for candidate in candidates {
            if await testConnection(to: candidate) {
                baseURL = candidate
                isConnected = true
                connectionStatus = "Connected to UATP"
                print("✅ UATP backend discovered at: \(candidate)")
                return
            }
        }
        
        // Fallback to manual configuration
        connectionStatus = "Backend not found. Check settings."
        isConnected = false
    }
    
    /// Test connection to a potential backend URL
    private func testConnection(to url: String) async -> Bool {
        guard let healthURL = URL(string: "\(url)/api/v1/health") else { return false }
        
        do {
            let (data, response) = try await session.data(from: healthURL)
            
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 200 {
                // Verify it's actually UATP by checking response structure
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   json["status"] as? String == "healthy" {
                    return true
                }
            }
        } catch {
            // Silent failure for discovery
        }
        
        return false
    }
    
    /// Get local network IP for discovery
    private func getLocalNetworkIP() -> String? {
        var address: String?
        var ifaddr: UnsafeMutablePointer<ifaddrs>?
        
        if getifaddrs(&ifaddr) == 0 {
            var ptr = ifaddr
            while ptr != nil {
                defer { ptr = ptr?.pointee.ifa_next }
                
                let interface = ptr?.pointee
                let addrFamily = interface?.ifa_addr.pointee.sa_family
                
                if addrFamily == UInt8(AF_INET) {
                    let name = String(cString: (interface?.ifa_name)!)
                    if name == "en0" || name == "en1" { // WiFi interfaces
                        var hostname = [CChar](repeating: 0, count: Int(NI_MAXHOST))
                        getnameinfo(interface?.ifa_addr, socklen_t((interface?.ifa_addr.pointee.sa_len)!),
                                   &hostname, socklen_t(hostname.count),
                                   nil, socklen_t(0), NI_NUMERICHOST)
                        address = String(cString: hostname)
                        break
                    }
                }
            }
            freeifaddrs(ifaddr)
        }
        
        return address.map { "http://\($0)" }
    }
    
    // MARK: - Network Monitoring
    private func startNetworkMonitoring() {
        monitor.pathUpdateHandler = { [weak self] path in
            Task { @MainActor in
                if path.status == .satisfied && !self?.isConnected ?? true {
                    // Network came back, try to reconnect
                    await self?.discoverUATPBackend()
                } else if path.status != .satisfied {
                    self?.isConnected = false
                    self?.connectionStatus = "No network connection"
                }
            }
        }
        monitor.start(queue: monitorQueue)
    }
    
    // MARK: - Capture Methods
    /// Capture a conversation with intelligent parsing
    func captureConversation(text: String, platform: String = "unknown") async -> CaptureResult {
        guard isConnected, !baseURL.isEmpty else {
            return CaptureResult(success: false, message: "Not connected to UATP backend")
        }
        
        // Parse the conversation text
        let parser = ConversationParser()
        let parsedConversation = parser.parseConversation(text: text, platform: platform)
        
        // Choose the best endpoint based on platform
        let endpoint: String
        switch platform.lowercased() {
        case "openai", "chatgpt":
            endpoint = "\(baseURL)/api/v1/live/capture/openai"
        case "claude", "anthropic":
            endpoint = "\(baseURL)/api/v1/live/capture/claude"
        default:
            endpoint = "\(baseURL)/api/v1/live/capture/message"
        }
        
        guard let url = URL(string: endpoint) else {
            return CaptureResult(success: false, message: "Invalid API endpoint")
        }
        
        // Build request payload
        let payload = buildPayload(for: parsedConversation, platform: platform)
        
        do {
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            
            let (data, response) = try await session.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 200 {
                    // Success!
                    captureCount += 1
                    lastCaptureTime = Date()
                    
                    // Try to extract session_id from response
                    if let responseData = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let sessionId = responseData["session_id"] as? String {
                        return CaptureResult(success: true, message: "Captured successfully", sessionId: sessionId)
                    }
                    
                    return CaptureResult(success: true, message: "Captured successfully")
                } else {
                    // Parse error message if available
                    if let errorData = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let errorMessage = errorData["error"] as? String {
                        return CaptureResult(success: false, message: "Server error: \(errorMessage)")
                    }
                    return CaptureResult(success: false, message: "Server error (\(httpResponse.statusCode))")
                }
            }
            
            return CaptureResult(success: false, message: "Invalid response from server")
            
        } catch {
            return CaptureResult(success: false, message: "Network error: \(error.localizedDescription)")
        }
    }
    
    /// Build appropriate payload based on conversation and platform
    private func buildPayload(for conversation: ParsedConversation, platform: String) -> [String: Any] {
        let sessionId = "ios-\(Date().timeIntervalSince1970)-\(UUID().uuidString.prefix(8))"
        let timestamp = ISO8601DateFormatter().string(from: Date())
        
        let metadata: [String: Any] = [
            "source": "ios_app",
            "timestamp": timestamp,
            "platform": platform,
            "app_version": "1.0",
            "device": UIDevice.current.model
        ]
        
        switch platform.lowercased() {
        case "openai", "chatgpt":
            return [
                "session_id": sessionId,
                "user_id": "ios_user",
                "messages": conversation.messages.map { message in
                    [
                        "role": message.role,
                        "content": message.content
                    ]
                },
                "model": conversation.model ?? "gpt-3.5-turbo",
                "metadata": metadata
            ]
            
        case "claude", "anthropic":
            return [
                "session_id": sessionId,
                "user_id": "ios_user",
                "user_message": conversation.userMessage ?? "",
                "assistant_message": conversation.assistantMessage ?? "",
                "metadata": metadata
            ]
            
        default:
            // Generic message format
            return [
                "session_id": sessionId,
                "user_id": "ios_user",
                "platform": platform,
                "role": "user",
                "content": conversation.rawText,
                "metadata": metadata
            ]
        }
    }
    
    // MARK: - Manual Configuration
    func setBackendURL(_ url: String) {
        baseURL = url
        Task {
            isConnected = await testConnection(to: url)
            connectionStatus = isConnected ? "Connected" : "Failed to connect"
        }
    }
}

// MARK: - Data Models
struct CaptureResult {
    let success: Bool
    let message: String
    let sessionId: String?
    
    init(success: Bool, message: String, sessionId: String? = nil) {
        self.success = success
        self.message = message
        self.sessionId = sessionId
    }
}

struct ParsedConversation {
    let rawText: String
    let messages: [ConversationMessage]
    let userMessage: String?
    let assistantMessage: String?
    let model: String?
    let platform: String
}

struct ConversationMessage {
    let role: String // "user" or "assistant"
    let content: String
}

#if canImport(UIKit)
import UIKit
#endif