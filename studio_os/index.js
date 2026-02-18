// --- TEMPLO OS v16.0 ---

const API_BASE = '';
let currentTab = 'command';
let globalData = {};

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
  fetchGlobalData();
  setInterval(fetchGlobalData, 5000);
});

// --- VIEW SWITCHING ---
// FIX: Uses .viewport-section consistently — this prevents the project view
// from persisting across all tabs.
function switchTab(tab) {
  currentTab = tab;

  // Sidebar highlight
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  const activeNav = Array.from(document.querySelectorAll('.nav-item'))
    .find(el => el.getAttribute('onclick')?.includes(tab));
  if (activeNav) activeNav.classList.add('active');

  // Hide ALL views (including project-deep)
  document.querySelectorAll('.viewport-section').forEach(el => el.style.display = 'none');

  // Show target
  const view = document.getElementById(`view-${tab}`);
  if (view) view.style.display = 'block';

  // Specific renders
  if (tab === 'portfolio') renderPortfolio();
  if (tab === 'financials') renderFinancials();
  if (tab === 'operations') renderOperations();
  if (tab === 'pipeline') renderPipeline();
  if (tab === 'system') fetchSystemLogs();
}

// --- DATA FETCHING ---
async function fetchGlobalData() {
  try {
    const [global, fin, ops, pipe] = await Promise.all([
      fetch(`${API_BASE}/founder/global`).then(r => r.json()),
      fetch(`${API_BASE}/founder/financials`).then(r => r.json()),
      fetch(`${API_BASE}/founder/operations`).then(r => r.json()),
      fetch(`${API_BASE}/founder/pipeline`).then(r => r.json())
    ]);
    globalData = { global, fin, ops, pipe };

    if (currentTab === 'command') renderCommandCenter();
    if (currentTab === 'financials') renderFinancials();
    if (currentTab === 'operations') renderOperations();
  } catch (e) {
    console.error("Pulse Failed:", e);
  }
}

// --- COMMAND CENTER ---
function renderCommandCenter() {
  const { global, ops } = globalData;

  document.getElementById('cmd-active-count').innerText = global.active_count;
  document.getElementById('cmd-pipeline-vol').innerText = formatCurrency(global.pipeline_volume);

  const cashEl = document.getElementById('cmd-cashflow-status');
  cashEl.innerText = global.cashflow_status;
  cashEl.style.color = global.cashflow_status === 'Healthy' ? 'var(--positive)' : 'var(--caution)';

  // Alerts
  const alertContainer = document.getElementById('cmd-alerts-container');
  let alerts = '';
  if (global.critical_risks_count > 0) {
    alerts += `<div class="status-badge status-locked">⚠ ${global.critical_risks_count} Critical Risks</div> `;
  }
  if (ops.deliverables_overdue > 0) {
    alerts += `<div class="status-badge status-pending">⚠ ${ops.deliverables_overdue} Overdue</div>`;
  }
  alertContainer.innerHTML = alerts || '<span class="text-muted" style="font-size:0.85rem;">No critical alerts.</span>';

  // Decision Queue
  const blockers = ops.active_projects.filter(p => p.blocker);
  document.getElementById('cmd-decision-list').innerHTML = blockers.map(p => `
    <div class="mini-item critical" onclick="openDeepProject(${p.id})">
      <span style="font-weight:600;">${p.name}</span>
      <span class="meta">${p.blocker}</span>
    </div>
  `).join('') || '<div class="empty-state">Queue clear. No decisions pending.</div>';

  // This Week
  document.getElementById('cmd-focus-list').innerHTML = `
    <div class="mini-item">
      <span style="font-weight:550;">Deliverables Due</span>
      <span style="font-size:1.3rem; font-weight:600; color:var(--accent);">${ops.deliverables_due_7d}</span>
    </div>
    <div class="mini-item">
      <span style="font-weight:550;">Revenue Forecast</span>
      <span style="font-size:1.3rem; font-weight:600; color:var(--positive);">${formatCurrency(global.revenue_forecast)}</span>
    </div>
  `;
}

// --- FINANCIALS ---
function renderFinancials() {
  const { fin } = globalData;
  document.getElementById('fin-overdue-count').innerText = fin.overdue_invoices_count;
  const overdueEl = document.getElementById('fin-overdue-val');
  overdueEl.innerText = formatCurrency(fin.overdue_value);
  overdueEl.style.color = fin.overdue_value > 0 ? 'var(--negative)' : 'var(--text-primary)';

  document.getElementById('fin-breakdown-list').innerHTML =
    `<div class="full-item" style="color:var(--text-muted); font-size:0.7rem; text-transform:uppercase; letter-spacing:0.5px;">
      <span>Project</span><span>Budget / Invoiced / Cost</span><span style="text-align:right;">Margin</span>
    </div>` +
    fin.project_financials.map(p => `
      <div class="full-item">
        <span style="font-weight:550;">${p.name}</span>
        <span>
          ${formatCurrency(p.budget)}
          <span style="color:var(--text-dim); margin:0 6px;">/</span>
          <span style="color:var(--positive);">${formatCurrency(p.invoiced)}</span>
          <span style="color:var(--text-dim); margin:0 6px;">/</span>
          <span style="color:var(--negative);">${formatCurrency(p.cost)}</span>
        </span>
        <span style="text-align:right; font-weight:700; color:${p.margin < 30 ? 'var(--negative)' : 'var(--positive)'};">${p.margin}%</span>
      </div>
    `).join('');
}

