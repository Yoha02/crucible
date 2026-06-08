import { applyPatch } from "fast-json-patch";
import { emptyState, GraphState } from "./types";

const configuredApiBase = process.env.NEXT_PUBLIC_API_BASE;
export const API_BASE =
  configuredApiBase && configuredApiBase.trim().length > 0
    ? configuredApiBase
    : "http://127.0.0.1:8000";

export function subscribeGraphState(onState: (state: GraphState) => void): EventSource {
  let current: GraphState = emptyState;
  const events = new EventSource(`${API_BASE}/agui`);
  events.addEventListener("STATE_SNAPSHOT", (event) => {
    current = JSON.parse((event as MessageEvent).data).snapshot;
    onState({ ...current });
  });
  events.addEventListener("STATE_DELTA", (event) => {
    const payload = JSON.parse((event as MessageEvent).data);
    current = applyPatch({ ...current }, payload.delta, true, false).newDocument as GraphState;
    onState({ ...current });
  });
  return events;
}

export async function postRun() {
  await fetch(`${API_BASE}/run`, { method: "POST" });
}

export async function postProjectUrl(url: string) {
  await fetch(`${API_BASE}/project-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
}

export async function postReplay() {
  await fetch(`${API_BASE}/replay`, { method: "POST" });
}

export async function postSteer(description: string) {
  await fetch(`${API_BASE}/steer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description })
  });
}

export async function postLiveAnchor() {
  await fetch(`${API_BASE}/live-anchor`, { method: "POST" });
}
