// E-Power Web Application JavaScript

function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span style="font-size: 1.2rem;">${type === 'success' ? '✔' : '✖'}</span>
    <div style="font-size: 0.9rem; font-weight: 500;">${message}</div>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Meter Reading Live Calculation
function setupMeterReadingPage() {
  const cboCustomer = document.getElementById('cboCustomer');
  const txtPrev = document.getElementById('txtPreviousReading');
  const txtCurr = document.getElementById('txtCurrentReading');
  const rbTiered = document.getElementById('rbTiered');
  const rbFlat = document.getElementById('rbFlat');
  const numFlatRate = document.getElementById('numFlatRate');
  const btnSave = document.getElementById('btnSaveReading');

  if (!cboCustomer || !txtCurr) return;

  // Auto-fetch latest reading when customer changes
  cboCustomer.addEventListener('change', async function() {
    const custId = this.value;
    if (!custId) {
      txtPrev.value = '0.00';
      recalc();
      return;
    }

    try {
      const res = await fetch(`/api/customers/${custId}/latest-reading`);
      const data = await res.json();
      txtPrev.value = parseFloat(data.previous_reading || 0).toFixed(2);
      recalc();
    } catch (err) {
      console.error(err);
      showToast('កំហុសក្នុងការទាញយកលេខកុងទ័រចាស់', 'danger');
    }
  });

  // Recalculate on current reading change or rate toggle
  txtCurr.addEventListener('input', recalc);
  if (rbTiered) rbTiered.addEventListener('change', recalc);
  if (rbFlat) rbFlat.addEventListener('change', recalc);
  
  if (numFlatRate) {
    numFlatRate.addEventListener('input', function() {
      if (rbFlat) rbFlat.checked = true;
      recalc();
    });
    numFlatRate.addEventListener('focus', function() {
      if (rbFlat) rbFlat.checked = true;
      recalc();
    });
  }

  function recalc() {
    const prev = parseFloat(txtPrev.value) || 0;
    const currStr = txtCurr.value.trim();
    const lblUsage = document.getElementById('lblUsage');
    const lblTier1 = document.getElementById('lblTier1');
    const lblTier2 = document.getElementById('lblTier2');
    const lblTotal = document.getElementById('lblTotal');
    const lblWarning = document.getElementById('lblWarning');

    if (!currStr) {
      if (lblUsage) lblUsage.textContent = '⚡ ថាមពលប្រើប្រាស់: 0.00 kWh';
      if (lblTier1) lblTier1.textContent = '• កាំទី ១ (1 - 50 kWh): 0 kWh × 400៛ = 0 ៛';
      if (lblTier2) lblTier2.textContent = '• កាំទី ២ (> 50 kWh): 0 kWh × 600៛ = 0 ៛';
      if (lblTotal) lblTotal.textContent = '0 ៛ (~$0.00)';
      if (lblWarning) lblWarning.textContent = '';
      if (btnSave) btnSave.disabled = true;
      return;
    }

    const curr = parseFloat(currStr);
    if (isNaN(curr) || curr < prev) {
      if (lblWarning) lblWarning.textContent = '⚠️ លេខកុងទ័រថ្មី មិនអាចតូចជាងលេខកុងទ័រចាស់បានទេ!';
      if (lblUsage) lblUsage.textContent = '⚡ ថាមពលប្រើប្រាស់: មិនត្រឹមត្រូវ (Invalid)';
      if (lblTotal) lblTotal.textContent = '0 ៛';
      if (btnSave) btnSave.disabled = true;
      return;
    }

    if (lblWarning) lblWarning.textContent = '';
    if (btnSave) btnSave.disabled = false;

    const usage = curr - prev;
    if (lblUsage) lblUsage.textContent = `⚡ ថាមពលប្រើប្រាស់: ${usage.toFixed(2)} kWh`;

    const isTiered = rbTiered ? rbTiered.checked : false;
    let total = 0;
    let t1KWh = 0, t1Cost = 0, t2KWh = 0, t2Cost = 0;

    if (isTiered) {
      if (usage <= 50) {
        t1KWh = usage;
        t1Cost = usage * 400;
        total = t1Cost;
      } else {
        t1KWh = 50;
        t1Cost = 50 * 400;
        t2KWh = usage - 50;
        t2Cost = t2KWh * 600;
        total = t1Cost + t2Cost;
      }
      if (lblTier1) lblTier1.textContent = `• កាំទី ១ (1 - 50 kWh): ${t1KWh.toFixed(1)} kWh × 400៛ = ${t1Cost.toLocaleString()} ៛`;
      if (lblTier2) lblTier2.textContent = `• កាំទី ២ (> 50 kWh): ${t2KWh.toFixed(1)} kWh × 600៛ = ${t2Cost.toLocaleString()} ៛`;
    } else {
      const rate = numFlatRate ? parseFloat(numFlatRate.value) || 800 : 800;
      total = usage * rate;
      if (lblTier1) lblTier1.textContent = `• តម្លៃថេរ (Flat Rate): ${usage.toFixed(1)} kWh × ${rate.toLocaleString()}៛ = ${total.toLocaleString()} ៛`;
      if (lblTier2) lblTier2.textContent = '• មិនគិតតាមកាំតម្លៃ (Flat Tariff Policy)';
    }

    const usd = (total / 4100).toFixed(2);
    if (lblTotal) lblTotal.textContent = `${total.toLocaleString()} ៛ (~$${usd})`;
  }

  // Handle Form Submit
  const form = document.getElementById('meterReadingForm');
  if (form) {
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      const custId = cboCustomer.value;
      const billingMonth = document.getElementById('txtBillingMonth').value;
      const prev = parseFloat(txtPrev.value) || 0;
      const curr = parseFloat(txtCurr.value) || 0;
      const isTiered = rbTiered ? rbTiered.checked : false;
      const flatRate = numFlatRate ? parseFloat(numFlatRate.value) || 800 : 800;

      if (!custId) {
        showToast('សូមជ្រើសរើសអតិថិជន!', 'danger');
        return;
      }

      if (curr < prev) {
        showToast('លេខកុងទ័រថ្មីមិនអាចតូចជាងលេខកុងទ័រចាស់បានទេ!', 'danger');
        return;
      }

      btnSave.disabled = true;
      btnSave.textContent = 'កំពុងរក្សាទុក...';

      try {
        const res = await fetch('/api/meter-reading', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            customer_id: custId,
            billing_month: billingMonth,
            previous_reading: prev,
            current_reading: curr,
            use_tiered: isTiered,
            flat_rate: flatRate
          })
        });
        const data = await res.json();

        if (data.success) {
          showToast(data.message, 'success');
          // Offer print
          if (confirm(`${data.message}\n\nតើអ្នកចង់មើល ឬបោះពុម្ពវិក័យបត្រនេះឥឡូវនេះទេ?`)) {
            window.open(`/invoice/${data.invoice_id}/print`, '_blank');
          }
          // Refresh page to show updated history
          setTimeout(() => window.location.reload(), 1000);
        } else {
          showToast(data.error || 'បរាជ័យក្នុងការកត់ត្រា', 'danger');
          btnSave.disabled = false;
          btnSave.textContent = '💾 កត់ត្រា & បង្កើតវិក័យបត្រ';
        }
      } catch (err) {
        showToast('កំហុសម៉ាស៊ីនបម្រើ (Server Error)', 'danger');
        btnSave.disabled = false;
        btnSave.textContent = '💾 កត់ត្រា & បង្កើតវិក័យបត្រ';
      }
    });
  }

  // Trigger initial fetch if customer already selected
  if (cboCustomer.value) {
    cboCustomer.dispatchEvent(new Event('change'));
  }
}

