(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const state = { registering: false, transactions: [] };

  function showToast(message, type = "error") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    $("toast-region").append(toast);
    window.setTimeout(() => toast.remove(), 4200);
  }

  async function request(path, options = {}) {
    const response = await fetch(`/api${path}`, {
      credentials: "same-origin",
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) }
    });
    let payload = {};
    try { payload = await response.json(); } catch (_) { /* non-JSON errors use status text */ }
    if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
    return payload;
  }

  function setLoading(button, loading, label) {
    button.disabled = loading;
    button.dataset.originalLabel ||= button.textContent;
    button.textContent = loading ? "Working…" : (label || button.dataset.originalLabel);
  }

  function shortHash(hash) {
    return hash.length > 16 ? `${hash.slice(0, 8)}…${hash.slice(-7)}` : hash;
  }

  function renderHistory() {
    const body = $("history-body");
    body.replaceChildren();
    $("transaction-count").textContent = state.transactions.length;
    $("table-count").textContent = `${state.transactions.length} record${state.transactions.length === 1 ? "" : "s"}`;
    $("empty-history").hidden = state.transactions.length > 0;
    state.transactions.forEach((transaction) => {
      const row = document.createElement("tr");
      const idCell = document.createElement("td");
      const id = document.createElement("span");
      id.className = "tx-id";
      id.title = transaction.tx_id;
      id.textContent = shortHash(transaction.tx_id);
      const copy = document.createElement("button");
      copy.className = "copy-button";
      copy.type = "button";
      copy.dataset.copy = transaction.tx_id;
      copy.setAttribute("aria-label", `Copy transaction ID ${transaction.tx_id}`);
      copy.textContent = "⧉";
      id.append(copy);
      idCell.append(id);
      const receiver = document.createElement("td");
      receiver.textContent = transaction.receiver;
      const amount = document.createElement("td");
      amount.textContent = `$${Number(transaction.amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 8 })}`;
      const timestamp = document.createElement("td");
      timestamp.textContent = new Date(transaction.timestamp).toLocaleString();
      const action = document.createElement("td");
      const proof = document.createElement("button");
      proof.className = "proof-button";
      proof.type = "button";
      proof.dataset.proof = transaction.tx_id;
      proof.textContent = "View proof";
      action.append(proof);
      row.append(idCell, receiver, amount, timestamp, action);
      body.append(row);
    });
  }

  function hierarchyFromLayers(layers) {
    if (!layers?.length || !layers[layers.length - 1]?.length) return null;
    const rootIndex = layers.length - 1;
    function node(level, index) {
      const value = layers[level][index];
      const children = level === 0 ? [] : [node(level - 1, index * 2)];
      if (level > 0 && index * 2 + 1 < layers[level - 1].length) children.push(node(level - 1, index * 2 + 1));
      return { hash: value, children };
    }
    return node(rootIndex, 0);
  }

  function renderTree(tree) {
    const svg = d3.select("#tree");
    svg.selectAll("*").remove();
    const data = hierarchyFromLayers(tree.layers);
    $("tree-empty").hidden = Boolean(data);
    if (!data) { $("root-value").textContent = "No transactions"; return; }
    $("root-value").textContent = shortHash(tree.root);
    const root = d3.hierarchy(data);
    const leaves = Math.max(root.leaves().length, 1);
    const width = Math.max($("tree-container").clientWidth, leaves * 120);
    const height = Math.max(root.height * 78 + 70, 250);
    svg.attr("viewBox", `0 0 ${width} ${height}`).attr("width", width).attr("height", height);
    d3.tree().size([width - 70, height - 55])(root);
    const graph = svg.append("g").attr("transform", "translate(35,25)");
    graph.append("g").selectAll("path").data(root.links()).join("path").attr("class", "tree-link").attr("d", d3.linkVertical().x(d => d.x).y(d => d.y));
    const nodes = graph.append("g").selectAll("g").data(root.descendants()).join("g").attr("class", d => `tree-node ${d.children ? "root" : "leaf"}`).attr("transform", d => `translate(${d.x},${d.y})`);
    nodes.append("circle").attr("r", 24);
    nodes.append("text").attr("text-anchor", "middle").attr("dy", 4).text(d => shortHash(d.data.hash));
    nodes.append("title").text(d => d.data.hash);
  }

  async function refreshLedger() {
    const [transactions, tree] = await Promise.all([request("/transactions"), request("/tree")]);
    state.transactions = transactions.transactions || [];
    renderHistory();
    renderTree(tree);
  }

  $("auth-switch").addEventListener("click", () => {
    state.registering = !state.registering;
    $("auth-heading").textContent = state.registering ? "Create your ledger" : "Sign in to your ledger";
    $("auth-subheading").textContent = state.registering ? "Start securing your transactions today." : "Access your secure transaction workspace.";
    $("auth-submit").textContent = state.registering ? "Create account" : "Sign in";
    $("auth-switch").textContent = state.registering ? "Already registered? Sign in" : "Need an account? Create one";
    $("password").autocomplete = state.registering ? "new-password" : "current-password";
  });

  $("auth-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = $("auth-submit");
    if (!$("email").validity.valid || !$("password").validity.valid) { showToast("Enter a valid email and a password of at least 12 characters."); return; }
    setLoading(button, true);
    try {
      await request(state.registering ? "/auth/register" : "/auth/login", { method: "POST", body: JSON.stringify({ email: $("email").value.trim(), password: $("password").value }) });
      if (state.registering) { showToast("Account created. You can now sign in.", "success"); $("auth-switch").click(); }
      else { $("auth-view").hidden = true; $("dashboard-view").hidden = false; await refreshLedger(); }
    } catch (error) { showToast(error.message); } finally { setLoading(button, false); }
  });

  $("logout").addEventListener("click", async () => {
    try { await request("/auth/logout", { method: "POST" }); window.location.reload(); }
    catch (error) { showToast(error.message); }
  });

  $("transaction-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const receiver = $("receiver").value.trim();
    const amount = Number($("amount").value);
    if (!receiver || !Number.isFinite(amount) || amount <= 0) { showToast("Enter a receiver and a positive amount."); return; }
    const button = $("submit-transaction");
    setLoading(button, true);
    try { await request("/transactions", { method: "POST", body: JSON.stringify({ receiver, amount }) }); event.target.reset(); showToast("Transaction submitted securely.", "success"); await refreshLedger(); }
    catch (error) { showToast(error.message); } finally { setLoading(button, false); }
  });

  $("history-body").addEventListener("click", async (event) => {
    const copyButton = event.target.closest("[data-copy]");
    if (copyButton) { try { await navigator.clipboard.writeText(copyButton.dataset.copy); showToast("Transaction ID copied.", "success"); } catch (_) { showToast("Unable to access the clipboard."); } return; }
    const proofButton = event.target.closest("[data-proof]");
    if (proofButton) { try { const proof = await request(`/proof/${encodeURIComponent(proofButton.dataset.proof)}`); showToast(`Proof verified against ${shortHash(proof.merkle_root)}.`, "success"); } catch (error) { showToast(error.message); } }
  });
})();
