/**
 * UATP Development Capture - VS Code Extension
 * Captures comprehensive development workflows for universal AI accountability
 */

import * as vscode from 'vscode';
import { UATPCaptureManager } from './captureManager';
import { UATPStatusBar } from './statusBar';
import { UATPViewProvider } from './viewProvider';
import { UATPCommands } from './commands';

export function activate(context: vscode.ExtensionContext) {
    console.log('🚀 UATP Development Capture extension is now active!');
    
    // Initialize core managers
    const captureManager = new UATPCaptureManager(context);
    const statusBar = new UATPStatusBar();
    const viewProvider = new UATPViewProvider(captureManager);
    const commands = new UATPCommands(captureManager, statusBar);
    
    // Register view providers
    vscode.window.registerTreeDataProvider('uatp.sessions', viewProvider.getSessionsProvider());
    vscode.window.registerTreeDataProvider('uatp.stats', viewProvider.getStatsProvider());
    
    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('uatp.startCapture', () => commands.startCapture()),
        vscode.commands.registerCommand('uatp.endCapture', () => commands.endCapture()),
        vscode.commands.registerCommand('uatp.captureCurrentFile', () => commands.captureCurrentFile()),
        vscode.commands.registerCommand('uatp.viewDashboard', () => commands.viewDashboard()),
        vscode.commands.registerCommand('uatp.toggleAutoCapture', () => commands.toggleAutoCapture()),
        vscode.commands.registerCommand('uatp.captureAIInteraction', () => commands.captureAIInteraction())
    );
    
    // Initialize capture manager
    captureManager.initialize();
    
    // Show welcome message on first activation
    const isFirstRun = context.globalState.get('uatp.firstRun', true);
    if (isFirstRun) {
        showWelcomeMessage();
        context.globalState.update('uatp.firstRun', false);
    }
    
    console.log('✅ UATP Development Capture extension initialized successfully');
}

export function deactivate() {
    console.log('👋 UATP Development Capture extension is deactivating');
}

async function showWelcomeMessage() {
    const action = await vscode.window.showInformationMessage(
        '🚀 UATP Development Capture is now active! Start capturing your development workflow for universal AI accountability.',
        'Start Capture Session',
        'View Dashboard',
        'Settings'
    );
    
    switch (action) {
        case 'Start Capture Session':
            vscode.commands.executeCommand('uatp.startCapture');
            break;
        case 'View Dashboard':
            vscode.commands.executeCommand('uatp.viewDashboard');
            break;
        case 'Settings':
            vscode.commands.executeCommand('workbench.action.openSettings', 'uatp');
            break;
    }
}