// Payment Function
async function payInvoice(invoiceId, customerName, totalAmount) {
  if (!confirm(`តើអ្នកពិតជាចង់ទទួលការបង់ប្រាក់សម្រាប់វិក័យបត្រ INV-${String(invoiceId).padStart(5, '0')} មែនទេ?\n\n• អតិថិជន: ${customerName}\n• ទឹកប្រាក់: ${totalAmount.toLocaleString()} ៛`)) {
    return;
  }

  try {
    const res = await fetch(`/api/invoices/${invoiceId}/pay`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      if (confirm('ការទូទាត់ជោគជ័យ! តើអ្នកចង់បោះពុម្ពបង្កាន់ដៃទទួលប្រាក់ (Receipt) ដែរឬទេ?')) {
        window.open(`/invoice/${invoiceId}/print`, '_blank');
      }
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast(data.message || 'បរាជ័យក្នុងការទូទាត់', 'danger');
    }
  } catch (err) {
    showToast('កំហុសម៉ាស៊ីនបម្រើ (Server Error)', 'danger');
  }
}

// Customer Modal Management (Tabs, Photo, Datalists, & Template Fields)
function switchCustomerTab(tab) {
  const btnGen = document.getElementById('tabBtnGen');
  const btnUsage = document.getElementById('tabBtnUsage');
  const contentGen = document.getElementById('tabContentGen');
  const contentUsage = document.getElementById('tabContentUsage');

  if (!btnGen || !btnUsage || !contentGen || !contentUsage) return;

  if (tab === 'gen') {
    btnGen.style.backgroundColor = '#ffffff';
    btnGen.style.borderTop = '3px solid #2563eb';
    btnGen.style.color = '#0f172a';
    btnGen.classList.add('active');

    btnUsage.style.backgroundColor = 'transparent';
    btnUsage.style.borderTop = 'none';
    btnUsage.style.color = '#64748b';
    btnUsage.classList.remove('active');

    contentGen.style.display = 'block';
    contentUsage.style.display = 'none';
  } else {
    btnUsage.style.backgroundColor = '#ffffff';
    btnUsage.style.borderTop = '3px solid #2563eb';
    btnUsage.style.color = '#0f172a';
    btnUsage.classList.add('active');

    btnGen.style.backgroundColor = 'transparent';
    btnGen.style.borderTop = 'none';
    btnGen.style.color = '#64748b';
    btnGen.classList.remove('active');

    contentUsage.style.display = 'block';
    contentGen.style.display = 'none';
  }
}

