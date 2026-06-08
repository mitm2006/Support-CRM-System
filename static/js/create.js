
'use strict';

const form       = document.getElementById('create-form');
const submitBtn  = document.getElementById('submit-btn');
const formError  = document.getElementById('form-error');
const errorText  = document.getElementById('form-error-text');

// Field refs
const nameInput  = document.getElementById('customer-name');
const emailInput = document.getElementById('customer-email');
const subjectInput = document.getElementById('subject');
const descInput  = document.getElementById('description');

// Error message refs
const errName    = document.getElementById('err-name');
const errEmail   = document.getElementById('err-email');
const errSubject = document.getElementById('err-subject');

// ── Helpers ───────────────────────────────────────────────────────────────
function showFieldError(input, errEl, message) {
  input.classList.add('error');
  errEl.textContent = message;
  errEl.classList.remove('hidden');
}

function clearFieldError(input, errEl) {
  input.classList.remove('error');
  errEl.classList.add('hidden');
}

function showFormError(message) {
  errorText.textContent = message;
  formError.style.display = 'flex';
}

function hideFormError() {
  formError.style.display = 'none';
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

// ── Inline validation on blur ─────────────────────────────────────────────
nameInput.addEventListener('blur', () => {
  if (!nameInput.value.trim()) showFieldError(nameInput, errName, 'Name is required.');
  else clearFieldError(nameInput, errName);
});
emailInput.addEventListener('blur', () => {
  if (!emailInput.value.trim()) showFieldError(emailInput, errEmail, 'Email is required.');
  else if (!isValidEmail(emailInput.value)) showFieldError(emailInput, errEmail, 'Enter a valid email address.');
  else clearFieldError(emailInput, errEmail);
});
subjectInput.addEventListener('blur', () => {
  if (!subjectInput.value.trim()) showFieldError(subjectInput, errSubject, 'Subject is required.');
  else clearFieldError(subjectInput, errSubject);
});

// Clear on input
[nameInput, emailInput, subjectInput].forEach((input, i) => {
  const errs = [errName, errEmail, errSubject];
  input.addEventListener('input', () => clearFieldError(input, errs[i]));
});

// ── Form submit ───────────────────────────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  hideFormError();

  // Validate all
  let valid = true;
  if (!nameInput.value.trim()) { showFieldError(nameInput, errName, 'Name is required.'); valid = false; }
  if (!emailInput.value.trim()) { showFieldError(emailInput, errEmail, 'Email is required.'); valid = false; }
  else if (!isValidEmail(emailInput.value)) { showFieldError(emailInput, errEmail, 'Enter a valid email address.'); valid = false; }
  if (!subjectInput.value.trim()) { showFieldError(subjectInput, errSubject, 'Subject is required.'); valid = false; }

  if (!valid) return;

  // Show loading state
  submitBtn.disabled = true;
  submitBtn.innerHTML = `
    <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
    </svg>
    Submitting…
  `;

  try {
    const payload = {
      customer_name:  nameInput.value.trim(),
      customer_email: emailInput.value.trim(),
      subject:        subjectInput.value.trim(),
      description:    descInput.value.trim() || null,
    };

    const res = await fetch('/api/tickets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Server error (${res.status})`);
    }

    const data = await res.json();
    // Redirect to detail page using the integer id
    window.location.href = `/detail?id=${data.id}`;

  } catch (err) {
    showFormError(err.message || 'Something went wrong. Please try again.');
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
      Submit Ticket
    `;
  }
});
