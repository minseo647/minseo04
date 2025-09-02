import React, { useEffect, useRef } from 'react';
import { Paper, Typography } from '@mui/material';
import type { NetworkData } from '../api/newsApi';

interface KeywordNetworkProps {
  data: NetworkData;
}

export const KeywordNetwork: React.FC<KeywordNetworkProps> = ({ data }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !data.nodes.length) return;

    // Simple D3-like network visualization using canvas
    const container = containerRef.current;
    const canvas = document.createElement('canvas');
    const width = container.offsetWidth;
    const height = 500;
    canvas.width = width;
    canvas.height = height;
    container.innerHTML = '';
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Simple force-directed layout
    const nodes = data.nodes.map((node) => ({
      ...node,
      x: Math.random() * width,
      y: Math.random() * height,
      vx: 0,
      vy: 0,
    }));

    const simulation = () => {
      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Draw edges
      data.edges.forEach(edge => {
        const source = nodes.find(n => n.id === edge.from);
        const target = nodes.find(n => n.id === edge.to);
        if (source && target) {
          // Edge thickness based on value
          const thickness = Math.max(1, Math.min(5, edge.value || 1));
          
          // Edge color with opacity based on value
          const maxEdgeValue = Math.max(...data.edges.map(e => e.value || 1));
          const opacity = 0.3 + (0.7 * (edge.value || 1)) / maxEdgeValue;
          
          ctx.strokeStyle = `rgba(25, 118, 210, ${opacity})`;
          ctx.lineWidth = thickness;
          
          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          ctx.lineTo(target.x, target.y);
          ctx.stroke();
          
          // Draw edge label for significant connections
          if (edge.value && edge.value >= 2) {
            const midX = (source.x + target.x) / 2;
            const midY = (source.y + target.y) / 2;
            
            // Background for label
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.font = 'bold 10px sans-serif';
            ctx.textAlign = 'center';
            const textWidth = ctx.measureText(edge.value.toString()).width;
            ctx.fillRect(midX - textWidth/2 - 3, midY - 8, textWidth + 6, 16);
            
            // Label text
            ctx.fillStyle = '#fff';
            ctx.fillText(edge.value.toString(), midX, midY + 3);
          }
        }
      });

      // Draw nodes
      nodes.forEach((node: any) => {
        const radius = Math.sqrt(node.value) * 3;
        
        // Node circle
        ctx.fillStyle = '#1976d2';
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.fill();

        // Node label background
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        const textWidth = ctx.measureText(node.label).width;
        const textHeight = 12;
        const padding = 2;
        
        // Semi-transparent background for better readability
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.fillRect(
          node.x - textWidth / 2 - padding,
          node.y - radius - textHeight - 5 - padding,
          textWidth + padding * 2,
          textHeight + padding * 2
        );
        
        // Node label text
        ctx.fillStyle = '#333';
        ctx.fillText(node.label, node.x, node.y - radius - 5);
      });
    };

    simulation();

    // Simple interaction
    canvas.addEventListener('mousemove', (e) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Find nearest node
      let nearestNode: any = null;
      let minDist = Infinity;
      nodes.forEach((node: any) => {
        const dist = Math.sqrt(Math.pow(node.x - x, 2) + Math.pow(node.y - y, 2));
        if (dist < minDist && dist < Math.sqrt(node.value) * 3) {
          minDist = dist;
          nearestNode = node;
        }
      });

      // Find nearest edge
      let nearestEdge: any = null;
      let minEdgeDist = Infinity;
      data.edges.forEach(edge => {
        const source = nodes.find(n => n.id === edge.from);
        const target = nodes.find(n => n.id === edge.to);
        if (source && target) {
          const midX = (source.x + target.x) / 2;
          const midY = (source.y + target.y) / 2;
          const dist = Math.sqrt(Math.pow(midX - x, 2) + Math.pow(midY - y, 2));
          if (dist < minEdgeDist && dist < 15) {
            minEdgeDist = dist;
            nearestEdge = edge;
          }
        }
      });

      if (nearestNode) {
        canvas.style.cursor = 'pointer';
        canvas.title = `${nearestNode.label} (${nearestNode.value}회 언급)`;
      } else if (nearestEdge) {
        canvas.style.cursor = 'pointer';
        canvas.title = nearestEdge.title || `${nearestEdge.from} ↔ ${nearestEdge.to} (${nearestEdge.value}회 동시 언급)`;
      } else {
        canvas.style.cursor = 'default';
        canvas.title = '';
      }
    });

  }, [data]);

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        키워드 네트워크
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        • 원의 크기는 키워드 언급 빈도를 나타냅니다
        • 선으로 연결된 키워드들은 함께 언급되는 경우가 많습니다
        • 마우스를 올리면 상세 정보를 확인할 수 있습니다
      </Typography>
      <div ref={containerRef} style={{ minHeight: 500 }} />
    </Paper>
  );
};