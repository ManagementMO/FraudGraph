'use client';

import { useRef, useMemo, useCallback, useEffect } from 'react';
import dynamic from 'next/dynamic';
import * as THREE from 'three';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { getNodeHDRColor } from '@/lib/colors';
import type { GraphData, GraphNode, AgentAssessment } from '@/lib/types';

// ForceGraph3D is client-only (WebGL). Dynamic import prevents SSR crash.
const ForceGraph3D = dynamic(
  () => import('react-force-graph-3d'),
  { ssr: false, loading: () => null }
);

interface GraphVisualizationProps {
  data: GraphData | null;
  assessments: AgentAssessment[];
}

export function GraphVisualization({ data, assessments }: GraphVisualizationProps) {
  const fgRef = useRef<any>(null);  // eslint-disable-line @typescript-eslint/no-explicit-any
  const bloomInitialized = useRef(false);

  // Reset bloom when new graph data arrives
  useEffect(() => {
    bloomInitialized.current = false;
  }, [data]);

  // Progressive node reveal based on assessment count:
  // 0 assessments → target node only
  // 1-3 assessments → proportional subset
  // 4+ assessments → full graph
  const visibleGraphData = useMemo(() => {
    if (!data) return { nodes: [], links: [] };

    const target = data.nodes.find(n => n.is_target);
    const others = data.nodes.filter(n => !n.is_target);

    if (assessments.length === 0) {
      return { nodes: target ? [target] : [], links: [] };
    }

    const totalAgents = 4;
    const progress = Math.min(assessments.length / totalAgents, 1);

    if (progress >= 1) return data;

    const visibleCount = Math.ceil(others.length * progress);
    const visibleOthers = others.slice(0, visibleCount);
    const visibleNodes = target ? [target, ...visibleOthers] : visibleOthers;
    const visibleIds = new Set(visibleNodes.map(n => n.id));

    const visibleLinks = data.links.filter(l => {
      const s = typeof l.source === 'string' ? l.source : (l.source as GraphNode).id;
      const t = typeof l.target === 'string' ? l.target : (l.target as GraphNode).id;
      return visibleIds.has(s) && visibleIds.has(t);
    });

    return { nodes: visibleNodes, links: visibleLinks };
  }, [data, assessments.length]);

  // Build 3D sphere mesh per node with HDR emissive color for bloom
  const nodeThreeObject = useCallback((node: object) => {
    const n = node as GraphNode;
    const color = getNodeHDRColor(n);

    // Radius: larger for target, scale with val otherwise
    const radius = n.is_target ? 8 : Math.max(3, (n.val ?? 5) * 0.6);

    const geo = new THREE.SphereGeometry(radius, 14, 14);
    const mat = new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: n.is_target ? 1.2 : (n.is_fraud ? 0.9 : 0.6),
      toneMapped: false,  // CRITICAL: allows HDR values past 1.0 to bloom
      roughness: 0.4,
      metalness: 0.1,
    });
    return new THREE.Mesh(geo, mat);
  }, []);

  // Link color based on whether endpoints are fraud-linked
  const linkColor = useCallback((link: object) => {
    const l = link as { source: unknown; target: unknown };
    const src = l.source as GraphNode;
    const tgt = l.target as GraphNode;
    if (src?.is_fraud && tgt?.is_fraud) return 'rgba(255, 69, 69, 0.25)';
    return 'rgba(196, 212, 232, 0.07)';
  }, []);

  const linkWidth = useCallback((link: object) => {
    const l = link as { weight?: number };
    return (l.weight ?? 0.5) * 0.8;
  }, []);

  // Add UnrealBloomPass after engine initializes
  const handleEngineStop = useCallback(() => {
    if (bloomInitialized.current || !fgRef.current) return;

    const fg = fgRef.current;
    const renderer = fg.renderer() as THREE.WebGLRenderer;

    // Must disable tone mapping BEFORE adding bloom
    // or HDR values are clamped to [0,1] before bloom sees them
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.toneMappingExposure = 1;

    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight),
      0.45,  // strength — low so clustered nodes don't compound into a white blob
      0.3,   // radius
      0.25   // threshold — only the brightest HDR values bloom
    );

    // Use the library's built-in EffectComposer
    fg.postProcessingComposer().addPass(bloomPass);

    // Tune forces for better 3D layout
    fg.d3Force('charge')?.strength(-180);
    fg.d3Force('link')?.distance(50);

    bloomInitialized.current = true;
  }, []);

  // Hover tooltip HTML
  const nodeLabel = useCallback((node: object) => {
    const n = node as GraphNode;
    const riskColor = n.is_target ? '#f5c842' : n.is_fraud ? '#ff4545' : '#2dffc8';
    const status = n.is_target ? 'TARGET' : n.is_fraud ? 'FRAUD-LINKED' : 'CLEAN';
    return `<div style="
      font-family: 'Fragment Mono', monospace;
      font-size: 11px;
      background: rgba(4, 8, 20, 0.92);
      border: 1px solid rgba(255,255,255,0.1);
      padding: 7px 11px;
      border-radius: 4px;
      color: #c4d4e8;
      line-height: 1.6;
      max-width: 200px;
    ">
      <div style="color: ${riskColor}; font-size: 10px; letter-spacing: 0.1em; margin-bottom: 3px">${status}</div>
      <div style="margin-bottom: 2px">${n.id}</div>
      <div style="color: rgba(196,212,232,0.5); font-size: 10px">
        ${n.type.toUpperCase()} · Community ${n.community}
      </div>
    </div>`;
  }, []);

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 0, background: '#04060f' }}>
      <ForceGraph3D
        ref={fgRef}
        graphData={visibleGraphData}
        backgroundColor="#04060f"
        numDimensions={3}
        d3AlphaDecay={0.015}
        d3VelocityDecay={0.25}
        cooldownTime={8000}
        nodeThreeObject={nodeThreeObject}
        nodeThreeObjectExtend={false}
        linkColor={linkColor}
        linkWidth={linkWidth}
        linkOpacity={1}
        nodeLabel={nodeLabel}
        onEngineStop={handleEngineStop}
        width={typeof window !== 'undefined' ? window.innerWidth : 1920}
        height={typeof window !== 'undefined' ? window.innerHeight : 1080}
      />
    </div>
  );
}
