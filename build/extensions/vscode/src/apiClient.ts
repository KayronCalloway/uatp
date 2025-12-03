
import * as vscode from 'vscode';

export class UATPApiClient {
    private apiBase: string = 'http://localhost:8000';
    
    constructor(private context: vscode.ExtensionContext) {}
    
    async startCaptureSession(data: any): Promise<void> {
        // API client implementation
    }
    
    async endCaptureSession(session: any): Promise<boolean> {
        // API client implementation
        return false;
    }
    
    async captureFileChange(sessionId: string, event: any): Promise<void> {
        // API client implementation
    }
    
    async captureAIInteraction(sessionId: string, interaction: any): Promise<void> {
        // API client implementation
    }
    
    async captureTerminalCommand(sessionId: string, command: any): Promise<void> {
        // API client implementation
    }
    
    async captureGitActivity(sessionId: string, activity: any): Promise<void> {
        // API client implementation
    }
}
            