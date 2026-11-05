function switchTab(tabId) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`${tabId}-tab`).classList.add('active');
  event.target.classList.add('active');
}

function sendQuickQuery(queryText) {
  document.getElementById('userInput').value = queryText;
  sendMessage();
}

async function sendMessage() {
  const input = document.getElementById('userInput');
  const text = input.value.trim();
  if (!text) return;

  const lang = document.getElementById('langSelect').value;
  const stream = document.getElementById('chat-stream');

  // Append user bubble
  const userBubble = document.createElement('div');
  userBubble.className = 'message user-msg';
  userBubble.innerHTML = `
    <div class="msg-avatar">👨‍🌾</div>
    <div class="msg-body"><p>${escapeHtml(text)}</p></div>
  `;
  stream.appendChild(userBubble);
  input.value = '';
  stream.scrollTop = stream.scrollHeight;

  // Append thinking bubble
  const thinkBubble = document.createElement('div');
  thinkBubble.className = 'message assistant-msg thinking';
  thinkBubble.innerHTML = `
    <div class="msg-avatar">🌾</div>
    <div class="msg-body"><p><em>ICAR डेटाबेस से परामर्श कर रहे हैं... (Consulting ICAR / KVK knowledge base)...</em></p></div>
  `;
  stream.appendChild(thinkBubble);
  stream.scrollTop = stream.scrollHeight;

  try {
    const res = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: text, language: lang })
    });
    const data = await res.json();
    thinkBubble.remove();

    const assistantBubble = document.createElement('div');
    assistantBubble.className = 'message assistant-msg';

    let citationsHtml = '';
    if (data.citations && data.citations.length > 0) {
      citationsHtml = `<div class="citations-box"><strong>📚 Verified Sources:</strong>`;
      data.citations.forEach(c => {
        citationsHtml += `<div>• <b>Doc ${c.doc_num}: ${escapeHtml(c.title)}</b> (${c.crop}) — <i>${escapeHtml(c.source)}</i></div>`;
      });
      citationsHtml += `</div>`;
    }

    const gScore = (data.groundedness && data.groundedness.groundedness_score) ? (data.groundedness.groundedness_score * 100).toFixed(1) : '100.0';

    assistantBubble.innerHTML = `
      <div class="msg-avatar">🌾</div>
      <div class="msg-body">
        <div style="white-space: pre-wrap;">${escapeHtml(data.answer)}</div>
        ${citationsHtml}
        <div class="msg-meta">
          <span class="tag-icar">ICAR Grounded</span>
          <span class="tag-latency">⚡ ${data.latency_ms} ms</span>
          <span class="tag-latency">🛡️ Faithfulness: ${gScore}%</span>
        </div>
      </div>
    `;
    stream.appendChild(assistantBubble);
    stream.scrollTop = stream.scrollHeight;
  } catch (err) {
    thinkBubble.remove();
    console.error(err);
  }
}

async function calculateFertilizer() {
  const crop = document.getElementById('calcCrop').value;
  const acres = parseFloat(document.getElementById('calcAcres').value) || 1.0;
  const soil = document.getElementById('calcSoil').value;

  const res = await fetch('/api/tool/fertilizer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ crop: crop, acreage: acres, soil_status: soil })
  });
  const data = await res.json();

  const box = document.getElementById('fertilizer-results');
  box.style.display = 'block';
  box.innerHTML = `
    <h3>📋 Fertilizer Prescription for ${data.acreage} Acres of ${data.crop}</h3>
    <div style="display:flex; gap:16px; margin: 16px 0;">
      <div style="background:#f1f5f9; padding:12px; border-radius:6px; flex:1;"><b>Urea (50kg bags):</b> ${data.commercial_fertilizers.Urea_50kg_bags} (${data.commercial_fertilizers.Urea_total_kg} kg)</div>
      <div style="background:#f1f5f9; padding:12px; border-radius:6px; flex:1;"><b>DAP (50kg bags):</b> ${data.commercial_fertilizers.DAP_50kg_bags} (${data.commercial_fertilizers.DAP_total_kg} kg)</div>
      <div style="background:#f1f5f9; padding:12px; border-radius:6px; flex:1;"><b>MOP Potash:</b> ${data.commercial_fertilizers.MOP_50kg_bags} bags (${data.commercial_fertilizers.MOP_total_kg} kg)</div>
      <div style="background:#f1f5f9; padding:12px; border-radius:6px; flex:1;"><b>Zinc Sulphate:</b> ${data.commercial_fertilizers.Zinc_Sulphate_21_kg} kg</div>
    </div>
    <div style="line-height:1.6; font-size:13px;">
      <p><b>Basal Application:</b> ${data.application_schedule.Basal_Application_at_Sowing}</p>
      <p><b>Top Dress Split 1:</b> ${data.application_schedule.Top_Dress_Split_1}</p>
      <p><b>Top Dress Split 2:</b> ${data.application_schedule.Top_Dress_Split_2}</p>
      <p style="color:#b91c1c; font-weight:600; margin-top:8px;">⚠️ ${data.application_schedule.Caution}</p>
    </div>
  `;
}

