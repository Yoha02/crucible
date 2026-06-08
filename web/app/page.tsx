"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bot,
  GitBranch,
  Play,
  Radio,
  RotateCcw,
  Send,
  Sparkles,
  Waypoints
} from "lucide-react";
import { API_BASE, postLiveAnchor, postProjectUrl, postReplay, postRun, postSteer, subscribeGraphState } from "../lib/api";
import { GraphNode, GraphState, emptyState } from "../lib/types";

const groupOrder = ["trades", "hvac", "propmgmt", "law", "realestate", "finance", "unaligned"];
const fallbackColors: Record<string, string> = {
  trades: "#E4572E",
  hvac: "#F3A712",
  propmgmt: "#669BBC",
  law: "#3D348B",
  realestate: "#06A77D",
  finance: "#7A6C5D",
  unaligned: "#737373"
};

function truncateLabel(label: string, max = 24) {
  return label.length > max ? `${label.slice(0, max - 1)}...` : label;
}

type Point = { x: number; y: number };

function hashNumber(id: string) {
  return [...id].reduce((acc, char) => acc + char.charCodeAt(0), 0);
}

function sortVariants(a: GraphNode, b: GraphNode) {
  const generationDelta = (a.generation ?? 0) - (b.generation ?? 0);
  if (generationDelta !== 0) return generationDelta;
  const statusDelta = Number(a.status === "dead") - Number(b.status === "dead");
  if (statusDelta !== 0) return statusDelta;
  return groupOrder.indexOf(a.group) - groupOrder.indexOf(b.group) || a.id.localeCompare(b.id);
}

function generationY(generation: number, maxGeneration: number, height: number) {
  const bottom = height - 126;
  const top = 76;
  return bottom - (generation / Math.max(1, maxGeneration)) * (bottom - top);
}

function buildPyramidPositions(nodes: GraphNode[], state: GraphState, width: number, height: number) {
  const positions = new Map<string, Point>();
  const personas = nodes.filter((node) => node.type === "persona").sort((a, b) => a.id.localeCompare(b.id));
  const variants = nodes.filter((node) => node.type === "variant").sort(sortVariants);
  const maxGeneration = Math.max(3, state.generation, ...variants.map((node) => node.generation ?? 0));
  const center = width / 2;

  personas.forEach((node, index) => {
    const spread = personas.length > 1 ? index / (personas.length - 1) : 0.5;
    positions.set(node.id, {
      x: 88 + spread * (width - 176),
      y: height - 44 - (index % 2) * 18
    });
  });

  for (let generation = 0; generation <= maxGeneration; generation += 1) {
    const generationNodes = variants.filter((node) => (node.generation ?? 0) === generation);
    const span = Math.max(70, (width - 205) * (1 - generation / (maxGeneration + 0.45)));
    const y = generationY(generation, maxGeneration, height);
    generationNodes.forEach((node, index) => {
      const deadOffset = node.status === "dead" ? 20 : 0;
      const jitter = ((hashNumber(node.id) % 5) - 2) * 3;
      const slot = generationNodes.length > 1 ? index / (generationNodes.length - 1) - 0.5 : 0;
      const convergedWinner = node.id === state.hud.wedge?.variant_id;
      positions.set(node.id, {
        x: convergedWinner ? center : center + slot * span,
        y: convergedWinner ? 62 : y + deadOffset + jitter
      });
    });
  }

  return { positions, maxGeneration };
}

function lineagePath(source: Point, target: Point) {
  const lift = Math.max(46, Math.abs(source.y - target.y) * 0.45);
  return `M ${source.x} ${source.y} C ${source.x} ${source.y - lift}, ${target.x} ${target.y + lift}, ${target.x} ${target.y}`;
}