// --- OPERATIONS ---
function renderOperations() {
  const { ops } = globalData;
  document.getElementById('ops-due-7d').innerText = ops.deliverables_due_7d;
  document.getElementById('ops-overdue').innerText = ops.deliverables_overdue;

  document.getElementById('ops-project-health-list').innerHTML = ops.active_projects.map(p => `
    <div class="full-item">
      <span style="font-weight:550;">${p.name} <span class="status-badge status-stable" style="margin-left:8px;">${p.stage}</span></span>
      <span style="color:var(--text-secondary);">${p.next_milestone || 'Ongoing'}</span>
      <span style="text-align:right; font-weight:700; color:${getHealthColor(p.health)};">${p.health}%</span>
    </div>
  `).join('');
}

// --- PIPELINE ---
function renderPipeline() {
  const { pipe } = globalData;
  document.getElementById('pipeline-list').innerHTML =
    `<div class="full-item" style="color:var(--text-muted); font-size:0.7rem; text-transform:uppercase; letter-spacing:0.5px;">
      <span>Lead</span><span>Status</span><span style="text-align:right;">Value</span>
    </div>` +
    pipe.map(p => `
      <div class="full-item">
        <span style="font-weight:550;">${p.name}</span>
        <span>${p.status} <span style="color:var(--text-muted);">(${p.probability}%)</span></span>
        <span style="text-align:right; color:var(--accent); font-weight:600;">${formatCurrency(p.value)}</span>
      </div>
    `).join('');
}

// --- PORTFOLIO ---
function renderPortfolio() {
  const { ops } = globalData;
  document.getElementById('portfolio-list').innerHTML = ops.active_projects.map(p => `
    <div class="portfolio-item" onclick="openDeepProject(${p.id})">
      <span style="font-weight:600;">${p.name}</span>
      <span class="status-badge status-stable">${p.stage}</span>
      <span style="color:${getHealthColor(p.health)}; font-weight:600;">${p.health}%</span>
      <span style="text-align:right; color:var(--text-muted);">→</span>
    </div>
  `).join('');
}

// ============================================
// PROJECT COMMAND CENTER (v16.0)
// ============================================

async function openDeepProject(projectId) {
  try {
    const response = await fetch(`${API_BASE}/founder/project/${projectId}`);
    const data = await response.json();

    // FIX: Hide ALL viewport-section views, then show project-deep
    document.querySelectorAll('.viewport-section').forEach(el => el.style.display = 'none');
    document.getElementById('view-project-deep').style.display = 'block';

    // Clear sidebar active state
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    renderProjectCommandCenter(data);
    window.currentProjectData = data;
  } catch (e) {
    console.error("Error loading project:", e);
  }
}

