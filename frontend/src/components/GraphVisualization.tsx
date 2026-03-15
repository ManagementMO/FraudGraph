"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import * as d3 from "d3";
import { Network } from "lucide-react";
import type {
  GraphData,
  GraphNode,
  GraphLink,
  AgentAssessment,
} from "@/lib/types";
import { COMMUNITY_COLORS } from "@/lib/types";

// ── Helpers ──────────────────────────────────────────────────────────

function communityColor(id: number): string {
  return COMMUNITY_COLORS[id % COMMUNITY_COLORS.length];
}

function communityColorRGBA(id: number, alpha: number): string {
  const hex = communityColor(id);
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

interface Star {
  x: number;
  y: number;
  r: number;
  alpha: number;
}

function generateStars(w: number, h: number, count: number): Star[] {
  const stars: Star[] = [];
  for (let i = 0; i < count; i++) {
    stars.push({
      x: Math.random() * w,
      y: Math.random() * h,
      r: 0.5 + Math.random() * 1.5,
      alpha: 0.3 + Math.random() * 0.7,
    });
  }
  return stars;
}

function drawStarfield(ctx: CanvasRenderingContext2D, stars: Star[]) {
  for (const s of stars) {
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(150,180,255,${s.alpha})`;
    ctx.fill();
  }
}

function drawEdges(
  ctx: CanvasRenderingContext2D,
  links: GraphLink[]
) {
  // Glow pass
  ctx.globalCompositeOperation = "lighter";
  ctx.lineWidth = 2.5;
  ctx.globalAlpha = 0.06;
  for (const l of links) {
    const s = l.source as GraphNode;
    const t = l.target as GraphNode;
    if (s.x == null || s.y == null || t.x == null || t.y == null) continue;
    ctx.strokeStyle = communityColor(s.community);
    ctx.beginPath();
    ctx.moveTo(s.x, s.y);
    ctx.lineTo(t.x, t.y);
    ctx.stroke();
  }

  // Sharp pass
  ctx.lineWidth = 0.4;
  ctx.globalAlpha = 0.25;
  for (const l of links) {
    const s = l.source as GraphNode;
    const t = l.target as GraphNode;
    if (s.x == null || s.y == null || t.x == null || t.y == null) continue;
    ctx.strokeStyle = communityColor(s.community);
    ctx.beginPath();
    ctx.moveTo(s.x, s.y);
    ctx.lineTo(t.x, t.y);
    ctx.stroke();
  }

  ctx.globalCompositeOperation = "source-over";
  ctx.globalAlpha = 1;
}

function drawNodes(
  ctx: CanvasRenderingContext2D,
  nodes: GraphNode[]
) {
  for (const n of nodes) {
    if (n.x == null || n.y == null) continue;
    const r = n.radius ?? 7;
    const color = communityColor(n.community);

    ctx.shadowBlur = 12;
    ctx.shadowColor = color;
    ctx.beginPath();
    ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();

    // White stroke for target node
    if (n.is_target) {
      ctx.shadowBlur = 0;
      ctx.lineWidth = 3;
      ctx.strokeStyle = "#ffffff";
      ctx.stroke();
    }
  }
  ctx.shadowBlur = 0;
}

function drawClusterLabels(
  ctx: CanvasRenderingContext2D,
  nodes: GraphNode[]
) {
  // Compute centroids per community
  const centroids = new Map<number, { sx: number; sy: number; count: number }>();
  for (const n of nodes) {
    if (n.x == null || n.y == null) continue;
    const c = centroids.get(n.community) || { sx: 0, sy: 0, count: 0 };
    c.sx += n.x;
    c.sy += n.y;
    c.count += 1;
    centroids.set(n.community, c);
  }

  ctx.font = "10px monospace";
  ctx.fillStyle = "rgba(160,170,200,0.6)";
  ctx.textAlign = "center";
  for (const [id, c] of centroids) {
    if (c.count < 2) continue;
    const cx = c.sx / c.count;
    const cy = c.sy / c.count;
    ctx.fillText(`C${id}`, cx, cy - 20);
  }
}

// ── Custom cluster force ────────────────────────────────────────────

function forceCluster(strength: number) {
  let nodes: GraphNode[] = [];

  function force(alpha: number) {
    const centroids = new Map<number, { sx: number; sy: number; count: number }>();
    for (const n of nodes) {
      const c = centroids.get(n.community) || { sx: 0, sy: 0, count: 0 };
      c.sx += n.x ?? 0;
      c.sy += n.y ?? 0;
      c.count += 1;
      centroids.set(n.community, c);
    }
    for (const n of nodes) {
      const c = centroids.get(n.community);
      if (!c || c.count < 2) continue;
      const cx = c.sx / c.count;
      const cy = c.sy / c.count;
      n.vx = (n.vx ?? 0) + (cx - (n.x ?? 0)) * strength * alpha;
      n.vy = (n.vy ?? 0) + (cy - (n.y ?? 0)) * strength * alpha;
    }
  }

  force.initialize = (n: GraphNode[]) => {
    nodes = n;
  };

  return force as unknown as d3.Force<GraphNode, GraphLink>;
}

// ── Props & State ───────────────────────────────────────────────────

interface GraphVisualizationProps {
  data: GraphData | null;
  assessments: AgentAssessment[];
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  node: GraphNode | null;
}

export function GraphVisualization({
  data,
  assessments,
}: GraphVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const simulationRef = useRef<d3.Simulation<GraphNode, GraphLink> | null>(null);
  const transformRef = useRef(d3.zoomIdentity);
  const starsRef = useRef<Star[]>([]);
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false,
    x: 0,
    y: 0,
    node: null,
  });

  // Stable render function ref to avoid re-binding canvas events
  const renderRef = useRef<() => void>(() => {});

  const render = useCallback(() => {
    renderRef.current();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container || !data) return;

    // Clean up previous simulation
    if (simulationRef.current) {
      simulationRef.current.stop();
      simulationRef.current = null;
    }

    const rect = container.getBoundingClientRect();
    const width = rect.width || 600;
    const height = rect.height || 400;
    const dpr = window.devicePixelRatio || 1;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext("2d")!;
    ctx.scale(dpr, dpr);

    // Generate starfield
    starsRef.current = generateStars(width, height, 200);

    // -- Compute visible nodes based on assessment progress --
    const totalAgents = 4;
    const assessmentCount = Math.min(assessments.length, totalAgents);

    const targetNode = data.nodes.find((n) => n.is_target);
    const otherNodes = data.nodes
      .filter((n) => !n.is_target)
      .sort((a, b) => {
        if (a.is_fraud && !b.is_fraud) return -1;
        if (!a.is_fraud && b.is_fraud) return 1;
        return 0;
      });

    let visibleNodes: GraphNode[];
    if (assessmentCount === 0) {
      visibleNodes = targetNode ? [targetNode] : [];
    } else if (assessmentCount >= totalAgents) {
      visibleNodes = [...data.nodes];
    } else {
      const visibleCount = Math.ceil(
        otherNodes.length * (assessmentCount / totalAgents)
      );
      const subset = otherNodes.slice(0, visibleCount);
      visibleNodes = targetNode ? [targetNode, ...subset] : [...subset];
    }

    const clonedNodes: GraphNode[] = visibleNodes.map((n) => ({ ...n }));
    const visibleIds = new Set(clonedNodes.map((n) => n.id));

    const visibleLinks: GraphLink[] = data.links
      .filter((l) => {
        const sourceId = typeof l.source === "string" ? l.source : l.source.id;
        const targetId = typeof l.target === "string" ? l.target : l.target.id;
        return visibleIds.has(sourceId) && visibleIds.has(targetId);
      })
      .map((l) => ({
        source: typeof l.source === "string" ? l.source : l.source.id,
        target: typeof l.target === "string" ? l.target : l.target.id,
        weight: l.weight,
      }));

    // -- Compute node radii from degree --
    const degreeMap = new Map<string, number>();
    visibleLinks.forEach((l) => {
      const s = typeof l.source === "string" ? l.source : l.source.id;
      const t = typeof l.target === "string" ? l.target : l.target.id;
      degreeMap.set(s, (degreeMap.get(s) || 0) + 1);
      degreeMap.set(t, (degreeMap.get(t) || 0) + 1);
    });
    for (const node of clonedNodes) {
      node.radius = Math.max(3, Math.min(16, 3 + Math.sqrt(degreeMap.get(node.id) || 1) * 2.5));
      if (node.is_target) node.radius = Math.max(14, node.radius);
    }

    // -- Determine link parameters based on community --
    const linkForce = d3
      .forceLink<GraphNode, GraphLink>(visibleLinks)
      .id((d) => d.id)
      .distance((l) => {
        const s = l.source as GraphNode;
        const t = l.target as GraphNode;
        return s.community === t.community ? 25 : 100;
      })
      .strength((l) => {
        const s = l.source as GraphNode;
        const t = l.target as GraphNode;
        return s.community === t.community ? 0.7 : 0.05;
      });

    // -- Force simulation --
    const simulation = d3
      .forceSimulation<GraphNode>(clonedNodes)
      .force("link", linkForce)
      .force("charge", d3.forceManyBody().strength(-250))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide<GraphNode>().radius((d) => (d.radius ?? 7) + 2))
      .force("cluster", forceCluster(0.3))
      .alphaDecay(0.015);

    // -- Render function --
    renderRef.current = () => {
      const t = transformRef.current;
      ctx.save();
      ctx.clearRect(0, 0, width, height);

      // Background
      ctx.fillStyle = "#0a0a1a";
      ctx.fillRect(0, 0, width, height);

      // Starfield (no transform — fixed background)
      drawStarfield(ctx, starsRef.current);

      // Apply zoom transform
      ctx.translate(t.x, t.y);
      ctx.scale(t.k, t.k);

      // Edges
      drawEdges(ctx, visibleLinks);

      // Nodes
      drawNodes(ctx, clonedNodes);

      // Cluster labels
      drawClusterLabels(ctx, clonedNodes);

      ctx.restore();
    };

    simulation.on("tick", render);

    if (assessmentCount > 0) {
      simulation.alpha(0.3).restart();
    }

    simulationRef.current = simulation;

    // -- Zoom behavior --
    const zoomBehavior = d3
      .zoom<HTMLCanvasElement, unknown>()
      .scaleExtent([0.3, 5])
      .on("zoom", (event: d3.D3ZoomEvent<HTMLCanvasElement, unknown>) => {
        transformRef.current = event.transform;
        render();
      });

    const canvasSelection = d3.select(canvas);
    canvasSelection.call(zoomBehavior);

    // -- Drag behavior --
    let dragSubject: GraphNode | null = null;

    const dragBehavior = d3
      .drag<HTMLCanvasElement, unknown>()
      .subject(() => {
        const [mx, my] = d3.pointer(event!, canvas);
        const t = transformRef.current;
        const sx = (mx - t.x) / t.k;
        const sy = (my - t.y) / t.k;
        const found = simulation.find(sx, sy, 20);
        return found || null;
      })
      .on("start", (event) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        dragSubject = event.subject as GraphNode;
        if (dragSubject) {
          dragSubject.fx = dragSubject.x;
          dragSubject.fy = dragSubject.y;
        }
      })
      .on("drag", (event) => {
        if (dragSubject) {
          const t = transformRef.current;
          dragSubject.fx = (event.sourceEvent.offsetX - t.x) / t.k;
          dragSubject.fy = (event.sourceEvent.offsetY - t.y) / t.k;
        }
      })
      .on("end", (event) => {
        if (!event.active) simulation.alphaTarget(0);
        if (dragSubject) {
          dragSubject.fx = null;
          dragSubject.fy = null;
          dragSubject = null;
        }
      });

    canvasSelection.call(dragBehavior as unknown as d3.DragBehavior<HTMLCanvasElement, unknown, unknown>);

    // -- Mousemove for tooltip --
    const handleMouseMove = (event: MouseEvent) => {
      const t = transformRef.current;
      const mx = (event.offsetX - t.x) / t.k;
      const my = (event.offsetY - t.y) / t.k;
      const found = simulation.find(mx, my, 20);
      if (found) {
        setTooltip({
          visible: true,
          x: event.offsetX,
          y: event.offsetY,
          node: found,
        });
        canvas.style.cursor = "pointer";
      } else {
        setTooltip({ visible: false, x: 0, y: 0, node: null });
        canvas.style.cursor = "grab";
      }
    };

    canvas.addEventListener("mousemove", handleMouseMove);

    return () => {
      simulation.stop();
      canvas.removeEventListener("mousemove", handleMouseMove);
    };
  }, [data, assessments.length, render]);

  // -- Empty state --
  if (!data) {
    return (
      <div className="flex-1 min-h-0 bg-card border border-border rounded-xl overflow-hidden relative flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <Network className="mx-auto mb-3 h-12 w-12 opacity-30" />
          <p className="text-sm">Submit a transaction to see the fraud network</p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="flex-1 min-h-0 bg-[#0a0a1a] border border-border rounded-xl overflow-hidden relative"
    >
      {/* Section label */}
      <span className="absolute top-3 left-3 text-xs uppercase tracking-wider text-muted-foreground z-10">
        Transaction network
      </span>

      <canvas ref={canvasRef} className="w-full h-full" />

      {/* Tooltip */}
      {tooltip.visible && tooltip.node && (
        <div
          className="absolute pointer-events-none bg-card/95 border border-border rounded-lg px-2.5 py-1.5 text-xs shadow-lg z-10"
          style={{ left: tooltip.x + 12, top: tooltip.y - 8 }}
        >
          <div className="font-mono text-foreground">{tooltip.node.id}</div>
          <div className="text-muted-foreground">
            Type: <span className="capitalize">{tooltip.node.type}</span>
          </div>
          <div className="text-muted-foreground">
            Community: <span className="font-mono">{tooltip.node.community}</span>
          </div>
          {tooltip.node.is_fraud && (
            <div className="text-red-400 font-semibold">Fraud-linked</div>
          )}
          {tooltip.node.is_target && (
            <div className="text-amber-400 font-semibold">Target card</div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-3 right-3 bg-card/90 backdrop-blur-sm p-2 rounded-lg text-xs border border-border">
        <div className="flex flex-col gap-1">
          {COMMUNITY_COLORS.slice(0, 5).map((color, i) => (
            <div key={i} className="flex items-center gap-1.5">
              <span
                className="inline-block w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: color, boxShadow: `0 0 4px ${color}` }}
              />
              <span className="text-muted-foreground">Community {i}</span>
            </div>
          ))}
          <div className="flex items-center gap-1.5 mt-1 pt-1 border-t border-border">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full border-2"
              style={{ borderColor: "#ffffff", backgroundColor: COMMUNITY_COLORS[0] }}
            />
            <span className="text-muted-foreground">Target</span>
          </div>
        </div>
      </div>
    </div>
  );
}
