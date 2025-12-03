import SwiftUI
import Foundation

struct ContentView: View {
    @StateObject private var captureService = CaptureService()
    @State private var conversationText = ""
    @State private var selectedPlatform = "openai"
    @State private var isCapturing = false
    @State private var lastCaptureStatus = ""
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Header
                Text("UATP Live Capture")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                // Platform Selection
                Picker("Platform", selection: $selectedPlatform) {
                    Text("OpenAI / ChatGPT").tag("openai")
                    Text("Claude").tag("claude")
                    Text("Other").tag("other")
                }
                .pickerStyle(SegmentedPickerStyle())
                
                // Conversation Input
                VStack(alignment: .leading) {
                    Text("Paste Conversation:")
                        .font(.headline)
                    
                    TextEditor(text: $conversationText)
                        .frame(minHeight: 200)
                        .border(Color.gray, width: 1)
                        .cornerRadius(8)
                }
                
                // Capture Button
                Button(action: captureConversation) {
                    HStack {
                        if isCapturing {
                            ProgressView()
                                .scaleEffect(0.8)
                        }
                        Text(isCapturing ? "Capturing..." : "Capture to UATP")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(conversationText.isEmpty ? Color.gray : Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
                .disabled(conversationText.isEmpty || isCapturing)
                
                // Status Display
                if !lastCaptureStatus.isEmpty {
                    Text(lastCaptureStatus)
                        .padding()
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(8)
                }
                
                // Instructions
                VStack(alignment: .leading, spacing: 8) {
                    Text("Quick Usage:")
                        .font(.headline)
                    Text("1. Copy conversation from ChatGPT/Claude")
                    Text("2. Paste above and select platform")
                    Text("3. Tap 'Capture to UATP'")
                    Text("4. Conversation saved automatically!")
                }
                .font(.caption)
                .foregroundColor(.secondary)
                
                Spacer()
            }
            .padding()
            .navigationBarHidden(true)
        }
    }
    
    private func captureConversation() {
        guard !conversationText.isEmpty else { return }
        
        isCapturing = true
        
        Task {
            do {
                let success = await captureService.submitConversation(
                    text: conversationText,
                    platform: selectedPlatform
                )
                
                await MainActor.run {
                    isCapturing = false
                    if success {
                        lastCaptureStatus = "✅ Conversation captured successfully!"
                        conversationText = "" // Clear for next use
                    } else {
                        lastCaptureStatus = "❌ Capture failed. Check connection."
                    }
                    
                    // Clear status after 3 seconds
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                        lastCaptureStatus = ""
                    }
                }
            }
        }
    }
}

// MARK: - Capture Service
@MainActor
class CaptureService: ObservableObject {
    private let baseURL: String
    private let apiKey = "your_api_key_here" // Replace with actual key
    
    init() {
        // Auto-detect Mac IP or use ngrok URL
        self.baseURL = findUATPBackend()
    }
    
    func submitConversation(text: String, platform: String) async -> Bool {
        let endpoint = "\(baseURL)/api/v1/live/capture/\(platform)"
        
        guard let url = URL(string: endpoint) else {
            print("Invalid URL: \(endpoint)")
            return false
        }
        
        let payload: [String: Any] = [
            "session_id": "ios-\(Date().timeIntervalSince1970)",
            "user_id": "ios_user",
            "user_message": text,
            "assistant_message": "", // Will be parsed from text
            "metadata": [
                "source": "ios_app",
                "timestamp": ISO8601DateFormatter().string(from: Date())
            ]
        ]
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            
            let (data, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 200 {
                print("Successfully captured conversation")
                return true
            } else {
                print("HTTP Error: \(response)")
                return false
            }
        } catch {
            print("Network error: \(error)")
            return false
        }
    }
    
    private func findUATPBackend() -> String {
        // Try common local network addresses
        let candidates = [
            "http://localhost:9090",           // Direct localhost
            "http://127.0.0.1:9090",          // Explicit loopback
            "http://192.168.1.100:9090",      // Common local IP
            "https://your-ngrok-url.ngrok.io" // Ngrok tunnel
        ]
        
        // In a real implementation, you'd ping these to find the active one
        // For now, return the most likely candidate
        return candidates[3] // Use ngrok for initial setup
    }
}

#Preview {
    ContentView()
}