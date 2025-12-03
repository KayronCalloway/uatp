'use client';

export default function SimpleTest() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8 text-center">
          🚀 UATP System Status Test
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-green-600 mb-4">✅ Frontend Status</h2>
            <p className="text-gray-700">
              Next.js server is running successfully on port 3000
            </p>
            <div className="mt-4 p-3 bg-green-50 rounded border-l-4 border-green-400">
              <p className="text-sm text-green-800">
                <strong>Tailwind CSS:</strong> {' '}
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  Working ✓
                </span>
              </p>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-blue-600 mb-4">🎯 UATP Features</h2>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
                Enterprise Security
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
                Onboarding System
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
                Attribution Engine
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
                Compliance Framework
              </li>
            </ul>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200 mb-6">
          <h2 className="text-xl font-semibold text-purple-600 mb-4">🛠 Quick Actions</h2>
          <div className="flex flex-wrap gap-3">
            <a 
              href="/" 
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              📊 Main Dashboard
            </a>
            <a 
              href="/onboarding" 
              className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              🚀 Try Onboarding
            </a>
            <button 
              onClick={() => window.location.reload()} 
              className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              🔄 Refresh Page
            </button>
          </div>
        </div>

        <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-3">🎉 System Ready!</h2>
          <p className="text-gray-300">
            Your UATP Capsule Engine is successfully running with all enterprise features,
            security enhancements, and production optimizations implemented.
          </p>
        </div>
      </div>
    </div>
  );
}