function Graph({ state, selected, onSelect }: { state: GraphState; selected?: string; onSelect: (id: string) => void }) {
  const width = 940;
  const height = 610;
  const nodes = Object.values(state.nodes);
  const variants = nodes.filter((node) => node.type === "variant").sort(sortVariants);
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const leaderIds = new Set<string>();
  for (const group of groupOrder) {
    const leader = nodes
      .filter((node) => node.type === "variant" && node.status !== "dead" && node.group === group && typeof node.fitness === "number")
      .sort((a, b) => (b.fitness ?? 0) - (a.fitness ?? 0))[0];
    if (leader) leaderIds.add(leader.id);
  }
  const winningPath = new Set<string>();
  let cursor = state.hud.wedge?.variant_id;
  while (cursor && nodeById.has(cursor)) {
    winningPath.add(cursor);
    cursor = nodeById.get(cursor)?.parents?.[0];
  }
  const { positions, maxGeneration } = buildPyramidPositions(nodes, state, width, height);
  const wedgeId = state.hud.wedge?.variant_id;
  const generationGroups = Array.from({ length: maxGeneration + 1 }, (_, generation) => ({
    generation,
    nodes: variants.filter((node) => (node.generation ?? 0) === generation)
  }));
  const collisionPairs = generationGroups.flatMap(({ generation, nodes: generationNodes }) =>
    generationNodes.slice(0, -1).map((node, index) => ({
      id: `${generation}-${node.id}-${generationNodes[index + 1].id}`,
      generation,
      a: node,
      b: generationNodes[index + 1],
      active:
        generation === state.generation &&
        (state.phase === "deliberating" || state.phase === "evolving" || state.phase === "converged")
    }))
  );
  const latestGeneration = Math.max(0, ...variants.map((node) => node.generation ?? 0));

  return (
    <section className="graph-surface pyramid-surface">
      <div className="graph-title">
        <b>Evolutionary wedge graph</b>
        <span>AG-UI patches move nodes as audience reactions mutate, collide, and converge.</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Crucible evolutionary pyramid graph">
        <defs>
          <filter id="halo" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <linearGradient id="winnerGradient" x1="0%" x2="100%" y1="0%" y2="0%">
            <stop offset="0%" stopColor="#d85634" />
            <stop offset="55%" stopColor="#d49313" />
            <stop offset="100%" stopColor="#0d7c67" />
          </linearGradient>
        </defs>
        <polygon className="pyramid-field" points={`${width / 2},56 78,508 ${width - 78},508`} />
        {[...Array(maxGeneration + 1)].map((_, generation) => {
          const y = generationY(generation, maxGeneration, height);
          return (
            <g key={generation}>
              <line className="pyramid-band" x1="84" x2={width - 84} y1={y} y2={y} />
              <text className="generation-tag" x="96" y={y - 9}>
                {generation === 0 ? "seed pairs" : generation === maxGeneration ? "converge" : `gen ${generation} mutations`}
              </text>
            </g>
          );
        })}
        <g className="audience-row">
          <text x="96" y={height - 18}>simulated audience decisions</text>
          <line x1="82" x2={width - 82} y1={height - 72} y2={height - 72} />
        </g>
        {collisionPairs.map((pair) => {
          const a = positions.get(pair.a.id);
          const b = positions.get(pair.b.id);
          if (!a || !b || Math.abs(a.y - b.y) > 45) return null;
          const mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
          const winner = (pair.a.fitness ?? 0) >= (pair.b.fitness ?? 0) ? pair.a : pair.b;
          return (
            <g className={`collision ${pair.active ? "active" : ""}`} key={pair.id}>
              <line x1={a.x} x2={b.x} y1={a.y} y2={b.y} />
              <circle cx={mid.x} cy={mid.y} r={pair.active ? 9 : 5} />
              <path d={`M ${mid.x - 8} ${mid.y - 8} L ${mid.x + 8} ${mid.y + 8} M ${mid.x + 8} ${mid.y - 8} L ${mid.x - 8} ${mid.y + 8}`} />
              {pair.active && <text x={mid.x + 12} y={mid.y - 10}>{truncateLabel(winner.group, 12)} wins</text>}
            </g>
          );
        })}
        {state.edges.map((edge, index) => {
          const source = positions.get(edge.source);
          const target = positions.get(edge.target);
          if (!source || !target) return null;
          const winningEdge = winningPath.has(edge.source) && winningPath.has(edge.target);
          const edgeClass =
            edge.kind === "objection"
              ? "edge objection audience-signal"
              : `edge lineage mutation-edge ${winningEdge ? "winner-edge" : ""}`;
          return (
            <path
              key={`${edge.source}-${edge.target}-${index}`}
              className={edgeClass}
              d={lineagePath(source, target)}
            />
          );
        })}
        {nodes
          .filter((node) => node.type === "persona")
          .map((node) => {
            const pos = positions.get(node.id)!;
            const color = node.color ?? state.islands[node.group]?.color ?? fallbackColors[node.group] ?? "#777";
            return (
              <g
                className={`node persona audience-persona ${selected === node.id ? "selected" : ""}`}
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => onSelect(node.id)}
              >
                <circle r={state.phase === "reacting" ? 7 : 5.5} fill={color} />
                {state.phase === "reacting" && <circle r="13" className="audience-pulse" />}
                <title>{node.preview}</title>
              </g>
            );
          })}
        {variants.map((node) => {
          const pos = positions.get(node.id)!;
          const color = node.color ?? state.islands[node.group]?.color ?? fallbackColors[node.group] ?? "#777";
          const dead = node.status === "dead";
          const isWinner = node.id === wedgeId;
          const radius = dead ? 7 : isWinner ? 22 : 14 + Math.min(8, (node.fitness ?? 0) * 10);
          const hasMutationPulse = !dead && (node.generation ?? 0) === latestGeneration && state.phase === "evolving";
          const showLabel = !dead && (selected === node.id || leaderIds.has(node.id) || winningPath.has(node.id) || isWinner);
          return (
            <g
              key={node.id}
              className={`node variant pyramid-node ${dead ? "dead" : ""} ${isWinner ? "winner-node" : ""} ${selected === node.id ? "selected" : ""}`}
              transform={`translate(${pos.x}, ${pos.y})`}
              onClick={() => onSelect(node.id)}
              filter={isWinner ? "url(#halo)" : undefined}
            >
              {hasMutationPulse && <circle r={radius + 15} className="mutation-pulse" />}
              <circle r={radius} fill={isWinner ? "url(#winnerGradient)" : color} />
              {!dead && <circle r={radius + 5} className="variant-ring" />}
              {dead && <text className="dead-x" x="-3" y="4">x</text>}
              <title>{node.preview}</title>
              {showLabel && (
                <>
                  <line className="label-leader" x1="17" y1="-3" x2="29" y2="-15" />
                  <text className="node-label" x="32" y="-17">{truncateLabel(node.label)}</text>
                </>
              )}
            </g>
          );
        })}
        {wedgeId && positions.get(wedgeId) && (
          <g className="convergence-crown">
            <text x={positions.get(wedgeId)!.x} y={positions.get(wedgeId)!.y - 34}>winner</text>
          </g>
        )}
      </svg>
      <p className="caption">
        Seed pairs start at the bottom. Audience reactions collide them, mutation edges lift survivors, and the best lineage converges at the top.
      </p>
    </section>
  );
}

