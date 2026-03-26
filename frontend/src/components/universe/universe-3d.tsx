'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Globe,
  RotateCcw,
  Play,
  Pause,
  ZoomIn,
  ZoomOut,
  Maximize,
  Settings,
  Eye,
  EyeOff
} from 'lucide-react';

interface CapsuleNode3D {
  id: string;
  x: number;
  y: number;
  z: number;
  radius: number;
  color: string;
  type: string;
  agent_id: string;
  connections: string[];
  brightness: number;
  velocity: { x: number; y: number; z: number };
}

interface Universe3DState {
  nodes: CapsuleNode3D[];
  camera: {
    x: number;
    y: number;
    z: number;
    rotationX: number;
    rotationY: number;
    zoom: number;
  };
  animation: {
    speed: number;
    autoRotate: boolean;
    showConnections: boolean;
    showLabels: boolean;
  };
}

export function Universe3D() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | undefined>(undefined);
  const [isAnimating, setIsAnimating] = useState(true);
  const [selectedNode, setSelectedNode] = useState<CapsuleNode3D | null>(null);
  const [universe, setUniverse] = useState<Universe3DState>({
    nodes: [],
    camera: {
      x: 0,
      y: 0,
      z: 500,
      rotationX: 0,
      rotationY: 0,
      zoom: 1
    },
    animation: {
      speed: 0.01,
      autoRotate: true,
      showConnections: true,
      showLabels: true
    }
  });

  const { data: capsulesData, isLoading } = useQuery({
    queryKey: ['capsules', { per_page: 100 }],
    queryFn: () => api.getCapsules({ per_page: 100 }),
    refetchInterval: 30000,
  });

  // Convert capsules to 3D nodes
  useEffect(() => {
    if (capsulesData?.capsules) {
      const nodes: CapsuleNode3D[] = capsulesData.capsules.map((capsule, index) => {
        // Create a 3D sphere distribution
        const phi = Math.acos(-1 + (2 * index) / capsulesData.capsules.length);
        const theta = Math.sqrt(capsulesData.capsules.length * Math.PI) * phi;
        const radius = 200 + (Math.random() - 0.5) * 100;

        return {
          id: capsule.id,
          x: radius * Math.cos(theta) * Math.sin(phi),
          y: radius * Math.sin(theta) * Math.sin(phi),
          z: radius * Math.cos(phi),
          radius: getNodeRadius(capsule.type),
          color: getNodeColor(capsule.type),
          type: capsule.type,
          agent_id: capsule.agent_id,
          connections: [], // Would be populated with actual relationships
          brightness: Math.random() * 0.5 + 0.5,
          velocity: {
            x: (Math.random() - 0.5) * 0.1,
            y: (Math.random() - 0.5) * 0.1,
            z: (Math.random() - 0.5) * 0.1
          }
        };
      });

      setUniverse(prev => ({ ...prev, nodes }));
    }
  }, [capsulesData]);

  // Animation loop
  useEffect(() => {
    if (!isAnimating) return;

    const animate = () => {
      setUniverse(prev => {
        const newNodes = prev.nodes.map(node => ({
          ...node,
          x: node.x + node.velocity.x,
          y: node.y + node.velocity.y,
          z: node.z + node.velocity.z,
          // Add some orbital motion
          brightness: Math.sin(Date.now() * 0.001 + node.x * 0.01) * 0.2 + 0.8
        }));

        return {
          ...prev,
          nodes: newNodes,
          camera: {
            ...prev.camera,
            rotationY: prev.animation.autoRotate ? prev.camera.rotationY + prev.animation.speed : prev.camera.rotationY
          }
        };
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isAnimating]);

  // 3D projection and rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Clear canvas with space background
    ctx.fillStyle = '#000008';
    ctx.fillRect(0, 0, width, height);

    // Draw stars background
    drawStarField3D(ctx, width, height);

    // Project 3D nodes to 2D screen coordinates
    const projectedNodes = universe.nodes.map(node => {
      const projected = project3D(node, universe.camera, width, height);
      return { ...node, ...projected };
    }).filter(node => node.z > 0) // Only render nodes in front of camera
     .sort((a, b) => b.z - a.z); // Sort by depth (back to front)

    // Draw connections in 3D space
    if (universe.animation.showConnections) {
      drawConnections3D(ctx, projectedNodes);
    }

    // Draw nodes
    projectedNodes.forEach((node: any) => {
      drawCapsuleNode3D(ctx, node);
    });

    // Draw labels
    if (universe.animation.showLabels) {
      projectedNodes.forEach((node: any) => {
        if (node.screenSize > 15) { // Only show labels for larger nodes
          drawNodeLabel3D(ctx, node);
        }
      });
    }

    // Draw selected node info
    if (selectedNode) {
      const projected = projectedNodes.find(n => n.id === selectedNode.id);
      if (projected) {
        drawNodeInfo3D(ctx, projected, width, height);
      }
    }

    // Draw 3D axis indicators
    drawAxisIndicators(ctx, universe.camera, width, height);

  }, [universe, selectedNode]);

  // Mouse interaction for 3D rotation
  const handleMouseMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (event.buttons === 1) { // Left mouse button
      const deltaX = event.movementX;
      const deltaY = event.movementY;

      setUniverse(prev => ({
        ...prev,
        camera: {
          ...prev.camera,
          rotationY: prev.camera.rotationY + deltaX * 0.01,
          rotationX: Math.max(-Math.PI/2, Math.min(Math.PI/2, prev.camera.rotationX + deltaY * 0.01))
        }
      }));
    }
  };

  const handleWheel = (event: React.WheelEvent<HTMLCanvasElement>) => {
    event.preventDefault();
    const zoomFactor = event.deltaY > 0 ? 1.1 : 0.9;

    setUniverse(prev => ({
      ...prev,
      camera: {
        ...prev.camera,
        zoom: Math.max(0.1, Math.min(5, prev.camera.zoom * zoomFactor))
      }
    }));
  };

  const handleReset = () => {
    setUniverse(prev => ({
      ...prev,
      camera: {
        x: 0,
        y: 0,
        z: 500,
        rotationX: 0,
        rotationY: 0,
        zoom: 1
      }
    }));
    setSelectedNode(null);
  };

  const toggleAnimation = () => {
    setIsAnimating(!isAnimating);
  };

  const toggleAutoRotate = () => {
    setUniverse(prev => ({
      ...prev,
      animation: {
        ...prev.animation,
        autoRotate: !prev.animation.autoRotate
      }
    }));
  };

  const toggleConnections = () => {
    setUniverse(prev => ({
      ...prev,
      animation: {
        ...prev.animation,
        showConnections: !prev.animation.showConnections
      }
    }));
  };

  const toggleLabels = () => {
    setUniverse(prev => ({
      ...prev,
      animation: {
        ...prev.animation,
        showLabels: !prev.animation.showLabels
      }
    }));
  };

  if (isLoading) {
    return (
      <Card className="w-full h-96">
        <CardContent className="flex items-center justify-center h-full">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
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
              <span>3D Universe Visualization</span>
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={handleReset}>
                <RotateCcw className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={toggleAnimation}>
                {isAnimating ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button variant="outline" size="sm" onClick={toggleAutoRotate}>
                <Settings className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={toggleConnections}>
                {universe.animation.showConnections ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
              </Button>
              <Button variant="outline" size="sm" onClick={toggleLabels}>
                <Maximize className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* 3D Canvas */}
      <Card>
        <CardContent className="p-0">
          <canvas
            ref={canvasRef}
            width={800}
            height={600}
            className="w-full h-96 cursor-move"
            onMouseMove={handleMouseMove}
            onWheel={handleWheel}
            style={{ touchAction: 'none' }}
          />
        </CardContent>
      </Card>

      {/* Universe Info */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">3D Nodes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{universe.nodes.length}</div>
            <p className="text-xs text-gray-500">Capsules in 3D space</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Camera Zoom</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(universe.camera.zoom * 100).toFixed(0)}%</div>
            <p className="text-xs text-gray-500">Current zoom level</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Auto Rotate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{universe.animation.autoRotate ? 'ON' : 'OFF'}</div>
            <p className="text-xs text-gray-500">Automatic rotation</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Connections</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{universe.animation.showConnections ? 'ON' : 'OFF'}</div>
            <p className="text-xs text-gray-500">Network links</p>
          </CardContent>
        </Card>
      </div>

      {/* Controls Help */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">3D Controls</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <strong>Mouse:</strong> Click and drag to rotate
            </div>
            <div>
              <strong>Wheel:</strong> Scroll to zoom in/out
            </div>
            <div>
              <strong>Click:</strong> Select capsule nodes
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper functions for 3D rendering
function project3D(node: CapsuleNode3D, camera: any, width: number, height: number) {
  // Apply camera transformations
  const cosX = Math.cos(camera.rotationX);
  const sinX = Math.sin(camera.rotationX);
  const cosY = Math.cos(camera.rotationY);
  const sinY = Math.sin(camera.rotationY);

  // Rotate around Y axis
  const x1 = node.x * cosY - node.z * sinY;
  const z1 = node.x * sinY + node.z * cosY;

  // Rotate around X axis
  const y2 = node.y * cosX - z1 * sinX;
  const z2 = node.y * sinX + z1 * cosX;

  // Translate by camera position
  const x3 = x1 - camera.x;
  const y3 = y2 - camera.y;
  const z3 = z2 - camera.z;

  // Perspective projection
  const scale = camera.zoom * 300 / (z3 + 300);
  const screenX = width / 2 + x3 * scale;
  const screenY = height / 2 - y3 * scale;

  return {
    screenX,
    screenY,
    z: z3,
    screenSize: node.radius * scale
  };
}

function getNodeRadius(type: string): number {
  const sizes = {
    'chat': 8,
    'joint': 12,
    'refusal': 6,
    'introspective': 10,
    'consent': 9,
    'perspective': 11,
    'governance': 15
  };
  return sizes[type as keyof typeof sizes] || 8;
}

function getNodeColor(type: string): string {
  const colors = {
    'chat': '#3B82F6',
    'joint': '#10B981',
    'refusal': '#EF4444',
    'introspective': '#8B5CF6',
    'consent': '#F59E0B',
    'perspective': '#06B6D4',
    'governance': '#F97316'
  };
  return colors[type as keyof typeof colors] || '#6B7280';
}

function drawStarField3D(ctx: CanvasRenderingContext2D, width: number, height: number) {
  ctx.fillStyle = '#FFFFFF';
  for (let i = 0; i < 300; i++) {
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

function drawCapsuleNode3D(ctx: CanvasRenderingContext2D, node: any) {
  // Draw glow effect
  const gradient = ctx.createRadialGradient(
    node.screenX, node.screenY, 0,
    node.screenX, node.screenY, node.screenSize * 2
  );
  gradient.addColorStop(0, node.color + '80');
  gradient.addColorStop(1, node.color + '00');

  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(node.screenX, node.screenY, node.screenSize * 2, 0, Math.PI * 2);
  ctx.fill();

  // Draw main node
  ctx.fillStyle = node.color;
  ctx.globalAlpha = node.brightness;
  ctx.beginPath();
  ctx.arc(node.screenX, node.screenY, node.screenSize, 0, Math.PI * 2);
  ctx.fill();

  // Draw bright center
  ctx.fillStyle = '#FFFFFF';
  ctx.globalAlpha = 0.8;
  ctx.beginPath();
  ctx.arc(node.screenX, node.screenY, node.screenSize * 0.3, 0, Math.PI * 2);
  ctx.fill();

  ctx.globalAlpha = 1;
}

function drawConnections3D(ctx: CanvasRenderingContext2D, nodes: any[]) {
  ctx.strokeStyle = '#FFFFFF20';
  ctx.lineWidth = 1;

  nodes.forEach((node, index) => {
    if (index > 0 && Math.random() > 0.85) {
      const targetIndex = Math.floor(Math.random() * index);
      const target = nodes[targetIndex];

      ctx.beginPath();
      ctx.moveTo(node.screenX, node.screenY);
      ctx.lineTo(target.screenX, target.screenY);
      ctx.stroke();
    }
  });
}

function drawNodeLabel3D(ctx: CanvasRenderingContext2D, node: any) {
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '10px Arial';
  ctx.textAlign = 'center';
  ctx.fillText(node.type, node.screenX, node.screenY + node.screenSize + 15);
}

function drawNodeInfo3D(ctx: CanvasRenderingContext2D, node: any, width: number, height: number) {
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
  ctx.fillText(`3D Position: (${node.x.toFixed(1)}, ${node.y.toFixed(1)}, ${node.z.toFixed(1)})`, infoX + 10, infoY + 50);
  ctx.fillText(`Screen: (${node.screenX.toFixed(1)}, ${node.screenY.toFixed(1)})`, infoX + 10, infoY + 65);
}

function drawAxisIndicators(ctx: CanvasRenderingContext2D, camera: any, width: number, height: number) {
  const size = 50;
  const x = width - size - 20;
  const y = height - size - 20;

  // Draw axis lines
  ctx.strokeStyle = '#FF0000';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x + size * Math.cos(camera.rotationY), y);
  ctx.stroke();

  ctx.strokeStyle = '#00FF00';
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x, y - size * Math.cos(camera.rotationX));
  ctx.stroke();

  ctx.strokeStyle = '#0000FF';
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x + size * Math.sin(camera.rotationY), y + size * Math.sin(camera.rotationX));
  ctx.stroke();

  // Draw labels
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '10px Arial';
  ctx.fillText('X', x + size + 5, y + 5);
  ctx.fillText('Y', x - 5, y - size - 5);
  ctx.fillText('Z', x + size + 5, y + size + 5);
}
