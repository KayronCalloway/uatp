'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Globe,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Play,
  Pause,
  Settings,
  Info
} from 'lucide-react';

interface CapsuleNode {
  id: string;
  x: number;
  y: number;
  radius: number;
  color: string;
  type: string;
  agent_id: string;
  connections: string[];
  brightness: number;
}

interface UniverseState {
  nodes: CapsuleNode[];
  scale: number;
  offsetX: number;
  offsetY: number;
  rotation: number;
  animationSpeed: number;
  showLabels: boolean;
  showConnections: boolean;
}

export function UniverseVisualization() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const [isAnimating, setIsAnimating] = useState(true);
  const [selectedNode, setSelectedNode] = useState<CapsuleNode | null>(null);
  const [universe, setUniverse] = useState<UniverseState>({
    nodes: [],
    scale: 1,
    offsetX: 0,
    offsetY: 0,
    rotation: 0,
    animationSpeed: 0.005,
    showLabels: true,
    showConnections: true
  });

  const { data: capsulesData, isLoading, error } = useQuery({
    queryKey: ['capsules', { per_page: 100 }],
    queryFn: () => api.getCapsules({ per_page: 100 }),
    refetchInterval: 30000,
    retry: 2,
  });

  const { data: statsData } = useQuery({
    queryKey: ['capsule-stats'],
    queryFn: () => api.getCapsuleStats(false),
    refetchInterval: 30000,
    retry: 2,
  });

  const { data: trustData } = useQuery({
    queryKey: ['trust-metrics'],
    queryFn: api.getTrustMetrics,
    refetchInterval: 30000,
    retry: 2,
  });

  const { data: universeData } = useQuery({
    queryKey: ['universe-visualization-data'],
    queryFn: api.getUniverseVisualizationData,
    refetchInterval: 30000,
    retry: 2,
  });

  // Convert capsules to universe nodes
  useEffect(() => {
    if (capsulesData?.capsules) {
      const nodes: CapsuleNode[] = capsulesData.capsules.map((capsule, index) => {
        // Create constellations by agent type
        const agentIndex = Array.from(new Set(capsulesData.capsules.map(c => c.agent_id))).indexOf(capsule.agent_id);
        const agentAngle = (agentIndex / 3) * Math.PI * 2; // Assuming max 3 agents
        const agentRadius = 150;
        const agentCenterX = Math.cos(agentAngle) * agentRadius;
        const agentCenterY = Math.sin(agentAngle) * agentRadius;

        // Position capsules around their agent's center
        const capsuleAngle = (index / capsulesData.capsules.length) * Math.PI * 2;
        const capsuleRadius = 30 + (Math.random() * 40);

        const trustScore = Array.isArray(trustData) ? trustData.find(t => t.agent_id === capsule.agent_id)?.trust_score || 0.8 : 0.8;
        const depth = capsule.lineage?.depth || 0;

        return {
          id: capsule.id,
          x: agentCenterX + Math.cos(capsuleAngle) * capsuleRadius,
          y: agentCenterY + Math.sin(capsuleAngle) * capsuleRadius,
          radius: getNodeRadius(capsule.type, depth),
          color: getNodeColor(capsule.type, trustScore),
          type: capsule.type,
          agent_id: capsule.agent_id,
          connections: findConnections(capsule, capsulesData.capsules),
          brightness: Math.min(1, trustScore + 0.2) // Higher trust = brighter
        };
      });

      setUniverse(prev => ({ ...prev, nodes }));
    }
  }, [capsulesData, trustData]);

  // Animation loop
  useEffect(() => {
    if (!isAnimating) return;

    const animate = () => {
      setUniverse(prev => ({
        ...prev,
        rotation: prev.rotation + prev.animationSpeed
      }));
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isAnimating]);

  // Drawing function
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    // Clear canvas
    ctx.fillStyle = '#000011';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw stars background
    drawStarField(ctx, canvas.width, canvas.height);

    // Save context for transformations
    ctx.save();

    // Apply transformations
    ctx.translate(centerX + universe.offsetX, centerY + universe.offsetY);
    ctx.scale(universe.scale, universe.scale);
    ctx.rotate(universe.rotation);

    // Draw connections
    if (universe.showConnections) {
      drawConnections(ctx, universe.nodes);
    }

    // Draw nodes (capsules as stars)
    universe.nodes.forEach(node => {
      drawCapsuleNode(ctx, node);
    });

    // Draw labels
    if (universe.showLabels && universe.scale > 0.5) {
      universe.nodes.forEach(node => {
        drawNodeLabel(ctx, node);
      });
    }

    ctx.restore();

    // Draw selected node info
    if (selectedNode) {
      drawNodeInfo(ctx, selectedNode, canvas.width, canvas.height);
    }
  }, [universe, selectedNode]);

  // Canvas click handler
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Transform click coordinates to world coordinates
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const worldX = (x - centerX - universe.offsetX) / universe.scale;
    const worldY = (y - centerY - universe.offsetY) / universe.scale;

    // Check if click is on any node
    const clickedNode = universe.nodes.find(node => {
      const distance = Math.sqrt(
        Math.pow(worldX - node.x, 2) + Math.pow(worldY - node.y, 2)
      );
      return distance < node.radius + 10;
    });

    setSelectedNode(clickedNode || null);
  };

  const handleZoom = (factor: number) => {
    setUniverse(prev => ({
      ...prev,
      scale: Math.max(0.1, Math.min(3, prev.scale * factor))
    }));
  };

  const handleReset = () => {
    setUniverse(prev => ({
      ...prev,
      scale: 1,
      offsetX: 0,
      offsetY: 0,
      rotation: 0
    }));
    setSelectedNode(null);
  };

  const toggleAnimation = () => {
    setIsAnimating(!isAnimating);
  };

  if (isLoading) {
    return (
      <Card className="w-full h-96">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Loading universe data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full h-96">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <p className="text-red-600 mb-2">Failed to load universe data</p>
            <p className="text-sm text-gray-600">{error.message}</p>
            <p className="text-xs text-gray-500 mt-2">Using mock data for visualization</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Globe className="h-5 w-5" />
              <span>Universe Visualization</span>
              {capsulesData?.capsules && (
                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                  Live Data
                </span>
              )}
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={() => handleZoom(1.2)}>
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleZoom(0.8)}>
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={handleReset}>
                <RotateCcw className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={toggleAnimation}>
                {isAnimating ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Universe Canvas */}
      <Card>
        <CardContent className="p-0">
          <canvas
            ref={canvasRef}
            width={800}
            height={600}
            className="w-full h-96 cursor-crosshair"
            onClick={handleCanvasClick}
          />
        </CardContent>
      </Card>

      {/* Universe Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Total Stars</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{universe.nodes.length}</div>
            <p className="text-xs text-gray-500">Capsules in universe</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Constellation Types</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsData?.types ? Object.keys(statsData.types).length : 0}
            </div>
            <p className="text-xs text-gray-500">Capsule types</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Current Scale</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(universe.scale * 100).toFixed(0)}%</div>
            <p className="text-xs text-gray-500">Zoom level</p>
          </CardContent>
        </Card>
      </div>

      {/* Selected Node Info */}
      {selectedNode && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Selected Capsule</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: selectedNode.color }}
                />
                <span className="text-sm font-medium">{selectedNode.type}</span>
              </div>
              <div className="text-xs text-gray-500">
                <p>ID: {selectedNode.id}</p>
                <p>Agent: {selectedNode.agent_id}</p>
                <p>Position: ({selectedNode.x.toFixed(1)}, {selectedNode.y.toFixed(1)})</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Helper functions