function toggleDobInput(enabled) {
  const dobInput = document.getElementById('txtDob');
  const pickerDob = document.getElementById('pickerDob');
  if (!enabled) {
    if (dobInput) dobInput.value = '';
    if (pickerDob) pickerDob.value = '';
  } else {
    if (dobInput) dobInput.focus();
  }
}

function onDobTextInput(e) {
  const chkDob = document.getElementById('chkEnableDob');
  if (chkDob && !chkDob.checked) {
    chkDob.checked = true;
    const dobInput = document.getElementById('txtDob');
    if (dobInput) dobInput.disabled = false;
    const btnPicker = document.getElementById('btnDobPicker');
    if (btnPicker) btnPicker.disabled = false;
  }

  let v = e.target.value;
  // If deleting with backspace or delete, do not auto-insert slash
  if (e.inputType && e.inputType.startsWith('delete')) {
    syncTextToPicker(v);
    return;
  }

  // Only allow digits, slashes, and dashes
  let clean = v.replace(/[^\d\/\-]/g, '');
  // Auto-insert slashes if typing pure digits like 15081990
  const digitsOnly = clean.replace(/\D/g, '');
  if (!clean.includes('/') && !clean.includes('-')) {
    if (digitsOnly.length > 4) {
      clean = digitsOnly.slice(0, 2) + '/' + digitsOnly.slice(2, 4) + '/' + digitsOnly.slice(4, 8);
    } else if (digitsOnly.length > 2) {
      clean = digitsOnly.slice(0, 2) + '/' + digitsOnly.slice(2);
    }
  } else if (clean.length === 2 && !clean.includes('/')) {
    clean += '/';
  } else if (clean.length === 5 && clean.charAt(2) === '/' && clean.indexOf('/', 3) === -1) {
    clean += '/';
  }
  e.target.value = clean;
  syncTextToPicker(clean);
}

function syncTextToPicker(val) {
  const pickerDob = document.getElementById('pickerDob');
  if (!pickerDob) return;
  const iso = parseToIsoDate(val);
  if (iso && /^\d{4}-\d{2}-\d{2}$/.test(iso)) {
    pickerDob.value = iso;
  }
}

