const API = location.origin.includes('5500') || location.protocol === 'file:' ? 'http://127.0.0.1:8000' : '';
let BUNDLE = null, CH = {};
const $ = id => document.getElementById(id);
const f2 = v => Number(v).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
const toast = m => { const t = $('toast'); t.textContent = m; t.style.display = 'block'; setTimeout(() => t.style.display = 'none', 3500); };
function err(m) { const e = $('error'); e.hidden = false; e.textContent = m; }
function clearErr() { $('error').hidden = true; }

// Connectivity self-check on page load: if the backend is down, say so immediately.
(async () => {
  try {
    const r = await fetch(API + '/api/health', { cache: 'no-store' });
    if (!r.ok) throw new Error('bad status');
  } catch (e) {
    err('Cannot reach the server at ' + (API || location.origin) + '. Start the backend first (PowerShell, from the backend folder): .\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000 — then reload this page.');
  }
})();

async function api(path, opts) {
  let r;
  try {
    r = await fetch(API + path, opts);
  } catch (e) {
    throw new Error('Cannot reach the server at ' + (API || location.origin) + '. Start the backend first (PowerShell, from the backend folder): .\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --port 8000 — then open http://127.0.0.1:8000 in your browser.');
  }
  if (!r.ok) { let d = {}; try { d = await r.json(); } catch {} throw new Error(d.detail || ('Request failed (' + r.status + ')')); }
  return r.json();
}

let searchTimer = null, searchSeq = 0, searchAbort = null, SEL = {pairId: null, name: null};
const CURSYM = {INR: '₹', USD: '$', EUR: '€', GBP: '£', JPY: '¥', CNY: '¥', CHF: 'CHF ', AUD: 'A$', CAD: 'C$'};
const ccode = () => (BUNDLE && BUNDLE.currency) || 'INR';
const csym = () => CURSYM[ccode()] || (ccode() + ' ');
function resultItems() { return [...$('searchResults').children]; }
function focusResult(i) {
  const items = resultItems();
  if (!items.length) return;
  items[(i + items.length) % items.length].focus();
}
function setExpanded(open) { $('q').setAttribute('aria-expanded', open ? 'true' : 'false'); }
async function runSearch() {
  clearErr();
  const q = $('q').value.trim();
  const box = $('searchResults');
  if (q.length < 2) { box.innerHTML = ''; setExpanded(false); return; }
  const my = ++searchSeq;
  if (searchAbort) searchAbort.abort();
  searchAbort = new AbortController();
  try {
    const d = await api('/api/stocks/search?q=' + encodeURIComponent(q), { signal: searchAbort.signal });
    if (my !== searchSeq) return;
    box.innerHTML = '';
    setExpanded(false);
    if (!d.results || !d.results.length) return err(d.message || "We couldn't find a matching NSE-listed stock.");
    setExpanded(true);
    d.results.forEach(r => {
      const div = document.createElement('div');
      div.className = 'result-item'; div.tabIndex = 0; div.setAttribute('role', 'option');
      div.innerHTML = `<span><strong>${r.name}</strong><br><span class="meta">${r.exchange} · ${r.symbol}</span></span><span class="meta">Select →</span>`;
      const pick = () => { $('symbol').value = r.symbol; SEL = {pairId: r.investing_pair_id || null, name: r.name}; $('q').value = r.name; box.innerHTML = ''; setExpanded(false); };
      div.onclick = pick;
      div.onkeydown = e => {
        const i = resultItems().indexOf(div);
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); }
        else if (e.key === 'ArrowDown') { e.preventDefault(); focusResult(i + 1); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); if (i <= 0) $('q').focus(); else focusResult(i - 1); }
        else if (e.key === 'Escape') { box.innerHTML = ''; setExpanded(false); $('q').focus(); }
      };
      box.appendChild(div);
    });
    if (d.results.length === 1) $('symbol').value = d.results[0].symbol;
  } catch (e) {
    if (e.name === 'AbortError' || my !== searchSeq) return;
    err(e.message);
  }
}