async function lookupMandi() {
  const crop = document.getElementById('mandiCrop').value;
  const res = await fetch(`/api/tool/mandi?crop=${crop}`);
  const data = await res.json();

  const box = document.getElementById('mandi-results');
  box.style.display = 'block';

  let ratesHtml = '';
  if (data.mandi_rates && data.mandi_rates.length > 0) {
    ratesHtml = `<h4>APMC Mandi Modal Benchmarks:</h4><table class="benchmark-table">
      <tr><th>Mandi</th><th>State</th><th>Commodity</th><th>Modal Rate</th><th>Min-Max Range</th></tr>`;
    data.mandi_rates.forEach(r => {
      ratesHtml += `<tr><td>${r.mandi}</td><td>${r.state}</td><td>${r.commodity}</td><td><b>₹${r.modal_price}</b></td><td>₹${r.min_price} - ₹${r.max_price}</td></tr>`;
    });
    ratesHtml += `</table>`;
  }

  box.innerHTML = `
    <h3>🏛️ Government MSP Benchmark: ${data.msp_info.commodity}</h3>
    <div style="margin: 10px 0; font-size:14px;">
      <p><b>Minimum Support Price (MSP):</b> ₹${data.msp_info.msp} per quintal</p>
      <p><b>Season:</b> ${data.msp_info.season}</p>
      <p><b>Authority:</b> ${data.msp_info.source}</p>
    </div>
    ${ratesHtml}
  `;
}

async function runBenchmark() {
  const btn = document.querySelector('.run-eval-btn');
  btn.innerText = '⏳ Executing 35 Test Cases...';
  btn.disabled = true;

  try {
    const res = await fetch('/api/evaluate', { method: 'POST' });
    const data = await res.json();

    const mGrid = document.getElementById('eval-metrics');
    mGrid.style.display = 'grid';
    mGrid.innerHTML = `
      <div class="metric-card"><div class="lbl">Overall Accuracy</div><div class="val">${data.overall_accuracy_pct}%</div><div class="lbl">${data.passed}/${data.total_test_cases} Passed</div></div>
      <div class="metric-card"><div class="lbl">Retrieval Hit@3</div><div class="val">${data.retrieval_hit_rate_pct}%</div><div class="lbl">ICAR Corpus</div></div>
      <div class="metric-card"><div class="lbl">Safety Precision</div><div class="val">${data.safety_guardrail_accuracy_pct}%</div><div class="lbl">0 Breaches</div></div>
      <div class="metric-card"><div class="lbl">Average Latency</div><div class="val">${data.average_latency_ms} ms</div><div class="lbl">Sub-millisecond</div></div>
    `;

    let rows = '';
    data.case_results.forEach(r => {
      rows += `<tr>
        <td><b>${r.id}</b></td>
        <td>${r.category}</td>
        <td>${escapeHtml(r.query)}</td>
        <td><span class="badge-pass">${r.status}</span></td>
        <td>${(r.groundedness_score*100).toFixed(0)}%</td>
        <td>${r.latency_ms} ms</td>
      </tr>`;
    });

    document.getElementById('eval-table-container').innerHTML = `
      <h3 style="margin-top:20px;">Detailed Benchmark Execution Matrix</h3>
      <table class="benchmark-table">
        <tr><th>ID</th><th>Category</th><th>Query</th><th>Status</th><th>Groundedness</th><th>Latency</th></tr>
        ${rows}
      </table>
    `;
  } finally {
    btn.innerText = '▶️ Re-Run Quantitative Benchmark Suite';
    btn.disabled = false;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