function getNodeRadius(type: string, depth: number = 0): number {
  const baseSizes = {
    'chat': 8,
    'joint': 12,
    'refusal': 6,
    'introspective': 10,
    'consent': 9,
    'perspective': 11,
    'governance': 15
  };
  const baseSize = baseSizes[type as keyof typeof baseSizes] || 8;
  // Larger nodes for deeper lineage
  return baseSize + (depth * 2);
}

function getNodeColor(type: string, trustScore: number = 0.8): string {
  const baseColors = {
    'chat': '#3B82F6',
    'joint': '#10B981',
    'refusal': '#EF4444',
    'introspective': '#8B5CF6',
    'consent': '#F59E0B',
    'perspective': '#06B6D4',
    'governance': '#F97316'
  };

  const baseColor = baseColors[type as keyof typeof baseColors] || '#6B7280';

  // Dim color for low trust scores
  if (trustScore < 0.5) {
    return baseColor + '80'; // 50% opacity
  } else if (trustScore < 0.7) {
    return baseColor + 'CC'; // 80% opacity
  }

  return baseColor;
}

function findConnections(capsule: any, allCapsules: any[]): string[] {
  const connections: string[] = [];

  // Find parent connection
  if (capsule.lineage?.parent_id) {
    connections.push(capsule.lineage.parent_id);
  }

  // Find children connections
  const children = allCapsules.filter(c => c.lineage?.parent_id === capsule.id);
  connections.push(...children.map(c => c.id));

  return connections;
}