function openDobPicker() {
  const chkDob = document.getElementById('chkEnableDob');
  if (chkDob && !chkDob.checked) {
    chkDob.checked = true;
    toggleDobInput(true);
  }

  const dobInput = document.getElementById('txtDob');
  const pickerDob = document.getElementById('pickerDob');
  if (dobInput && dobInput.value && pickerDob) {
    const iso = parseToIsoDate(dobInput.value);
    if (iso) pickerDob.value = iso;
  }

  if (pickerDob) {
    if (typeof pickerDob.showPicker === 'function') {
      pickerDob.showPicker();
    } else {
      pickerDob.focus();
      pickerDob.click();
    }
  }
}

function onDobPickerChange(val) {
  if (!val) return;
  const parts = val.split('-');
  if (parts.length === 3) {
    const dmy = `${parts[2]}/${parts[1]}/${parts[0]}`;
    const dobInput = document.getElementById('txtDob');
    const chkDob = document.getElementById('chkEnableDob');
    if (chkDob) chkDob.checked = true;
    if (dobInput) {
      dobInput.disabled = false;
      dobInput.value = dmy;
    }
    const btnPicker = document.getElementById('btnDobPicker');
    if (btnPicker) btnPicker.disabled = false;
  }
}

function formatIsoToDmy(isoDate) {
  if (!isoDate) return '';
  const str = String(isoDate).trim();
  const parts = str.split(/[\-\/]/);
  if (parts.length === 3 && parts[0].length === 4) {
    return `${parts[2].padStart(2, '0')}/${parts[1].padStart(2, '0')}/${parts[0]}`;
  }
  return str;
}

function parseToIsoDate(val) {
  if (!val) return null;
  val = String(val).trim();
  if (!val) return null;

  // DD/MM/YYYY or DD-MM-YYYY
  const dmy = val.match(/^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$/);
  if (dmy) {
    const d = dmy[1].padStart(2, '0');
    const m = dmy[2].padStart(2, '0');
    const y = dmy[3];
    return `${y}-${m}-${d}`;
  }

  // YYYY-MM-DD
  const ymd = val.match(/^(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})$/);
  if (ymd) {
    const y = ymd[1];
    const m = ymd[2].padStart(2, '0');
    const d = ymd[3].padStart(2, '0');
    return `${y}-${m}-${d}`;
  }

  // Pure 4-digit year e.g. 1990
  if (/^\d{4}$/.test(val)) {
    return `${val}-01-01`;
  }

  return val;
}

function updateComposedAddress() {
  const house = (document.getElementById('txtHouseNo')?.value || '').trim();
  const street = (document.getElementById('txtStreetNo')?.value || '').trim();
  const village = (document.getElementById('cboVillage')?.value || '').trim();
  const commune = (document.getElementById('cboCommune')?.value || '').trim();
  const district = (document.getElementById('cboDistrict')?.value || '').trim();
  const province = (document.getElementById('cboProvince')?.value || '').trim();
  const pole = (document.getElementById('txtPoleNo')?.value || '').trim();

  const parts = [];
  if (house) parts.push(`ផ្ទះលេខ ${house}`);
  if (street) parts.push(`ផ្លូវលេខ ${street}`);
  if (village) parts.push(`ភូមិ${village.startsWith('ភូមិ') ? village.replace('ភូមិ', '') : ' ' + village}`);
  if (commune) parts.push(`ឃុំ/សង្កាត់ ${commune}`);
  if (district) parts.push(`ស្រុក/ក្រុង ${district}`);
  if (province) parts.push(`ខេត្ត/រាជធានី ${province}`);
  if (pole) parts.push(`(បង្គោល ${pole})`);

  const txtAddr = document.getElementById('txtAddress');
  if (txtAddr && !txtAddr.dataset.userEdited) {
    txtAddr.value = parts.join(', ');
  }
}

function handlePhotoUpload(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function(e) {
      const preview = document.getElementById('photoPreview');
      preview.innerHTML = `<img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">`;
      const txtPhoto = document.getElementById('txtPhotoData');
      if (txtPhoto) txtPhoto.value = e.target.result;
    };
    reader.readAsDataURL(file);
  }
}

