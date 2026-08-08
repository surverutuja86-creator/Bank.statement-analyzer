/* ==========================================================================
   FinPulse AI - Client Script Engine (Chart.js, Filters, Animated Counters)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initScrollAnimations();
    initAnimatedCounters();
    initChartJS();
    fetchSummaryData();
    fetchTransactionsTable();
    initFileUpload();
    initContactForm();
    initAuthModals();
});

// Global Chart Instances
let categoryChartInstance = null;
let monthlyChartInstance = null;

/* -------------------------------------------------------------------
   1. Animated Statistics Counters
   ------------------------------------------------------------------- */
function initAnimatedCounters() {
    const counters = document.querySelectorAll('.stat-number');
    const observerOptions = { threshold: 0.5 };

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const finalVal = parseInt(target.getAttribute('data-target') || '0', 10);
                const suffix = target.getAttribute('data-suffix') || '';
                animateValue(target, 0, finalVal, 2000, suffix);
                obs.unobserve(target);
            }
        });
    }, observerOptions);

    counters.forEach(counter => observer.observe(counter));
}

function animateValue(obj, start, end, duration, suffix = '') {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const currentVal = Math.floor(progress * (end - start) + start);
        obj.innerHTML = currentVal.toLocaleString() + suffix;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

/* -------------------------------------------------------------------
   2. Scroll Animations & Navigation
   ------------------------------------------------------------------- */
function initScrollAnimations() {
    const navLinks = document.querySelectorAll('.nav-link');
    window.addEventListener('scroll', () => {
        let fromTop = window.scrollY + 100;
        navLinks.forEach(link => {
            let section = document.querySelector(link.getAttribute('href'));
            if (section) {
                if (
                    section.offsetTop <= fromTop &&
                    section.offsetTop + section.offsetHeight > fromTop
                ) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            }
        });
    });
}

/* -------------------------------------------------------------------
   3. Chart.js Dashboard Visualizations
   ------------------------------------------------------------------- */
function initChartJS() {
    const ctxCat = document.getElementById('categoryPieChart');
    const ctxMonthly = document.getElementById('monthlyBarChart');

    if (!ctxCat || !ctxMonthly) return;

    // Fetch live Category breakdown from API
    fetch('/api/analytics/categories')
        .then(res => res.json())
        .then(data => {
            const labels = data.labels.length ? data.labels : ['Salary', 'Shopping', 'Subscriptions', 'UPI', 'EMIs', 'Utilities'];
            const values = data.values.length ? data.values : [125000, 51999, 1417, 12879, 32500, 3329];

            if (categoryChartInstance) categoryChartInstance.destroy();

            categoryChartInstance = new Chart(ctxCat, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: [
                            '#06B6D4', '#10B981', '#8B5CF6', '#F59E0B', '#F43F5E', '#3B82F6', '#EC4899'
                        ],
                        borderWidth: 2,
                        borderColor: '#0F172A'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: '#94A3B8', font: { family: 'Plus Jakarta Sans', size: 12 } } },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return ` ${context.label}: ₹${context.raw.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
                                }
                            }
                        }
                    },
                    cutout: '70%'
                }
            });
        });

    // Fetch live Monthly Trend from API
    fetch('/api/analytics/monthly')
        .then(res => res.json())
        .then(data => {
            const labels = data.labels.length ? data.labels : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
            const income = data.income.length ? data.income : [120000, 125000, 125000, 140000, 125000, 149500];
            const expense = data.expense.length ? data.expense : [85000, 92000, 78000, 110000, 94000, 107567.50];

            if (monthlyChartInstance) monthlyChartInstance.destroy();

            monthlyChartInstance = new Chart(ctxMonthly, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Income (₹)',
                            data: income,
                            backgroundColor: '#10B981',
                            borderRadius: 6
                        },
                        {
                            label: 'Expense (₹)',
                            data: expense,
                            backgroundColor: '#F43F5E',
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: '#94A3B8' } },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => ` ${ctx.dataset.label}: ₹${ctx.raw.toLocaleString('en-IN')}`
                            }
                        }
                    },
                    scales: {
                        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94A3B8' } },
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94A3B8' } }
                    }
                }
            });
        });
}

/* -------------------------------------------------------------------
   4. Summary KPIs & Analytics Fetcher
   ------------------------------------------------------------------- */
function fetchSummaryData() {
    fetch('/api/analytics/summary')
        .then(res => res.json())
        .then(data => {
            document.getElementById('kpi-total-income').innerText = data.total_income || '₹2,45,000.00';
            document.getElementById('kpi-total-expense').innerText = data.total_expense || '₹1,12,450.00';
            document.getElementById('kpi-net-savings').innerText = data.net_savings || '₹1,32,550.00';
            document.getElementById('kpi-savings-rate').innerText = `${data.savings_rate || 54.1}%`;
            document.getElementById('kpi-anomalies').innerText = data.anomalies_count || '3';
        })
        .catch(err => console.log('Using default KPI data'));
}

/* -------------------------------------------------------------------
   5. Interactive Transactions Table & Filters
   ------------------------------------------------------------------- */
function fetchTransactionsTable(category = 'All', search = '', flag = '') {
    const tbody = document.getElementById('txnsTableBody');
    if (!tbody) return;

    let url = `/api/transactions?limit=50`;
    if (category && category !== 'All') url += `&category=${encodeURIComponent(category)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (flag) url += `&flag=${encodeURIComponent(flag)}`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            tbody.innerHTML = '';

            if (!data.transactions || data.transactions.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-dim);">No transactions found matching criteria.</td></tr>`;
                return;
            }

            data.transactions.forEach(t => {
                const tr = document.createElement('tr');
                
                let tagsHtml = '';
                if (t.is_salary) tagsHtml += `<span class="tag-flag salary">[Salary]</span>`;
                if (t.is_upi) tagsHtml += `<span class="tag-flag upi">[UPI]</span>`;
                if (t.is_emi) tagsHtml += `<span class="tag-flag emi">[EMI]</span>`;
                if (t.is_subscription) tagsHtml += `<span class="tag-flag subscription">[Subscription]</span>`;
                if (t.is_duplicate) tagsHtml += `<span class="tag-flag duplicate">[Duplicate]</span>`;
                if (t.is_spike) tagsHtml += `<span class="tag-flag spike">[Spike]</span>`;

                const typeBadgeClass = t.type === 'CREDIT' ? 'credit' : 'debit';

                tr.innerHTML = `
                    <td><span style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted);">${t.date}</span></td>
                    <td>
                        <div style="font-weight: 500;">${t.description}</div>
                        <div>${tagsHtml}</div>
                    </td>
                    <td><span class="badge-tag" style="background: rgba(255,255,255,0.05); color: #cbd5e1;">${t.category}</span></td>
                    <td><span class="badge-tag ${typeBadgeClass}">${t.type}</span></td>
                    <td style="font-family: var(--font-mono); font-weight: 600; text-align: right; color: ${t.type === 'CREDIT' ? '#34d399' : '#fff'};">${t.amount_formatted}</td>
                `;
                tbody.appendChild(tr);
            });
        });
}

