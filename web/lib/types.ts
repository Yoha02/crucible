export type NodeType = "persona" | "variant";
export type Phase = "idle" | "curating" | "reacting" | "deliberating" | "evolving" | "converged";

export type GraphNode = {
  id: string;
  type: NodeType;
  group: string;
  generation: number | null;
  fitness: number | null;
  status: "alive" | "dead";
  label: string;
  preview: string;
  parents: string[];
  genes: Record<string, unknown>;
  color?: string;
  role?: string;
  jtbd?: string;
  is_control?: boolean;
  niche?: string | null;
  weave_url?: string | null;
  fitness_detail?: {
    overall_intent: number;
    by_segment: Record<string, { intent: number; value: number; readiness: number; wtp: number }>;
  } | null;
};

export type GraphEdge = {
  source: string;
  target: string;
  kind: "lineage" | "objection";
  label?: string;
  ttl_ms?: number;
};

export type Island = {
  value: number;
  readiness: number;
  intent_best: number;
  status: string;
  label?: string;
  color?: string;
};

export type Report = {
  title: string;
  wedge_group: string;
  summary: string;
  segment_verdict: { segment: string; verdict: string }[];
  diff: { field: string; before: string; after: string }[];
  test: { name: string; instruction: string; bar: string; cost: string };
  generality?: {
    product: string;
    one_liner: string;
    method: string;
    winner: { segment: string; variant: string; intent: number };
    runner_up: { segment: string; intent: number };
    gated_segment: string;
    takeaway: string;
  };
  integrity?: {
    framing: string;
    fallback: string;
    lead_claim: string;
  };
};

export type GraphState = {
  run_id: string;
  phase: Phase;
  generation: number;
  islands: Record<string, Island>;
  nodes: Record<string, GraphNode>;
  edges: GraphEdge[];
  hud: {
    calls_made: number;
    cache_hits: number;
    skeptic_ratio: number;
    wedge: null | {
      group: string;
      variant_id: string;
      value: number;
      readiness: number;
      confidence: number;
    };
  };
  narration: string;
  orchestration_events: { actor: string; action: string }[];
  report: Report | null;
  active_tools: string[];
};

export const emptyState: GraphState = {
  run_id: "r1",
  phase: "idle",
  generation: 0,
  islands: {},
  nodes: {},
  edges: [],
  hud: { calls_made: 0, cache_hits: 0, skeptic_ratio: 0, wedge: null },
  narration: "Connect to the Crucible engine.",
  orchestration_events: [],
  report: null,
  active_tools: []
};