function renderProjectCommandCenter(data) {
  const ov = data.overview;

  // 1. OVERVIEW
  if (ov) {
    document.getElementById('pcc-name').textContent = ov.name || "Untitled";
    document.getElementById('pcc-client').textContent = ov.client || "Client";
    document.getElementById('pcc-stage').textContent = ov.stage || "Intake";
    document.getElementById('pcc-status').textContent = ov.scope_stability || "Stable";
    document.getElementById('pcc-margin').textContent =
      `${ov.margin_trend === 'Up' ? '↑' : '→'} ${data.financials?.margin_percent || 0}%`;
    document.getElementById('pcc-budget').textContent =
      `${formatCurrency(data.financials?.invoiced || 0)} / ${formatCurrency(data.financials?.budget || 0)}`;
    document.getElementById('pcc-action').textContent = ov.next_action || "Review";
  }

  // >>>>>> WORKFLOW TIMELINE (v17.0) <<<<<<
  if (ov?.id) loadAndRenderWorkflow(ov.id);

  // 2. STRATEGY
  const s = data.strategy;
  const hasStrategy = s?.executive_summary && s.executive_summary !== "Conscious nightlife platform." && s.executive_summary.length > 30;
  const hasTensions = s?.tensions && s.tensions !== '[]' && s.tensions !== '[""]';
  const hasPrinciples = s?.principles && s.principles !== '[]' && s.principles !== '[""]';

  let stratHtml = '';
  if (!hasStrategy && !hasTensions && !hasPrinciples) {
    // Empty state with agent prompt
    stratHtml = `
      <div class="agent-prompt">
        <div class="agent-prompt-avatar">🧠</div>
        <div class="agent-prompt-body">
          <div class="agent-prompt-name">Strategist</div>
          <p>I need the brand strategy to begin positioning work. Could you define:</p>
          <ul class="agent-prompt-list">
            <li>An executive summary of the project vision</li>
            <li>Design principles that guide decisions</li>
            <li>Key strategic tensions to navigate</li>
          </ul>
          <button onclick="openStrategyEditor()" class="btn-agent-action">📝 Define Strategy</button>
        </div>
      </div>
    `;
  } else {
    stratHtml = `<p class="strategy-brief">"${s?.executive_summary || s?.brief || "No strategy defined."}"</p>`;
    if (hasTensions) {
      try {
        const tensions = JSON.parse(s.tensions);
        stratHtml += `<div class="pcc-list-group"><h4>Strategic Tensions</h4><ul class="clean-list">`;
        tensions.forEach(t => stratHtml += `<li>⚡ ${t}</li>`);
        stratHtml += `</ul></div>`;
      } catch (e) { }
    }
    if (hasPrinciples) {
      try {
        const principles = JSON.parse(s.principles);
        stratHtml += `<div class="pcc-list-group"><h4>Design Principles</h4><ul class="clean-list">`;
        principles.forEach(p => stratHtml += `<li>◆ ${p}</li>`);
        stratHtml += `</ul></div>`;
      } catch (e) { }
    }
  }
  document.getElementById('pcc-strategy-content').innerHTML = stratHtml;

  // 3. ROADMAP (Stage-Based)
  const deliverables = data.production?.deliverables || [];
  const tasks = data.production?.tasks || [];
  const stages = ['Strategy', 'Design', 'Production'];
  const getStageItems = (list, stageName) => {
    return list.filter(item => {
      if (stageName === 'Strategy' && (item.title.includes('Brand') || item.title.includes('Research'))) return true;
      if (stageName === 'Design' && (item.title.includes('Visual') || item.title.includes('UI') || item.title.includes('Wireframe'))) return true;
      if (stageName === 'Production' && (item.title.includes('Website') || item.title.includes('Dev') || item.title.includes('App'))) return true;
      return false;
    });
  };

  let roadMapHtml = '';
  if (deliverables.length === 0 && tasks.length === 0) {
    roadMapHtml = `
      <div class="agent-prompt">
        <div class="agent-prompt-avatar">🎯</div>
        <div class="agent-prompt-body">
          <div class="agent-prompt-name">Director</div>
          <p>No deliverables or milestones defined yet. I need a production roadmap to coordinate the team.</p>
          <p style="color:var(--text-muted); font-size:0.8rem; margin-top:6px;">Add deliverables via the New Project wizard or inline below.</p>
          <button onclick="openNewProjectWizard(); wizardStep=3; updateWizardView();" class="btn-agent-action">📦 Add Deliverables</button>
        </div>
      </div>
    `;
  } else {
    roadMapHtml = `<div class="roadmap-container">`;
    stages.forEach(stage => {
      const stageDelivs = getStageItems(deliverables, stage);
      const stageTasks = getStageItems(tasks, stage);
      const isActive = ov?.stage === stage;

      roadMapHtml += `
        <div class="stage-block ${isActive ? 'active-stage' : ''}" style="opacity:${isActive ? 1 : 0.6};">
          <h4 style="color:${isActive ? 'var(--accent)' : 'var(--text-muted)'};">
            ${isActive ? '▶ ' : ''}${stage}
          </h4>
          ${stageDelivs.length > 0 ? `
            <div style="margin-bottom:8px;">
              <span style="font-size:0.68rem; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.5px;">Deliverables</span>
              <ul class="clean-list">
                ${stageDelivs.map(d => `<li style="display:flex; justify-content:space-between;">
                  <span>${d.title}</span>
                  <span class="status-badge status-${d.status.toLowerCase()}">${d.status}</span>
                </li>`).join('')}
              </ul>
            </div>
          ` : ''}
          ${stageTasks.length > 0 ? `
            <div>
              <span style="font-size:0.68rem; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.5px;">Tasks</span>
              <ul class="clean-list">
                ${stageTasks.map(t => `<li>
                  <input type="checkbox" ${t.status === 'Done' ? 'checked' : ''}> ${t.title}
                </li>`).join('')}
              </ul>
            </div>
          ` : ''}
          ${stageDelivs.length === 0 && stageTasks.length === 0 ? '<div class="empty-state" style="padding:8px 0;">No active items</div>' : ''}
        </div>
      `;
    });
    roadMapHtml += `</div>`;
  }
  document.getElementById('pcc-production-content').innerHTML = roadMapHtml;

  // 4. TASKS
  if (tasks.length === 0) {
    document.getElementById('pcc-tasks-content').innerHTML = `
      <div class="agent-prompt compact">
        <div class="agent-prompt-avatar">✅</div>
        <div class="agent-prompt-body">
          <div class="agent-prompt-name">Director</div>
          <p>No action items yet. Once deliverables are defined, I'll break them into executable tasks.</p>
        </div>
      </div>
    `;
  } else {
    document.getElementById('pcc-tasks-content').innerHTML =
      `<ul class="task-list">${tasks.map(t =>
        `<li class="task-item"><input type="checkbox" ${t.status === 'Done' ? 'checked' : ''}> ${t.title}</li>`
      ).join('')}</ul>`;
  }

  // 7. DOCUMENTS
  renderPCC_Documents(data.documents || []);

  // 8. GOVERNANCE
  const risks = data.governance?.risks || [];
  let govHtml = '';
  if (risks.length === 0) {
    govHtml = `
      <div class="agent-prompt compact">
        <div class="agent-prompt-avatar">💰</div>
        <div class="agent-prompt-body">
          <div class="agent-prompt-name">CFO</div>
          <p>No risks flagged. I'll monitor budget burn, scope drift, and timeline risks as the project progresses.</p>
        </div>
      </div>
    `;
  } else {
    govHtml = risks.map(r => `<div class="risk-card"><strong>${r.severity}:</strong> ${r.description}</div>`).join('');
  }
  document.getElementById('pcc-governance-content').innerHTML = govHtml;

  // 9. AGENT REQUESTS
  renderPCC_AgentRequests(data.requests || []);
}

