const BRIDGE_BASE_URL = "http://127.0.0.1:8765";
const BRIDGE_SESSION_ID = "browser-dom";
const COMMAND_POLL_INTERVAL_MS = 500;
const ports = new Map();

function portKey(port) {
  return String(port.sender?.tab?.id ?? port.name);
}

function setPortState(port, state) {
  ports.set(portKey(port), state);
}

function clearPortState(port) {
  const key = portKey(port);
  const state = ports.get(key);
  if (!state || state.port !== port) {
    return;
  }
  if (state?.pollTimer !== null) {
    clearInterval(state.pollTimer);
  }
  ports.delete(key);
}

function startPollingCommands(sessionId) {
  const state = ports.get(sessionId);
  if (!state || state.pollTimer !== null) {
    return;
  }

  const poll = async () => {
    const currentState = ports.get(sessionId);
    if (!currentState) {
      return;
    }
    if (currentState.awaitingSnapshot) {
      requestSnapshotFromPort(currentState.port);
    }
    try {
      const response = await fetch(
        `${BRIDGE_BASE_URL}/session/${encodeURIComponent(BRIDGE_SESSION_ID)}/commands`
      );
      if (!response.ok) {
        console.warn(
          `browser-dom bridge command poll failed for ${sessionId}: ${response.status} ${response.statusText}`
        );
        return;
      }

      const body = await response.json();
      const commands = Array.isArray(body?.commands) ? body.commands : [];
      if (commands.length > 0) {
        const latestState = ports.get(sessionId);
        if (!latestState || latestState.port !== state.port) {
          return;
        }
        latestState.awaitingSnapshot = true;
        latestState.port.postMessage({
          type: "bridge_commands",
          session_id: BRIDGE_SESSION_ID,
          commands,
        });
      }
    } catch (error) {
      console.warn(`browser-dom bridge command poll error for ${sessionId}:`, error);
    }
  };

  void poll();
  state.pollTimer = setInterval(() => {
    void poll();
  }, COMMAND_POLL_INTERVAL_MS);
}

function requestSnapshotFromPort(port) {
  port.postMessage({ type: "request_snapshot" });
}

async function postSnapshotToBridge(snapshot, sessionId) {
  try {
    const response = await fetch(
      `${BRIDGE_BASE_URL}/session/${encodeURIComponent(sessionId)}/snapshot`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(snapshot),
      }
    );
    if (!response.ok) {
      console.warn(
        `browser-dom bridge snapshot POST failed for ${sessionId}: ${response.status} ${response.statusText}`
      );
      return false;
    }
    return true;
  } catch (error) {
    console.warn(`browser-dom bridge snapshot POST error for ${sessionId}:`, error);
    return false;
  }
}

chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== "minesweeperonline-bridge") {
    return;
  }

  const key = portKey(port);
  const previousState = ports.get(key);
  if (previousState && previousState.pollTimer !== null) {
    clearInterval(previousState.pollTimer);
  }
  setPortState(port, {
    port,
    pollTimer: null,
    awaitingSnapshot: true,
  });
  startPollingCommands(key);

  port.onMessage.addListener((message) => {
    if (!message || typeof message !== "object") {
      return;
    }

    if (message.type === "content_ready") {
      const currentState = ports.get(key);
      if (currentState && currentState.port === port) {
        currentState.awaitingSnapshot = true;
      }
      requestSnapshotFromPort(port);
      return;
    }

    if (message.type === "snapshot") {
      void postSnapshotToBridge(message.snapshot, BRIDGE_SESSION_ID).then((ok) => {
        const currentState = ports.get(key);
        if (!currentState || currentState.port !== port) {
          return;
        }
        currentState.awaitingSnapshot = !ok;
      });
      return;
    }

    if (message.type === "log") {
      return;
    }
  });

  port.onDisconnect.addListener(() => {
    clearPortState(port);
  });
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || typeof message !== "object") {
    sendResponse({ ok: false, error: "message must be an object" });
    return false;
  }

  if (message.type === "request_snapshot") {
    for (const port of ports.values()) {
      port.port.postMessage({ type: "request_snapshot" });
    }
    sendResponse({ ok: true });
    return false;
  }

  if (message.type === "broadcast") {
    for (const port of ports.values()) {
      port.port.postMessage(message.payload);
    }
    sendResponse({ ok: true });
    return false;
  }

  sendResponse({ ok: false, error: `unsupported message type: ${message.type}` });
  return false;
});