function Leaderboard({ state }: { state: GraphState }) {
  const rows = Object.entries(state.islands)
    .sort((a, b) => b[1].intent_best - a[1].intent_best)
    .slice(0, 6);
  return (
    <section className="panel leaderboard">
      <div className="panel-title"><Activity size={16} /> Audience Verdicts</div>
      {rows.map(([id, island], index) => (
        <div className="leader-row" key={id}>
          <span className="rank">{index + 1}</span>
          <span className="dot" style={{ background: island.color ?? fallbackColors[id] }} />
          <span className="leader-name">{id}</span>
          <span className="bar"><i style={{ width: `${Math.max(4, island.intent_best * 100)}%` }} /></span>
          <span className="score">{island.intent_best.toFixed(2)}</span>
        </div>
      ))}
    </section>
  );
}

function StackRibbon({ active }: { active: string[] }) {
  const tools = [
    ["CopilotKit", "live steering UI"],
    ["Weave", "reaction ledger"],
    ["Redis", "cache/vector memory"],
    ["OpenAI", "orchestration"]
  ];
  return (
    <div className="ribbon">
      {tools.map(([name, detail]) => (
        <span className={active.includes(name) ? "tool active" : "tool"} key={name} title={detail}>
          {name}
        </span>
      ))}
    </div>
  );
}