// Attach input & filter listeners
document.getElementById('txnSearchInput')?.addEventListener('input', (e) => {
    const val = e.target.value;
    const cat = document.getElementById('txnCategoryFilter')?.value || 'All';
    const flag = document.getElementById('txnFlagFilter')?.value || '';
    fetchTransactionsTable(cat, val, flag);
});

document.getElementById('txnCategoryFilter')?.addEventListener('change', (e) => {
    const cat = e.target.value;
    const search = document.getElementById('txnSearchInput')?.value || '';
    const flag = document.getElementById('txnFlagFilter')?.value || '';
    fetchTransactionsTable(cat, search, flag);
});

document.getElementById('txnFlagFilter')?.addEventListener('change', (e) => {
    const flag = e.target.value;
    const cat = document.getElementById('txnCategoryFilter')?.value || 'All';
    const search = document.getElementById('txnSearchInput')?.value || '';
    fetchTransactionsTable(cat, search, flag);
});

/* -------------------------------------------------------------------
   6. Drag and Drop File Upload
   ------------------------------------------------------------------- */
function initFileUpload() {
    const dropzone = document.getElementById('fileDropzone');
    const fileInput = document.getElementById('statementFileInput');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--primary)';
        dropzone.style.background = 'rgba(6, 182, 212, 0.12)';
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.style.borderColor = 'var(--border-highlight)';
        dropzone.style.background = 'rgba(6, 182, 212, 0.03)';
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--border-highlight)';
        dropzone.style.background = 'rgba(6, 182, 212, 0.03)';
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const statusBox = document.getElementById('uploadStatusBox');
    if (statusBox) {
        statusBox.innerHTML = `<span style="color: var(--primary);"><i class="fas fa-spinner fa-spin"></i> Parsing statement with Decimal precision engine...</span>`;
    }

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            if (statusBox) statusBox.innerHTML = `<span style="color: var(--accent-rose);"><i class="fas fa-exclamation-triangle"></i> ${data.error}</span>`;
        } else {
            if (statusBox) {
                statusBox.innerHTML = `<span style="color: var(--secondary);"><i class="fas fa-check-circle"></i> ${data.message} (${data.records_processed} txns)</span>`;
            }
            // Refresh Dashboard & Charts
            fetchSummaryData();
            fetchTransactionsTable();
            initChartJS();
        }
    })
    .catch(err => {
        if (statusBox) statusBox.innerHTML = `<span style="color: var(--accent-rose);">Upload failed. Please check server logs.</span>`;
    });
}

/* -------------------------------------------------------------------
   7. Contact Form Toast
   ------------------------------------------------------------------- */
function initContactForm() {
    const form = document.getElementById('contactForm');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        alert('Thank you! Your message has been sent to the FinPulse AI team. We will reach out shortly.');
        form.reset();
    });
}

/* -------------------------------------------------------------------
   8. Auth Modals Setup
   ------------------------------------------------------------------- */
function initAuthModals() {
    const loginModal = document.getElementById('loginModal');
    const loginBtn = document.getElementById('loginNavBtn');
    const closeBtn = document.getElementById('closeModalBtn');

    if (loginBtn && loginModal) {
        loginBtn.addEventListener('click', () => loginModal.style.display = 'flex');
    }
    if (closeBtn && loginModal) {
        closeBtn.addEventListener('click', () => loginModal.style.display = 'none');
    }
    window.addEventListener('click', (e) => {
        if (e.target === loginModal) loginModal.style.display = 'none';
    });

    const loginForm = document.getElementById('loginModalForm');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('loginUsername').value;
            alert(`Welcome back, ${username}! Demo session activated.`);
            if (loginModal) loginModal.style.display = 'none';
        });
    }
}
