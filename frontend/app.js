// Keep the API and page on the same local hostname so session cookies match.
const API_BASE = `${window.location.protocol}//${window.location.hostname}:5000/api`;

const $ = (id) => document.getElementById(id);
const status = (message) => $('status').textContent = message;
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
})[character]);

// Centralized API request handler with CORS credentials included
const request = (url, options = {}) => 
    fetch(`${API_BASE}${url}`, {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // Crucial for persistent login sessions
        ...options
    }).then(async (r) => {
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(data.error || `Request failed (${r.status})`);
        return data; 
    }).catch((error) => {
        if (error instanceof TypeError) throw new Error('Unable to connect to the API. Is the backend running on port 5000?');
        throw error;
    });

// D3.js Hierarchical Tree Builder
function renderTree(layers) {
    const svg = d3.select('#tree');
    svg.selectAll('*').remove(); // Clear previous tree
    
    if (!layers || layers.length === 0) return;

    // Ensure the array is top-down (root must be at index 0 for hierarchy builder)
    let topDownLayers = layers;
    if (layers[0].length > 1 && layers[layers.length - 1].length === 1) {
        topDownLayers = layers.slice().reverse();
    }

    // Recursively convert flat layer arrays into D3-compatible hierarchy objects
    function buildHierarchy(level, index) {
        if (level >= topDownLayers.length) return null;
        const name = topDownLayers[level][index];
        if (!name) return null;
        
        const node = { name };
        if (level < topDownLayers.length - 1) {
            const left = buildHierarchy(level + 1, index * 2);
            const right = buildHierarchy(level + 1, index * 2 + 1);
            node.children = [];
            if (left) node.children.push(left);
            if (right) node.children.push(right);
        }
        return node;
    }

    const rootData = buildHierarchy(0, 0);
    if (!rootData) return;

    // Set responsive SVG boundaries
    const width = $('tree').clientWidth || 800;
    const height = Math.max(300, topDownLayers.length * 80);
    const margin = { top: 40, right: 20, bottom: 40, left: 20 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    // Generate D3 layout
    const treeLayout = d3.tree().size([innerWidth, innerHeight]);
    const root = d3.hierarchy(rootData);
    treeLayout(root);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // 1. Draw connecting lines (paths) first so they render under the nodes
    g.selectAll(".link")
        .data(root.links())
        .enter().append("path")
        .attr("class", "link")
        .attr("fill", "none")
        .attr("stroke", "#cbd5e1") // Tailwind slate-300
        .attr("stroke-width", 2)
        .attr("d", d3.linkVertical()
            .x(d => d.x)
            .y(d => d.y)
        );

    // 2. Draw nodes
    const nodeGroup = g.selectAll(".node")
        .data(root.descendants())
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${d.x},${d.y})`);

    nodeGroup.append("circle")
        .attr("r", 20)
        .attr("fill", "#6366f1") // Tailwind indigo-500
        .attr("stroke", "#4f46e5")
        .attr("stroke-width", 2);

    // 3. Add tooltips for the full hash on hover
    nodeGroup.append("title")
        .text(d => d.data.name);

    // 4. Add truncated hash text inside circles
    nodeGroup.append("text")
        .attr("dy", 4)
        .attr("text-anchor", "middle")
        .attr("fill", "white")
        .style("font-size", "11px")
        .style("font-family", "monospace")
        .text(d => d.data.name.slice(0, 6));
}

// Fetch & populate ledger dashboard
async function loadHistory() { 
    const data = await request('/transactions'); 
    
    // Inject Tailwind-styled list items into the UI
    $('history').innerHTML = data.transactions.map(t => `
        <li class="flex justify-between items-center p-3 bg-slate-50 border border-slate-100 rounded-lg">
            <span class="font-mono text-sm text-slate-600 truncate mr-2" title="${t.tx_id}">
                ${escapeHTML(t.tx_id.slice(0,10))}... : <span class="text-emerald-600 font-semibold">${escapeHTML(t.amount)}</span> to ${escapeHTML(t.receiver)}
            </span>
            <button data-tx="${t.tx_id}" class="bg-indigo-100 hover:bg-indigo-200 text-indigo-700 px-3 py-1 rounded text-xs font-semibold transition">Proof</button>
        </li>
    `).join(''); 
    
    // Fetch and build the visual tree
    const treeData = await request('/tree'); 
    renderTree(treeData.layers);
}

// Event Listeners
$('login').onclick = async () => { 
    try { 
        await request('/auth/login', {
            method: 'POST', 
            body: JSON.stringify({email: $('email').value, password: $('password').value})
        }); 
        $('auth').hidden = true; 
        $('ledger').hidden = false; 
        status('');
        await loadHistory(); 
    } catch (e) { 
        status(e.message); 
    } 
};

$('register').onclick = async () => { 
    try { 
        await request('/auth/register', {
            method: 'POST', 
            body: JSON.stringify({email: $('email').value, password: $('password').value})
        }); 
        status('Registered successfully; please log in.'); 
        $('email').value = '';
        $('password').value = '';
    } catch (e) { 
        status(e.message); 
    } 
};

$('logout').onclick = async () => {
    try {
        await request('/auth/logout', { method: 'POST' });
        location.reload();
    } catch (error) {
        status(error.message);
    }
};

$('transaction').onsubmit = async (e) => { 
    e.preventDefault(); 
    try { 
        await request('/transactions', {
            method: 'POST', 
            body: JSON.stringify({receiver: $('receiver').value, amount: $('amount').value})
        }); 
        e.target.reset(); 
        status('');
        await loadHistory(); 
    } catch (err) { 
        status(err.message); 
    } 
};

// Reveal Proof Data smoothly when clicked
$('history').onclick = async (e) => { 
    if (e.target.dataset.tx) {
        const proofEl = $('proof');
        proofEl.classList.remove('hidden');
        proofEl.textContent = 'Verifying cryptographic proof...';
        try {
            const proofData = await request(`/proof/${e.target.dataset.tx}`);
            proofEl.textContent = JSON.stringify(proofData, null, 2);
        } catch (err) {
            proofEl.textContent = `Verification Error: ${err.message}`;
        }
    }
};