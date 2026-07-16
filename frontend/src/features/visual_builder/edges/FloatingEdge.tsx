import { BaseEdge, getBezierPath, useInternalNode } from '@xyflow/react';

import { getEdgeParams } from './utils.js';

function FloatingEdge({ id, source, target, markerEnd, style }: any) {
  const sourceNode = useInternalNode(source);
  const targetNode = useInternalNode(target);

  if (!sourceNode || !targetNode) {
    return null;
  }

  const { sx, sy, tx, ty, sourcePos, targetPos } = getEdgeParams(sourceNode, targetNode);

  const [edgePath] = getBezierPath({
    sourceX: sx,
    sourceY: sy,
    sourcePosition: sourcePos,
    targetPosition: targetPos,
    targetX: tx,
    targetY: ty,
  });

  return (
    <BaseEdge id={id} path={edgePath} markerEnd={markerEnd} style={style} />
  );
}

export default FloatingEdge;
