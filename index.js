// ===== Templo Atelier — Studio OS | Information Architecture =====

const API_BASE = window.location.protocol === 'file:'
  ? 'http://localhost:8000'
  : (window.location.hostname === 'localhost' ? 'http://localhost:8000' : '');

// ===== Navigation State =====
let currentLevel = 'categories'; // 'categories' | 'projects' | 'detail'
let currentCategory = null;       // { name, slug }
let currentProject = null;        // full project object

// Status grouping config
const STATUS_COLUMNS = [
  { key: 'Intake', label: 'Onboarding', match: s => s === 'Intake' },
  { key: 'Strategy', label: 'In Progress', match: s => ['Strategy', 'Design'].includes(s) },
  { key: 'Pending', label: 'Pending', match: s => s === 'Pending' || s === 'Blocked' },
  { key: 'Delivery', label: 'Near Handoff', match: s => ['Delivery', 'Closed'].includes(s) },
];

// ===== Navigation =====
function navigateTo(level, params = {}) {
  currentLevel = level;

  document.getElementById('level-categories').style.display = 'none';
  document.getElementById('level-projects').style.display = 'none';
  document.getElementById('level-detail').style.display = 'none';

  if (level === 'categories') {
    currentCategory = null;
    currentProject = null;
    document.getElementById('level-categories').style.display = 'block';
    loadCategories();
    updateSidebar('categories');
  } else if (level === 'projects') {
    currentCategory = params;
    currentProject = null;
    document.getElementById('level-projects').style.display = 'block';
    document.getElementById('category-title').innerText = params.name;
    document.getElementById('category-subtitle').innerText = `All projects in ${params.name}`;
    loadProjects(params.slug);
    updateSidebar('projects');
  } else if (level === 'detail') {
    currentProject = params;
    document.getElementById('level-detail').style.display = 'block';
    loadProjectDetail(params);
    updateSidebar('detail');
  }

  renderBreadcrumb();
  document.querySelector('main').scrollTop = 0;
}

function renderBreadcrumb() {
  const bc = document.getElementById('breadcrumb');
  let html = '';

  if (currentLevel === 'categories') {
    html = '<span class="breadcrumb-item active">Categories</span>';
  } else if (currentLevel === 'projects') {
    html = `<span class="breadcrumb-item" onclick="navigateTo('categories')">Categories</span>
            <span class="breadcrumb-sep">›</span>
            <span class="breadcrumb-item active">${escHtml(currentCategory.name)}</span>`;
  } else if (currentLevel === 'detail') {
    html = `<span class="breadcrumb-item" onclick="navigateTo('categories')">Categories</span>
            <span class="breadcrumb-sep">›</span>
            <span class="breadcrumb-item" onclick="navigateTo('projects', currentCategory)">${escHtml(currentCategory.name)}</span>
            <span class="breadcrumb-sep">›</span>
            <span class="breadcrumb-item active">${escHtml(currentProject.name)}</span>`;
  }

  bc.innerHTML = html;
}

function updateSidebar(level) {
  const nav = document.getElementById('sidebar-nav');

  if (level === 'categories') {
    nav.innerHTML = `
      <div class="nav-item active" onclick="navigateTo('categories')">
        <span class="nav-icon">⊞</span> Categories
      </div>`;
  } else if (level === 'projects') {
    nav.innerHTML = `
      <div class="nav-item" onclick="navigateTo('categories')">
        <span class="nav-icon">⊞</span> Categories
      </div>
      <div class="nav-divider" style="margin:8px 4px;"></div>
      <div class="nav-section-label">${escHtml(currentCategory.name)}</div>
      <div class="nav-item active">
        <span class="nav-icon">▦</span> Projects
      </div>`;
  } else if (level === 'detail') {
    nav.innerHTML = `
      <div class="nav-item" onclick="navigateTo('categories')">
        <span class="nav-icon">⊞</span> Categories
      </div>
      <div class="nav-item" onclick="navigateTo('projects', currentCategory)">
        <span class="nav-icon">▦</span> ${escHtml(currentCategory.name)}
      </div>
      <div class="nav-divider" style="margin:8px 4px;"></div>
      <div class="nav-section-label">Project</div>
      <div class="nav-item active" onclick="switchDetailTab('overview')">
        <span class="nav-icon">◉</span> Overview
      </div>
      <div class="nav-item" onclick="switchDetailTab('documents')">
        <span class="nav-icon">📄</span> Documents
      </div>
      <div class="nav-item" onclick="switchDetailTab('tasks')">
        <span class="nav-icon">☐</span> Tasks
      </div>
      <div class="nav-item" onclick="switchDetailTab('decisions')">
        <span class="nav-icon">⚖</span> Decisions
      </div>
      <div class="nav-item" onclick="switchDetailTab('timeline')">
        <span class="nav-icon">◷</span> Timeline
      </div>`;
  }
}

