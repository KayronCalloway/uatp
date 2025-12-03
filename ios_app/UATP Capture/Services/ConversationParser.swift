import Foundation
import Network

/// Intelligent conversation parser that understands different AI chat formats
/// Steve Jobs would approve: It figures out what you mean, not what you said
class ConversationParser {
    
    // MARK: - Main Parsing Method
    func parseConversation(text: String, platform: String) -> ParsedConversation {
        let cleanText = text.trimmingCharacters(in: .whitespacesAndNewlines)
        
        switch platform.lowercased() {
        case "openai", "chatgpt":
            return parseOpenAIConversation(text: cleanText)
        case "claude", "anthropic":
            return parseClaudeConversation(text: cleanText)
        default:
            return parseGenericConversation(text: cleanText, platform: platform)
        }
    }
    
    // MARK: - Platform-Specific Parsers
    
    /// Parse OpenAI/ChatGPT conversation format
    private func parseOpenAIConversation(text: String) -> ParsedConversation {
        var messages: [ConversationMessage] = []
        var detectedModel: String? = nil
        
        // Pattern matching for common ChatGPT formats
        let patterns = [
            // "You: ... \n ChatGPT: ..."
            ("(?i)you:\\s*([\\s\\S]*?)(?=chatgpt:|gpt:|assistant:|$)", "(?i)(?:chatgpt|gpt|assistant):\\s*([\\s\\S]*?)(?=you:|user:|$)"),
            // "User: ... \n Assistant: ..."
            ("(?i)user:\\s*([\\s\\S]*?)(?=assistant:|$)", "(?i)assistant:\\s*([\\s\\S]*?)(?=user:|$)"),
            // Simple alternating format
            ("^([\\s\\S]*?)(?=\\n\\n|$)", "")
        ]
        
        for (userPattern, assistantPattern) in patterns {
            let userMatches = findMatches(in: text, pattern: userPattern)
            if !assistantPattern.isEmpty {
                let assistantMatches = findMatches(in: text, pattern: assistantPattern)
                
                // Interleave user and assistant messages
                for (index, userMatch) in userMatches.enumerated() {
                    messages.append(ConversationMessage(role: "user", content: userMatch.trimmingCharacters(in: .whitespacesAndNewlines)))
                    
                    if index < assistantMatches.count {
                        let assistantContent = assistantMatches[index].trimmingCharacters(in: .whitespacesAndNewlines)
                        messages.append(ConversationMessage(role: "assistant", content: assistantContent))
                        
                        // Try to detect model from assistant response
                        if detectedModel == nil {
                            detectedModel = detectOpenAIModel(from: assistantContent)
                        }
                    }
                }
                
                if !messages.isEmpty {
                    break
                }
            }
        }
        
        // Fallback: treat entire text as user message if no patterns match
        if messages.isEmpty {
            messages.append(ConversationMessage(role: "user", content: text))
        }
        
        return ParsedConversation(
            rawText: text,
            messages: messages,
            userMessage: messages.first { $0.role == "user" }?.content,
            assistantMessage: messages.first { $0.role == "assistant" }?.content,
            model: detectedModel ?? "gpt-3.5-turbo",
            platform: "openai"
        )
    }
    
    /// Parse Claude conversation format
    private func parseClaudeConversation(text: String) -> ParsedConversation {
        var userMessage: String = ""
        var assistantMessage: String = ""
        
        // Claude-specific patterns
        let patterns = [
            // "Human: ... \n Assistant: ..."
            ("(?i)human:\\s*([\\s\\S]*?)(?=assistant:|$)", "(?i)assistant:\\s*([\\s\\S]*?)(?=human:|$)"),
            // "You: ... \n Claude: ..."
            ("(?i)you:\\s*([\\s\\S]*?)(?=claude:|$)", "(?i)claude:\\s*([\\s\\S]*?)(?=you:|$)"),
            // Look for Claude's characteristic responses
            ("^([\\s\\S]*?)(?=I'd be happy to help|I can help|I understand|Let me help)", "(?:I'd be happy to help|I can help|I understand|Let me help)([\\s\\S]*)")
        ]
        
        for (userPattern, assistantPattern) in patterns {
            let userMatches = findMatches(in: text, pattern: userPattern)
            let assistantMatches = findMatches(in: text, pattern: assistantPattern)
            
            if !userMatches.isEmpty {
                userMessage = userMatches.first!.trimmingCharacters(in: .whitespacesAndNewlines)
            }
            
            if !assistantMatches.isEmpty {
                assistantMessage = assistantMatches.first!.trimmingCharacters(in: .whitespacesAndNewlines)
            }
            
            if !userMessage.isEmpty || !assistantMessage.isEmpty {
                break
            }
        }
        
        // Fallback: assume entire text is user message
        if userMessage.isEmpty && assistantMessage.isEmpty {
            userMessage = text
        }
        
        let messages = [
            userMessage.isEmpty ? nil : ConversationMessage(role: "user", content: userMessage),
            assistantMessage.isEmpty ? nil : ConversationMessage(role: "assistant", content: assistantMessage)
        ].compactMap { $0 }
        
        return ParsedConversation(
            rawText: text,
            messages: messages,
            userMessage: userMessage.isEmpty ? nil : userMessage,
            assistantMessage: assistantMessage.isEmpty ? nil : assistantMessage,
            model: "claude-3-sonnet",
            platform: "claude"
        )
    }
    