$('btnSearch').onclick = runSearch;
$('q').addEventListener('input', () => { SEL = {pairId: null, name: null}; clearTimeout(searchTimer); searchTimer = setTimeout(runSearch, 300); });
$('q').addEventListener('keydown', e => {
  if (e.key === 'Enter') { clearTimeout(searchTimer); runSearch(); }
  else if (e.key === 'ArrowDown' && resultItems().length) { e.preventDefault(); focusResult(0); }
  else if (e.key === 'Escape') { $('searchResults').innerHTML = ''; setExpanded(false); }
});

const STEPS = ['Fetching historical data', 'Preparing dataset', 'Calculating statistics', 'Running regression', 'Calculating probability', 'Running hypothesis test', 'Preparing report'];
function loader(i) {
  const L = $('loader'); L.hidden = false;
  L.innerHTML = '<strong>Analyzing ' + ($('symbol').value || '') + '</strong>' + STEPS.map((s, k) =>
    `<div class="${k < i ? 'done' : ''}">${k < i ? '✓' : k === i ? '…' : '·'} ${s}</div>`).join('');
}

$('btnAnalyze').onclick = async () => {
  clearErr(); $('dashboard').hidden = true; $('empty').style.display = 'none';
  const symbol = $('symbol').value.trim();
  if (!symbol) return err("We couldn't find a matching NSE-listed stock.");
  const s = $('start').value, e = $('end').value, dayRe = /^\d{4}-\d{2}-\d{2}$/;
  if (!s || !e) return err("Pick both a start and an end date.");
  if (!dayRe.test(s) || !dayRe.test(e)) return err("Dates must be YYYY-MM-DD.");
  if (s > e) return err("Start date must be on or before end date.");
  const btn = $('btnAnalyze'); btn.disabled = true;
  try {
    for (let i = 0; i < STEPS.length; i++) { loader(i); await new Promise(r => setTimeout(r, 120)); }
    BUNDLE = await api('/api/analyze', { method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ symbol, start: s, end: e, investing_pair_id: SEL.pairId, stock_name: SEL.name }) });
    loader(STEPS.length); render();
    $('dashboard').hidden = false; $('loader').hidden = true;
  } catch (e) { $('loader').hidden = true; $('empty').style.display = 'block'; err(e.message); }
  finally { btn.disabled = false; }
};

const tabBtns = [...document.querySelectorAll('nav.tabs button')];
function activateTab(b) {
  tabBtns.forEach(x => x.setAttribute('aria-selected', 'false'));
  b.setAttribute('aria-selected', 'true');
  document.querySelectorAll('section.panel').forEach(p => p.classList.remove('active'));
  $('panel-' + b.dataset.tab).classList.add('active');
}
tabBtns.forEach((b, i) => {
  b.onclick = () => activateTab(b);
  b.onkeydown = e => {
    let j = null;
    if (e.key === 'ArrowRight') j = (i + 1) % tabBtns.length;
    else if (e.key === 'ArrowLeft') j = (i - 1 + tabBtns.length) % tabBtns.length;
    else if (e.key === 'Home') j = 0;
    else if (e.key === 'End') j = tabBtns.length - 1;
    if (j !== null) { e.preventDefault(); tabBtns[j].focus(); activateTab(tabBtns[j]); }
  };
});

function explain(title, formula, calc, interp) {
  return `<h3>${title}</h3><div class="formula">${formula}</div><div>${calc}</div><div class="explain">${interp}</div>`;
}
function statRows(s) {
  return `<div class="table-scroll"><table><tbody>
  ${[['n (observations)', s.n], ['Mean (x̄)', csym() + f2(s.mean)], ['Median', csym() + f2(s.median)], ['Mode', csym() + f2(s.mode) + ` <span class="meta">(×${s.mode_count})</span>`], ['Minimum', csym() + f2(s.min)], ['Maximum', csym() + f2(s.max)], ['Range', csym() + f2(s.range)], ['Variance (sample, ddof=1)', f2(s.variance_sample)], ['Std dev (sample)', csym() + f2(s.std_sample)], ['Q1 / Q2 / Q3', `${csym()}${f2(s.q1)} / ${csym()}${f2(s.q2)} / ${csym()}${f2(s.q3)}`], ['IQR', csym() + f2(s.iqr)], ['CV', s.cv_percent.toFixed(2) + '%']].map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('')}
  </tbody></table></div><p class="meta">Method: ${s.method}. Currency → 2 dp; full precision used internally.</p>`;
}

