'use client';

import React, { useState } from 'react';
import { useOnboarding } from '@/contexts/onboarding-context';
import { Button } from '@/components/ui/button';

export function SupportButton() {
  const { actions } = useOnboarding();
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [supportResponse, setSupportResponse] = useState<any>(null);

  const handleGetSupport = async (issueType?: string) => {
    setIsLoading(true);
    try {
      const response = await actions.getSupport(issueType, 'I need help with onboarding');
      setSupportResponse(response);
    } catch (error) {
      console.error('Failed to get support:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const quickHelpOptions = [
    { id: 'setup_issue', label: 'Setup Problems', icon: '⚙️' },
    { id: 'api_key_help', label: 'API Key Issues', icon: '🔑' },
    { id: 'platform_connection', label: 'Platform Connection', icon: '🔗' },
    { id: 'general_question', label: 'General Questions', icon: '❓' },
  ];

  return (
    <>
      {/* Floating Action Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center text-xl z-50"
        title="Get Help"
      >
        💬
      </button>

      {/* Support Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[80vh] overflow-y-auto">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white p-6 rounded-t-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">💬</span>
                  <h3 className="text-lg font-semibold">Need Help?</h3>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-white hover:text-gray-200 text-xl"
                >
                  ×
                </button>
              </div>
              <p className="text-purple-100 text-sm mt-2">
                Get instant help with your UATP setup
              </p>
            </div>

            <div className="p-6">
              {!supportResponse ? (
                <div className="space-y-4">
                  <p className="text-gray-600 text-sm">
                    What can we help you with?
                  </p>
                  
                  {/* Quick Help Options */}
                  <div className="space-y-2">
                    {quickHelpOptions.map((option) => (
                      <button
                        key={option.id}
                        onClick={() => handleGetSupport(option.id)}
                        disabled={isLoading}
                        className="w-full flex items-center space-x-3 p-3 text-left border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-colors disabled:opacity-50"
                      >
                        <span className="text-xl">{option.icon}</span>
                        <span className="font-medium text-gray-700">{option.label}</span>
                      </button>
                    ))}
                  </div>

                  {/* Loading State */}
                  {isLoading && (
                    <div className="text-center py-4">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto" />
                      <p className="text-gray-600 text-sm mt-2">Getting help...</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Support Response */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-2">Here's how we can help:</h4>
                    <p className="text-blue-800 text-sm mb-3">{supportResponse.message}</p>
                    
                    {/* Immediate Actions */}
                    {supportResponse.immediate_actions && supportResponse.immediate_actions.length > 0 && (
                      <div className="mb-3">
                        <h5 className="font-medium text-blue-900 text-sm mb-2">Try these steps:</h5>
                        <ul className="list-disc list-inside space-y-1 text-sm text-blue-800">
                          {supportResponse.immediate_actions.map((action: string, index: number) => (
                            <li key={index}>{action}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Resources */}
                  {supportResponse.resources && supportResponse.resources.length > 0 && (
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">Helpful Resources:</h5>
                      <div className="space-y-2">
                        {supportResponse.resources.map((resource: any, index: number) => (
                          <a
                            key={index}
                            href={resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center space-x-2 text-purple-600 hover:text-purple-700 text-sm"
                          >
                            <span>
                              {resource.type === 'documentation' ? '📚' : 
                               resource.type === 'video' ? '🎥' : '🎯'}
                            </span>
                            <span>{resource.title}</span>
                            <span className="text-xs">→</span>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex space-x-2 pt-4">
                    <Button
                      onClick={() => {
                        setSupportResponse(null);
                        setIsOpen(false);
                      }}
                      className="flex-1"
                    >
                      Got it, thanks!
                    </Button>
                    <Button
                      onClick={() => setSupportResponse(null)}
                      variant="outline"
                      className="flex-1"
                    >
                      Ask Another Question
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}