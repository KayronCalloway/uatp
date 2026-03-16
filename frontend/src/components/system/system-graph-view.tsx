'use client';

import { useEffect, useRef } from 'react';
import { Network } from 'vis-network/standalone';

export function SystemGraphView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Define nodes
    const nodes = [
      // Core Engine
      { id: 'capsule_engine', label: 'UATP\nCapsule Engine', shape: 'star', color: '#ff6b6b', size: 50, font: { color: 'white', size: 14, bold: true } },

      // LLM Providers
      { id: 'openai', label: 'OpenAI', shape: 'dot', color: '#10a37f', size: 30, font: { color: 'white' } },
      { id: 'anthropic', label: 'Anthropic', shape: 'dot', color: '#d97706', size: 30, font: { color: 'white' } },
      { id: 'claude', label: 'Claude', shape: 'dot', color: '#8b5cf6', size: 30, font: { color: 'white' } },

      // Spatial AI Providers
      { id: 'zed_camera', label: 'ZED Camera', shape: 'dot', color: '#3b82f6', size: 30, font: { color: 'white' } },
      { id: 'velodyne_lidar', label: 'Velodyne LiDAR', shape: 'dot', color: '#6366f1', size: 30, font: { color: 'white' } },
      { id: 'moveit_planner', label: 'MoveIt Planner', shape: 'dot', color: '#8b5cf6', size: 30, font: { color: 'white' } },
      { id: 'ur5_controller', label: 'UR5 Controller', shape: 'dot', color: '#a855f7', size: 30, font: { color: 'white' } },
      { id: 'gps_imu', label: 'GPS+IMU Nav', shape: 'dot', color: '#c084fc', size: 30, font: { color: 'white' } },
      { id: 'robotiq_gripper', label: 'Robotiq Gripper', shape: 'dot', color: '#d8b4fe', size: 30, font: { color: 'white' } },

      // Capsule Types
      { id: 'chat', label: 'Chat', shape: 'box', color: '#22c55e', size: 25, font: { color: 'white' } },
      { id: 'reasoning', label: 'Reasoning', shape: 'box', color: '#16a34a', size: 25, font: { color: 'white' } },
      { id: 'joint', label: 'Joint', shape: 'box', color: '#15803d', size: 25, font: { color: 'white' } },
      { id: 'refusal', label: 'Refusal', shape: 'box', color: '#dc2626', size: 25, font: { color: 'white' } },
      { id: 'consent', label: 'Consent', shape: 'box', color: '#ea580c', size: 25, font: { color: 'white' } },
      { id: 'perspective', label: 'Perspective', shape: 'box', color: '#d97706', size: 25, font: { color: 'white' } },
      { id: 'spatial_perception', label: 'Spatial\nPerception', shape: 'box', color: '#0ea5e9', size: 25, font: { color: 'white' } },
      { id: 'spatial_planning', label: 'Spatial\nPlanning', shape: 'box', color: '#0284c7', size: 25, font: { color: 'white' } },
      { id: 'spatial_control', label: 'Spatial\nControl', shape: 'box', color: '#0369a1', size: 25, font: { color: 'white' } },
      { id: 'spatial_navigation', label: 'Spatial\nNavigation', shape: 'box', color: '#075985', size: 25, font: { color: 'white' } },
      { id: 'spatial_manipulation', label: 'Spatial\nManipulation', shape: 'box', color: '#0c4a6e', size: 25, font: { color: 'white' } },

      // System Components
      { id: 'trust_scorer', label: 'Trust Scorer', shape: 'diamond', color: '#f59e0b', size: 35, font: { color: 'white' } },
      { id: 'fcde', label: 'FCDE\nEconomics', shape: 'diamond', color: '#eab308', size: 35, font: { color: 'white' } },
      { id: 'physical_ai_insurance', label: 'Physical AI\nInsurance', shape: 'diamond', color: '#84cc16', size: 35, font: { color: 'white' } },
      { id: 'verification_system', label: 'Verification\nSystem', shape: 'diamond', color: '#10b981', size: 35, font: { color: 'white' } },
      { id: 'governance', label: 'Governance', shape: 'diamond', color: '#14b8a6', size: 35, font: { color: 'white' } },
    ];

    // Define edges
    const edges = [
      // Engine integrates providers
      { from: 'capsule_engine', to: 'openai', label: 'integrates', color: '#666', arrows: 'to' },
      { from: 'capsule_engine', to: 'anthropic', label: 'integrates', color: '#666', arrows: 'to' },
      { from: 'capsule_engine', to: 'claude', label: 'integrates', color: '#666', arrows: 'to' },
      { from: 'capsule_engine', to: 'zed_camera', label: 'integrates', color: '#666', arrows: 'to' },
      { from: 'capsule_engine', to: 'velodyne_lidar', label: 'integrates', color: '#666', arrows: 'to' },
      { from: 'capsule_engine', to: 'moveit_planner', label: 'integrates', color: '#666', arrows: 'to' },
      { from: 'capsule_engine', to: 'ur5_controller', label: 'integrates', color: '#666', arrows: 'to' },
      { from: 'capsule_engine', to: 'gps_imu', label: 'integrates', color: '#666', arrows: 'to' },
      { from: 'capsule_engine', to: 'robotiq_gripper', label: 'integrates', color: '#666', arrows: 'to' },

      // LLM providers create capsules
      { from: 'openai', to: 'chat', label: 'creates', color: '#4ade80', arrows: 'to' },
      { from: 'openai', to: 'reasoning', label: 'creates', color: '#4ade80', arrows: 'to' },
      { from: 'anthropic', to: 'chat', label: 'creates', color: '#4ade80', arrows: 'to' },
      { from: 'anthropic', to: 'reasoning', label: 'creates', color: '#4ade80', arrows: 'to' },
      { from: 'claude', to: 'refusal', label: 'creates', color: '#f87171', arrows: 'to' },
      { from: 'claude', to: 'consent', label: 'creates', color: '#fb923c', arrows: 'to' },

      // Spatial providers create spatial capsules
      { from: 'zed_camera', to: 'spatial_perception', label: 'creates', color: '#60a5fa', arrows: 'to' },
      { from: 'velodyne_lidar', to: 'spatial_perception', label: 'creates', color: '#60a5fa', arrows: 'to' },
      { from: 'moveit_planner', to: 'spatial_planning', label: 'creates', color: '#60a5fa', arrows: 'to' },
      { from: 'ur5_controller', to: 'spatial_control', label: 'creates', color: '#60a5fa', arrows: 'to' },
      { from: 'robotiq_gripper', to: 'spatial_manipulation', label: 'creates', color: '#60a5fa', arrows: 'to' },
      { from: 'gps_imu', to: 'spatial_navigation', label: 'creates', color: '#60a5fa', arrows: 'to' },

      // Engine uses system components
      { from: 'capsule_engine', to: 'trust_scorer', label: 'uses', color: '#94a3b8', arrows: 'to' },
      { from: 'capsule_engine', to: 'fcde', label: 'uses', color: '#94a3b8', arrows: 'to' },
      { from: 'capsule_engine', to: 'physical_ai_insurance', label: 'uses', color: '#94a3b8', arrows: 'to' },
      { from: 'capsule_engine', to: 'verification_system', label: 'uses', color: '#94a3b8', arrows: 'to' },
      { from: 'capsule_engine', to: 'governance', label: 'uses', color: '#94a3b8', arrows: 'to' },

      // Trust scorer evaluates providers (dashed)
      { from: 'trust_scorer', to: 'openai', label: 'evaluates', color: '#fbbf24', arrows: 'to', dashes: true },
      { from: 'trust_scorer', to: 'zed_camera', label: 'evaluates', color: '#fbbf24', arrows: 'to', dashes: true },

      // FCDE pays providers (dashed)
      { from: 'fcde', to: 'openai', label: 'pays', color: '#a3e635', arrows: 'to', dashes: true },
      { from: 'fcde', to: 'zed_camera', label: 'pays', color: '#a3e635', arrows: 'to', dashes: true },

      // Insurance assesses spatial capsules (dashed)
      { from: 'physical_ai_insurance', to: 'spatial_perception', label: 'assesses', color: '#86efac', arrows: 'to', dashes: true },
      { from: 'physical_ai_insurance', to: 'spatial_control', label: 'assesses', color: '#86efac', arrows: 'to', dashes: true },

      // Verification verifies capsules (dashed)
      { from: 'verification_system', to: 'chat', label: 'verifies', color: '#6ee7b7', arrows: 'to', dashes: true },
      { from: 'verification_system', to: 'spatial_perception', label: 'verifies', color: '#6ee7b7', arrows: 'to', dashes: true },

      // Governance manages (dashed)
      { from: 'governance', to: 'consent', label: 'manages', color: '#5eead4', arrows: 'to', dashes: true },
      { from: 'governance', to: 'refusal', label: 'manages', color: '#5eead4', arrows: 'to', dashes: true },

      // Example chains (thick lines)
      { from: 'spatial_perception', to: 'spatial_planning', label: 'chains_to', color: '#38bdf8', arrows: 'to', width: 3 },
      { from: 'spatial_planning', to: 'spatial_control', label: 'chains_to', color: '#38bdf8', arrows: 'to', width: 3 },
      { from: 'chat', to: 'reasoning', label: 'chains_to', color: '#4ade80', arrows: 'to', width: 3 },
      { from: 'reasoning', to: 'joint', label: 'chains_to', color: '#4ade80', arrows: 'to', width: 3 },
    ];

    const data = { nodes, edges };

    const options = {
      layout: {
        randomSeed: 42,
        improvedLayout: true,
      },
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -8000,
          centralGravity: 0.3,
          springLength: 200,
          springConstant: 0.001,
          damping: 0.09,
          avoidOverlap: 0.5,
        },
        stabilization: {
          iterations: 1000,
        },
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
        dragView: true,
      },
      nodes: {
        borderWidth: 2,
        borderWidthSelected: 4,
        font: {
          size: 12,
          face: 'Inter, system-ui, sans-serif',
        },
      },
      edges: {
        width: 2,
        smooth: {
          type: 'continuous',
          roundness: 0.5,
        },
        font: {
          size: 10,
          align: 'middle',
          color: '#ffffff',
          background: '#00000080',
        },
      },
    };

    networkRef.current = new Network(containerRef.current, data, options);

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
      }
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Complete UATP System Network</h1>
        <p className="text-gray-600">Interactive visualization of the entire UATP ecosystem</p>
      </div>

      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h2 className="text-xl font-semibold mb-3">Interactive System Graph</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-6">
          <div>
            <h3 className="font-semibold text-blue-600 mb-2">Node Types:</h3>
            <ul className="space-y-1 text-gray-700">
              <li> <span className="text-red-500 font-medium">Core Engine</span> - UATP Capsule Engine</li>
              <li> <span className="text-green-500 font-medium">LLM Providers</span> - OpenAI, Anthropic, Claude</li>
              <li> <span className="text-blue-500 font-medium">Spatial Providers</span> - Cameras, LiDAR, Controllers</li>
              <li> <span className="text-cyan-500 font-medium">Capsule Types</span> - All capsule types</li>
              <li> <span className="text-orange-500 font-medium">System Components</span> - Trust, FCDE, Insurance, etc.</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-purple-600 mb-2">Edge Types:</h3>
            <ul className="space-y-1 text-gray-700">
              <li><span className="text-gray-600">—</span> Solid: Direct relationships (integrates, creates, uses)</li>
              <li><span className="text-yellow-500">- -</span> Dashed: System interactions (evaluates, pays, assesses)</li>
              <li><span className="text-blue-500">━</span> Thick: Capsule chains (chains_to)</li>
            </ul>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden" style={{ height: '600px' }}>
          <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="text-3xl font-bold text-green-500">3</div>
          <div className="text-sm text-gray-600">LLM Providers</div>
        </div>
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="text-3xl font-bold text-blue-500">6</div>
          <div className="text-sm text-gray-600">Spatial Providers</div>
        </div>
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="text-3xl font-bold text-cyan-500">11</div>
          <div className="text-sm text-gray-600">Capsule Types</div>
        </div>
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="text-3xl font-bold text-orange-500">5</div>
          <div className="text-sm text-gray-600">System Components</div>
        </div>
      </div>

      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 border border-blue-200">
        <h3 className="text-lg font-semibold mb-2"> Interaction Tips</h3>
        <ul className="space-y-1 text-sm text-gray-700">
          <li>• <strong>Drag nodes</strong> to rearrange the graph layout</li>
          <li>• <strong>Scroll</strong> to zoom in/out</li>
          <li>• <strong>Click and drag background</strong> to pan around</li>
          <li>• <strong>Hover over nodes/edges</strong> to highlight connections</li>
        </ul>
      </div>
    </div>
  );
}
