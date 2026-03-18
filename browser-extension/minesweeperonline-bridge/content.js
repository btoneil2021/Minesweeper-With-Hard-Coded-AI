const TILE_ID_RE = /^\d+_\d+$/;

const port = chrome.runtime.connect({ name: "minesweeperonline-bridge" });

port.postMessage({ type: "content_ready" });

port.onMessage.addListener((message) => {
  if (!message || typeof message !== "object") {
    return;
  }

  if (message.type === "request_snapshot") {
    void postSnapshot();
    return;
  }

  if (message.type === "bridge_commands" && Array.isArray(message.commands)) {
    executeCommands(message.commands);
  }
});

async function postSnapshot() {
  port.postMessage({ type: "snapshot", snapshot: scanBoard() });
}

function executeCommands(commands) {
  for (const command of commands) {
    if (!command || typeof command !== "object") {
      continue;
    }

    if (command.type === "execute_moves" && Array.isArray(command.moves)) {
      for (const move of command.moves) {
        executeMove(move);
      }
      continue;
    }

    if (command.type === "restart") {
      clickRestart(command.target);
    }
  }

  queueMicrotask(() => {
    void postSnapshot();
  });
}

function scanBoard() {
  const tiles = [];
  const elements = document.querySelectorAll("[id]");

  for (const element of elements) {
    if (!TILE_ID_RE.test(element.id)) {
      continue;
    }

    const tile = parseTileElement(element);
    if (tile) {
      tiles.push(tile);
    }
  }

  return {
    type: "board_snapshot",
    width: inferDimension(tiles, "x"),
    height: inferDimension(tiles, "y"),
    face_state: parseFaceState(),
    tiles
  };
}

function parseTileElement(element) {
  const [rowText, colText] = element.id.split("_");
  const row = Number.parseInt(rowText, 10);
  const col = Number.parseInt(colText, 10);
  const classTokens = new Set(element.className.split(/\s+/).filter(Boolean));

  if (!classTokens.has("square")) {
    return null;
  }

  const payload = { x: col, y: row };
  if (classTokens.has("bombflagged")) {
    payload.state = "flagged";
    return payload;
  }
  if (classTokens.has("bombdeath")) {
    payload.state = "exploded";
    return payload;
  }
  if (classTokens.has("bombrevealed")) {
    payload.state = "mine_revealed";
    return payload;
  }

  for (const token of classTokens) {
    if (!token.startsWith("open")) {
      continue;
    }
    const count = Number.parseInt(token.slice("open".length), 10);
    payload.state = "revealed";
    payload.adjacent_mines = Number.isFinite(count) ? count : 0;
    return payload;
  }

  payload.state = "hidden";
  return payload;
}

function parseFaceState() {
  const face = document.getElementById("face");
  if (!face) {
    return "in_progress";
  }

  const classTokens = new Set(face.className.split(/\s+/).filter(Boolean));
  if (classTokens.has("facewin") || classTokens.has("facewon")) {
    return "won";
  }
  if (classTokens.has("facedead") || classTokens.has("facelost")) {
    return "lost";
  }
  return "in_progress";
}

function executeMove(move) {
  if (!move || typeof move !== "object") {
    return;
  }

  const tile = getTileElement(move.x, move.y);
  if (!tile) {
    return;
  }

  if (move.action === "reveal") {
    triggerLeftClick(tile);
    return;
  }

  if (move.action === "flag") {
    triggerRightClick(tile);
  }
}

function clickRestart(target) {
  const selector = typeof target === "string" && target ? target : "#face";
  const face = document.querySelector(selector) || document.getElementById("face");
  if (!face) {
    return;
  }

  triggerLeftClick(face);
}

function getTileElement(x, y) {
  return document.getElementById(`${y}_${x}`);
}

function triggerLeftClick(element) {
  dispatchMouseEvent(element, "mousedown", { button: 0, buttons: 1 });
  dispatchMouseEvent(element, "mouseup", { button: 0, buttons: 0 });
  dispatchMouseEvent(element, "click", { button: 0, buttons: 0 });
}

function triggerRightClick(element) {
  dispatchMouseEvent(element, "mousedown", { button: 2, buttons: 2 });
  dispatchMouseEvent(element, "mouseup", { button: 2, buttons: 0 });
  dispatchMouseEvent(element, "contextmenu", { button: 2, buttons: 2 });
}

function dispatchMouseEvent(element, type, { button, buttons }) {
  const rect = element.getBoundingClientRect();
  const clientX = Math.round(rect.left + rect.width / 2);
  const clientY = Math.round(rect.top + rect.height / 2);
  const event = new MouseEvent(type, {
    bubbles: true,
    cancelable: true,
    composed: true,
    button,
    buttons,
    clientX,
    clientY,
    screenX: clientX,
    screenY: clientY,
  });
  element.dispatchEvent(event);
}

function inferDimension(tiles, axis) {
  let max = -1;
  for (const tile of tiles) {
    max = Math.max(max, tile[axis]);
  }
  return max + 1;
}
