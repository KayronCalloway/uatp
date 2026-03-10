'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Globe, Stars, Network, Zap } from 'lucide-react';

export function UniversePreview() {
  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Globe className="h-5 w-5" />
            <span>Universe View Preview</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">
            The Universe View will transform capsule data into an explorable cosmic landscape where:
          </p>
        </CardContent>
      </Card>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <Stars className="h-5 w-5 text-yellow-500" />
              <span>Capsules as Stars</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-3">
              Each capsule becomes a star in the universe, with brightness indicating influence and importance.
            </p>
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
              <span className="text-xs">Chat Capsules</span>
            </div>
            <div className="flex items-center space-x-3 mt-1">
              <div className="w-4 h-4 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-xs">Joint Capsules</span>
            </div>
            <div className="flex items-center space-x-3 mt-1">
              <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
              <span className="text-xs">Refusal Capsules</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <Network className="h-5 w-5 text-purple-500" />
              <span>Constellation Groups</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-3">
              Related capsules form constellations representing projects, teams, or thematic clusters.
            </p>
            <div className="bg-gray-100 p-3 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-600">Project Alpha</span>
                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">12 capsules</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <Zap className="h-5 w-5 text-orange-500" />
              <span>Economic Flows</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-3">
              Visualize economic attribution as energy flows between capsules and contributors.
            </p>
            <div className="bg-gradient-to-r from-orange-100 to-yellow-100 p-3 rounded-lg">
              <div className="text-xs text-orange-700">
                Attribution streams connecting value creators
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <Globe className="h-5 w-5 text-blue-500" />
              <span>Temporal Navigation</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-3">
              Navigate through time to see how the universe of capsules evolves and grows.
            </p>
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="text-xs text-blue-700">
                Timeline controls for exploring capsule history
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Technical Implementation */}
      <Card>
        <CardHeader>
          <CardTitle>Technical Implementation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-sm mb-2">Rendering Technology</h4>
              <p className="text-sm text-gray-600">
                WebGL-based 3D rendering with Three.js for smooth performance even with millions of capsules.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-sm mb-2">Data Processing</h4>
              <p className="text-sm text-gray-600">
                Efficient spatial indexing and level-of-detail systems to handle civilization-scale datasets.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-sm mb-2">Real-time Updates</h4>
              <p className="text-sm text-gray-600">
                WebSocket connections for live updates as new capsules are created and relationships form.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Coming Soon */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
        <CardContent className="p-6 text-center">
          <h3 className="font-semibold text-lg mb-2">Coming Soon</h3>
          <p className="text-gray-600 mb-4">
            The Universe View is being developed as part of our civilization-scale infrastructure roadmap.
          </p>
          <div className="text-sm text-blue-600">
            Expected in Phase 2 of development
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