// ============================================
// WORKFLOW TIMELINE ENGINE (v17.0)
// ============================================

const AGENT_ICONS = { Strategist: '🧠', Director: '🎯', Designer: '🎨', CFO: '💰', System: '✓' };

async function loadAndRenderWorkflow(projectId) {
  const timeline = document.getElementById('pcc-workflow-timeline');
  if (!timeline) return;

  // Auto-seed workflow if none exists
  try {
    await fetch(`${API_BASE}/founder/project/${projectId}/workflow/seed`, { method: 'POST' });
  } catch (e) { /* already seeded */ }

  // Load steps
  try {
    const res = await fetch(`${API_BASE}/founder/project/${projectId}/workflow`);
    const steps = await res.json();
    renderWorkflowTimeline(steps, projectId);
  } catch (e) {
    timeline.innerHTML = '<div class="empty-state">No workflow data.</div>';
  }
}

function renderWorkflowTimeline(steps, projectId) {
  const container = document.getElementById('pcc-workflow-timeline');
  if (!container || steps.length === 0) {
    if (container) container.innerHTML = '';
    return;
  }

  let html = '<div class="wf-timeline">';

  steps.forEach((step, i) => {
    const icon = AGENT_ICONS[step.agent] || '🤖';
    const isActive = step.status === 'active';
    const isResolved = step.status === 'resolved';
    const isLast = i === steps.length - 1;

    html += `
      <div class="wf-step ${isActive ? 'wf-active' : ''} ${isResolved ? 'wf-resolved' : ''}" data-step-id="${step.id}">
        <div class="wf-connector ${isLast ? 'wf-last' : ''}">
          <div class="wf-dot ${isResolved ? 'wf-dot-done' : ''} ${isActive ? 'wf-dot-active' : ''}">${isResolved ? '✓' : icon}</div>
          ${!isLast ? '<div class="wf-line"></div>' : ''}
        </div>
        <div class="wf-card ${isActive ? 'wf-card-active' : ''} ${isResolved ? 'wf-card-resolved' : ''}">
          <div class="wf-card-header">
            <span class="wf-agent-name">@${step.agent}</span>
            <span class="wf-step-title">${step.title}</span>
            ${step.phase ? `<span class="wf-phase">${step.phase}</span>` : ''}
            ${isResolved && step.chosen_option ? `<span class="wf-chosen">→ ${step.chosen_option}</span>` : ''}
          </div>
          <div class="wf-card-body">${formatWorkflowBody(step.body)}</div>
          ${isActive ? renderWorkflowActions(step, projectId) : ''}
        </div>
      </div>
    `;
  });

  html += '</div>';
  container.innerHTML = html;
}

