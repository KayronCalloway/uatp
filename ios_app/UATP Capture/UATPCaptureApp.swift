import SwiftUI

@main
struct UATPCaptureApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(UATPAPIClient.shared)
                .onAppear {
                    // Initialize the API client with user settings
                    UATPAPIClient.shared.initialize()
                }
        }
    }
}