async function openNewCustomerModal() {
  const modal = document.getElementById('customerModal');
  const title = document.getElementById('modalTitle');
  const form = document.getElementById('customerForm');
  if (!modal || !form) return;

  title.textContent = 'បន្ថែមអតិថិជន';
  form.reset();
  document.getElementById('txtCustId').value = '';
  document.getElementById('txtPhotoData').value = '';
  document.getElementById('cboTitle').value = 'លោក';
  document.getElementById('cboGender').value = 'ប្រុស';
  document.getElementById('cboIdType').value = 'អត្តសញ្ញាណប័ណ្ណ';
  document.getElementById('cboCustomerType').value = 'បុគ្គលមិនជាប់អាករ';
  document.getElementById('cboProvince').value = 'កណ្តាល';
  document.getElementById('cboDistrict').value = 'មុខកំពូល';
  document.getElementById('cboCommune').value = 'ឫស្សីជ្រោយ';
  document.getElementById('cboVillage').value = 'ឫស្សីជ្រោយ';
  document.getElementById('cboZone').value = 'តំបន់ ១';
  document.getElementById('numFamilyMembers').value = 1;
  document.getElementById('chkIsPoorFamily').checked = false;
  
  const chkDob = document.getElementById('chkEnableDob');
  if (chkDob) {
    chkDob.checked = false;
    toggleDobInput(false);
  }

  const preview = document.getElementById('photoPreview');
  if (preview) {
    preview.innerHTML = `<span style="font-size: 2.8rem; color: #cbd5e1;">👤</span>`;
  }

  // Reset manual edit flag on address
  const txtAddr = document.getElementById('txtAddress');
  if (txtAddr) delete txtAddr.dataset.userEdited;

  // Reset Tab 2 fields
  if (document.getElementById('cboPhase')) document.getElementById('cboPhase').value = '1-Phase (220V)';
  if (document.getElementById('txtPoleNo')) document.getElementById('txtPoleNo').value = '';
  if (document.getElementById('txtBoxNo')) document.getElementById('txtBoxNo').value = '';
  if (document.getElementById('cboBreaker')) document.getElementById('cboBreaker').value = '20A';
  if (document.getElementById('cboTariffType')) document.getElementById('cboTariffType').value = 'tiered';

  // Fetch next sequential code from server
  try {
    const res = await fetch('/api/customers/next-code');
    const data = await res.json();
    if (data.success && data.next_code) {
      document.getElementById('txtCustomerCode').value = data.next_code;
    } else {
      document.getElementById('txtCustomerCode').value = '004158';
    }
  } catch (e) {
    document.getElementById('txtCustomerCode').value = '004158';
  }

  updateComposedAddress();
  switchCustomerTab('gen');
  modal.classList.add('open');
}

