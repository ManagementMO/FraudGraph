"use client";

import { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import type {
  GraphData,
  GraphNode,
  GraphLink,
  AgentAssessment,
} from "@/lib/types";
import { NODE_COLORS, FRAUD_GLOW_COLOR, TARGET_BORDER } from "@/lib/types";

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
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<d3.Simulation<GraphNode, GraphLink> | null>(
    null
  );
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false,
    x: 0,
    y: 0,
    node: null,
  });

  useEffect(() => {
    if (!svgRef.current || !data) return;

    // Clean up previous simulation
    if (simulationRef.current) {
      simulationRef.current.stop();
      simulationRef.current = null;
    }

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const container = svgRef.current.parentElement;
    const width = container?.clientWidth || 600;
    const height = container?.clientHeight || 400;

    // Set explicit dimensions on SVG so D3 has a coordinate space
    svg.attr("width", width).attr("height", height);

    // -- Compute visible nodes based on assessment progress (split transition) --
    const totalAgents = 4;
    const assessmentCount = Math.min(assessments.length, totalAgents);

    // Find the target node (always visible)
    const targetNode = data.nodes.find((n) => n.is_target);

    // Sort remaining nodes: fraud first, then by type relevance
    const otherNodes = data.nodes
      .filter((n) => !n.is_target)
      .sort((a, b) => {
        if (a.is_fraud && !b.is_fraud) return -1;
        if (!a.is_fraud && b.is_fraud) return 1;
        return 0;
      });

    let visibleNodes: GraphNode[];
    if (assessmentCount === 0) {
      // Only show target node when no assessments yet
      visibleNodes = targetNode ? [targetNode] : [];
    } else if (assessmentCount >= totalAgents) {
      // Show all nodes when all agents have reported
      visibleNodes = [...data.nodes];
    } else {
      // Progressive reveal
      const visibleCount = Math.ceil(
        otherNodes.length * (assessmentCount / totalAgents)
      );
      const subset = otherNodes.slice(0, visibleCount);
      visibleNodes = targetNode ? [targetNode, ...subset] : [...subset];
    }

    // Deep clone nodes so D3 can mutate x/y/vx/vy without corrupting React state
    const clonedNodes: GraphNode[] = visibleNodes.map((n) => ({ ...n }));
    const visibleIds = new Set(clonedNodes.map((n) => n.id));

    // Filter links to only include those between visible nodes
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

    // -- SVG structure --
    const defs = svg.append("defs");

    // Glow filter for fraud nodes
    const filter = defs
      .append("filter")
      .attr("id", "glow")
      .attr("x", "-50%")
      .attr("y", "-50%")
      .attr("width", "200%")
      .attr("height", "200%");
    filter
      .append("feGaussianBlur")
      .attr("stdDeviation", "4")
      .attr("result", "coloredBlur");
    const merge = filter.append("feMerge");
    merge.append("feMergeNode").attr("in", "coloredBlur");
    merge.append("feMergeNode").attr("in", "SourceGraphic");

    // Container group for zoom transform
    const g = svg.append("g");

    // Zoom behavior
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 5])
      .on("zoom", (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
        g.attr("transform", event.transform.toString());
      });

    svg.call(zoom);

    // -- Draw links --
    const link = g
      .append("g")
      .attr("class", "links")
      .selectAll<SVGLineElement, GraphLink>("line")
      .data(visibleLinks)
      .join("line")
      .attr("stroke", "#475569")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", (d) => Math.min(d.weight, 4));

    // -- Draw nodes --
    const node = g
      .append("g")
      .attr("class", "nodes")
      .selectAll<SVGCircleElement, GraphNode>("circle")
      .data(clonedNodes)
      .join("circle")
      .attr("r", 0) // start at 0 for enter animation
      .attr("fill", (d) =>
        d.is_fraud ? FRAUD_GLOW_COLOR : NODE_COLORS[d.type] || NODE_COLORS.unknown
      )
      .attr("stroke", (d) => (d.is_target ? TARGET_BORDER : "none"))
      .attr("stroke-width", (d) => (d.is_target ? 3 : 0))
      .attr("filter", (d) => (d.is_fraud ? "url(#glow)" : "none"))
      .attr("cursor", "grab")
      .attr("opacity", 0);

    // Enter animation: scale radius and fade in
    node
      .transition()
      .duration(500)
      .attr("opacity", 1)
      .attr("r", (d) => (d.is_target ? 14 : d.is_fraud ? 10 : 7));

    // -- Draw labels (only for target and fraud nodes) --
    const label = g
      .append("g")
      .attr("class", "labels")
      .selectAll<SVGTextElement, GraphNode>("text")
      .data(clonedNodes.filter((d) => d.is_target || d.is_fraud))
      .join("text")
      .text((d) => d.id.slice(0, 10))
      .attr("font-size", "9px")
      .attr("fill", "#94a3b8")
      .attr("text-anchor", "middle")
      .attr("dy", (d) => (d.is_target ? 22 : 18))
      .attr("opacity", 0)
      .transition()
      .duration(500)
      .attr("opacity", 1);

    // Suppress unused variable warning for label
    void label;

    // -- Tooltip via mouseover --
    node
      .on("mouseover", function (event: MouseEvent, d: GraphNode) {
        d3.select(this).attr("stroke-width", d.is_target ? 4 : 2);
        if (!d.is_target) {
          d3.select(this).attr("stroke", "#f1f5f9");
        }
        setTooltip({
          visible: true,
          x: event.offsetX,
          y: event.offsetY,
          node: d,
        });
      })
      .on("mousemove", function (event: MouseEvent) {
        setTooltip((prev) => ({
          ...prev,
          x: event.offsetX,
          y: event.offsetY,
        }));
      })
      .on("mouseout", function (_event: MouseEvent, d: GraphNode) {
        d3.select(this)
          .attr("stroke-width", d.is_target ? 3 : 0)
          .attr("stroke", d.is_target ? TARGET_BORDER : "none");
        setTooltip({ visible: false, x: 0, y: 0, node: null });
      });

    // -- Drag behavior --
    const drag = d3
      .drag<SVGCircleElement, GraphNode>()
      .on("start", (event: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>, d) => {
        if (!event.active && simulationRef.current) {
          simulationRef.current.alphaTarget(0.3).restart();
        }
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>, d) => {
        if (!event.active && simulationRef.current) {
          simulationRef.current.alphaTarget(0);
        }
        d.fx = null;
        d.fy = null;
      });

    node.call(drag);

    // -- Force simulation --
    const simulation = d3
      .forceSimulation<GraphNode>(clonedNodes)
      .force(
        "link",
        d3
          .forceLink<GraphNode, GraphLink>(visibleLinks)
          .id((d) => d.id)
          .distance(80)
          .strength(0.5)
      )
      .force("charge", d3.forceManyBody().strength(-250))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius(20))
      .on("tick", () => {
        link
          .attr("x1", (d) =>
            typeof d.source === "object" ? (d.source as GraphNode).x ?? 0 : 0
          )
          .attr("y1", (d) =>
            typeof d.source === "object" ? (d.source as GraphNode).y ?? 0 : 0
          )
          .attr("x2", (d) =>
            typeof d.target === "object" ? (d.target as GraphNode).x ?? 0 : 0
          )
          .attr("y2", (d) =>
            typeof d.target === "object" ? (d.target as GraphNode).y ?? 0 : 0
          );

        node.attr("cx", (d) => d.x ?? 0).attr("cy", (d) => d.y ?? 0);

        g.selectAll<SVGTextElement, GraphNode>(".labels text")
          .attr("x", (d) => d.x ?? 0)
          .attr("y", (d) => d.y ?? 0);
      });

    // Re-energize on progressive reveal
    if (assessmentCount > 0) {
      simulation.alpha(0.3).restart();
    }

    simulationRef.current = simulation;

    return () => {
      simulation.stop();
    };
  }, [data, assessments.length]);

  // -- Empty state --
  if (!data) {
    return (
      <div className="flex-1 min-h-0 bg-card-bg border border-border rounded-lg overflow-hidden relative flex items-center justify-center" style={{ minHeight: "300px" }}>
        <div className="text-center text-text-secondary">
          <svg
            className="mx-auto mb-3 opacity-30"
            width="64"
            height="64"
            viewBox="0 0 64 64"
            fill="none"
          >
            <circle cx="20" cy="20" r="6" stroke="currentColor" strokeWidth="2" />
            <circle cx="44" cy="16" r="5" stroke="currentColor" strokeWidth="2" />
            <circle cx="32" cy="44" r="7" stroke="currentColor" strokeWidth="2" />
            <line
              x1="25"
              y1="22"
              x2="39"
              y2="18"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <line
              x1="22"
              y1="25"
              x2="29"
              y2="39"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <line
              x1="42"
              y1="21"
              x2="36"
              y2="39"
              stroke="currentColor"
              strokeWidth="1.5"
            />
          </svg>
          <p className="text-sm">Submit a transaction to see the fraud network</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 min-h-0 bg-card-bg border border-border rounded-lg overflow-hidden relative" style={{ minHeight: "300px" }}>
      <svg ref={svgRef} className="w-full h-full" style={{ display: "block" }} />

      {/* Tooltip */}
      {tooltip.visible && tooltip.node && (
        <div
          className="absolute pointer-events-none bg-bg-primary/95 border border-border rounded px-2 py-1 text-xs shadow-lg z-10"
          style={{
            left: tooltip.x + 12,
            top: tooltip.y - 8,
          }}
        >
          <div className="font-mono text-text-primary">{tooltip.node.id}</div>
          <div className="text-text-secondary">
            Type: <span className="capitalize">{tooltip.node.type}</span>
          </div>
          {tooltip.node.is_fraud && (
            <div className="text-danger font-semibold">Fraud-linked</div>
          )}
          {tooltip.node.is_target && (
            <div className="text-warning font-semibold">Target card</div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-2 right-2 bg-bg-primary/80 backdrop-blur-sm p-2 rounded text-xs border border-border">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: NODE_COLORS.card }}
            />
            <span className="text-text-secondary">Card</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: NODE_COLORS.merchant }}
            />
            <span className="text-text-secondary">Merchant</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: NODE_COLORS.device }}
            />
            <span className="text-text-secondary">Device</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full"
              style={{
                backgroundColor: FRAUD_GLOW_COLOR,
                boxShadow: `0 0 6px ${FRAUD_GLOW_COLOR}`,
              }}
            />
            <span className="text-text-secondary">Fraud</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full border-2"
              style={{ borderColor: TARGET_BORDER, backgroundColor: "transparent" }}
            />
            <span className="text-text-secondary">Target</span>
          </div>
        </div>
      </div>
    </div>
  );
}
