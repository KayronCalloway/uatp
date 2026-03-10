export default function SimplePage() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-2xl">
        <h1 className="text-3xl font-bold text-green-600 mb-4">React Frontend Working!</h1>

        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h2 className="font-semibold text-green-800">System Status</h2>
            <ul className="text-sm text-green-700 mt-2 space-y-1">
              <li>• Next.js server running on port 3000</li>
              <li>• React components rendering properly</li>
              <li>• TailwindCSS styles loading</li>
              <li>• No JavaScript errors on this page</li>
            </ul>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h2 className="font-semibold text-blue-800">Available Pages</h2>
            <ul className="text-sm text-blue-700 mt-2 space-y-1">
              <li>• <a href="/simple" className="underline hover:text-blue-900">/simple</a> - This minimal page</li>
              <li>• <a href="/test" className="underline hover:text-blue-900">/test</a> - Feature test page</li>
              <li>• <a href="/" className="underline hover:text-blue-900">/</a> - Full UATP application</li>
            </ul>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h2 className="font-semibold text-purple-800">Ready Features</h2>
            <ul className="text-sm text-purple-700 mt-2 space-y-1">
              <li>• Universe 3D Visualization</li>
              <li>• Hallucination Detection System</li>
              <li>• Backend API Integration</li>
              <li>• Real-time System Monitoring</li>
            </ul>
          </div>

          <div className="text-center mt-6">
            <p className="text-gray-600 text-sm">
              If you can see this page clearly, the React frontend is working perfectly!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