function VerdictCards({ state }: { state: GraphState }) {
  if (!state.report) {
    return (
      <section className="panel empty-payoff">
        <div className="panel-title"><Sparkles size={16} /> Payoff</div>
        <p>The wedge, variant diff, and Monday validation test appear here at convergence.</p>
      </section>
    );
  }
  return (
    <section className="payoff">
      <article className="result-card">
        <div className="eyebrow">Wedge verdict</div>
        <h2>{state.report.title}</h2>
        <p>{state.report.summary}</p>
      </article>
      <article className="result-card compact">
        <div className="eyebrow">Winning variant diff</div>
        {state.report.diff.map((item) => (
          <div className="diff-row" key={item.field}>
            <b>{item.field}</b>
            <span>{item.before}</span>
            <strong>{item.after}</strong>
          </div>
        ))}
      </article>
      <article className="result-card compact">
        <div className="eyebrow">{state.report.test.name}</div>
        <p>{state.report.test.instruction}</p>
        <p className="test-bar">{state.report.test.bar}</p>
        <p className="muted">{state.report.test.cost}</p>
      </article>
      {state.report.generality && (
        <article className="result-card compact">
          <div className="eyebrow">Generality check</div>
          <h3>{state.report.generality.product}</h3>
          <p>{state.report.generality.one_liner}</p>
          <div className="mini-grid">
            <span>Winner</span>
            <b>{state.report.generality.winner.segment} {state.report.generality.winner.intent.toFixed(2)}</b>
            <span>Runner-up</span>
            <b>{state.report.generality.runner_up.segment} {state.report.generality.runner_up.intent.toFixed(2)}</b>
            <span>Gated</span>
            <b>{state.report.generality.gated_segment}</b>
          </div>
          <p className="muted">{state.report.generality.takeaway}</p>
        </article>
      )}
      {state.report.integrity && (
        <article className="result-card compact integrity-card">
          <div className="eyebrow">Integrity guardrail</div>
          <p>{state.report.integrity.framing}</p>
          <p>{state.report.integrity.fallback}</p>
          <p className="muted">{state.report.integrity.lead_claim}</p>
        </article>
      )}
    </section>
  );
}

