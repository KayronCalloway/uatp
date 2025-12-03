/**
 * UATP Capture Manager - Core capture logic for VS Code development workflows
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { UATPApiClient } from './apiClient';
import { SignificanceAnalyzer } from './significanceAnalyzer';

export interface CaptureSession {
    id: string;
    workspacePath: string;
    startTime: Date;
    endTime?: Date;
    fileChanges: FileChangeEvent[];
    aiInteractions: AIInteractionEvent[];
    terminalCommands: TerminalCommandEvent[];
    gitActivities: GitActivityEvent[];
    significanceScore: number;
}

export interface FileChangeEvent {
    filePath: string;
    changeType: 'create' | 'modify' | 'delete' | 'rename';
    content?: string;
    diff?: string;
    timestamp: Date;
    language: string;
    linesChanged: number;
}

export interface AIInteractionEvent {
    type: 'copilot_suggestion' | 'inline_chat' | 'external_ai' | 'manual_entry';
    userInput: string;
    aiResponse: string;
    timestamp: Date;
    context: string;
    accepted: boolean;
}

export interface TerminalCommandEvent {
    command: string;
    output?: string;
    exitCode?: number;
    timestamp: Date;
    workingDirectory: string;
}

export interface GitActivityEvent {
    type: 'commit' | 'branch' | 'merge' | 'pull' | 'push' | 'tag';
    details: string;
    timestamp: Date;
    author?: string;
    files?: string[];
}

export class UATPCaptureManager {
    private currentSession?: CaptureSession;
    private apiClient: UATPApiClient;
    private significanceAnalyzer: SignificanceAnalyzer;
    private fileWatcher?: vscode.FileSystemWatcher;
    private terminalWatcher?: vscode.Disposable;
    private autoCapture: boolean = true;
    
    constructor(private context: vscode.ExtensionContext) {
        this.apiClient = new UATPApiClient(context);
        this.significanceAnalyzer = new SignificanceAnalyzer();
    }
    
    async initialize() {
        // Load settings
        await this.loadSettings();
        
        // Set up file system watcher
        this.setupFileWatcher();
        
        // Set up terminal watcher
        this.setupTerminalWatcher();
        
        // Set up Git watcher
        this.setupGitWatcher();
        
        // Auto-start capture if enabled
        if (this.autoCapture && vscode.workspace.workspaceFolders) {
            await this.startCaptureSession();
        }
        
        console.log('✅ UATP Capture Manager initialized');
    }
    
    private async loadSettings() {
        const config = vscode.workspace.getConfiguration('uatp');
        this.autoCapture = config.get<boolean>('autoCapture', true);
    }
    
    async startCaptureSession(): Promise<string> {
        if (this.currentSession) {
            throw new Error('Capture session already active');
        }
        
        const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspacePath) {
            throw new Error('No workspace folder found');
        }
        
        const sessionId = `vscode-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        this.currentSession = {
            id: sessionId,
            workspacePath,
            startTime: new Date(),
            fileChanges: [],
            aiInteractions: [],
            terminalCommands: [],
            gitActivities: [],
            significanceScore: 0
        };
        
        // Set context for command palette
        vscode.commands.executeCommand('setContext', 'uatp.sessionActive', true);
        
        // Notify API about session start
        try {
            await this.apiClient.startCaptureSession({
                sessionId,
                workspacePath,
                projectName: path.basename(workspacePath),
                language: await this.detectPrimaryLanguage(),
                metadata: {
                    vscodeVersion: vscode.version,
                    extensionVersion: this.context.extension.packageJSON.version,
                    platform: process.platform
                }
            });
        } catch (error) {
            console.error('Failed to start API session:', error);
            // Continue with local capture even if API fails
        }
        
        vscode.window.showInformationMessage(
            `🚀 UATP capture session started for ${path.basename(workspacePath)}`
        );
        
        return sessionId;
    }
    
    async endCaptureSession(): Promise<void> {
        if (!this.currentSession) {
            throw new Error('No active capture session');
        }
        
        this.currentSession.endTime = new Date();
        this.currentSession.significanceScore = await this.significanceAnalyzer.calculateSessionSignificance(this.currentSession);
        
        // Set context for command palette
        vscode.commands.executeCommand('setContext', 'uatp.sessionActive', false);
        
        // Send final session data to API
        try {
            const capsuleCreated = await this.apiClient.endCaptureSession(this.currentSession);
            
            if (capsuleCreated) {
                vscode.window.showInformationMessage(
                    `✅ UATP capture session completed. Capsule created with significance ${(this.currentSession.significanceScore * 100).toFixed(0)}%`
                );
            } else {
                vscode.window.showInformationMessage(
                    `📝 UATP capture session completed. Session recorded (significance: ${(this.currentSession.significanceScore * 100).toFixed(0)}%)`
                );
            }
        } catch (error) {
            console.error('Failed to end API session:', error);
            vscode.window.showWarningMessage('Failed to sync session with UATP API');
        }
        
        // Store session locally as backup
        await this.storeSessionLocally(this.currentSession);
        
        this.currentSession = undefined;
    }
    
    private setupFileWatcher() {
        const config = vscode.workspace.getConfiguration('uatp');
        const monitoredTypes = config.get<string[]>('monitoredFileTypes', []);
        
        if (!config.get<boolean>('captureFileChanges', true)) {
            return;
        }
        
        // Watch for file changes
        this.fileWatcher = vscode.workspace.createFileSystemWatcher('**/*');
        
        this.fileWatcher.onDidCreate(async (uri) => {
            await this.onFileChange(uri, 'create');
        });
        
        this.fileWatcher.onDidChange(async (uri) => {
            await this.onFileChange(uri, 'modify');
        });
        
        this.fileWatcher.onDidDelete(async (uri) => {
            await this.onFileChange(uri, 'delete');
        });
        
        // Watch for active text editor changes
        vscode.workspace.onDidChangeTextDocument(async (event) => {
            if (event.document.uri.scheme === 'file' && event.contentChanges.length > 0) {
                await this.onTextDocumentChange(event);
            }
        });
    }
    
    private setupTerminalWatcher() {
        const config = vscode.workspace.getConfiguration('uatp');
        if (!config.get<boolean>('captureTerminalOutput', true)) {
            return;
        }
        
        // Watch for terminal events
        this.terminalWatcher = vscode.window.onDidOpenTerminal(async (terminal) => {
            // Note: VS Code API has limitations for terminal output capture
            // This is a placeholder for terminal monitoring
            await this.onTerminalActivity({
                command: 'terminal_opened',
                timestamp: new Date(),
                workingDirectory: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || ''
            });
        });
    }
    
    private setupGitWatcher() {
        const config = vscode.workspace.getConfiguration('uatp');
        if (!config.get<boolean>('captureGitActivity', true)) {
            return;
        }
        
        // Monitor Git activities through file system changes in .git folder
        const gitWatcher = vscode.workspace.createFileSystemWatcher('**/.git/**');
        
        gitWatcher.onDidChange(async (uri) => {
            if (uri.fsPath.includes('COMMIT_EDITMSG') || uri.fsPath.includes('HEAD')) {
                await this.detectGitActivity();
            }
        });
        
        this.context.subscriptions.push(gitWatcher);
    }
    
    private async onFileChange(uri: vscode.Uri, changeType: 'create' | 'modify' | 'delete') {
        if (!this.currentSession) return;
        
        const filePath = vscode.workspace.asRelativePath(uri);
        const language = this.getLanguageFromPath(filePath);
        
        // Skip non-code files and hidden files
        if (!this.shouldMonitorFile(filePath, language)) {
            return;
        }
        
        let content: string | undefined;
        let linesChanged = 0;
        
        try {
            if (changeType !== 'delete') {
                const document = await vscode.workspace.openTextDocument(uri);
                content = document.getText();
                linesChanged = document.lineCount;
            }
        } catch (error) {
            console.error('Failed to read file content:', error);
        }
        
        const fileChangeEvent: FileChangeEvent = {
            filePath,
            changeType,
            content: content?.substring(0, 5000), // Limit content size
            timestamp: new Date(),
            language,
            linesChanged
        };
        
        this.currentSession.fileChanges.push(fileChangeEvent);
        
        // Analyze significance and potentially send to API
        if (await this.significanceAnalyzer.isSignificantFileChange(fileChangeEvent)) {
            await this.apiClient.captureFileChange(this.currentSession.id, fileChangeEvent);
        }
    }
    
    private async onTextDocumentChange(event: vscode.TextDocumentChangeEvent) {
        if (!this.currentSession) return;
        
        const filePath = vscode.workspace.asRelativePath(event.document.uri);
        const language = event.document.languageId;
        
        if (!this.shouldMonitorFile(filePath, language)) {
            return;
        }
        
        // Calculate diff information
        const totalChanges = event.contentChanges.reduce((sum, change) => sum + change.text.length, 0);
        
        if (totalChanges > 10) { // Only capture meaningful changes
            const fileChangeEvent: FileChangeEvent = {
                filePath,
                changeType: 'modify',
                content: event.document.getText().substring(0, 5000),
                timestamp: new Date(),
                language,
                linesChanged: event.contentChanges.length
            };
            
            this.currentSession.fileChanges.push(fileChangeEvent);
        }
    }
    
    private async onTerminalActivity(event: TerminalCommandEvent) {
        if (!this.currentSession) return;
        
        this.currentSession.terminalCommands.push(event);
        
        // Check if this is a significant command
        if (await this.significanceAnalyzer.isSignificantTerminalCommand(event)) {
            await this.apiClient.captureTerminalCommand(this.currentSession.id, event);
        }
    }
    
    private async detectGitActivity() {
        if (!this.currentSession) return;
        
        try {
            // Use Git extension API if available
            const gitExtension = vscode.extensions.getExtension('vscode.git');
            if (gitExtension) {
                const git = gitExtension.exports.getAPI(1);
                const repo = git.repositories[0];
                
                if (repo) {
                    const head = repo.state.HEAD;
                    if (head) {
                        const gitEvent: GitActivityEvent = {
                            type: 'commit',
                            details: `${head.name}: ${head.commit?.substring(0, 7)}`,
                            timestamp: new Date(),
                            author: head.ahead?.toString()
                        };
                        
                        this.currentSession.gitActivities.push(gitEvent);
                        await this.apiClient.captureGitActivity(this.currentSession.id, gitEvent);
                    }
                }
            }
        } catch (error) {
            console.error('Failed to detect Git activity:', error);
        }
    }
    
    async captureAIInteraction(userInput: string, aiResponse: string, type: AIInteractionEvent['type'] = 'manual_entry') {
        if (!this.currentSession) {
            throw new Error('No active capture session');
        }
        
        const interaction: AIInteractionEvent = {
            type,
            userInput,
            aiResponse,
            timestamp: new Date(),
            context: vscode.window.activeTextEditor?.document.fileName || '',
            accepted: true // Default to accepted for manual entries
        };
        
        this.currentSession.aiInteractions.push(interaction);
        
        // Always send AI interactions to API as they're inherently significant
        await this.apiClient.captureAIInteraction(this.currentSession.id, interaction);
        
        vscode.window.showInformationMessage('🤖 AI interaction captured for UATP attribution');
    }
    
    private shouldMonitorFile(filePath: string, language: string): boolean {
        // Skip hidden files and directories
        if (filePath.startsWith('.') || filePath.includes('/.')) {
            return false;
        }
        
        // Skip node_modules and other common ignore patterns
        const ignorePatterns = ['node_modules', 'dist', 'build', 'target', '.git', '__pycache__'];
        if (ignorePatterns.some(pattern => filePath.includes(pattern))) {
            return false;
        }
        
        // Check if language is monitored
        const config = vscode.workspace.getConfiguration('uatp');
        const monitoredTypes = config.get<string[]>('monitoredFileTypes', []);
        
        return monitoredTypes.length === 0 || monitoredTypes.includes(language);
    }
    
    private getLanguageFromPath(filePath: string): string {
        const ext = path.extname(filePath).toLowerCase();
        const languageMap: { [key: string]: string } = {
            '.js': 'javascript',
            '.ts': 'typescript',
            '.py': 'python',
            '.java': 'java',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin'
        };
        
        return languageMap[ext] || 'unknown';
    }
    
    private async detectPrimaryLanguage(): Promise<string> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) return 'unknown';
        
        // Simple heuristic: check for common project files
        const files = await vscode.workspace.findFiles('**/package.json', '**/node_modules/**', 1);
        if (files.length > 0) return 'javascript';
        
        const pyFiles = await vscode.workspace.findFiles('**/requirements.txt', null, 1);
        if (pyFiles.length > 0) return 'python';
        
        const javaFiles = await vscode.workspace.findFiles('**/pom.xml', null, 1);
        if (javaFiles.length > 0) return 'java';
        
        return 'unknown';
    }
    
    private async storeSessionLocally(session: CaptureSession) {
        try {
            const sessions = this.context.globalState.get<CaptureSession[]>('uatp.sessions', []);
            sessions.push(session);
            
            // Keep only last 10 sessions locally
            if (sessions.length > 10) {
                sessions.splice(0, sessions.length - 10);
            }
            
            await this.context.globalState.update('uatp.sessions', sessions);
        } catch (error) {
            console.error('Failed to store session locally:', error);
        }
    }
    
    // Getters for other components
    getCurrentSession(): CaptureSession | undefined {
        return this.currentSession;
    }
    
    isSessionActive(): boolean {
        return !!this.currentSession;
    }
    
    async getLocalSessions(): Promise<CaptureSession[]> {
        return this.context.globalState.get<CaptureSession[]>('uatp.sessions', []);
    }
    
    toggleAutoCapture(): boolean {
        this.autoCapture = !this.autoCapture;
        const config = vscode.workspace.getConfiguration('uatp');
        config.update('autoCapture', this.autoCapture, vscode.ConfigurationTarget.Global);
        return this.autoCapture;
    }
}