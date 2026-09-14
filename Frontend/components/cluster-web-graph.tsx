"use client";

import React, { useEffect, useRef, useState } from "react";
import { Cluster, getRiskColor, isDarknetOrTor } from "@/lib/data";

interface Node {
  id: string;
  label: string;
  shortLabel: string;
  type: "cluster_core" | "seed_wallet" | "member_wallet" | "transaction" | "external_neighbor";
  riskScore: number;
  color: string;
  radius: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  isDragging?: boolean;
  degree?: number;
  details?: Record<string, any>;
}

interface Edge {
  source: string;
  target: string;
  type: "belongs_to" | "transfers_to" | "common_input" | "peel_hop";
  confidence: number;
  flowParticles: { offset: number; speed: number; color: string }[];
}

interface ClusterWebGraphProps {
  cluster: Cluster;
  subgraphData?: { nodes: any[]; edges: any[] } | null;
  activeAddress?: string | null;
  onSelectAddress?: (addr: string) => void;
}

export function ClusterWebGraph({
  cluster,
  subgraphData,
  activeAddress,
  onSelectAddress,
}: ClusterWebGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Graph state refs (for 60fps animation loop without React render lags)
  const nodesRef = useRef<Node[]>([]);
  const edgesRef = useRef<Edge[]>([]);
  const transformRef = useRef({ x: 0, y: 0, k: 1 });
  const alphaRef = useRef(1.0);
  const mouseRef = useRef<{ x: number; y: number; isDown: boolean; dragNode: Node | null; lastX: number; lastY: number }>({
    x: 0,
    y: 0,
    isDown: false,
    dragNode: null,
    lastX: 0,
    lastY: 0,
  });

  const [physicsActive, setPhysicsActive] = useState(true);
  const [flowActive, setFlowActive] = useState(true);
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [copied, setCopied] = useState(false);

  // Build graph nodes & edges whenever cluster or subgraphData changes
  useEffect(() => {
    alphaRef.current = 1.0;
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    const nodeMap = new Map<string, Node>();

    const width = containerRef.current?.clientWidth || 700;
    const height = containerRef.current?.clientHeight || 460;
    const cx = width / 2;
    const cy = height / 2;

    const isDarknetCluster = isDarknetOrTor({ label: cluster.label, explanation: cluster.description });
    const coreColor = isDarknetCluster ? "#c084fc" : "#00f0ff";

    // 1. Central Master Cluster Core Node
    const coreNode: Node = {
      id: `cluster_${cluster.cluster_id}`,
      label: cluster.label,
      shortLabel: isDarknetCluster ? "DNM" : "CORE",
      type: "cluster_core",
      riskScore: cluster.avg_risk_score,
      color: coreColor,
      radius: 26,
      x: cx,
      y: cy,
      vx: 0,
      vy: 0,
      details: {
        method: cluster.clustering_method,
        membersCount: cluster.member_count,
        description: cluster.description,
        networkLayer: isDarknetCluster ? "Tor Onion Network (.onion)" : "Clearnet P2P (8333)",
        entityCategory: isDarknetCluster ? "Darknet Marketplace / Hidden Service" : "Clustered Entity",
      },
    };
    nodes.push(coreNode);
    nodeMap.set(coreNode.id, coreNode);

    // 2. Member Wallet Nodes
    const members = cluster.member_addresses || [];
    const numMembers = Math.min(14, members.length);

    members.slice(0, numMembers).forEach((addr, i) => {
      const angle = (i / numMembers) * Math.PI * 2;
      const dist = 110 + (i % 2) * 45;
      const isSeed = i === 0;

      // Deterministic pseudo-risk around cluster average
      const risk = isSeed
        ? cluster.avg_risk_score
        : Math.max(0.1, Math.min(0.99, cluster.avg_risk_score + (Math.sin(i * 3.7) * 0.15)));
      const color = isDarknetCluster ? (i % 2 === 0 ? "#c084fc" : getRiskColor(risk)) : getRiskColor(risk);

      const torRole = isSeed
        ? "🧅 Primary Darknet Escrow Vault"
        : i % 3 === 1
        ? "🧅 Tor Exit Relay Node (Port 9050)"
        : i % 3 === 2
        ? "🧅 Darknet Vendor Deposit Seed"
        : "🧅 Layered Onion Cashout Mule";

      const node: Node = {
        id: addr,
        label: addr,
        shortLabel: isDarknetCluster && i < 3 ? (i === 0 ? "ESCROW" : i === 1 ? "TOR-9050" : "VENDOR") : addr.slice(0, 5) + "…" + addr.slice(-3),
        type: isSeed ? "seed_wallet" : "member_wallet",
        riskScore: risk,
        color,
        radius: isSeed ? 18 : 14,
        x: cx + Math.cos(angle) * dist,
        y: cy + Math.sin(angle) * dist,
        vx: 0,
        vy: 0,
        details: {
          role: isDarknetCluster ? torRole : (isSeed ? "Primary Seed Wallet" : "Consolidation / Member"),
          clusterId: cluster.cluster_id,
          networkProtocol: isDarknetCluster ? "Tor v3 Onion Hidden Service / Relay" : "Clearnet P2P",
        },
      };
      nodes.push(node);
      nodeMap.set(addr, node);

      // Edge from core to member
      edges.push({
        source: coreNode.id,
        target: addr,
        type: "belongs_to",
        confidence: 0.95,
        flowParticles: [
          { offset: Math.random(), speed: 0.006 + Math.random() * 0.006, color: isDarknetCluster ? "#c084fc" : "#00f0ff" },
        ],
      });

      // Synthetic peer-to-peer / peel-chain links between consecutive members
      if (i > 0 && i < numMembers) {
        const prevAddr = members[i - 1];
        edges.push({
          source: prevAddr,
          target: addr,
          type: "peel_hop",
          confidence: 0.85,
          flowParticles: [
            { offset: Math.random(), speed: 0.008 + Math.random() * 0.005, color: isDarknetCluster ? "#d8b4fe" : risk > 0.7 ? "#ff5267" : "#00ffcc" },
          ],
        });
      }
    });

    // 3. Intermediate Synthetic Transaction Hubs for rich topology
    if (numMembers >= 3) {
      const tx1Id = `tx_hop_alpha_${cluster.cluster_id}`;
      const tx1: Node = {
        id: tx1Id,
        label: `TX: Layering Hub Alpha`,
        shortLabel: "TX-α",
        type: "transaction",
        riskScore: cluster.avg_risk_score,
        color: "#c084fc",
        radius: 11,
        x: cx - 80,
        y: cy + 70,
        vx: 0,
        vy: 0,
        details: { txid: "4b8e...12a4", value: "14.28 BTC", hops: 2 },
      };
      nodes.push(tx1);
      nodeMap.set(tx1Id, tx1);

      if (members[0]) edges.push({ source: members[0], target: tx1Id, type: "transfers_to", confidence: 0.9, flowParticles: [{ offset: 0.3, speed: 0.01, color: "#c084fc" }] });
      if (members[1]) edges.push({ source: tx1Id, target: members[1], type: "transfers_to", confidence: 0.9, flowParticles: [{ offset: 0.7, speed: 0.01, color: "#c084fc" }] });
    }

    // 4. Merge Subgraph Data from Neo4j/GraphML if available
    if (subgraphData && subgraphData.nodes && subgraphData.nodes.length > 0) {
      subgraphData.nodes.slice(0, 10).forEach((sn) => {
        if (!nodeMap.has(sn.id)) {
          const angle = Math.random() * Math.PI * 2;
          const dist = 180 + Math.random() * 60;
          const extNode: Node = {
            id: sn.id,
            label: sn.label || sn.id,
            shortLabel: (sn.label || sn.id).slice(0, 6) + "…",
            type: "external_neighbor",
            riskScore: cluster.avg_risk_score * 0.7,
            color: "#60a5fa",
            radius: 11,
            x: cx + Math.cos(angle) * dist,
            y: cy + Math.sin(angle) * dist,
            vx: 0,
            vy: 0,
            details: { type: sn.type || "external_neighbor" },
          };
          nodes.push(extNode);
          nodeMap.set(sn.id, extNode);
        }
      });

      if (subgraphData.edges) {
        subgraphData.edges.forEach((se) => {
          if (nodeMap.has(se.source) && nodeMap.has(se.target)) {
            edges.push({
              source: se.source,
              target: se.target,
              type: "transfers_to",
              confidence: se.confidence || 0.75,
              flowParticles: [
                { offset: Math.random(), speed: 0.007, color: "#60a5fa" },
              ],
            });
          }
        });
      }
    }

    // Compute degrees
    const degreeCount: Record<string, number> = {};
    edges.forEach(e => {
      degreeCount[e.source] = (degreeCount[e.source] || 0) + 1;
      degreeCount[e.target] = (degreeCount[e.target] || 0) + 1;
    });
    nodes.forEach(n => {
      n.degree = degreeCount[n.id] || 0;
    });

    nodesRef.current = nodes;
    edgesRef.current = edges;

    // Default selection to seed address
    const initialSelected = nodes.find(n => n.id === activeAddress) || nodes[1] || nodes[0];
    setSelectedNode(initialSelected);
  }, [cluster, subgraphData]);

  // Sync activeAddress prop changes
  useEffect(() => {
    if (activeAddress) {
      const match = nodesRef.current.find(n => n.id === activeAddress);
      if (match) setSelectedNode(match);
    }
  }, [activeAddress]);

  // Main Canvas Render & Force-Directed Physics Animation Loop
  useEffect(() => {
    let animationFrameId: number;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Handle high-DPI
    const resizeCanvas = () => {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    const animate = () => {
      const width = canvas.getBoundingClientRect().width;
      const height = canvas.getBoundingClientRect().height;
      const cx = width / 2;
      const cy = height / 2;

      // 1. Force-Directed Physics Step (Alpha cooling + Coulomb repulsion + Hooke springs + gravity)
      if (physicsActive && alphaRef.current > 0.001) {
        const alpha = alphaRef.current;
        const nodes = nodesRef.current;
        const edges = edgesRef.current;
        const nodeMap = new Map(nodes.map(n => [n.id, n]));

        // Coulomb repulsion between all node pairs
        for (let i = 0; i < nodes.length; i++) {
          const n1 = nodes[i];
          for (let j = i + 1; j < nodes.length; j++) {
            const n2 = nodes[j];
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const distSq = dx * dx + dy * dy || 1;
            const dist = Math.max(25, Math.sqrt(distSq));

            if (dist < 200) {
              const repulse = ((n1.radius + n2.radius) * 12 * alpha) / dist;
              const fx = (dx / dist) * repulse;
              const fy = (dy / dist) * repulse;
              if (!n1.isDragging && n1.type !== "cluster_core") { n1.vx -= fx; n1.vy -= fy; }
              if (!n2.isDragging && n2.type !== "cluster_core") { n2.vx += fx; n2.vy += fy; }
            }
          }

          // Gentle center anchor & gravity
          if (!n1.isDragging) {
            if (n1.type === "cluster_core") {
              // Lock core node near center smoothly
              n1.vx += (cx - n1.x) * 0.1 * alpha;
              n1.vy += (cy - n1.y) * 0.1 * alpha;
            } else {
              const cdx = cx - n1.x;
              const cdy = cy - n1.y;
              n1.vx += cdx * 0.0012 * alpha;
              n1.vy += cdy * 0.0012 * alpha;
            }
          }
        }

        // Spring attraction along edges
        edges.forEach(e => {
          const src = nodeMap.get(e.source);
          const tgt = nodeMap.get(e.target);
          if (!src || !tgt) return;

          const dx = tgt.x - src.x;
          const dy = tgt.y - src.y;
          const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
          const idealDist = src.type === "cluster_core" || tgt.type === "cluster_core" ? 115 : 65;
          const spring = (dist - idealDist) * 0.025 * alpha;

          // Clamp spring force to prevent wild swings
          const clampedSpring = Math.max(-5, Math.min(5, spring));
          const fx = (dx / dist) * clampedSpring;
          const fy = (dy / dist) * clampedSpring;

          if (!src.isDragging && src.type !== "cluster_core") { src.vx += fx; src.vy += fy; }
          if (!tgt.isDragging && tgt.type !== "cluster_core") { tgt.vx += fx; tgt.vy += fy; }
        });

        // Position update & strong velocity damping
        nodes.forEach(n => {
          if (!n.isDragging) {
            // Strong damping for tranquil settling
            n.vx *= 0.80;
            n.vy *= 0.80;

            // Velocity clamp
            const speed = Math.hypot(n.vx, n.vy);
            const maxSpeed = 4 * alpha;
            if (speed > maxSpeed && speed > 0) {
              n.vx = (n.vx / speed) * maxSpeed;
              n.vy = (n.vy / speed) * maxSpeed;
            }

            // Cutoff jitter at near-zero
            if (speed < 0.02) {
              n.vx = 0;
              n.vy = 0;
            }

            n.x += n.vx;
            n.y += n.vy;

            // Soft container boundary containment without bounce
            const pad = n.radius + 20;
            if (n.x < pad) { n.x = pad; n.vx = 0; }
            if (n.x > width - pad) { n.x = width - pad; n.vx = 0; }
            if (n.y < pad) { n.y = pad; n.vy = 0; }
            if (n.y > height - pad) { n.y = height - pad; n.vy = 0; }
          }
        });

        // Cool alpha down smoothly
        alphaRef.current *= 0.985;
      }

      // 2. Render Scene
      ctx.save();
      ctx.clearRect(0, 0, width, height);

      const transform = transformRef.current;
      ctx.translate(transform.x, transform.y);
      ctx.scale(transform.k, transform.k);

      // Deep space grid background
      ctx.strokeStyle = "rgba(16, 42, 86, 0.25)";
      ctx.lineWidth = 1;
      const gridSize = 40;
      for (let x = -width; x < width * 2; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, -height);
        ctx.lineTo(x, height * 2);
        ctx.stroke();
      }
      for (let y = -height; y < height * 2; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(-width, y);
        ctx.lineTo(width * 2, y);
        ctx.stroke();
      }

      const nodes = nodesRef.current;
      const edges = edgesRef.current;
      const nodeMap = new Map(nodes.map(n => [n.id, n]));

      // 3. Cluster Boundary Halo Hull
      if (nodes.length > 2) {
        const memberNodes = nodes.filter(n => n.type !== "external_neighbor");
        if (memberNodes.length > 0) {
          const avgX = memberNodes.reduce((acc, n) => acc + n.x, 0) / memberNodes.length;
          const avgY = memberNodes.reduce((acc, n) => acc + n.y, 0) / memberNodes.length;
          let maxR = 60;
          memberNodes.forEach(n => {
            const d = Math.hypot(n.x - avgX, n.y - avgY) + n.radius + 20;
            if (d > maxR) maxR = d;
          });

          const isTor = isDarknetOrTor({ label: cluster.label, description: cluster.description });
          const grad = ctx.createRadialGradient(avgX, avgY, maxR * 0.2, avgX, avgY, maxR);
          if (isTor) {
            grad.addColorStop(0, "rgba(192, 132, 252, 0.15)");
            grad.addColorStop(0.7, "rgba(147, 51, 234, 0.06)");
            grad.addColorStop(1, "rgba(192, 132, 252, 0)");
          } else {
            grad.addColorStop(0, "rgba(0, 240, 255, 0.09)");
            grad.addColorStop(0.7, "rgba(0, 150, 255, 0.04)");
            grad.addColorStop(1, "rgba(0, 240, 255, 0)");
          }

          ctx.save();
          ctx.beginPath();
          ctx.arc(avgX, avgY, maxR, 0, Math.PI * 2);
          ctx.fillStyle = grad;
          ctx.fill();

          ctx.strokeStyle = isTor ? "rgba(192, 132, 252, 0.3)" : "rgba(0, 240, 255, 0.18)";
          ctx.setLineDash([4, 6]);
          ctx.lineWidth = 1.5;
          ctx.stroke();
          ctx.restore();
        }
      }

      // 4. Draw Edges
      edges.forEach(e => {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (!src || !tgt) return;

        const isHighlighted = (hoveredNode && (hoveredNode.id === src.id || hoveredNode.id === tgt.id)) ||
                              (selectedNode && (selectedNode.id === src.id || selectedNode.id === tgt.id));

        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);

        if (isHighlighted) {
          ctx.strokeStyle = "#00f0ff";
          ctx.lineWidth = 2.5;
          ctx.shadowColor = "#00f0ff";
          ctx.shadowBlur = 10;
        } else if (e.type === "belongs_to") {
          ctx.strokeStyle = "rgba(0, 240, 255, 0.22)";
          ctx.lineWidth = 1.6;
          ctx.shadowBlur = 0;
        } else if (e.type === "peel_hop") {
          ctx.strokeStyle = "rgba(255, 190, 61, 0.35)";
          ctx.lineWidth = 1.5;
          ctx.shadowBlur = 0;
        } else {
          ctx.strokeStyle = "rgba(168, 85, 247, 0.3)";
          ctx.lineWidth = 1.2;
          ctx.shadowBlur = 0;
        }
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Animated Electric Flow Particles
        if (flowActive) {
          e.flowParticles.forEach(p => {
            p.offset = (p.offset + p.speed) % 1;
            const px = src.x + (tgt.x - src.x) * p.offset;
            const py = src.y + (tgt.y - src.y) * p.offset;

            ctx.save();
            ctx.beginPath();
            ctx.arc(px, py, isHighlighted ? 3 : 2, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.shadowColor = p.color;
            ctx.shadowBlur = 8;
            ctx.fill();
            ctx.restore();
          });
        }
      });

      // 5. Draw Nodes
      nodes.forEach(n => {
        const isSelected = selectedNode?.id === n.id;
        const isHovered = hoveredNode?.id === n.id;

        // Outer Target Ring for Selected Node
        if (isSelected) {
          const pulse = (Math.sin(Date.now() * 0.005) + 1) * 3;
          ctx.save();
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius + 7 + pulse, 0, Math.PI * 2);
          ctx.strokeStyle = "#00f0ff";
          ctx.lineWidth = 2;
          ctx.shadowColor = "#00f0ff";
          ctx.shadowBlur = 16;
          ctx.setLineDash([3, 4]);
          ctx.stroke();
          ctx.restore();
        }

        // Node Glow Halo
        ctx.save();
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + (isHovered ? 6 : 3), 0, Math.PI * 2);
        ctx.fillStyle = isSelected ? "rgba(0, 240, 255, 0.3)" : `${n.color}25`;
        ctx.shadowColor = n.color;
        ctx.shadowBlur = isHovered || isSelected ? 18 : 8;
        ctx.fill();
        ctx.restore();

        // Node Main Body
        ctx.save();
        ctx.beginPath();
        if (n.type === "transaction") {
          // Diamond shape for transactions
          const s = n.radius * 1.2;
          ctx.moveTo(n.x, n.y - s);
          ctx.lineTo(n.x + s, n.y);
          ctx.lineTo(n.x, n.y + s);
          ctx.lineTo(n.x - s, n.y);
          ctx.closePath();
        } else {
          ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        }

        ctx.fillStyle = "#091738";
        ctx.fill();
        ctx.lineWidth = isSelected ? 3 : 2;
        ctx.strokeStyle = n.color;
        ctx.stroke();

        // Core Center Dot
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius * 0.45, 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        ctx.fill();

        // Node Glyphs
        if (n.type === "cluster_core") {
          ctx.fillStyle = "#fff";
          ctx.font = "bold 11px Inter, sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          const isDarknet = isDarknetOrTor({ label: cluster.label, explanation: cluster.description });
          ctx.fillText(isDarknet ? "🧅" : "⚡", n.x, n.y);
        } else if (n.type === "transaction") {
          ctx.fillStyle = "#fff";
          ctx.font = "bold 9px monospace";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText("TX", n.x, n.y);
        }
        ctx.restore();

        // Label under node
        ctx.save();
        ctx.font = isSelected || isHovered ? "bold 11px Inter, sans-serif" : "10px Inter, sans-serif";
        ctx.fillStyle = isSelected ? "#00f0ff" : isHovered ? "#fff" : "rgba(220, 235, 255, 0.85)";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.shadowColor = "#000";
        ctx.shadowBlur = 4;
        ctx.fillText(n.shortLabel, n.x, n.y + n.radius + 5);

        // Risk badge under label if wallet
        if (n.type !== "cluster_core" && n.type !== "transaction") {
          ctx.font = "bold 8px monospace";
          ctx.fillStyle = n.color;
          ctx.fillText(`${(n.riskScore * 100).toFixed(0)}%`, n.x, n.y + n.radius + 18);
        }
        ctx.restore();
      });

      ctx.restore();
      animationFrameId = requestAnimationFrame(animate);
    };

    animationFrameId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", resizeCanvas);
    };
  }, [physicsActive, flowActive, hoveredNode, selectedNode]);

  // Mouse Interaction Handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left - transformRef.current.x) / transformRef.current.k;
    const my = (e.clientY - rect.top - transformRef.current.y) / transformRef.current.k;

    // Hit test nodes in reverse order (top to bottom)
    const nodes = [...nodesRef.current].reverse();
    const hit = nodes.find(n => Math.hypot(n.x - mx, n.y - my) <= n.radius + 6);

    if (hit) {
      hit.isDragging = true;
      mouseRef.current.dragNode = hit;
      setSelectedNode(hit);
      alphaRef.current = Math.max(alphaRef.current, 0.4);
      if (hit.type !== "cluster_core" && hit.type !== "transaction" && onSelectAddress) {
        onSelectAddress(hit.id);
      }
    } else {
      mouseRef.current.isDown = true;
      mouseRef.current.lastX = e.clientX;
      mouseRef.current.lastY = e.clientY;
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left - transformRef.current.x) / transformRef.current.k;
    const my = (e.clientY - rect.top - transformRef.current.y) / transformRef.current.k;

    if (mouseRef.current.dragNode) {
      mouseRef.current.dragNode.x = mx;
      mouseRef.current.dragNode.y = my;
      mouseRef.current.dragNode.vx = 0;
      mouseRef.current.dragNode.vy = 0;
      alphaRef.current = Math.max(alphaRef.current, 0.25);
    } else if (mouseRef.current.isDown) {
      const dx = e.clientX - mouseRef.current.lastX;
      const dy = e.clientY - mouseRef.current.lastY;
      transformRef.current.x += dx;
      transformRef.current.y += dy;
      mouseRef.current.lastX = e.clientX;
      mouseRef.current.lastY = e.clientY;
    } else {
      // Hover detection
      const nodes = [...nodesRef.current].reverse();
      const hit = nodes.find(n => Math.hypot(n.x - mx, n.y - my) <= n.radius + 6);
      setHoveredNode(hit || null);
      canvas.style.cursor = hit ? "pointer" : "grab";
    }
  };

  const handleMouseUp = () => {
    if (mouseRef.current.dragNode) {
      mouseRef.current.dragNode.isDragging = false;
      mouseRef.current.dragNode = null;
      alphaRef.current = Math.max(alphaRef.current, 0.35);
    }
    mouseRef.current.isDown = false;
  };

  // Native non-passive Wheel listener to guarantee page doesn't scroll while zooming
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const onWheelNative = (e: WheelEvent) => {
      e.preventDefault();
      e.stopPropagation();

      const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
      const currentK = transformRef.current.k;
      const newK = Math.max(0.4, Math.min(3.0, currentK * zoomFactor));

      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      transformRef.current.x = mouseX - (mouseX - transformRef.current.x) * (newK / currentK);
      transformRef.current.y = mouseY - (mouseY - transformRef.current.y) * (newK / currentK);
      transformRef.current.k = newK;
    };

    canvas.addEventListener("wheel", onWheelNative, { passive: false });

    return () => {
      canvas.removeEventListener("wheel", onWheelNative);
    };
  }, []);

  const handleResetView = () => {
    transformRef.current = { x: 0, y: 0, k: 1 };
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard?.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div className="cluster-web-wrapper" ref={containerRef}>
      {/* Top HUD Info Bar */}
      <div className="cluster-web-topbar">
        <div className="web-title">
          <span className="live-dot" />
          <b>TOPOLOGICAL NETWORK WEB</b>
          <small>Interactive Force Simulation • {nodesRef.current.length} Entities • {edgesRef.current.length} Relations</small>
        </div>
        <div className="web-actions">
          <button
            className={`web-btn ${flowActive ? "active" : ""}`}
            onClick={() => setFlowActive(!flowActive)}
            title="Toggle animated flow particles"
          >
            ⚡ {flowActive ? "Flow Active" : "Flow Paused"}
          </button>
          <button
            className={`web-btn ${physicsActive ? "active" : ""}`}
            onClick={() => {
              if (!physicsActive) alphaRef.current = 0.5;
              setPhysicsActive(!physicsActive);
            }}
            title="Freeze/unfreeze node layout physics"
          >
            {physicsActive ? "⏸ Freeze" : "▶ Float"}
          </button>
          <button className="web-btn" onClick={handleResetView} title="Reset zoom and center view">
            ⛶ Recenter
          </button>
        </div>
      </div>

      {/* Main Canvas */}
      <canvas
        ref={canvasRef}
        className="cluster-canvas"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      />

      {/* Floating Cyberpunk HUD on Selected Node */}
      {selectedNode && (
        <div className="node-hud glass">
          <div className="node-hud-header">
            <span
              className="node-hud-type"
              style={{ color: selectedNode.color, borderColor: `${selectedNode.color}66` }}
            >
              {selectedNode.type === "cluster_core"
                ? isDarknetOrTor({ label: cluster.label, explanation: cluster.description }) ? "DARKNET MARKET HUB (TOR)" : "MASTER CLUSTER HUB"
                : selectedNode.type === "seed_wallet"
                ? isDarknetOrTor({ label: cluster.label, explanation: cluster.description }) ? "DARKNET VENDOR SEED" : "SEED ORIGIN WALLET"
                : selectedNode.type === "transaction"
                ? "TRANSACTION HOP"
                : selectedNode.type === "external_neighbor"
                ? "TOPOLOGICAL NEIGHBOR"
                : isDarknetOrTor({ label: cluster.label, explanation: cluster.description }) ? "DARKNET ESCROW / MEMBER" : "MEMBER WALLET"}
            </span>
            <button className="node-hud-close" onClick={() => setSelectedNode(null)}>×</button>
          </div>

          <div className="node-hud-body">
            <div className="node-hud-id">
              <code title={selectedNode.id}>
                {selectedNode.id.length > 24
                  ? `${selectedNode.id.slice(0, 10)}…${selectedNode.id.slice(-8)}`
                  : selectedNode.id}
              </code>
              <button
                className="copy-btn"
                onClick={() => copyToClipboard(selectedNode.id)}
                title="Copy Address / ID"
              >
                {copied ? "✓ Copied" : "📋"}
              </button>
            </div>

            <div className="node-hud-grid">
              <div>
                <span>Risk Metric</span>
                <strong style={{ color: selectedNode.color }}>
                  {(selectedNode.riskScore * 100).toFixed(1)}%
                </strong>
              </div>
              <div>
                <span>Connected Links</span>
                <strong>{selectedNode.degree || 1} edges</strong>
              </div>
              <div>
                <span>Network Transport</span>
                <strong style={{ color: isDarknetOrTor({ label: cluster.label, explanation: cluster.description }) ? "#c084fc" : "var(--cyan)", fontSize: "10px" }}>
                  {isDarknetOrTor({ label: cluster.label, explanation: cluster.description }) ? "🧅 Tor Onion Overlay" : "🌐 Clearnet (8333)"}
                </strong>
              </div>
              {selectedNode.details?.method && (
                <div style={{ gridColumn: "span 2" }}>
                  <span>Heuristic Classifier</span>
                  <code style={{ fontSize: "9px", color: "var(--cyan)" }}>
                    {selectedNode.details.method}
                  </code>
                </div>
              )}
            </div>

            {selectedNode.type !== "cluster_core" && selectedNode.type !== "transaction" && (
              <button
                className="node-hud-inspect-btn"
                onClick={() => onSelectAddress && onSelectAddress(selectedNode.id)}
              >
                🔍 Query Subgraph from Neo4j
              </button>
            )}
          </div>
        </div>
      )}

      {/* Canvas Floating Instruction Bar */}
      <div className="canvas-footer-hint">
        <span>🖱 <b>Click & Drag</b> nodes to test elastic physics</span>
        <span>•</span>
        <span><b>Scroll</b> to zoom</span>
        <span>•</span>
        <span><b>Click</b> node to query subgraph</span>
      </div>
    </div>
  );
}
