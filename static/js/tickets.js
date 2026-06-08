
'use strict';

// ── State ─────────────────────────────────────────────────────────────────
let activeStatus = 'All';
let debounceTimer = null;
let allTickets = [];   // full cache for client-side stat counts

// ── DOM refs ──────────────────────────────────────────────────────────────
const searchInput   = document.getElementById('search-input');
const tableBody     = document.getElementById('ticket-table-body');
const emptyState    = document.getElementById('empty-state');
const loadingState  = document.getElementById('loading-state');
const resultCount   = document.getElementById('result-count');

const countTotal    = document.getElementById('count-total');
const countOpen     = document.getElementById('count-open');
const countProgress = document.getElementById('count-progress');
const countClosed   = document.getElementById('count-closed');

// ── Helpers ───────────────────────────────────────────────────────────────
function badgeClass(status) {
  switch (status) {
    case 'Open':        return 'badge-open';
    case 'In Progress': return 'badge-progress';
    case 'Closed':      return 'badge-closed';
    default:            return 'badge-open';
  }
}

function formatDate(isoStr) {
  if (!isoStr) return '—';
  return new Date(isoStr).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric'
  });
}

// ── Render ────────────────────────────────────────────────────────────────
function renderTable(tickets) {
  tableBody.innerHTML = '';
  loadingState.classList.add('hidden');

  if (tickets.length === 0) {
    emptyState.classList.remove('hidden');
    resultCount.textContent = '';
    return;
  }
  emptyState.classList.add('hidden');
  resultCount.textContent = `Showing ${tickets.length} ticket${tickets.length !== 1 ? 's' : ''}`;

  tickets.forEach(t => {
    const tr = document.createElement('tr');
    tr.className = 'ticket-row border-b border-white/5';
    tr.setAttribute('data-ticket-id', t.id);
    tr.innerHTML = `
      <td class="px-6 py-4">
        <span class="font-mono text-brand-500 font-semibold text-sm">${t.ticket_id}</span>
      </td>
      <td class="px-6 py-4">
        <p class="text-white font-medium text-sm truncate max-w-[140px]">${escapeHtml(t.customer_name)}</p>
        <p class="text-slate-500 text-xs truncate max-w-[140px]">${escapeHtml(t.customer_email)}</p>
      </td>
      <td class="px-6 py-4 hidden md:table-cell">
        <span class="text-slate-300 text-sm truncate max-w-[220px] block">${escapeHtml(t.subject)}</span>
      </td>
      <td class="px-6 py-4">
        <span class="${badgeClass(t.status)} text-xs font-semibold px-3 py-1 rounded-full">${escapeHtml(t.status)}</span>
      </td>
      <td class="px-6 py-4 hidden sm:table-cell text-slate-400 text-xs">${formatDate(t.created_at)}</td>
    `;
    tr.addEventListener('click', () => {
      window.location.href = `/detail?id=${t.id}`;
    });
    tableBody.appendChild(tr);
  });
}

function updateStats(tickets) {
  const open     = tickets.filter(t => t.status === 'Open').length;
  const progress = tickets.filter(t => t.status === 'In Progress').length;
  const closed   = tickets.filter(t => t.status === 'Closed').length;

  countTotal.textContent    = tickets.length;
  countOpen.textContent     = open;
  countProgress.textContent = progress;
  countClosed.textContent   = closed;
}

// ── Escape HTML ───────────────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

// ── API fetch ─────────────────────────────────────────────────────────────
async function fetchTickets() {
  const params = new URLSearchParams();
  const search = searchInput.value.trim();
  if (search) params.set('search', search);
  if (activeStatus !== 'All') params.set('status', activeStatus);

  try {
    const res = await fetch(`/api/tickets?${params}`);
    if (!res.ok) throw new Error(`API error ${res.status}`);
    const data = await res.json();
    renderTable(data);

    // Stats always based on unfiltered data when no search
    if (!search && activeStatus === 'All') {
      allTickets = data;
      updateStats(data);
    } else {
      // Fetch totals separately for stat counters
      const allRes = await fetch('/api/tickets');
      const allData = await allRes.json();
      updateStats(allData);
    }
  } catch (err) {
    console.error('Failed to fetch tickets:', err);
    tableBody.innerHTML = `<tr><td colspan="5" class="px-6 py-10 text-center text-red-400 text-sm">Failed to load tickets. Please refresh.</td></tr>`;
    loadingState.classList.add('hidden');
  }
}

// ── Filter tabs ───────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeStatus = btn.dataset.status;
    fetchTickets();
  });
});

// ── Debounced search ──────────────────────────────────────────────────────
searchInput.addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(fetchTickets, 300);
});

// ── Init ──────────────────────────────────────────────────────────────────
fetchTickets();
