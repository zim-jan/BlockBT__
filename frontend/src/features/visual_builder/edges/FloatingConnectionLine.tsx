import { getBezierPath } from '@xyflow/react';

import { getEdgeParams } from './utils.js';

function FloatingConnectionLine({
  toX,
  toY,
  fromPosition,
  toPosition,
  fromNode,
}: any) {
  if (!fromNode) {
    return null;
  }

  const targetNode = {
    id: 'connection-target',
    measured: {
      width: 1,
      height: 1,
    },
    internals: {
      positionAbsolute: { x: toX, y: toY },
    },
  };

  const { sx, sy, tx, ty, sourcePos, targetPos } = getEdgeParams(fromNode, targetNode);

  // Faza 9.2: `??` zamiast `||` — współrzędna 0 jest poprawną wartością,
  // a `||` traktował ją jak brak i podmieniał na pozycję kursora.
  const [edgePath] = getBezierPath({
    sourceX: sx,
    sourceY: sy,
    sourcePosition: sourcePos ?? fromPosition,
    targetPosition: targetPos ?? toPosition,
    targetX: tx ?? toX,
    targetY: ty ?? toY,
  });

  return (
    <g>
      <path
        fill="none"
        stroke="#b1b1b7"
        strokeWidth={1.5}
        className="animated"
        d={edgePath}
      />
      <circle
        cx={toX}
        cy={toY}
        fill="#fff"
        r={3}
        stroke="#b1b1b7"
        strokeWidth={1.5}
      />
    </g>
  );
}

export default FloatingConnectionLine;