function OrchestrationTrace({ state }: { state: GraphState }) {
  return (
    <section className="panel trace-panel">
      <div className="panel-title"><GitBranch size={16} /> Orchestration</div>
      {state.orchestration_events.length === 0 ? (
        <p className="muted">Conductor and Facilitator decisions appear during a run.</p>
      ) : (
        <div className="trace-list">
          {state.orchestration_events.map((event, index) => (
            <div className="trace-step" key={`${event.actor}-${index}`}>
              <b>{event.actor}</b>
              <span>{event.action}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function NodeInspector({ node }: { node?: GraphNode }) {
  if (!node) {
    return <p className="muted">Click an audience dot or variant node to inspect genes, reactions, and the Weave trace.</p>;
  }
  return (
    <div className="inspector">
      <div className="panel-title"><Radio size={16} /> {node.label}</div>
      <p>{node.preview}</p>
      {node.type === "variant" && (
        <>
          <div className="mini-grid">
            <span>Fitness</span><b>{(node.fitness ?? 0).toFixed(2)}</b>
            <span>Group</span><b>{node.group}</b>
            <span>Status</span><b>{node.status}</b>
          </div>
          <a className="trace" href={node.weave_url ?? `${API_BASE}/node/${node.id}`} target="_blank">
            Open Weave trace
          </a>
        </>
      )}
      {node.type === "persona" && <p className="muted">{node.role} - {node.jtbd}</p>}
    </div>
  );
}

export default function Home() {
  const [state, setState] = useState<GraphState>(emptyState);
  const [selectedId, setSelectedId] = useState<string>();
  const [steer, setSteer] = useState("Add more price-sensitive HVAC owners");
  const [mode, setMode] = useState<"demo" | "live">("demo");
  const [projectUrl, setProjectUrl] = useState("https://www.upfirst.ai/");
  const [history, setHistory] = useState<Record<number, GraphState>>({});
  const [scrubGen, setScrubGen] = useState<number | null>(null);

  useEffect(() => {
    const events = subscribeGraphState((next) => {
      setState(next);
      setHistory((prev) => ({ ...prev, [next.generation]: next }));
      setScrubGen(null);
    });
    return () => events.close();
  }, []);

  const displayState = scrubGen !== null && history[scrubGen] ? history[scrubGen] : state;
  const selected = useMemo(
    () => (selectedId ? displayState.nodes[selectedId] : undefined),
    [selectedId, displayState.nodes]
  );
  const maxRecordedGen = Math.max(0, ...Object.keys(history).map(Number), state.generation);
  const generationMarks = Array.from({ length: Math.max(3, maxRecordedGen) + 1 }, (_, index) => index);

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <Waypoints size={24} />
          <div>
            <h1>Crucible</h1>
            <span>live evolutionary wedge discovery</span>
          </div>
        </div>
        <div className="controls">
          <div className="mode-toggle" aria-label="Run mode">
            <button className={mode === "demo" ? "active" : ""} onClick={() => setMode("demo")}>Demo</button>
            <button className={mode === "live" ? "active" : ""} onClick={() => setMode("live")}>Live</button>
          </div>
          <button onClick={() => (mode === "demo" ? postRun() : postProjectUrl(projectUrl))}>
            <Play size={16} /> {mode === "demo" ? "Run" : "Analyze URL"}
          </button>
          <button onClick={() => postReplay()}><RotateCcw size={16} /> Replay</button>
          <button onClick={() => postLiveAnchor()}><Radio size={16} /> Live Anchor</button>
          <div className="gen-control">
            <label>gen <b>{displayState.generation}</b></label>
            <input
              className="gen-scrubber"
              type="range"
              min="0"
              max={Math.max(3, maxRecordedGen)}
              value={displayState.generation}
              onChange={(event) => setScrubGen(Number(event.target.value))}
              title="Scrub recorded generations"
            />
            <div className="gen-steps" aria-label="Recorded generations">
              {generationMarks.map((generation) => (
                <button
                  className={displayState.generation === generation ? "active" : ""}
                  disabled={!history[generation] && generation !== state.generation}
                  key={generation}
                  onClick={() => setScrubGen(generation)}
                  title={`Generation ${generation}`}
                >
                  {generation}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <section className="hud">
        <span>{displayState.phase}</span>
        <span>{displayState.hud.calls_made} calls</span>
        <span>{displayState.hud.cache_hits} cache hits</span>
        <span>{Math.round(displayState.hud.skeptic_ratio * 100)}% skeptics</span>
        <span>{displayState.hud.wedge ? `wedge: ${displayState.hud.wedge.group}` : "wedge: pending"}</span>
        <span>AG-UI live state</span>
      </section>

      <div className="layout">
        <div className="left">
          <section className="panel founder-chat">
            <div className="panel-title"><Bot size={16} /> Founder Chat</div>
            <div className="chat-copy">
              {mode === "demo"
                ? "Demo mode uses the rehearsed Upfirst seed and recorded fallback."
                : "Live mode sources the project URL, builds a synthetic audience, and streams the evaluation into the graph."}
            </div>
            <form
              className="url-row"
              onSubmit={(event) => {
                event.preventDefault();
                if (mode === "demo") postRun();
                else postProjectUrl(projectUrl);
              }}
            >
              <input
                aria-label="Project URL"
                disabled={mode === "demo"}
                onChange={(event) => setProjectUrl(event.target.value)}
                placeholder="https://project-site.com"
                value={projectUrl}
              />
              <button type="submit">{mode === "demo" ? "Run Demo" : "Start Live"}</button>
            </form>
          </section>
          <Graph state={displayState} selected={selectedId} onSelect={setSelectedId} />
          <StackRibbon active={displayState.active_tools} />
        </div>
        <aside className={`right ${displayState.report ? "converged-side" : ""}`}>
          {displayState.report && <VerdictCards state={displayState} />}
          <section className="panel narration">
            <div className="panel-title"><Bot size={16} /> Narration</div>
            <p>{displayState.narration}</p>
          </section>
          <OrchestrationTrace state={displayState} />
          <Leaderboard state={displayState} />
          <section className="panel steering">
            <div className="panel-title"><GitBranch size={16} /> Steering</div>
            <div className="steer-row">
              <input value={steer} onChange={(event) => setSteer(event.target.value)} />
              <button onClick={() => postSteer(steer)}><Send size={15} /></button>
            </div>
          </section>
          <section className="panel">
            <NodeInspector node={selected} />
          </section>
          {!displayState.report && <VerdictCards state={displayState} />}
        </aside>
      </div>
    </main>
  );
}
