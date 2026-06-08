
'use strict';

// ── URL Param ─────────────────────────────────────────────────────────────
const ticketId = new URLSearchParams(window.location.search).get('id');

// ── DOM refs ──────────────────────────────────────────────────────────────
const loadingView   = document.getElementById('loading-view');
const errorView     = document.getElementById('error-view');
const mainContent   = document.getElementById('main-content');

const navTicketId   = document.getElementById('nav-ticket-id');
const titleEl       = document.getElementById('ticket-id-title');
const subjectSub    = document.getElementById('ticket-subject-sub');
const statusBadge   = document.getElementById('status-badge');

const detailName    = document.getElementById('detail-name');
const detailEmail   = document.getElementById('detail-email');
const detailSubject = document.getElementById('detail-subject');
const detailDesc    = document.getElementById('detail-description');
const descContainer = document.getElementById('desc-container');
const detailCreated = document.getElementById('detail-created');
const detailUpdated = document.getElementById('detail-updated');

const statusSelect  = document.getElementById('status-select');
const noteInput     = document.getElementById('note-input');
const updateBtn     = document.getElementById('update-btn');

const notesList     = document.getElementById('notes-list');
const notesEmpty    = document.getElementById('notes-empty');
const notesCount    = document.getElementById('notes-count');

const toast         = document.getElementById('toast');

// ── Helpers ───────────────────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

function formatDate(isoStr) {
  if (!isoStr) return '—';
  return new Date(isoStr).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

function badgeClass(status) {
  switch (status) {
    case 'Open':        return 'badge-open';
    case 'In Progress': return 'badge-progress';
    case 'Closed':      return 'badge-closed';
    default:            return 'badge-open';
  }
}

function showToast(msg = '✓ Updated successfully', isError = false) {
  toast.textContent = msg;
  toast.className = `fixed top-5 right-5 z-50 px-5 py-3 rounded-xl glass border text-sm font-medium shadow-lg ${
    isError
      ? 'border-red-500/30 bg-red-500/10 text-red-400'
      : 'border-green-500/30 bg-green-500/10 text-green-400'
  }`;
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 3000);
}

// ── Render Notes ──────────────────────────────────────────────────────────
function renderNotes(notes) {
  notesList.innerHTML = '';
  if (!notes || notes.length === 0) {
    notesEmpty.classList.remove('hidden');
    notesCount.textContent = '0 notes';
    return;
  }
  notesEmpty.classList.add('hidden');
  notesCount.textContent = `${notes.length} note${notes.length !== 1 ? 's' : ''}`;

  notes.forEach(note => {
    const div = document.createElement('div');
    div.className = 'note-item glass rounded-xl p-4 space-y-2';
    div.innerHTML = `
      <p class="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap">${escapeHtml(note.note_text)}</p>
      <p class="text-slate-600 text-xs">${formatDate(note.created_at)}</p>
    `;
    notesList.appendChild(div);
  });
}

// ── Load Ticket ───────────────────────────────────────────────────────────
async function loadTicket() {
  if (!ticketId || isNaN(Number(ticketId))) {
    loadingView.classList.add('hidden');
    errorView.classList.remove('hidden');
    return;
  }

  try {
    const res = await fetch(`/api/tickets/${ticketId}`);
    if (res.status === 404) throw new Error('not_found');
    if (!res.ok) throw new Error(`api_error_${res.status}`);

    const ticket = await res.json();
    populatePage(ticket);

  } catch (err) {
    loadingView.classList.add('hidden');
    errorView.classList.remove('hidden');
  }
}

function populatePage(ticket) {
  // Nav breadcrumb
  navTicketId.textContent = ticket.ticket_id;
  document.title = `${ticket.ticket_id} — Datastraw CRM`;

  // Title row
  titleEl.textContent    = ticket.ticket_id;
  subjectSub.textContent = ticket.subject;

  // Status badge
  statusBadge.textContent = ticket.status;
  statusBadge.className   = `text-xs font-semibold px-3 py-1 rounded-full ${badgeClass(ticket.status)}`;

  // Detail fields
  detailName.textContent    = ticket.customer_name;
  detailEmail.textContent   = ticket.customer_email;
  detailSubject.textContent = ticket.subject;

  if (ticket.description) {
    detailDesc.textContent = ticket.description;
  } else {
    descContainer.classList.add('hidden');
  }

  detailCreated.textContent = formatDate(ticket.created_at);
  detailUpdated.textContent = formatDate(ticket.updated_at);

  // Pre-select current status in dropdown
  statusSelect.value = ticket.status;

  // Notes
  renderNotes(ticket.notes);

  // Show content
  loadingView.classList.add('hidden');
  mainContent.classList.remove('hidden');
}

// ── Update Ticket ─────────────────────────────────────────────────────────
updateBtn.addEventListener('click', async () => {
  const payload = {
    status:    statusSelect.value,
    note_text: noteInput.value.trim() || null,
  };

  updateBtn.disabled = true;
  updateBtn.innerHTML = `
    <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
    </svg>
    Saving…
  `;

  try {
    const res = await fetch(`/api/tickets/${ticketId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Error ${res.status}`);
    }

    // Clear note input and reload ticket data
    noteInput.value = '';
    showToast('✓ Ticket updated successfully');
    await loadTicket();   // re-fetch to reflect updated_at + notes

  } catch (err) {
    showToast(err.message || 'Failed to update ticket.', true);
  } finally {
    updateBtn.disabled = false;
    updateBtn.innerHTML = `
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
      Save Changes
    `;
  }
});

// ── Init ──────────────────────────────────────────────────────────────────
loadTicket();
