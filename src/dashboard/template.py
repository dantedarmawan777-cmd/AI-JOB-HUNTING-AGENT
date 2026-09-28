"""
HTML/CSS/JS Template for Job Hunting Agent Web Dashboard.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Job-Hunting & HITL Dashboard | Aditya Darmawan</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card: #111827;
      --card-hover: #172033;
      --card-sub: #162032;
      --border: #1f293d;
      --border-accent: #2d3e5e;
      --text: #f3f4f6;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --emerald: #10b981;
      --emerald-bg: rgba(16, 185, 129, 0.12);
      --amber: #f59e0b;
      --amber-bg: rgba(245, 158, 11, 0.12);
      --rose: #f43f5e;
      --rose-bg: rgba(244, 63, 94, 0.12);
      --purple: #8b5cf6;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      font-size: 14px;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* Navigation Header */
    header {
      background: rgba(17, 24, 39, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 50;
      padding: 14px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand-group {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .logo-badge {
      width: 38px;
      height: 38px;
      background: linear-gradient(135deg, var(--primary), var(--purple));
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 16px;
      color: #fff;
    }
    .brand-title {
      font-size: 16px;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: #fff;
    }
    .brand-sub {
      font-size: 12px;
      color: var(--text-muted);
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s ease;
      text-decoration: none;
    }
    .btn-primary {
      background: var(--primary);
      color: #fff;
    }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-outline {
      background: var(--card-sub);
      color: var(--text);
      border-color: var(--border);
    }
    .btn-outline:hover { background: var(--card-hover); border-color: var(--border-accent); }
    .btn-success {
      background: var(--emerald);
      color: #fff;
    }
    .btn-success:hover { background: #059669; }
    .btn-danger {
      background: var(--rose-bg);
      color: var(--rose);
      border-color: rgba(244, 63, 94, 0.3);
    }
    .btn-danger:hover { background: var(--rose); color: #fff; }

    /* Main Container */
    main {
      flex: 1;
      max-width: 1380px;
      width: 100%;
      margin: 0 auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    /* Stats Grid */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
    }
    .stat-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .stat-label {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }
    .stat-val {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #fff;
    }
    .stat-sub {
      font-size: 11.5px;
      color: var(--text-muted);
    }

    /* Tabs Bar */
    .tabs-bar {
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 8px;
    }
    .tab-btn {
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 13.5px;
      font-weight: 600;
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .tab-btn.active {
      background: var(--card);
      color: var(--primary);
      border: 1px solid var(--border);
    }
    .tab-btn:hover:not(.active) {
      color: var(--text);
      background: rgba(255, 255, 255, 0.03);
    }

    /* Filter Controls */
    .controls-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }
    .filter-pills {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .pill {
      background: var(--card);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .pill.active {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }
    .search-input {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: #fff;
      padding: 8px 14px;
      font-size: 13px;
      min-width: 260px;
      outline: none;
    }
    .search-input:focus { border-color: var(--primary); }

    /* Job Card Grid */
    .jobs-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .job-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 22px 24px;
      transition: border-color 0.2s ease, transform 0.15s ease;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .job-card:hover {
      border-color: var(--border-accent);
    }
    .job-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
    }
    .job-title-group {
      flex: 1;
    }
    .job-title {
      font-size: 17px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 4px;
    }
    .job-meta-row {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      font-size: 12.5px;
      color: var(--text-muted);
    }
    .company-tag {
      font-weight: 600;
      color: var(--text);
    }
    .score-badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 12.5px;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
    }
    .score-high { background: var(--emerald-bg); color: var(--emerald); border: 1px solid rgba(16, 185, 129, 0.3); }
    .score-med { background: var(--amber-bg); color: var(--amber); border: 1px solid rgba(245, 158, 11, 0.3); }
    .score-low { background: var(--rose-bg); color: var(--rose); border: 1px solid rgba(244, 63, 94, 0.3); }

    .rationale-box {
      background: var(--card-sub);
      border-left: 3px solid var(--primary);
      border-radius: 0 6px 6px 0;
      padding: 10px 14px;
      font-size: 12.5px;
      color: #cbd5e1;
      line-height: 1.5;
    }
    .strengths-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .strength-pill {
      background: rgba(59, 130, 246, 0.1);
      border: 1px solid rgba(59, 130, 246, 0.2);
      color: #93c5fd;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 11.5px;
      font-weight: 500;
    }

    .job-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid var(--border);
      padding-top: 12px;
      gap: 12px;
      flex-wrap: wrap;
    }
    .status-badge {
      font-size: 11.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 3px 8px;
      border-radius: 4px;
    }
    .status-shortlisted { background: var(--amber-bg); color: var(--amber); }
    .status-approved { background: var(--emerald-bg); color: var(--emerald); }
    .status-submitted { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
    .status-rejected { background: var(--rose-bg); color: var(--rose); }

    .action-group {
      display: flex;
      gap: 8px;
      align-items: center;
    }

    /* Chat Section */
    .chat-container {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      height: 650px;
    }
    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .chat-msg {
      max-width: 80%;
      padding: 12px 16px;
      border-radius: 10px;
      font-size: 13.5px;
      line-height: 1.5;
    }
    .chat-msg-user {
      align-self: flex-end;
      background: var(--primary);
      color: #fff;
    }
    .chat-msg-bot {
      align-self: flex-start;
      background: var(--card-sub);
      border: 1px solid var(--border);
      color: var(--text);
    }
    .chat-input-bar {
      border-top: 1px solid var(--border);
      padding: 14px 18px;
      display: flex;
      gap: 10px;
    }
    .chat-input {
      flex: 1;
      background: var(--card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: #fff;
      padding: 10px 14px;
      font-size: 13.5px;
      outline: none;
    }
    .chat-input:focus { border-color: var(--primary); }

    /* Profile View */
    .profile-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 28px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    /* Modal */
    .modal {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(4px);
      z-index: 100;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .modal-content {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      max-width: 700px;
      width: 100%;
      max-height: 85vh;
      overflow-y: auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    /* Empty state */
    .empty-state {
      text-align: center;
      padding: 48px 20px;
      color: var(--text-muted);
    }
  </style>
</head>
<body>

  <header>
    <div class="brand-group">
      <div class="logo-badge">AD</div>
      <div>
        <div class="brand-title">AI Job-Hunting &amp; HITL Copilot</div>
        <div class="brand-sub">Aditya Darmawan | Senior Credit Risk &amp; Underwriting Specialist</div>
      </div>
    </div>
    <div class="header-actions">
      <button class="btn btn-outline" onclick="triggerScrape()" id="scrape-btn">
        <span>⚡ Scrape Lowongan Baru</span>
      </button>
      <a class="btn btn-outline" href="https://t.me/Baby_LP_Bot" target="_blank">
        <span>📱 Open Telegram Bot</span>
      </a>
    </div>
  </header>

  <main>
    <!-- Stats Row -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Total Lowongan Terpindai</div>
        <div class="stat-val" id="stat-total">0</div>
        <div class="stat-sub">JobStreet, Glints, Kalibrr</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Shortlisted (Awaiting HITL)</div>
        <div class="stat-val" style="color: var(--amber)" id="stat-shortlisted">0</div>
        <div class="stat-sub">Match score &ge; 75%</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Disetujui / Submitted</div>
        <div class="stat-val" style="color: var(--emerald)" id="stat-submitted">0</div>
        <div class="stat-sub">Auto-Apply Playwright</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Rata-rata Match Score</div>
        <div class="stat-val" style="color: var(--primary)" id="stat-avg-score">0%</div>
        <div class="stat-sub">5-Pillar Credit Risk Fit</div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tabs-bar">
      <button class="tab-btn active" onclick="switchTab('jobs')">📋 Pipeline Lowongan</button>
      <button class="tab-btn" onclick="switchTab('chat')">💬 Gemini AI Copilot</button>
      <button class="tab-btn" onclick="switchTab('profile')">👤 Profil &amp; Berkas CV</button>
    </div>

    <!-- TAB 1: JOBS PIPELINE -->
    <section id="tab-jobs">
      <div class="controls-row">
        <div class="filter-pills">
          <div class="pill active" onclick="filterStatus('all', this)">Semua (<span id="count-all">0</span>)</div>
          <div class="pill" onclick="filterStatus('shortlisted', this)">Menunggu Approval (<span id="count-shortlisted">0</span>)</div>
          <div class="pill" onclick="filterStatus('approved', this)">Approved (<span id="count-approved">0</span>)</div>
          <div class="pill" onclick="filterStatus('submitted', this)">Submitted (<span id="count-submitted">0</span>)</div>
          <div class="pill" onclick="filterStatus('rejected', this)">Skipped (<span id="count-rejected">0</span>)</div>
        </div>
        <input type="text" class="search-input" id="search-input" placeholder="🔍 Cari posisi, perusahaan, skill..." oninput="renderJobs()">
      </div>

      <div class="jobs-list" id="jobs-container" style="margin-top: 18px;">
        <div class="empty-state">Memuat data lowongan...</div>
      </div>
    </section>

    <!-- TAB 2: GEMINI CHAT -->
    <section id="tab-chat" style="display: none;">
      <div class="chat-container">
        <div class="chat-messages" id="chat-box">
          <div class="chat-msg chat-msg-bot">
            👋 <strong>Halo Bos Aditya!</strong> Saya asisten AI Gemini karir Anda. Tanyakan status lowongan, minta review posisi tertentu, atau minta buatkan draf <em>Cover Letter</em> khusus!
          </div>
        </div>
        <div class="chat-input-bar">
          <input type="text" class="chat-input" id="chat-input-field" placeholder="Ketik pesan atau pertanyaan seputar lowongan..." onkeypress="if(event.key==='Enter') sendChatMessage()">
          <button class="btn btn-primary" onclick="sendChatMessage()">Kirim</button>
        </div>
      </div>
    </section>

    <!-- TAB 3: PROFILE -->
    <section id="tab-profile" style="display: none;">
      <div class="profile-card" id="profile-details">
        <div>
          <h2 style="font-size: 22px; color: #fff;">Aditya Darmawan</h2>
          <div style="color: var(--text-muted); font-size: 14px; margin-top: 2px;">Senior Credit Risk &amp; Underwriting Specialist (15+ Tahun Pengalaman)</div>
          <div style="margin-top: 10px; display: flex; gap: 10px;">
            <a href="/api/resumes/EN" target="_blank" class="btn btn-outline">📄 Download CV (EN)</a>
            <a href="/api/resumes/ID" target="_blank" class="btn btn-outline">📄 Download CV (ID)</a>
          </div>
        </div>
        <hr style="border-color: var(--border);">
        <div>
          <h3 style="font-size: 14px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Ringkasan Profesional</h3>
          <p style="color: #cbd5e1; font-size: 13.5px; line-height: 1.6;">
            Senior Credit Risk and Underwriting Specialist dengan lebih dari 15 tahun pengalaman kumulatif di perbankan komersial tier-1 (Maybank, CIMB Niaga, Bank Mega) dan FinTech Lending regional Asia Tenggara (Aspire SEA). Ahli dalam underwriting SME, analisis DSCR laporan keuangan, dan kalibrasi digital risk scorecards.
          </p>
        </div>
      </div>
    </section>
  </main>

  <script>
    let allJobs = [];
    let currentFilter = 'all';

    async function fetchStats() {
      try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('stat-total').innerText = data.total || 0;
        document.getElementById('stat-shortlisted').innerText = (data.by_status && data.by_status.shortlisted) || 0;
        document.getElementById('stat-submitted').innerText = ((data.by_status && data.by_status.submitted) || 0) + ((data.by_status && data.by_status.approved) || 0);
        document.getElementById('stat-avg-score').innerText = (data.avg_match_score || 0).toFixed(1) + '%';
        
        document.getElementById('count-all').innerText = data.total || 0;
        document.getElementById('count-shortlisted').innerText = (data.by_status && data.by_status.shortlisted) || 0;
        document.getElementById('count-approved').innerText = (data.by_status && data.by_status.approved) || 0;
        document.getElementById('count-submitted').innerText = (data.by_status && data.by_status.submitted) || 0;
        document.getElementById('count-rejected').innerText = (data.by_status && data.by_status.rejected) || 0;
      } catch (e) {
        console.error('Stats fetch error:', e);
      }
    }

    async function fetchJobs() {
      try {
        const res = await fetch('/api/jobs');
        allJobs = await res.json();
        renderJobs();
      } catch (e) {
        console.error('Jobs fetch error:', e);
      }
    }

    function renderJobs() {
      const container = document.getElementById('jobs-container');
      const query = document.getElementById('search-input').value.toLowerCase();
      
      let filtered = allJobs.filter(j => {
        const matchStatus = currentFilter === 'all' || j.status === currentFilter;
        const text = `${j.title} ${j.company} ${j.location} ${j.description}`.toLowerCase();
        const matchQuery = !query || text.includes(query);
        return matchStatus && matchQuery;
      });

      if (filtered.length === 0) {
        container.innerHTML = '<div class="empty-state">Tidak ada lowongan dalam kategori ini.</div>';
        return;
      }

      container.innerHTML = filtered.map(job => {
        const score = (job.match_result && job.match_result.score) || job.match_score || 0;
        let scoreClass = 'score-low';
        if (score >= 85) scoreClass = 'score-high';
        else if (score >= 70) scoreClass = 'score-med';

        const rationale = (job.match_result && job.match_result.reasoning) || job.match_reasoning || 'Evaluasi kecocokan standar profil 15+ tahun.';
        const strengths = (job.match_result && job.match_result.matching_points) || [];

        return `
          <div class="job-card">
            <div class="job-header">
              <div class="job-title-group">
                <div class="job-title">${job.title}</div>
                <div class="job-meta-row">
                  <span class="company-tag">🏢 ${job.company}</span>
                  <span>📍 ${job.location || 'Indonesia'}</span>
                  <span>💰 ${job.salary || (job.salary_min ? `IDR ${Number(job.salary_min).toLocaleString()} - ${Number(job.salary_max).toLocaleString()}` : 'Gaji Kompetitif')}</span>
                  <span style="text-transform: uppercase; font-weight: 700; color: var(--primary);">#${job.platform}</span>
                </div>
              </div>
              <div class="score-badge ${scoreClass}">🎯 ${score}% FIT</div>
            </div>

            <div class="rationale-box">
              <strong>💡 Analisis Kecocokan:</strong> ${rationale}
            </div>

            ${strengths.length > 0 ? `
              <div class="strengths-row">
                ${strengths.slice(0, 4).map(s => `<span class="strength-pill">✓ ${s}</span>`).join('')}
              </div>
            ` : ''}

            <div class="job-footer">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="status-badge status-${job.status}">${job.status}</span>
                <span style="font-size: 11.5px; color: var(--text-muted);">CV Target: <strong>${job.cv_language || 'EN'}</strong></span>
              </div>
              <div class="action-group">
                ${job.status === 'shortlisted' ? `
                  <button class="btn btn-success" onclick="approveJob('${job.id}')">✅ Approve &amp; Auto-Apply</button>
                  <button class="btn btn-outline" onclick="toggleCv('${job.id}', '${job.cv_language === 'ID' ? 'EN' : 'ID'}')">📄 CV: ${job.cv_language === 'ID' ? 'ID ➔ EN' : 'EN ➔ ID'}</button>
                  <button class="btn btn-danger" onclick="rejectJob('${job.id}')">❌ Skip</button>
                ` : ''}
                <a href="${job.url}" target="_blank" class="btn btn-outline">🔗 Buka Sumber</a>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    function filterStatus(status, el) {
      currentFilter = status;
      document.querySelectorAll('.filter-pills .pill').forEach(p => p.classList.remove('active'));
      if (el) el.classList.add('active');
      renderJobs();
    }

    function switchTab(tab) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-jobs').style.display = 'none';
      document.getElementById('tab-chat').style.display = 'none';
      document.getElementById('tab-profile').style.display = 'none';

      document.getElementById(`tab-${tab}`).style.display = 'block';
      event.target.classList.add('active');
    }

    async function approveJob(jobId) {
      if (!confirm('Setujui pengajuan otomatis untuk lowongan ini?')) return;
      try {
        const res = await fetch(`/api/jobs/${jobId}/approve`, { method: 'POST' });
        if (res.ok) {
          alert('✅ Lowongan berhasil di-approve! Background Playwright worker dijalankan.');
          fetchJobs();
          fetchStats();
        }
      } catch (e) {
        alert('Gagal approve: ' + e);
      }
    }

    async function rejectJob(jobId) {
      try {
        const res = await fetch(`/api/jobs/${jobId}/reject`, { method: 'POST' });
        if (res.ok) {
          fetchJobs();
          fetchStats();
        }
      } catch (e) {
        alert('Gagal skip: ' + e);
      }
    }

    async function toggleCv(jobId, newLang) {
      try {
        await fetch(`/api/jobs/${jobId}/toggle-cv`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cv_language: newLang })
        });
        fetchJobs();
      } catch (e) {
        console.error('Toggle CV error:', e);
      }
    }

    async function triggerScrape() {
      const btn = document.getElementById('scrape-btn');
      btn.innerText = '⏳ Sedang Memindai...';
      btn.disabled = true;
      try {
        await fetch('/api/scrape', { method: 'POST' });
        setTimeout(() => {
          btn.innerText = '⚡ Scrape Lowongan Baru';
          btn.disabled = false;
          fetchJobs();
          fetchStats();
        }, 5000);
      } catch (e) {
        btn.innerText = '⚡ Scrape Lowongan Baru';
        btn.disabled = false;
      }
    }

    async function sendChatMessage() {
      const input = document.getElementById('chat-input-field');
      const text = input.value.trim();
      if (!text) return;

      const chatBox = document.getElementById('chat-box');
      chatBox.innerHTML += `<div class="chat-msg chat-msg-user">${text}</div>`;
      input.value = '';
      chatBox.scrollTop = chatBox.scrollHeight;

      const typingId = 'typing-' + Date.now();
      chatBox.innerHTML += `<div class="chat-msg chat-msg-bot" id="${typingId}"><em>Gemini sedang berpikir...</em></div>`;
      chatBox.scrollTop = chatBox.scrollHeight;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        document.getElementById(typingId).innerHTML = data.reply.replace(/\\n/g, '<br>');
      } catch (e) {
        document.getElementById(typingId).innerHTML = '⚠️ Maaf, ada kendala koneksi AI.';
      }
      chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Initial Load
    fetchStats();
    fetchJobs();
    setInterval(() => {
      fetchStats();
      fetchJobs();
    }, 15000);
  </script>
</body>
</html>
"""