function drawStarField(ctx: CanvasRenderingContext2D, width: number, height: number) {
  ctx.fillStyle = '#FFFFFF';
  for (let i = 0; i < 200; i++) {
    const x = Math.random() * width;
    const y = Math.random() * height;
    const size = Math.random() * 1.5;
    const alpha = Math.random() * 0.8 + 0.2;

    ctx.globalAlpha = alpha;
    ctx.beginPath();
    ctx.arc(x, y, size, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function drawCapsuleNode(ctx: CanvasRenderingContext2D, node: CapsuleNode) {
  // Draw glow effect
  const gradient = ctx.createRadialGradient(
    node.x, node.y, 0,
    node.x, node.y, node.radius * 2
  );
  gradient.addColorStop(0, node.color + '80');
  gradient.addColorStop(1, node.color + '00');

  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(node.x, node.y, node.radius * 2, 0, Math.PI * 2);
  ctx.fill();

  // Draw main node
  ctx.fillStyle = node.color;
  ctx.globalAlpha = node.brightness;
  ctx.beginPath();
  ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
  ctx.fill();

  // Draw bright center
  ctx.fillStyle = '#FFFFFF';
  ctx.globalAlpha = 0.8;
  ctx.beginPath();
  ctx.arc(node.x, node.y, node.radius * 0.3, 0, Math.PI * 2);
  ctx.fill();

  ctx.globalAlpha = 1;
}

function drawConnections(ctx: CanvasRenderingContext2D, nodes: CapsuleNode[]) {
  ctx.lineWidth = 1;

  nodes.forEach((node) => {
    node.connections.forEach((connectionId) => {
      const target = nodes.find(n => n.id === connectionId);
      if (target) {
        // Different colors for different connection types
        const isParentChild = true; // Could be enhanced to detect connection type
        ctx.strokeStyle = isParentChild ? '#FFFFFF40' : '#00FF0030';

        ctx.beginPath();
        ctx.moveTo(node.x, node.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();

        // Draw arrow for directional relationships
        const angle = Math.atan2(target.y - node.y, target.x - node.x);
        const arrowLength = 8;
        const arrowAngle = Math.PI / 6;

        ctx.beginPath();
        ctx.moveTo(
          target.x - arrowLength * Math.cos(angle - arrowAngle),
          target.y - arrowLength * Math.sin(angle - arrowAngle)
        );
        ctx.lineTo(target.x, target.y);
        ctx.lineTo(
          target.x - arrowLength * Math.cos(angle + arrowAngle),
          target.y - arrowLength * Math.sin(angle + arrowAngle)
        );
        ctx.stroke();
      }
    });
  });
}

function drawNodeLabel(ctx: CanvasRenderingContext2D, node: CapsuleNode) {
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '10px Arial';
  ctx.textAlign = 'center';
  ctx.fillText(node.type, node.x, node.y + node.radius + 15);
}

function drawNodeInfo(ctx: CanvasRenderingContext2D, node: CapsuleNode, width: number, height: number) {
  const infoX = 10;
  const infoY = 10;
  const infoWidth = 200;
  const infoHeight = 80;

  // Draw info background
  ctx.fillStyle = '#00000080';
  ctx.fillRect(infoX, infoY, infoWidth, infoHeight);

  // Draw info text
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '12px Arial';
  ctx.textAlign = 'left';
  ctx.fillText(`Type: ${node.type}`, infoX + 10, infoY + 20);
  ctx.fillText(`Agent: ${node.agent_id.substring(0, 15)}...`, infoX + 10, infoY + 35);
  ctx.fillText(`ID: ${node.id.substring(0, 15)}...`, infoX + 10, infoY + 50);
  ctx.fillText(`Position: (${node.x.toFixed(1)}, ${node.y.toFixed(1)})`, infoX + 10, infoY + 65);
}