function openCustomerModal(custData = null) {
  if (!custData) {
    openNewCustomerModal();
    return;
  }

  const modal = document.getElementById('customerModal');
  const title = document.getElementById('modalTitle');
  const form = document.getElementById('customerForm');
  if (!modal || !form) return;

  title.textContent = 'កែប្រែព័ត៌មានអតិថិជន';
  document.getElementById('txtCustId').value = custData.customer_id || '';
  document.getElementById('txtCustomerCode').value = custData.customer_code || '';
  document.getElementById('cboTitle').value = custData.title || 'លោក';
  document.getElementById('txtLastName').value = custData.last_name || '';
  document.getElementById('txtFirstName').value = custData.first_name || '';
  document.getElementById('txtLastNameEn').value = custData.last_name_en || '';
  document.getElementById('txtFirstNameEn').value = custData.first_name_en || '';
  document.getElementById('cboGender').value = custData.gender || 'ប្រុស';

  const chkDob = document.getElementById('chkEnableDob');
  const txtDob = document.getElementById('txtDob');
  const pickerDob = document.getElementById('pickerDob');
  if (custData.dob) {
    if (chkDob) chkDob.checked = true;
    if (txtDob) {
      txtDob.value = formatIsoToDmy(custData.dob);
    }
    if (pickerDob) pickerDob.value = parseToIsoDate(custData.dob) || '';
  } else {
    if (chkDob) chkDob.checked = false;
    if (txtDob) {
      txtDob.value = '';
    }
    if (pickerDob) pickerDob.value = '';
  }

  document.getElementById('txtPob').value = custData.pob || '';
  document.getElementById('txtOccupation').value = custData.occupation || '';
  document.getElementById('cboIdType').value = custData.id_type || 'អត្តសញ្ញាណប័ណ្ណ';
  document.getElementById('txtIdNumber').value = custData.id_number || '';
  document.getElementById('numFamilyMembers').value = custData.family_members || 1;
  document.getElementById('cboCustomerType').value = custData.customer_type || 'បុគ្គលមិនជាប់អាករ';
  document.getElementById('chkIsPoorFamily').checked = !!custData.is_poor_family;
  document.getElementById('txtRepresentative').value = custData.representative || '';

  document.getElementById('txtPhone').value = custData.phone_number || '';
  document.getElementById('txtAccountNumber').value = custData.account_number || '';
  document.getElementById('cboProvince').value = custData.province || 'កណ្តាល';
  document.getElementById('cboDistrict').value = custData.district || 'មុខកំពូល';
  document.getElementById('cboCommune').value = custData.commune || 'ឫស្សីជ្រោយ';
  document.getElementById('cboVillage').value = custData.village || 'ឫស្សីជ្រោយ';
  document.getElementById('cboZone').value = custData.zone || 'តំបន់ ១';
  document.getElementById('txtHouseNo').value = custData.house_no || '';
  document.getElementById('txtStreetNo').value = custData.street_no || '';

  const txtAddr = document.getElementById('txtAddress');
  if (txtAddr) {
    txtAddr.value = custData.address || '';
    txtAddr.dataset.userEdited = 'true';
  }

  // Tab 2 fields
  if (document.getElementById('cboPhase')) document.getElementById('cboPhase').value = custData.phase || '1-Phase (220V)';
  if (document.getElementById('txtPoleNo')) document.getElementById('txtPoleNo').value = custData.pole_no || '';
  if (document.getElementById('txtBoxNo')) document.getElementById('txtBoxNo').value = custData.box_no || '';
  if (document.getElementById('cboBreaker')) document.getElementById('cboBreaker').value = custData.breaker || '20A';
  if (document.getElementById('cboTariffType')) document.getElementById('cboTariffType').value = custData.tariff_type || 'tiered';

  // Photo
  const preview = document.getElementById('photoPreview');
  document.getElementById('txtPhotoData').value = '';
  if (preview) {
    if (custData.photo_path) {
      preview.innerHTML = `<img src="${custData.photo_path}" style="width: 100%; height: 100%; object-fit: cover;">`;
    } else {
      preview.innerHTML = `<span style="font-size: 2.8rem; color: #cbd5e1;">👤</span>`;
    }
  }

  switchCustomerTab('gen');
  modal.classList.add('open');
}

async function editCustomerById(id) {
  try {
    const res = await fetch(`/api/customers/${id}`);
    const data = await res.json();
    if (data.success) {
      openCustomerModal(data.customer);
    } else {
      showToast('រកមិនឃើញព័ត៌មានអតិថិជន', 'danger');
    }
  } catch (err) {
    showToast('កំហុសក្នុងការទាញយកទិន្នន័យ', 'danger');
  }
}

function closeCustomerModal() {
  const modal = document.getElementById('customerModal');
  if (modal) modal.classList.remove('open');
}