// ===== LEVEL 1: Categories =====
async function loadCategories() {
  try {
    const res = await fetch(`${API_BASE}/categories/`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const categories = await res.json();
    renderCategories(categories);
  } catch (e) {
    console.warn('Failed to load categories:', e.message);
  }
}

function renderCategories(categories) {
  const grid = document.getElementById('categories-grid');

  if (categories.length === 0) {
    grid.innerHTML = '<div class="empty-state"><div class="empty-icon">⊞</div><p>No categories yet</p></div>';
    return;
  }

  grid.innerHTML = categories.map(cat => {
    const statusChips = Object.entries(cat.status_breakdown || {})
      .map(([status, count]) => {
        const cls = status.toLowerCase();
        return `<span class="status-chip ${cls}">${status}: ${count}</span>`;
      }).join('');

    const attention = cat.needs_attention
      ? '<div class="attention-badge">⚠ Needs Attention</div>'
      : '';

    return `
      <div class="category-card" onclick="navigateTo('projects', { name: '${escAttr(cat.name)}', slug: '${escAttr(cat.slug)}' })">
        <span class="category-icon">${cat.icon || '●'}</span>
        <div class="category-name">${escHtml(cat.name)}</div>
        <div class="category-count">${cat.project_count} project${cat.project_count !== 1 ? 's' : ''}</div>
        <div class="category-statuses">${statusChips}</div>
        ${attention}
      </div>`;
  }).join('');
}

// ===== LEVEL 2: Projects =====
async function loadProjects(categorySlug) {
  try {
    const res = await fetch(`${API_BASE}/categories/${categorySlug}/projects`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const projects = await res.json();
    renderProjects(projects);
  } catch (e) {
    console.warn('Failed to load projects:', e.message);
  }
}

function renderProjects(projects) {
  const board = document.getElementById('projects-board');

  board.innerHTML = STATUS_COLUMNS.map(col => {
    const colProjects = projects.filter(p => col.match(p.stage || p.status || 'Intake'));
    const cards = colProjects.length > 0
      ? colProjects.map(p => renderProjectCard(p)).join('')
      : '<div class="empty-column-state">No projects</div>';

    return `
      <div class="status-column">
        <div class="column-header">
          <span class="column-title">${col.label}</span>
          <span class="column-count">${colProjects.length}</span>
        </div>
        ${cards}
      </div>`;
  }).join('');
}

function renderProjectCard(project) {
  const needsApproval = project.review_status === 'PENDING';
  const approvalBadge = needsApproval
    ? '<span class="approval-badge">● Needs Approval</span>'
    : '';

  const dueDate = project.deadline
    ? new Date(project.deadline).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    : '—';

  return `
    <div class="project-card" onclick="navigateTo('detail', ${escAttr(JSON.stringify(project))})">
      <div class="project-card-name">${escHtml(project.name)}</div>
      <div class="project-card-client">${escHtml(project.client || 'No client')}</div>
      <div class="project-card-meta">
        <div class="project-card-row">
          <span class="label">Milestone</span>
          <span>${escHtml(project.next_milestone || '—')}</span>
        </div>
        <div class="project-card-row">
          <span class="label">Due</span>
          <span>${dueDate}</span>
        </div>
        <div class="project-card-row">
          <span class="label">Health</span>
          <span>${project.health_score || 0}%</span>
        </div>
        ${approvalBadge}
      </div>
    </div>`;
}

// ===== LEVEL 3: Detail =====
function loadProjectDetail(project) {
  // Header
  document.getElementById('detail-project-name').innerText = project.name || 'Untitled';
  const statusEl = document.getElementById('detail-project-status');
  const status = project.review_status || 'PENDING';
  statusEl.innerText = status;
  statusEl.className = `status-badge status-${status.toLowerCase()}`;
  document.getElementById('detail-project-client').innerText = project.client || '';
  document.getElementById('detail-health-score').innerText = `${project.health_score || 0}%`;

  // Show AI Strategy button and Export button
  const aiBtn = document.getElementById('btn-run-ai');
  if (aiBtn) aiBtn.style.display = 'inline-flex';
  const exportBtn = document.getElementById('btn-export');
  if (exportBtn) exportBtn.style.display = 'inline-flex';

  // Overview sub-tab
  renderDetailOverview(project);

  // Load async data for other tabs
  loadDocuments(project.id);
  loadTasks(project.id);
  loadDecisions(project.id);
  loadTimeline(project.id);

  // Reset to overview tab
  switchDetailTab('overview');
}

function renderDetailOverview(project) {
  document.getElementById('d-executive-summary').innerText =
    project.executive_summary || 'Awaiting Director Agent synthesis…';

  // Risks
  const risks = safeParse(project.risks_json);
  const riskEl = document.getElementById('d-risk-list');
  if (risks.length > 0) {
    riskEl.innerHTML = risks.map(r => {
      const text = typeof r === 'string' ? r : (r.item || 'Unknown Risk');
      const sev = typeof r === 'object' ? (r.severity || 'Low') : 'Low';
      return `<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border-subtle);">
        <span>${escHtml(text)}</span>
        <span class="status-badge" style="font-size:0.65rem;padding:2px 8px;">${sev}</span>
      </div>`;
    }).join('');
  }

  // Strategy pillars
  const pillars = safeParse(project.strategy_json);
  const pillarsEl = document.getElementById('d-strategy-pillars');
  if (pillars.length > 0) {
    pillarsEl.innerHTML = pillars.map(p =>
      `<div style="padding:6px 0;border-bottom:1px solid var(--border-subtle);font-size:0.88rem;">${escHtml(p)}</div>`
    ).join('');
  }

  // Budget
  const cap = project.budget_cap || 0;
  const spent = project.budget_spent || 0;
  const remaining = Math.max(cap - spent, 0);
  document.getElementById('d-budget-cap').innerText = `$${formatNum(cap)}`;
  document.getElementById('d-budget-spent').innerText = `$${formatNum(spent)}`;
  document.getElementById('d-budget-remaining').innerText = `$${formatNum(remaining)}`;
  const pct = cap > 0 ? Math.min((spent / cap) * 100, 100) : 0;
  document.getElementById('d-budget-bar').style.width = `${pct}%`;

  // Milestone
  const milestoneEl = document.getElementById('d-next-milestone');
  if (project.next_milestone) {
    milestoneEl.innerHTML = `
      <div class="milestone-name">${escHtml(project.next_milestone)}</div>
      <div class="milestone-stage">Stage: ${escHtml(project.stage || 'Strategy')}</div>`;
  }

  // Blockers
  const blockerEl = document.getElementById('d-blockers');
  if (project.blocker_summary) {
    blockerEl.innerHTML = `<div style="color:var(--accent-amber);font-size:0.88rem;">${escHtml(project.blocker_summary)}</div>`;
  }
}

// --- Load sub-tab data ---
let _currentDocs = [];  // Cache for doc viewer
let _currentTasks = []; // Cache for task CRUD
let _currentDocId = null;

async function loadDocuments(projectId) {
  try {
    const res = await fetch(`${API_BASE}/founder/project/${projectId}`);
    if (!res.ok) return;
    const data = await res.json();
    const docs = data.documents || [];
    _currentDocs = docs;
    const el = document.getElementById('d-documents-list');
    if (docs.length === 0) {
      el.innerHTML = '<div class="empty-state"><div class="empty-icon">📄</div><p>No documents generated yet</p></div>';
      return;
    }
    el.innerHTML = docs.map(d => `
      <div class="doc-row" onclick="openDocViewer(${d.id})">
        <div>
          <div class="doc-name">${escHtml(d.name)}</div>
          <div class="doc-meta">${escHtml(d.category || 'General')}</div>
        </div>
        <div class="doc-version">v${d.version || 1}</div>
      </div>
    `).join('');
  } catch (e) { console.warn('loadDocuments:', e.message); }
}

async function loadTasks(projectId) {
  try {
    const res = await fetch(`${API_BASE}/tasks/`);
    if (!res.ok) return;
    const allTasks = await res.json();
    const tasks = allTasks.filter(t => t.project_id === projectId);
    _currentTasks = tasks;
    renderTasksList(tasks);
  } catch (e) { console.warn('loadTasks:', e.message); }
}

function renderTasksList(tasks) {
  const el = document.getElementById('d-tasks-list');
  if (tasks.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">☐</div><p>No tasks yet</p></div>';
    return;
  }
  el.innerHTML = tasks.map(t => {
    const isDone = t.status === 'Done';
    const prioClass = (t.priority || 'Normal').toLowerCase();
    return `
      <div class="task-item" data-task-id="${t.id}">
        <button class="task-toggle ${isDone ? 'done' : ''}" onclick="toggleTask(${t.id}, '${isDone ? 'Todo' : 'Done'}')">${isDone ? '✓' : ''}</button>
        <span class="task-title ${isDone ? 'done' : ''}">${escHtml(t.title)}</span>
        <span class="task-priority ${prioClass}">${t.priority || 'Normal'}</span>
        <button class="task-delete" onclick="deleteTask(${t.id})">✕</button>
      </div>`;
  }).join('');
}

async function loadDecisions(projectId) {
  try {
    const res = await fetch(`${API_BASE}/founder/project/${projectId}/workflow`);
    if (!res.ok) return;
    const data = await res.json();
    const steps = (data.steps || []).filter(s =>
      ['decision_gate', 'approval_gate'].includes(s.step_type)
    );
    const el = document.getElementById('d-decisions-list');
    if (steps.length === 0) return;
    el.innerHTML = steps.map(s => `
      <div class="decision-item">
        <div class="decision-agent">${escHtml(s.agent)}</div>
        <div class="decision-title">${escHtml(s.title)}</div>
        <div class="decision-status ${s.status}">${s.status}${s.chosen_option ? ': ' + escHtml(s.chosen_option) : ''}</div>
      </div>
    `).join('');
  } catch (e) { console.warn('loadDecisions:', e.message); }
}

async function loadTimeline(projectId) {
  try {
    const res = await fetch(`${API_BASE}/logs/?limit=50`);
    if (!res.ok) return;
    const allLogs = await res.json();
    const logs = allLogs.filter(l => l.project_id === projectId);
    const el = document.getElementById('d-timeline-list');
    if (logs.length === 0) return;
    el.innerHTML = logs.map(l => {
      const time = new Date(l.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      return `
        <div class="timeline-item">
          <span class="timeline-time">${time}</span>
          <span class="timeline-agent">${escHtml(l.agent_name)}</span>
          <span class="timeline-message">${escHtml(l.message)}</span>
        </div>`;
    }).join('');
  } catch (e) { console.warn('loadTimeline:', e.message); }
}

// ===== Detail Sub-Tabs =====
function switchDetailTab(tabName) {
  // Hide all detail views
  document.querySelectorAll('.detail-view').forEach(el => {
    el.style.display = 'none';
    el.classList.remove('active');
  });

  // Deactivate all tab buttons
  document.querySelectorAll('.detail-tab').forEach(el => el.classList.remove('active'));

  // Show target
  const view = document.getElementById(`detail-${tabName}`);
  if (view) {
    view.style.display = 'block';
    view.classList.add('active');
  }

  // Activate button
  document.querySelectorAll('.detail-tab').forEach(el => {
    if (el.textContent.toLowerCase().includes(tabName)) el.classList.add('active');
  });

  // Update sidebar active state
  const sidebarItems = document.querySelectorAll('#sidebar-nav .nav-item');
  sidebarItems.forEach(el => {
    el.classList.remove('active');
    const text = el.textContent.toLowerCase().trim();
    if (text.includes(tabName)) el.classList.add('active');
  });
}

// ===== Utilities =====
function safeParse(jsonStr) {
  if (!jsonStr) return [];
  try {
    const parsed = JSON.parse(jsonStr);
    if (Array.isArray(parsed)) return parsed;
    if (typeof parsed === 'object' && parsed !== null) return Object.values(parsed);
    return [];
  } catch { return []; }
}

function escHtml(str) {
  if (str === null || str === undefined) return '';
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}

function escAttr(str) {
  return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function formatNum(n) {
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

// ===== Init =====
navigateTo('categories');

// ===== New Project Modal =====
function openNewProjectModal() {
  document.getElementById('new-project-modal').style.display = 'flex';
  document.getElementById('np-name').focus();
}

function closeNewProjectModal() {
  document.getElementById('new-project-modal').style.display = 'none';
  document.getElementById('new-project-form').reset();
}

async function handleNewProject(event) {
  event.preventDefault();
  const btn = document.getElementById('np-submit-btn');
  btn.disabled = true;
  btn.textContent = 'Creating…';

  const payload = {
    name: document.getElementById('np-name').value.trim(),
    category: document.getElementById('np-category').value,
    client: document.getElementById('np-client').value.trim(),
    client_brief: document.getElementById('np-brief').value.trim(),
    budget_cap: parseInt(document.getElementById('np-budget').value) || 10000,
    stage: document.getElementById('np-stage').value,
  };

  try {
    const res = await fetch(`${API_BASE}/founder/project`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const result = await res.json();

    closeNewProjectModal();

    // Navigate to the new project's category, then to the project itself
    const slug = payload.category.toLowerCase().replace(/\s+/g, '-');
    navigateTo('projects', { name: payload.category, slug });
  } catch (e) {
    console.error('Failed to create project:', e);
    alert('Failed to create project: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Create Project';
  }
}

// ===== AI Strategy Runner =====
async function runAIStrategy() {
  if (!currentProject || !currentProject.id) {
    alert('No project selected.');
    return;
  }

  const overlay = document.getElementById('ai-loading-overlay');
  const aiBtn = document.getElementById('btn-run-ai');
  overlay.style.display = 'flex';
  aiBtn.disabled = true;

  try {
    document.getElementById('ai-loading-msg').textContent = 'Analyzing brief and generating strategic directions…';

    const res = await fetch(`${API_BASE}/founder/project/${currentProject.id}/run-strategy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const result = await res.json();

    document.getElementById('ai-loading-msg').textContent = 'Strategy generated! Reloading project data…';

    // Reload project data to show AI-generated content
    const projectRes = await fetch(`${API_BASE}/founder/project/${currentProject.id}`);
    if (projectRes.ok) {
      const updatedProject = await projectRes.json();
      currentProject = updatedProject;
      loadProjectDetail(updatedProject);
    }

    overlay.style.display = 'none';
  } catch (e) {
    console.error('AI Strategy failed:', e);
    overlay.style.display = 'none';
    alert('AI Strategy generation failed: ' + e.message);
  } finally {
    aiBtn.disabled = false;
  }
}

// Close modals on escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeNewProjectModal();
    closeDocViewer();
    closeAddTaskModal();
    document.getElementById('ai-loading-overlay').style.display = 'none';
  }
});

// ===== Document Viewer/Editor =====
function openDocViewer(docId) {
  const doc = _currentDocs.find(d => d.id === docId);
  if (!doc) return;
  _currentDocId = docId;
  document.getElementById('doc-viewer-title').textContent = doc.name;
  document.getElementById('doc-viewer-category').textContent = doc.category || 'General';
  document.getElementById('doc-viewer-body').innerHTML = doc.content || '<p>No content yet. Start writing…</p>';
  document.getElementById('doc-viewer-version').textContent = `v${doc.version || 1}`;
  document.getElementById('doc-viewer-modal').style.display = 'flex';
}

function closeDocViewer() {
  document.getElementById('doc-viewer-modal').style.display = 'none';
  _currentDocId = null;
}

async function saveDocument() {
  if (!_currentDocId) return;
  const content = document.getElementById('doc-viewer-body').innerHTML;
  try {
    const res = await fetch(`${API_BASE}/documents/${_currentDocId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    closeDocViewer();
    // Reload documents
    if (currentProject) loadDocuments(currentProject.id);
  } catch (e) {
    console.error('Save document failed:', e);
    alert('Failed to save: ' + e.message);
  }
}

// ===== Task CRUD =====
async function toggleTask(taskId, newStatus) {
  try {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    // Update local cache and re-render
    const task = _currentTasks.find(t => t.id === taskId);
    if (task) task.status = newStatus;
    renderTasksList(_currentTasks);
  } catch (e) {
    console.error('Toggle task failed:', e);
  }
}

async function deleteTask(taskId) {
  if (!confirm('Delete this task?')) return;
  try {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    _currentTasks = _currentTasks.filter(t => t.id !== taskId);
    renderTasksList(_currentTasks);
  } catch (e) {
    console.error('Delete task failed:', e);
  }
}

function openAddTaskModal() {
  document.getElementById('add-task-modal').style.display = 'flex';
  document.getElementById('task-title').focus();
}

function closeAddTaskModal() {
  document.getElementById('add-task-modal').style.display = 'none';
  document.getElementById('add-task-form').reset();
}

async function handleAddTask(event) {
  event.preventDefault();
  if (!currentProject) return;

  const payload = {
    title: document.getElementById('task-title').value.trim(),
    priority: document.getElementById('task-priority').value,
    status: 'Todo',
    project_id: currentProject.id,
  };

  try {
    const res = await fetch(`${API_BASE}/tasks/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const newTask = await res.json();
    _currentTasks.push(newTask);
    renderTasksList(_currentTasks);
    closeAddTaskModal();
  } catch (e) {
    console.error('Create task failed:', e);
    alert('Failed to create task: ' + e.message);
  }
}

// ===== Export =====
function exportProject() {
  if (!currentProject || !currentProject.id) return;
  window.open(`${API_BASE}/founder/project/${currentProject.id}/export`, '_blank');
}