function render() {
  const b = BUNDLE, s = b.statistics, n = b.nifty_statistics, r = b.regression, p = b.probability, h = b.hypothesis;
  $('provenance').textContent = `Data source: ${b.provider} · Retrieved: ${b.retrieved_at} · Period: ${b.start} – ${b.end} · Observations: ${b.n} trading days`;
  $('overviewMetrics').innerHTML = [['Mean', csym() + f2(s.mean)], ['Median', csym() + f2(s.median)], ['Std dev', csym() + f2(s.std_sample)], ['CV', s.cv_percent.toFixed(2) + '%', 1], ['Last close', csym() + f2(b.last_close) + ` <span class="meta">${b.last_date}</span>`], ['Trading days', b.n]]
    .map(m => `<div class="metric"><div class="k">${m[0]}</div><div class="v${m[2] ? ' accent' : ''}">${m[1]}</div></div>`).join('');
  $('overviewDetail').innerHTML = `<p><strong>${b.stock_name}</strong> · ${b.symbol} · ${b.exchange} · ${ccode()} · ${b.start} → ${b.end} · ${b.n} trading observations · last close ${csym()}${f2(b.last_close)} (${b.last_date}). Weekends/holidays excluded; no dates fabricated.</p>`;
  $('statsDetail').innerHTML =
    explain('Mean', 'x̄ = Σx / n', `Σ of ${s.n} closes ÷ ${s.n} = <strong>${csym()}${f2(s.mean)}</strong>`, 'The average closing price — the centre of the dataset.') +
    explain('Median', 'Middle value of sorted data', `Median = <strong>${csym()}${f2(s.median)}</strong>`, 'The middle price; robust to outliers.') +
    explain('Mode', 'Most frequent value', `Mode = <strong>${csym()}${f2(s.mode)}</strong>`, 'The most frequently observed close.') +
    explain('Standard deviation (sample)', 's = √(Σ(x−x̄)² / (n−1))', `s = <strong>${csym()}${f2(s.std_sample)}</strong>`, 'Typical spread of prices around the mean.') +
    explain('Coefficient of variation', 'CV = s / x̄ × 100', `CV = ${f2(s.std_sample)} / ${f2(s.mean)} × 100 = <strong>${s.cv_percent.toFixed(2)}%</strong>`, 'Relative variability; lets us compare assets with different price scales.') +
    statRows(s);
  $('niftyDetail').innerHTML = `<div class="table-scroll"><table><thead><tr><th>Metric</th><th>Stock</th><th>NIFTY 50</th></tr></thead><tbody>
    ${[['Mean', f2(s.mean), f2(n.mean)], ['Std dev', f2(s.std_sample), f2(n.std_sample)], ['CV', s.cv_percent.toFixed(2) + '%', n.cv_percent.toFixed(2) + '%']].map(x => `<tr><td>${x[0]}</td><td>${x[1]}</td><td>${x[2]}</td></tr>`).join('')}
    </tbody></table></div><div class="explain">CV comparison is a statistical dispersion comparison, not investment advice. Lower CV means lower relative dispersion.</div>${b.currency && b.currency !== 'INR' ? `<div class="explain">Note: ${b.stock_name} trades in ${b.currency} while NIFTY 50 is quoted in INR — absolute price comparisons span currencies.</div>` : ''}`;
  $('regDetail').innerHTML = explain('Line of regression', 'Y = a + bX; b = Σ(x−x̄)(y−ȳ)/Σ(x−x̄)², a = ȳ − bx̄',
    `Y = <strong>${r.intercept.toFixed(4)}</strong> + <strong>${r.slope.toFixed(4)}</strong>·X · R² = <strong>${r.r_squared.toFixed(4)}</strong> · r = ${r.r.toFixed(4)} · SE(estimate) = ${f2(r.std_err_estimate)}`,
    'Trend of closing price against trading-day number (first observation = 1). R² is the fraction of price variation explained by the linear trend.');
  $('probDetail').innerHTML = explain('Probability of a rise one week later', 'P(increase) = (# positive 5-trading-day returns) / (# valid observations); R<sub>t</sub> = (P<sub>t+5</sub>−P<sub>t</sub>)/P<sub>t</sub>',
    `Observations: ${p.observations} · Positive: ${p.positive} · Negative: ${p.negative} · Flat: ${p.flat} · <strong>P(increase) = ${p.p_positive.toFixed(4)}</strong> · P(decrease) = ${p.p_negative.toFixed(4)} · P(flat) = ${p.p_flat.toFixed(4)}`,
    'Historical probability estimate based on the selected dataset — not a guaranteed prediction of what the stock will do.');
  renderHyp(h);
  $('mu0').value = s.mean.toFixed(2);
  $('rawCount').textContent = `(${b.records.length} rows)`;
  drawRaw(b.records);
  $('assignDetail').innerHTML = `
    <h3>STATISTICS AND PROBABILITY ANALYSIS — ${b.stock_name} (${b.symbol}), ${b.start} to ${b.end}</h3>
    <p class="meta">1. Historical data: ${b.n} trading days from ${b.provider}. 2. Descriptive statistics: mean ${csym()}${f2(s.mean)}, median ${csym()}${f2(s.median)}, s ${csym()}${f2(s.std_sample)}, CV ${s.cv_percent.toFixed(2)}%.
    3. NIFTY 50 CV ${n.cv_percent.toFixed(2)}%. 4. Regression: ${r.equation}, R² ${r.r_squared.toFixed(4)}. 5. P(weekly increase) ${p.p_positive.toFixed(4)} (historical estimate).
    6. H0: μ = ${h.mu0}: ${h.decision} (t = ${h.t_statistic.toFixed(4)}, p = ${h.p_value.toFixed(6)}). 7. Academic analysis only — not investment advice.</p>
    <div class="search-row"><button class="ghost" onclick="document.querySelector('[data-tab=statistics]').click()">Review calculations</button></div>`;
  drawCharts();
  if (window.lucide) lucide.createIcons();
}
function renderHyp(h) {
  const sym = h.alternative === 'two-sided' ? '≠' : h.alternative === 'greater' ? '>' : '<';
  $('hypDetail').innerHTML = explain('One-sample t-test', `H₀: μ = ${h.mu0}; H₁: μ ${sym} ${h.mu0} · t = (x̄ − μ₀)/(s/√n)`,
    `x̄ = ${f2(h.sample_mean)}, s = ${f2(h.sample_std)}, n = ${h.n}, α = ${h.alpha}, t = <strong>${h.t_statistic.toFixed(4)}</strong>, p = <strong>${h.p_value.toFixed(6)}</strong>, critical = ${h.critical_value.toFixed(4)}, df = ${h.df}<br>Decision: <strong>${h.decision}</strong>`,
    h.reject_null ? 'There is sufficient statistical evidence at this α to reject H₀ for this dataset.' : 'There is not sufficient statistical evidence at this α to reject H₀ for this dataset.');
}
function drawCharts() {
  const b = BUNDLE;
  Object.values(CH).forEach(c => c && c.destroy()); CH = {};
  const grid = { color: 'rgba(255,255,255,.07)' };
  CH.price = new Chart($('chPrice'), { type: 'line', data: { labels: b.dates, datasets: [{ data: b.close, borderColor: '#E8FF5A', pointRadius: 0, borderWidth: 1.5 }] },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#71717A', maxTicksLimit: 8 }, grid }, y: { ticks: { color: '#71717A' }, grid } } } });
  CH.idx = new Chart($('chIndexed'), { type: 'line', data: { labels: b.dates.map((_, i) => i + 1), datasets: [
    { label: 'Stock (base=100)', data: b.indexed_stock, borderColor: '#E8FF5A', pointRadius: 0, borderWidth: 1.5 },
    { label: 'NIFTY 50 (base=100)', data: b.indexed_nifty, borderColor: '#A1A1AA', pointRadius: 0, borderWidth: 1.5 }] },
    options: { responsive: true, plugins: { legend: { labels: { color: '#A1A1AA' } } }, scales: { x: { ticks: { color: '#71717A' }, grid }, y: { ticks: { color: '#71717A' }, grid } } } });
  CH.reg = new Chart($('chReg'), { type: 'scatter', data: { datasets: [
    { label: 'Actual', data: b.close.map((y, i) => ({ x: i + 1, y })), backgroundColor: 'rgba(232,255,90,.5)', pointRadius: 2 },
    { label: 'Regression', type: 'line', data: b.regression.fitted.map((y, i) => ({ x: i + 1, y })), borderColor: '#F4F4F5', pointRadius: 0, borderWidth: 1.5 }] },
    options: { responsive: true, plugins: { legend: { labels: { color: '#A1A1AA' } } }, scales: { x: { title: { display: true, text: 'Trading day (X)', color: '#71717A' }, ticks: { color: '#71717A' }, grid }, y: { title: { display: true, text: 'Close (' + ccode() + ')', color: '#71717A' }, ticks: { color: '#71717A' }, grid } } } });
}
function drawRaw(records) {
  const q = ($('rawSearch').value || '').toLowerCase();
  const rows = records.filter(r => !q || r.date.includes(q)).slice(0, 500);
  $('rawBody').innerHTML = rows.map(r => `<tr><td>${r.date}</td><td>${f2(r.open)}</td><td>${f2(r.high)}</td><td>${f2(r.low)}</td><td>${f2(r.close)}</td><td>${r.volume.toLocaleString('en-IN')}</td></tr>`).join('');
}
$('rawSearch').oninput = () => BUNDLE && drawRaw(BUNDLE.records);
$('btnHyp').onclick = async () => {
  try { BUNDLE = await api('/api/analyze/hypothesis', { method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ analysis_id: BUNDLE.analysis_id, mu0: parseFloat($('mu0').value), alpha: parseFloat($('alpha').value), alternative: $('alt').value }) });
    renderHyp(BUNDLE.hypothesis); toast('Hypothesis test updated.');
  } catch (e) { err(e.message); }
};
async function downloadFile(path, fallbackName) {
  clearErr();
  try {
    let r;
    try {
      r = await fetch(API + path);
    } catch (e) {
      throw new Error('Cannot reach the server. Start the backend first, click Analyze again, then download.');
    }
    if (!r.ok) {
      let msg = 'Download failed (' + r.status + ')';
      try { const d = await r.json(); if (d.detail) msg = d.detail; } catch {}
      if (r.status === 404 && path.includes('/excel')) msg = 'Excel export not found on the server. Restart the backend (uvicorn) to pick up the latest code, hard-refresh this page (Ctrl+F5), then click Analyze again before downloading.';
      else if (r.status === 404) msg = 'This analysis is no longer on the server (it restarts clear results). Click Analyze again, then download.';
      throw new Error(msg);
    }
    const blob = await r.blob();
    let name = fallbackName;
    const m = (r.headers.get('Content-Disposition') || '').match(/filename=([^;]+)/);
    if (m) name = m[1].trim().replace(/^"|"$/g, '');
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    toast('Download started: ' + name);
  } catch (e) { err(e.message); }
}
function needBundle() {
  if (!BUNDLE) { toast('Click Analyze first, wait for the results, then download.'); return false; }
  return true;
}
$('btnPDF').onclick = () => { if (needBundle()) downloadFile('/api/report/' + BUNDLE.analysis_id, 'report.pdf'); };
$('btnExcel').onclick = () => { if (needBundle()) downloadFile('/api/export/' + BUNDLE.analysis_id + '/excel', 'raw-data.xlsx'); };
$('btnCSV').onclick = () => { if (needBundle()) downloadFile('/api/export/' + BUNDLE.analysis_id + '?kind=raw', 'raw-data.csv'); };
$('btnRawExcel').onclick = () => { if (needBundle()) downloadFile('/api/export/' + BUNDLE.analysis_id + '/excel', 'raw-data.xlsx'); };
$('btnRawCSV').onclick = () => { if (needBundle()) downloadFile('/api/export/' + BUNDLE.analysis_id + '?kind=raw', 'raw-data.csv'); };