async function saveCustomerForm(e) {
  e.preventDefault();
  const id = document.getElementById('txtCustId').value;
  const lastName = (document.getElementById('txtLastName')?.value || '').trim();
  const phone = (document.getElementById('txtPhone')?.value || '').trim();

  if (!lastName) {
    switchCustomerTab('gen');
    showToast('សូមបញ្ចូល គោត្តនាម អតិថិជន!', 'danger');
    document.getElementById('txtLastName').focus();
    return;
  }

  if (!phone) {
    switchCustomerTab('gen');
    showToast('សូមបញ្ចូល លេខទូរស័ព្ទ អតិថិជន!', 'danger');
    document.getElementById('txtPhone').focus();
    return;
  }

  const rawDob = (document.getElementById('txtDob')?.value || '').trim();
  const dobVal = rawDob ? parseToIsoDate(rawDob) : null;

  const payload = {
    customer_code: (document.getElementById('txtCustomerCode')?.value || '').trim(),
    title: document.getElementById('cboTitle')?.value || 'លោក',
    last_name: lastName,
    first_name: (document.getElementById('txtFirstName')?.value || '').trim(),
    last_name_en: (document.getElementById('txtLastNameEn')?.value || '').trim(),
    first_name_en: (document.getElementById('txtFirstNameEn')?.value || '').trim(),
    gender: document.getElementById('cboGender')?.value || 'ប្រុស',
    dob: dobVal || null,
    pob: (document.getElementById('txtPob')?.value || '').trim(),
    occupation: (document.getElementById('txtOccupation')?.value || '').trim(),
    id_type: document.getElementById('cboIdType')?.value || 'អត្តសញ្ញាណប័ណ្ណ',
    id_number: (document.getElementById('txtIdNumber')?.value || '').trim(),
    family_members: parseInt(document.getElementById('numFamilyMembers')?.value) || 1,
    customer_type: document.getElementById('cboCustomerType')?.value || 'បុគ្គលមិនជាប់អាករ',
    is_poor_family: document.getElementById('chkIsPoorFamily')?.checked || false,
    representative: (document.getElementById('txtRepresentative')?.value || '').trim(),

    phone_number: phone,
    account_number: (document.getElementById('txtAccountNumber')?.value || '').trim(),
    province: (document.getElementById('cboProvince')?.value || '').trim(),
    district: (document.getElementById('cboDistrict')?.value || '').trim(),
    commune: (document.getElementById('cboCommune')?.value || '').trim(),
    village: (document.getElementById('cboVillage')?.value || '').trim(),
    zone: (document.getElementById('cboZone')?.value || '').trim(),
    house_no: (document.getElementById('txtHouseNo')?.value || '').trim(),
    street_no: (document.getElementById('txtStreetNo')?.value || '').trim(),
    address: (document.getElementById('txtAddress')?.value || '').trim(),

    phase: document.getElementById('cboPhase')?.value || '1-Phase (220V)',
    pole_no: (document.getElementById('txtPoleNo')?.value || '').trim(),
    box_no: (document.getElementById('txtBoxNo')?.value || '').trim(),
    breaker: document.getElementById('cboBreaker')?.value || '20A',
    tariff_type: document.getElementById('cboTariffType')?.value || 'tiered',

    photo_data: document.getElementById('txtPhotoData')?.value || null,
    status: true
  };

  const url = id ? `/api/customers/${id}` : '/api/customers';

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      closeCustomerModal();
      setTimeout(() => window.location.reload(), 600);
    } else {
      showToast(data.error || 'បរាជ័យក្នុងការរក្សាទុក', 'danger');
    }
  } catch (err) {
    showToast('កំហុសម៉ាស៊ីនបម្រើ', 'danger');
  }
}

async function deleteCustomer(id, name) {
  if (!confirm(`តើអ្នកពិតជាចង់លុបអតិថិជន "${name}" មែនទេ?\nការលុបនេះនឹងលុបទាំងទិន្នន័យកុងទ័រ និងវិក័យបត្រដែលពាក់ព័ន្ធទាំងអស់!`)) {
    return;
  }

  try {
    const res = await fetch(`/api/customers/${id}/delete`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      setTimeout(() => window.location.reload(), 700);
    } else {
      showToast(data.message || 'បរាជ័យក្នុងការលុប', 'danger');
    }
  } catch (err) {
    showToast('កំហុសម៉ាស៊ីនបម្រើ', 'danger');
  }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  setupMeterReadingPage();

  const custForm = document.getElementById('customerForm');
  if (custForm) {
    custForm.addEventListener('submit', saveCustomerForm);
  }

  const txtAddress = document.getElementById('txtAddress');
  if (txtAddress) {
    txtAddress.addEventListener('input', function() {
      this.dataset.userEdited = 'true';
    });
  }

  // Close modal when clicking on backdrop
  const modal = document.getElementById('customerModal');
  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        closeCustomerModal();
      }
    });
  }

  // Close modal on Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeCustomerModal();
      closeModal('modalAddUser');
      closeModal('modalEditUser');
      closeModal('modalResetPassword');
    }
  });
});