function formatWorkflowBody(body) {
  if (!body) return '';
  // Simple markdown-to-HTML: bold, headers, lists
  return body
    .replace(/## (.+)/g, '<h4>$1</h4>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/\n\n/g, '<br/>')
    .replace(/\n/g, '<br/>');
}

function renderWorkflowActions(step, projectId) {
  if (step.step_type === 'input_needed') {
    return `
      <div class="wf-action-area">
        <textarea id="wf-input-${step.id}" class="wf-input" placeholder="Type your response..." rows="4"></textarea>
        <button onclick="resolveWorkflowStep(${projectId}, ${step.id}, 'input')" class="btn-agent-action">Submit</button>
      </div>
    `;
  }

  if (step.step_type === 'decision_gate') {
    const options = step.options || [];

    // Special UI for deliverable selection (has cost + selected fields)
    if (step.title === 'Deliverable Selection' && options.length > 0 && options[0].cost !== undefined) {
      const phases = [...new Set(options.map(o => o.phase))];
      return `
        <div class="wf-action-area wf-deliverable-selection">
          ${phases.map(phase => `
            <div class="wf-del-phase">
              <div class="wf-del-phase-label">${phase}</div>
              ${options.filter(o => o.phase === phase).map(o => `
                <label class="wf-del-item ${o.selected ? 'wf-del-selected' : ''}" data-key="${o.key}" data-cost="${o.cost}">
                  <input type="checkbox" ${o.selected ? 'checked' : ''} onchange="toggleDeliverable(this)" />
                  <span class="wf-del-name">${o.title}</span>
                  <span class="wf-del-cost">$${o.cost.toLocaleString()}</span>
                </label>
              `).join('')}
            </div>
          `).join('')}
          <div class="wf-del-total" id="wf-del-total-${step.id}">
            Estimated total: $${options.filter(o => o.selected).reduce((s, o) => s + o.cost, 0).toLocaleString()}
          </div>
          <div class="wf-del-custom">
            <label class="wf-del-custom-label">Add custom deliverables (comma-separated):</label>
            <input type="text" id="wf-custom-del-${step.id}" class="wf-input" placeholder="e.g. Packaging Design, Menu Design, Uniforms" />
          </div>
          <button onclick="resolveDeliverableSelection(${projectId}, ${step.id})" class="btn-agent-action">Confirm Deliverables</button>
        </div>
      `;
    }

    // Standard single-select decision gate
    return `
      <div class="wf-action-area">
        <div class="wf-options">
          ${options.map(o => `
            <div class="wf-option-card" onclick="selectWorkflowOption(this, '${o.key}')" data-key="${o.key}">
              <div class="wf-option-key">${o.key}</div>
              <div class="wf-option-title">${o.title}</div>
              <div class="wf-option-desc">${o.description || ''}</div>
            </div>
          `).join('')}
        </div>
        <button onclick="resolveWorkflowStep(${projectId}, ${step.id}, 'choose')" class="btn-agent-action" id="wf-submit-${step.id}" disabled>Confirm Selection</button>
      </div>
    `;
  }

  if (step.step_type === 'approval_gate') {
    const options = step.options || [];
    return `
      <div class="wf-action-area wf-approval">
        ${options.map(o => `
          <button onclick="resolveWorkflowStep(${projectId}, ${step.id}, '${o.key === 'approve' ? 'approve' : 'reject'}', '${o.key}')"
            class="btn-agent-action ${o.key === 'approve' ? 'wf-approve-btn' : 'wf-reject-btn'}">${o.title}</button>
        `).join('')}
      </div>
    `;
  }

  if (step.step_type === 'agent_output') {
    return `
      <div class="wf-action-area">
        <button onclick="resolveWorkflowStep(${projectId}, ${step.id}, 'acknowledge')" class="btn-agent-action">Acknowledged</button>
      </div>
    `;
  }

  return '';
}

window._selectedOption = null;
function selectWorkflowOption(el, key) {
  // Remove selection from siblings
  el.parentElement.querySelectorAll('.wf-option-card').forEach(c => c.classList.remove('wf-selected'));
  el.classList.add('wf-selected');
  window._selectedOption = key;
  // Enable submit button
  const stepId = el.closest('.wf-step').dataset.stepId;
  const btn = document.getElementById(`wf-submit-${stepId}`);
  if (btn) btn.disabled = false;
}

// --- Deliverable Selection helpers ---
window.toggleDeliverable = function (checkbox) {
  const label = checkbox.closest('.wf-del-item');
  if (checkbox.checked) {
    label.classList.add('wf-del-selected');
  } else {
    label.classList.remove('wf-del-selected');
  }
  // Recalculate total
  const area = checkbox.closest('.wf-deliverable-selection');
  if (!area) return;
  let total = 0;
  area.querySelectorAll('.wf-del-item input[type="checkbox"]:checked').forEach(cb => {
    total += parseInt(cb.closest('.wf-del-item').dataset.cost) || 0;
  });
  const totalEl = area.querySelector('[id^="wf-del-total-"]');
  if (totalEl) totalEl.textContent = `Estimated total: $${total.toLocaleString()}`;
};

window.resolveDeliverableSelection = async function (projectId, stepId) {
  // Collect checked deliverable keys
  const area = document.querySelector(`.wf-step[data-step-id="${stepId}"] .wf-deliverable-selection`);
  if (!area) return;

  const selectedKeys = [];
  area.querySelectorAll('.wf-del-item input[type="checkbox"]:checked').forEach(cb => {
    selectedKeys.push(cb.closest('.wf-del-item').dataset.key);
  });

  const customInput = document.getElementById(`wf-custom-del-${stepId}`);
  const customText = customInput ? customInput.value.trim() : '';

  if (selectedKeys.length === 0 && !customText) {
    alert('Please select at least one deliverable or add a custom one.');
    return;
  }

  const payload = {
    step_id: stepId,
    action: 'choose',
    chosen_option: JSON.stringify(selectedKeys),
    input_text: customText || null
  };

  try {
    const res = await fetch(`${API_BASE}/founder/project/${projectId}/workflow/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await openDeepProject(projectId);
  } catch (e) {
    console.error('Deliverable selection failed:', e);
  }
};

async function resolveWorkflowStep(projectId, stepId, action, optionKey) {
  const payload = { step_id: stepId, action: action };

  if (action === 'input') {
    const textarea = document.getElementById(`wf-input-${stepId}`);
    payload.input_text = textarea ? textarea.value : '';
    if (!payload.input_text.trim()) return;
  }

  if (action === 'choose') {
    payload.chosen_option = window._selectedOption || optionKey;
    if (!payload.chosen_option) return;
  }

  if (action === 'approve' || action === 'reject') {
    payload.chosen_option = optionKey || action;
  }

  try {
    const res = await fetch(`${API_BASE}/founder/project/${projectId}/workflow/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    window._selectedOption = null;

    // Reload the project to refresh everything
    await openDeepProject(projectId);
  } catch (e) {
    console.error('Workflow resolve failed:', e);
  }
}

// ============================================
// DELETE PROJECT
// ============================================

async function deleteCurrentProject() {
  const data = window.currentProjectData;
  if (!data?.overview?.id) return;

  const confirmed = confirm(`Delete "${data.overview.name}"? This cannot be undone.`);
  if (!confirmed) return;

  try {
    const res = await fetch(`${API_BASE}/founder/project/${data.overview.id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    // Go back to projects list
    await fetchGlobalData();
    switchTab('portfolio');
  } catch (e) {
    console.error('Delete failed:', e);
    alert('Failed to delete project.');
  }
}

// ============================================
// DOCUMENT SYSTEM
// ============================================

function renderPCC_Documents(docs) {
  const folders = ['All', 'Strategy', 'Design', 'Legal', 'Production', 'Assets'];
  const folderContainer = document.getElementById('pcc-doc-folders');

  folderContainer.innerHTML = folders.map((f, i) =>
    `<div class="folder-item${i === 0 ? ' active' : ''}" onclick="filterDocs('${f}')">${f === 'All' ? '📚' : '📁'} ${f}</div>`
  ).join('');

  window.currentDocs = docs;
  renderFileList(docs);

  window.filterDocs = (category) => {
    document.querySelectorAll('.folder-item').forEach(el => el.classList.remove('active'));
    if (event && event.target) event.target.classList.add('active');
    if (category === 'All') {
      renderFileList(window.currentDocs);
    } else {
      const filtered = window.currentDocs.filter(d => d.category === category);
      renderFileList(filtered);
    }
  };
}

const DOC_AGENT_ICONS = { 'Strategy': '🧠', 'Design': '🎨', 'Legal': '⚖️', 'Production': '🎬', 'Assets': '📦' };

function renderFileList(list) {
  const container = document.getElementById('pcc-doc-files');
  if (list.length === 0) {
    container.innerHTML = `<div class="empty-state">No documents yet. Agent-generated research will appear here as you progress through the workflow.</div>`;
    return;
  }
  container.innerHTML = list.map(d => `
    <div class="file-card${d.doc_type === 'html' ? ' file-card-rich' : ''}" onclick="openDocument(${d.id})">
      <span class="file-icon">${d.doc_type === 'html' ? (DOC_AGENT_ICONS[d.category] || '📝') : d.doc_type === 'link' ? '🔗' : '📄'}</span>
      <div class="file-info">
        <div class="file-name">${d.name}</div>
        <div class="file-meta">${d.category}${d.doc_type === 'html' ? ' · Agent Generated' : ''}</div>
      </div>
    </div>
  `).join('');
}

// --- DOCUMENT VIEWER (HTML + PDF) ---
window.openDocument = function (docId) {
  const doc = window.currentDocs.find(d => d.id === docId);
  if (!doc) { console.error("Doc not found:", docId); return; }

  if (doc.doc_type === 'link') {
    window.open(doc.url, '_blank');
    return;
  }

  const modal = document.getElementById('doc-modal');
  const viewer = document.getElementById('doc-view-mode');
  const editor = document.getElementById('doc-editor-content');
  const toggleBtn = document.getElementById('doc-toggle-edit');

  if (!modal) return;

  // Set title
  document.getElementById('doc-modal-title').textContent = doc.name;

  // Rich HTML docs get an iframe, plain text gets markdown rendering
  if (doc.doc_type === 'html' && doc.content && doc.content.includes('<!DOCTYPE')) {
    viewer.innerHTML = '<iframe id="doc-iframe" class="doc-iframe"></iframe>';
    const iframe = document.getElementById('doc-iframe');
    iframe.onload = () => {
      // Adjust iframe height to fit content
      try {
        iframe.style.height = iframe.contentDocument.body.scrollHeight + 40 + 'px';
      } catch (e) { /* cross-origin fallback */ }
    };
    const blob = new Blob([doc.content], { type: 'text/html' });
    iframe.src = URL.createObjectURL(blob);
    toggleBtn.style.display = 'none'; // No editing for rich HTML docs
  } else {
    viewer.innerHTML = renderDocAsHTML(doc);
    toggleBtn.style.display = '';
  }

  viewer.style.display = 'block';
  editor.style.display = 'none';
  editor.value = doc.content || "";
  toggleBtn.textContent = '✎ Edit';

  window.currentDocId = docId;
  modal.style.display = 'flex';
};

function renderDocAsHTML(doc) {
  const content = doc.content || "No content available.";
  // Convert markdown-like content to styled HTML
  const lines = content.split('\n');
  let html = '<div class="doc-rendered">';

  lines.forEach(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith('# ')) {
      html += `<h1>${trimmed.substring(2)}</h1>`;
    } else if (trimmed.startsWith('## ')) {
      html += `<h2>${trimmed.substring(3)}</h2>`;
    } else if (trimmed.startsWith('### ')) {
      html += `<h3>${trimmed.substring(4)}</h3>`;
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      html += `<li>${trimmed.substring(2)}</li>`;
    } else if (trimmed.startsWith('> ')) {
      html += `<blockquote>${trimmed.substring(2)}</blockquote>`;
    } else if (trimmed === '') {
      html += '<br>';
    } else {
      html += `<p>${trimmed}</p>`;
    }
  });

  html += '</div>';
  return html;
}

window.toggleDocEdit = function () {
  const viewer = document.getElementById('doc-view-mode');
  const editor = document.getElementById('doc-editor-content');
  const toggleBtn = document.getElementById('doc-toggle-edit');

  if (viewer.style.display !== 'none') {
    // Switch to edit
    viewer.style.display = 'none';
    editor.style.display = 'block';
    toggleBtn.textContent = '👁 View';
  } else {
    // Switch to view — re-render from editor content
    const doc = window.currentDocs.find(d => d.id === window.currentDocId);
    if (doc) {
      doc.content = editor.value;
      viewer.innerHTML = renderDocAsHTML(doc);
    }
    editor.style.display = 'none';
    viewer.style.display = 'block';
    toggleBtn.textContent = '✎ Edit';
  }
};

window.saveDocument = function () {
  const editor = document.getElementById('doc-editor-content');
  const doc = window.currentDocs.find(d => d.id === window.currentDocId);
  if (doc) doc.content = editor.value;
  alert("Document saved.");
  window.closeDocModal();
};

window.closeDocModal = function () {
  document.getElementById('doc-modal').style.display = 'none';
};

// --- PDF DOWNLOAD ---
window.downloadDocPDF = function () {
  const doc = window.currentDocs.find(d => d.id === window.currentDocId);
  if (!doc) return;

  const content = doc.content || "No content.";
  const lines = content.split('\n');

  // Build a clean, print-optimized HTML document
  let bodyHtml = '';
  lines.forEach(line => {
    const t = line.trim();
    if (t.startsWith('# ')) bodyHtml += `<h1>${t.substring(2)}</h1>`;
    else if (t.startsWith('## ')) bodyHtml += `<h2>${t.substring(3)}</h2>`;
    else if (t.startsWith('### ')) bodyHtml += `<h3>${t.substring(4)}</h3>`;
    else if (t.startsWith('- ') || t.startsWith('* ')) bodyHtml += `<li>${t.substring(2)}</li>`;
    else if (t.startsWith('> ')) bodyHtml += `<blockquote>${t.substring(2)}</blockquote>`;
    else if (t === '') bodyHtml += '<br>';
    else bodyHtml += `<p>${t}</p>`;
  });

  const pdfHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${doc.name}</title>
  <style>
    @page { size: A4; margin: 2.5cm 2cm; }
    body {
      font-family: 'Georgia', 'Times New Roman', serif;
      font-size: 11pt;
      line-height: 1.7;
      color: #1d1d1f;
      max-width: 100%;
    }
    h1 { font-size: 22pt; font-weight: 700; margin: 0 0 12pt 0; color: #000; letter-spacing: -0.5px; }
    h2 { font-size: 16pt; font-weight: 600; margin: 18pt 0 8pt 0; color: #1d1d1f; border-bottom: 0.5pt solid #ddd; padding-bottom: 4pt; }
    h3 { font-size: 13pt; font-weight: 600; margin: 14pt 0 6pt 0; color: #333; }
    p { margin: 0 0 8pt 0; text-align: justify; }
    li { margin: 2pt 0; padding-left: 4pt; }
    blockquote { border-left: 2pt solid #c8a96e; padding-left: 12pt; color: #555; font-style: italic; margin: 10pt 0; }
    .doc-footer { margin-top: 40pt; padding-top: 10pt; border-top: 0.5pt solid #ddd; font-size: 8pt; color: #999; text-align: center; }
  </style>
</head>
<body>
  ${bodyHtml}
  <div class="doc-footer">
    ${doc.name} — Templo Atelier — Generated ${new Date().toLocaleDateString()}
  </div>
</body>
</html>`;

  // Open in new window for print-to-PDF
  const win = window.open('', '_blank');
  win.document.write(pdfHtml);
  win.document.close();

  // Auto-trigger print dialog after a short delay
  setTimeout(() => { win.print(); }, 500);
};

// ============================================
// AGENT REQUESTS
// ============================================

function renderPCC_AgentRequests(requests) {
  const container = document.getElementById('pcc-agent-log');
  container.innerHTML = requests.map(r => `
    <div class="chat-entry">
      <span class="agent-name">@${r.target_agent}</span>
      <span class="msg">${r.request}</span>
      ${r.response ? `<div class="response">↳ ${r.response}</div>` : ''}
    </div>
  `).join('');
}

async function sendAgentRequest() {
  const agent = document.getElementById('pcc-agent-select').value;
  const text = document.getElementById('pcc-agent-input').value;
  if (!text) return;

  const container = document.getElementById('pcc-agent-log');
  container.innerHTML += `
    <div class="chat-entry">
      <span class="agent-name">@${agent}</span>
      <span class="msg">${text}</span>
      <div class="response">Sending...</div>
    </div>
  `;
  document.getElementById('pcc-agent-input').value = '';
  container.scrollTop = container.scrollHeight;
}

// ============================================
// CREATIVE FOCUS MODE
// ============================================

function toggleCreativeMode() {
  const overlay = document.getElementById('creative-focus-mode');
  if (overlay.style.display === 'none') {
    const data = window.currentProjectData?.creative_mode;
    if (data) {
      document.getElementById('cfm-objective').textContent = data.objective;

      let insights = '';
      try {
        const parsed = JSON.parse(data.insights);
        if (parsed.competitors) {
          parsed.competitors.forEach(c => insights += `<p style="font-size:1.1rem; color:var(--text-secondary); margin-bottom:10px;">${c}</p>`);
        }
      } catch (e) { }
      document.getElementById('cfm-insights').innerHTML = insights;

      try {
        const principles = JSON.parse(data.principles);
        document.getElementById('cfm-guardrails').innerHTML =
          principles.map(p => `<p style="color:var(--text-secondary); margin-bottom:6px;">• ${p}</p>`).join('');
      } catch (e) {
        document.getElementById('cfm-guardrails').textContent = "No guardrails defined.";
      }
    }
    overlay.style.display = 'flex';
  } else {
    overlay.style.display = 'none';
  }
}

// ============================================
// UTILS
// ============================================

function formatCurrency(val) {
  if (val === undefined || val === null) return '$0';
  return '$' + val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function getHealthColor(score) {
  if (score >= 90) return 'var(--positive)';
  if (score >= 70) return 'var(--caution)';
  return 'var(--negative)';
}

// --- SYSTEM LOGS ---
async function fetchSystemLogs() {
  try {
    const res = await fetch(`${API_BASE}/logs/?limit=20`);
    const logs = await res.json();
    document.getElementById('system-log-terminal').innerHTML = logs.map(log => `
      <div class="log-entry">
        <span class="log-timestamp">[${new Date(log.timestamp).toLocaleTimeString()}]</span>
        <span class="log-agent">${log.agent_name}</span>
        <span style="${log.severity === 'ERROR' ? 'color:var(--negative);' : ''}">${log.message}</span>
      </div>
    `).join('');
  } catch (e) { console.error(e); }
}

// ============================================
// NEW PROJECT WIZARD (v16.0)
// ============================================

let wizardStep = 1;
const WIZARD_STEPS = 3;

function openNewProjectWizard() {
  wizardStep = 1;
  updateWizardView();

  // Clear form
  ['np-name', 'np-client', 'np-brief', 'np-budget', 'np-strategy', 'np-principles', 'np-tensions'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  document.getElementById('np-deliverables-list').innerHTML = '';
  addDeliverableInput(); // Start with one empty row

  document.getElementById('new-project-modal').style.display = 'flex';
}

function closeNewProjectWizard() {
  document.getElementById('new-project-modal').style.display = 'none';
}

function updateWizardView() {
  // Show/hide steps
  document.querySelectorAll('.wizard-step').forEach(el => {
    el.style.display = el.dataset.step == wizardStep ? 'block' : 'none';
  });

  // Dots
  document.querySelectorAll('.step-dot').forEach(dot => {
    dot.classList.toggle('active', dot.dataset.dot == wizardStep);
  });

  // Buttons
  document.getElementById('wizard-back').style.display = wizardStep > 1 ? 'inline-block' : 'none';
  document.getElementById('wizard-next').textContent = wizardStep === WIZARD_STEPS ? 'Create Project' : 'Next →';

  // Title
  const titles = { 1: 'New Project — Basics', 2: 'Strategy', 3: 'Deliverables' };
  document.getElementById('wizard-title').textContent = titles[wizardStep] || 'New Project';
}

function wizardNext() {
  if (wizardStep < WIZARD_STEPS) {
    // Validate step 1
    if (wizardStep === 1) {
      const name = document.getElementById('np-name').value.trim();
      if (!name) {
        document.getElementById('np-name').style.borderColor = 'var(--negative)';
        document.getElementById('np-name').focus();
        return;
      }
    }
    wizardStep++;
    updateWizardView();
  } else {
    submitNewProject();
  }
}

function wizardBack() {
  if (wizardStep > 1) {
    wizardStep--;
    updateWizardView();
  }
}

function addDeliverableInput() {
  const container = document.getElementById('np-deliverables-list');
  const row = document.createElement('div');
  row.className = 'deliverable-row';
  row.innerHTML = `
    <input type="text" class="form-input" placeholder="Deliverable name..." style="flex:1;">
    <button onclick="this.parentElement.remove()" class="btn-text" style="color:var(--negative); padding:0 8px;">✕</button>
  `;
  container.appendChild(row);
}

async function submitNewProject() {
  const name = document.getElementById('np-name').value.trim();
  if (!name) return;

  // Parse comma-separated values into JSON arrays
  const principlesRaw = document.getElementById('np-principles').value.trim();
  const tensionsRaw = document.getElementById('np-tensions').value.trim();

  const principles = principlesRaw ? JSON.stringify(principlesRaw.split(',').map(s => s.trim()).filter(Boolean)) : '[]';
  const tensions = tensionsRaw ? JSON.stringify(tensionsRaw.split(',').map(s => s.trim()).filter(Boolean)) : '[]';

  // Gather deliverables
  const deliverables = [];
  document.querySelectorAll('#np-deliverables-list .deliverable-row input').forEach(input => {
    const title = input.value.trim();
    if (title) deliverables.push({ title, status: 'Pending' });
  });

  const payload = {
    name,
    client: document.getElementById('np-client').value.trim(),
    client_brief: document.getElementById('np-brief').value.trim(),
    budget_cap: parseFloat(document.getElementById('np-budget').value) || 0,
    stage: document.getElementById('np-stage').value,
    executive_summary: document.getElementById('np-strategy').value.trim(),
    design_principles: principles,
    strategic_tensions: tensions,
    deliverables
  };

  // Submit
  document.getElementById('wizard-next').textContent = 'Creating...';
  document.getElementById('wizard-next').disabled = true;

  try {
    const res = await fetch(`${API_BASE}/founder/project`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const result = await res.json();
    closeNewProjectWizard();

    // Refresh data and open the new project
    await fetchGlobalData();
    openDeepProject(result.project_id);
  } catch (e) {
    console.error('Failed to create project:', e);
    alert('Failed to create project. Check the console for details.');
  } finally {
    document.getElementById('wizard-next').textContent = 'Create Project';
    document.getElementById('wizard-next').disabled = false;
  }
}