    /// Parse generic conversation format
    private func parseGenericConversation(text: String, platform: String) -> ParsedConversation {
        // Try to identify conversation structure automatically
        let lines = text.components(separatedBy: .newlines)
        var messages: [ConversationMessage] = []
        
        // Look for alternating speakers
        var currentRole = "user"
        var currentContent = ""
        
        for line in lines {
            let trimmedLine = line.trimmingCharacters(in: .whitespacesAndNewlines)
            
            if trimmedLine.isEmpty {
                continue
            }
            
            // Check if this line indicates a role change
            if isRoleIndicator(line: trimmedLine) {
                // Save previous message if any
                if !currentContent.isEmpty {
                    messages.append(ConversationMessage(role: currentRole, content: currentContent.trimmingCharacters(in: .whitespacesAndNewlines)))
                    currentContent = ""
                }
                
                // Switch role
                currentRole = currentRole == "user" ? "assistant" : "user"
                
                // Extract content after role indicator
                let content = extractContentAfterRoleIndicator(line: trimmedLine)
                currentContent = content
            } else {
                // Continue current content
                if !currentContent.isEmpty {
                    currentContent += "\n"
                }
                currentContent += trimmedLine
            }
        }
        
        // Add final message
        if !currentContent.isEmpty {
            messages.append(ConversationMessage(role: currentRole, content: currentContent.trimmingCharacters(in: .whitespacesAndNewlines)))
        }
        
        // If no structure detected, treat as single user message
        if messages.isEmpty {
            messages.append(ConversationMessage(role: "user", content: text))
        }
        
        return ParsedConversation(
            rawText: text,
            messages: messages,
            userMessage: messages.first { $0.role == "user" }?.content,
            assistantMessage: messages.first { $0.role == "assistant" }?.content,
            model: nil,
            platform: platform
        )
    }
    
    // MARK: - Helper Methods
    
    /// Find regex matches in text
    private func findMatches(in text: String, pattern: String) -> [String] {
        guard let regex = try? NSRegularExpression(pattern: pattern, options: [.caseInsensitive, .dotMatchesLineSeparators]) else {
            return []
        }
        
        let range = NSRange(text.startIndex..., in: text)
        let matches = regex.matches(in: text, options: [], range: range)
        
        return matches.compactMap { match in
            if match.numberOfRanges > 1 {
                let captureRange = match.range(at: 1)
                if let range = Range(captureRange, in: text) {
                    return String(text[range])
                }
            }
            return nil
        }
    }
    
    /// Detect OpenAI model from response content
    private func detectOpenAIModel(from content: String) -> String? {
        if content.contains("GPT-4") || content.contains("gpt-4") {
            return "gpt-4"
        } else if content.contains("GPT-3.5") || content.contains("gpt-3.5") {
            return "gpt-3.5-turbo"
        }
        return nil
    }
    
    /// Check if line indicates a role change
    private func isRoleIndicator(line: String) -> Bool {
        let rolePatterns = [
            "^(you|user|human|me):",
            "^(assistant|ai|bot|chatgpt|gpt|claude):",
            "^\\d+\\.",  // Numbered items
            "^[A-Z][a-z]+:",  // Names followed by colon
        ]
        
        return rolePatterns.contains { pattern in
            line.range(of: pattern, options: [.regularExpression, .caseInsensitive]) != nil
        }
    }
    
    /// Extract content after role indicator
    private func extractContentAfterRoleIndicator(line: String) -> String {
        // Remove common role indicators
        let patterns = [
            "^(you|user|human|me|assistant|ai|bot|chatgpt|gpt|claude):\\s*",
            "^\\d+\\.\\s*",
            "^[A-Z][a-z]+:\\s*"
        ]
        
        var result = line
        for pattern in patterns {
            if let range = result.range(of: pattern, options: [.regularExpression, .caseInsensitive]) {
                result = String(result[range.upperBound...])
                break
            }
        }
        
        return result
    }
}