// --- User Management Functions (Admin) ---

function openAddUserModal() {
  const form = document.getElementById('formAddUser');
  if (form) form.reset();
  const modal = document.getElementById('modalAddUser');
  if (modal) modal.style.display = 'flex';
}

function openEditUserModal(userId, fullName, role) {
  document.getElementById('editUserId').value = userId;
  document.getElementById('editFullName').value = fullName;
  document.getElementById('editRole').value = role;
  const modal = document.getElementById('modalEditUser');
  if (modal) modal.style.display = 'flex';
}

function openResetPasswordModal(userId, username, fullName) {
  document.getElementById('resetUserId').value = userId;
  document.getElementById('resetNewPassword').value = '';
  document.getElementById('resetUserPrompt').innerHTML = `កំពុងកំណត់ពាក្យសម្ងាត់ឡើងវិញសម្រាប់ <strong>${fullName}</strong> (<code>${username}</code>)`;
  const modal = document.getElementById('modalResetPassword');
  if (modal) modal.style.display = 'flex';
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.style.display = 'none';
}

async function submitAddUser(event) {
  event.preventDefault();
  const fullName = document.getElementById('addFullName').value.trim();
  const username = document.getElementById('addUsername').value.trim();
  const password = document.getElementById('addPassword').value;
  const role = document.getElementById('addRole').value;

  try {
    const res = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: fullName, username, password, role })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message || 'បានបន្ថែមអ្នកប្រើប្រាស់ជោគជ័យ!', 'success');
      closeModal('modalAddUser');
      setTimeout(() => location.reload(), 800);
    } else {
      showToast(data.error || 'មានបញ្ហាក្នុងការបង្កើត!', 'danger');
    }
  } catch (err) {
    showToast('បរាជ័យក្នុងការតភ្ជាប់: ' + err.message, 'danger');
  }
}

async function submitEditUser(event) {
  event.preventDefault();
  const userId = document.getElementById('editUserId').value;
  const fullName = document.getElementById('editFullName').value.trim();
  const role = document.getElementById('editRole').value;

  try {
    const res = await fetch(`/api/users/${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: fullName, role })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message || 'បានកែប្រែព័ត៌មានជោគជ័យ!', 'success');
      closeModal('modalEditUser');
      setTimeout(() => location.reload(), 800);
    } else {
      showToast(data.error || 'មានបញ្ហាក្នុងការកែប្រែ!', 'danger');
    }
  } catch (err) {
    showToast('បរាជ័យក្នុងការតភ្ជាប់: ' + err.message, 'danger');
  }
}

async function submitResetPassword(event) {
  event.preventDefault();
  const userId = document.getElementById('resetUserId').value;
  const newPassword = document.getElementById('resetNewPassword').value;

  try {
    const res = await fetch(`/api/users/${userId}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_password: newPassword })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message || 'បានប្តូរពាក្យសម្ងាត់ជោគជ័យ!', 'success');
      closeModal('modalResetPassword');
    } else {
      showToast(data.error || 'មានបញ្ហាក្នុងការប្តូរពាក្យសម្ងាត់!', 'danger');
    }
  } catch (err) {
    showToast('បរាជ័យក្នុងការតភ្ជាប់: ' + err.message, 'danger');
  }
}

async function deleteUser(userId, fullName) {
  if (!confirm(`តើអ្នកប្រាកដជាចង់លុបអ្នកប្រើប្រាស់ "${fullName}" នេះចេញពីប្រព័ន្ធមែនទេ?\n(សកម្មភាពនេះមិនអាចត្រឡប់ក្រោយវិញបានទេ)`)) {
    return;
  }

  try {
    const res = await fetch(`/api/users/${userId}/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message || 'បានលុបអ្នកប្រើប្រាស់ជោគជ័យ!', 'success');
      setTimeout(() => location.reload(), 800);
    } else {
      showToast(data.error || 'មានបញ្ហាក្នុងការលុប!', 'danger');
    }
  } catch (err) {
    showToast('បរាជ័យក្នុងការតភ្ជាប់: ' + err.message, 'danger');
  }
}
