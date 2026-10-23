/**
 * VDOWN - Universal Video & Audio Downloader
 * Client Application Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    currentMedia: null,
    selectedMode: 'video', // 'video', 'audio', 'raw'
    selectedQualityId: '1080',
    selectedLabel: '1080p Full HD',
    selectedSize: 'Estimating...',
    activeDownloadId: null,
    activeSocket: null,
    pollingInterval: null,
    pendingDeleteItem: null
  };

  // DOM Elements - Search & Input
  const urlInput = document.getElementById('video-url-input');
  const pasteBtn = document.getElementById('paste-btn');
  const clearBtn = document.getElementById('clear-btn');
  const fetchBtn = document.getElementById('fetch-info-btn');
  const platformIcon = document.getElementById('current-platform-icon');
  
  // Error Banner
  const errorBanner = document.getElementById('error-banner');
  const errorTitle = document.getElementById('error-title');
  const errorMessage = document.getElementById('error-message');
  const errorCloseBtn = document.getElementById('error-close-btn');

  // Inspected Result Section
  const resultSection = document.getElementById('result-section');
  const mediaThumbnail = document.getElementById('media-thumbnail');
  const mediaDuration = document.getElementById('media-duration');
  const mediaPlatformBadge = document.getElementById('media-platform-badge');
  const mediaPlatformName = document.getElementById('media-platform-name');
  const mediaTitle = document.getElementById('media-title');
  const mediaUploader = document.getElementById('media-uploader');
  const mediaViews = document.getElementById('media-views');
  const mediaDate = document.getElementById('media-date');
  const mediaOriginalLink = document.getElementById('media-original-link');
  const previewPlayBtn = document.getElementById('preview-play-btn');

  // Format Tabs & Grids
  const tabBtns = document.querySelectorAll('.hub-tab-btn');
  const videoTab = document.getElementById('video-tab');
  const audioTab = document.getElementById('audio-tab');
  const rawTab = document.getElementById('raw-tab');
  const videoQualitiesGrid = document.getElementById('video-qualities-grid');
  const audioQualitiesGrid = document.getElementById('audio-qualities-grid');
  const rawFormatsTbody = document.getElementById('raw-formats-tbody');

  // Preferences & Download Trigger
  const prefContainer = document.getElementById('pref-container');
  const prefSubtitles = document.getElementById('pref-subtitles');
  const prefCustomName = document.getElementById('pref-custom-name');
  const selectedQualityBadge = document.getElementById('selected-quality-badge');
  const selectedSizeBadge = document.getElementById('selected-size-badge');
  const startDownloadBtn = document.getElementById('start-download-btn');

  // Active Download Progress Elements
  const activeDownloadSection = document.getElementById('active-download-section');
  const progressThumb = document.getElementById('progress-thumbnail');
  const progressStatusBadge = document.getElementById('progress-status-badge');
  const progressQualityBadge = document.getElementById('progress-quality-badge');
  const progressTitle = document.getElementById('progress-title');
  const progressStage = document.getElementById('progress-stage');
  const progressMeterFill = document.getElementById('progress-meter-fill');
  const metricPercent = document.getElementById('metric-percent');
  const metricSpeed = document.getElementById('metric-speed');
  const metricBytes = document.getElementById('metric-bytes');
  const metricEta = document.getElementById('metric-eta');

  // Completed Action Buttons
  const downloadSuccessActions = document.getElementById('download-success-actions');
  const actionBrowserDownload = document.getElementById('action-browser-download');
  const actionPlayBtn = document.getElementById('action-play-btn');
  const actionOpenFileBtn = document.getElementById('action-open-file-btn');
  const actionShowFolderBtn = document.getElementById('action-show-folder-btn');

  // Library / History Elements
  const historyContainer = document.getElementById('history-items-container');
  const libraryCountBadge = document.getElementById('library-count-badge');
  const headerHistoryCount = document.getElementById('header-history-count');
  const libraryRefreshBtn = document.getElementById('library-refresh-btn');
  const libraryOpenFolderBtn = document.getElementById('library-open-folder-btn');
  const libraryClearAllBtn = document.getElementById('library-clear-all-btn');
  const headerOpenFolderBtn = document.getElementById('header-open-folder-btn');
  const footerOpenFolderBtn = document.getElementById('footer-open-folder-btn');

  // Modals
  const playerModal = document.getElementById('player-modal');
  const playerModalTitle = document.getElementById('player-modal-title');
  const modalVideoElement = document.getElementById('modal-video-element');
  const modalAudioElement = document.getElementById('modal-audio-element');
  const playerModalClose = document.getElementById('player-modal-close');

  const deleteConfirmModal = document.getElementById('delete-confirm-modal');
  const deleteItemTitleDesc = document.getElementById('delete-item-title-desc');
  const deleteFileCheckbox = document.getElementById('delete-file-checkbox');
  const deleteConfirmBtn = document.getElementById('delete-confirm-btn');
  const deleteCancelBtn = document.getElementById('delete-cancel-btn');

  const clearConfirmModal = document.getElementById('clear-confirm-modal');
  const clearFilesCheckbox = document.getElementById('clear-files-checkbox');
  const clearConfirmBtn = document.getElementById('clear-confirm-btn');
  const clearCancelBtn = document.getElementById('clear-cancel-btn');

  // ==========================================================================
  // Platform Detection Helper
  // ==========================================================================
  function updatePlatformIcon(url) {
    const u = (url || '').toLowerCase();
    platformIcon.className = '';
    
    // Adult sites
    if (u.includes('xhamster')) {
      platformIcon.className = 'fas fa-shield-halved';
      platformIcon.style.color = '#f97316';
    } else if (u.includes('eporner')) {
      platformIcon.className = 'fas fa-circle-play';
      platformIcon.style.color = '#3b82f6';
    } else if (u.includes('tnaflix')) {
      platformIcon.className = 'fas fa-film';
      platformIcon.style.color = '#ef4444';
    } else if (u.includes('viralxxxporn')) {
      platformIcon.className = 'fas fa-fire';
      platformIcon.style.color = '#f43f5e';
    } else if (u.includes('pimpbunny')) {
      platformIcon.className = 'fas fa-rabbit';
      platformIcon.style.color = '#d946ef';
    } else if (u.includes('pornhub')) {
      platformIcon.className = 'fas fa-circle-play';
      platformIcon.style.color = '#f59e0b';
    } else if (u.includes('xvideos')) {
      platformIcon.className = 'fas fa-play';
      platformIcon.style.color = '#ef4444';
    } else if (u.includes('xnxx')) {
      platformIcon.className = 'fas fa-play';
      platformIcon.style.color = '#3b82f6';
    } else if (u.includes('spankbang')) {
      platformIcon.className = 'fas fa-bolt';
      platformIcon.style.color = '#f97316';
    }
    // Music sites
    else if (u.includes('soundcloud')) {
      platformIcon.className = 'fab fa-soundcloud';
      platformIcon.style.color = '#f97316';
    } else if (u.includes('bandcamp')) {
      platformIcon.className = 'fab fa-bandcamp';
      platformIcon.style.color = '#06b6d4';
    } else if (u.includes('mixcloud')) {
      platformIcon.className = 'fab fa-mixcloud';
      platformIcon.style.color = '#6366f1';
    } else if (u.includes('audiomack')) {
      platformIcon.className = 'fas fa-music';
      platformIcon.style.color = '#f59e0b';
    } else if (u.includes('freesound')) {
      platformIcon.className = 'fas fa-wave-square';
      platformIcon.style.color = '#0ea5e9';
    }
    // Mainstream video & social
    else if (u.includes('youtube') || u.includes('youtu.be')) {
      platformIcon.className = 'fab fa-youtube';
      platformIcon.style.color = '#ef4444';
    } else if (u.includes('tiktok')) {
      platformIcon.className = 'fab fa-tiktok';
      platformIcon.style.color = '#06b6d4';
    } else if (u.includes('instagram')) {
      platformIcon.className = 'fab fa-instagram';
      platformIcon.style.color = '#ec4899';
    } else if (u.includes('twitter') || u.includes('x.com')) {
      platformIcon.className = 'fab fa-x-twitter';
      platformIcon.style.color = '#f1f5f9';
    } else if (u.includes('facebook') || u.includes('fb.watch')) {
      platformIcon.className = 'fab fa-facebook';
      platformIcon.style.color = '#3b82f6';
    } else if (u.includes('reddit')) {
      platformIcon.className = 'fab fa-reddit';
      platformIcon.style.color = '#f97316';
    } else if (u.includes('vimeo')) {
      platformIcon.className = 'fab fa-vimeo-v';
      platformIcon.style.color = '#0ea5e9';
    } else if (u.includes('twitch')) {
      platformIcon.className = 'fab fa-twitch';
      platformIcon.style.color = '#a855f7';
    } else {
      platformIcon.className = 'fas fa-link';
      platformIcon.style.color = '';
    }
  }

  // ==========================================================================
  // URL Input Events
  // ==========================================================================
  urlInput.addEventListener('input', () => {
    const val = urlInput.value.trim();
    clearBtn.style.display = val ? 'inline-flex' : 'none';
    updatePlatformIcon(val);
  });

  urlInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      fetchVideoInfo();
    }
  });

  pasteBtn.addEventListener('click', async () => {
    try {
      let text = '';
      if (navigator.clipboard && navigator.clipboard.readText) {
        text = await navigator.clipboard.readText();
      } else {
        text = prompt('Paste video or audio URL here:');
      }
      if (text) {
        urlInput.value = text.trim();
        clearBtn.style.display = 'inline-flex';
        updatePlatformIcon(text);
        showToast('Link pasted', 'info');
        fetchVideoInfo();
      }
    } catch (err) {
      const fallback = prompt('Paste video or audio URL here:');
      if (fallback) {
        urlInput.value = fallback.trim();
        clearBtn.style.display = 'inline-flex';
        updatePlatformIcon(fallback);
        fetchVideoInfo();
      }
    }
  });

  clearBtn.addEventListener('click', () => {
    urlInput.value = '';
    clearBtn.style.display = 'none';
    updatePlatformIcon('');
    urlInput.focus();
  });

  // Demo Sample Pills & Dropdown
  document.querySelectorAll('.sample-chip[data-url]').forEach(pill => {
    pill.addEventListener('click', () => {
      const demoUrl = pill.dataset.url;
      urlInput.value = demoUrl;
      clearBtn.style.display = 'inline-flex';
      updatePlatformIcon(demoUrl);
      fetchVideoInfo();
    });
  });

  const demoDropdownToggle = document.getElementById('demo-dropdown-toggle');
  const demoDropdownMenu = document.getElementById('demo-dropdown-menu');
  if (demoDropdownToggle && demoDropdownMenu) {
    demoDropdownToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      demoDropdownMenu.classList.toggle('show');
    });

    document.querySelectorAll('.demo-menu-item').forEach(item => {
      item.addEventListener('click', () => {
        const demoUrl = item.dataset.url;
        urlInput.value = demoUrl;
        clearBtn.style.display = 'inline-flex';
        updatePlatformIcon(demoUrl);
        demoDropdownMenu.classList.remove('show');
        fetchVideoInfo();
      });
    });

    document.addEventListener('click', (e) => {
      if (!demoDropdownToggle.contains(e.target) && !demoDropdownMenu.contains(e.target)) {
        demoDropdownMenu.classList.remove('show');
      }
    });
  }

  errorCloseBtn.addEventListener('click', () => {
    errorBanner.style.display = 'none';
  });

  function showError(title, msg) {
    errorTitle.textContent = title || 'Extraction Error';
    errorMessage.textContent = msg || 'Could not fetch video info. Please verify the URL.';
    errorBanner.style.display = 'flex';
  }

  function hideError() {
    errorBanner.style.display = 'none';
  }

  // ==========================================================================
  // Fetch / Extract Video Metadata
  // ==========================================================================
  fetchBtn.addEventListener('click', fetchVideoInfo);

  async function fetchVideoInfo() {
    const url = urlInput.value.trim();
    if (!url) {
      showError('Empty URL', 'Please enter or paste a valid video URL.');
      urlInput.focus();
      return;
    }

    hideError();
    setFetchLoading(true);

    try {
      const res = await fetch('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      const json = await res.json();
      if (!res.ok || !json.success) {
        throw new Error(json.detail || 'Failed to extract video information.');
      }

      state.currentMedia = json.data;
      renderMediaDetails(json.data);
      renderQualitySelectors(json.data);

      // Auto-switch to audio tab if no video streams exist (e.g. music/audio sites)
      if ((!json.data.video_qualities || json.data.video_qualities.length === 0) && (json.data.audio_options && json.data.audio_options.length > 0)) {
        const audioTabBtn = document.getElementById('tab-btn-audio');
        if (audioTabBtn) audioTabBtn.click();
      } else {
        const videoTabBtn = document.getElementById('tab-btn-video');
        if (videoTabBtn) videoTabBtn.click();
      }

      resultSection.style.display = 'block';
      resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      showToast('Media inspected & formats ready', 'info');
    } catch (err) {
      console.error(err);
      showError('Extraction Error', err.message);
    } finally {
      setFetchLoading(false);
    }
  }

  function setFetchLoading(isLoading) {
    const btnText = fetchBtn.querySelector('.btn-text');
    const btnLoader = fetchBtn.querySelector('.btn-loader');
    if (isLoading) {
      btnText.style.display = 'none';
      btnLoader.style.display = 'inline-flex';
      fetchBtn.disabled = true;
    } else {
      btnText.style.display = 'inline-flex';
      btnLoader.style.display = 'none';
      fetchBtn.disabled = false;
    }
  }

  // ==========================================================================
  // Render Media Header Details
  // ==========================================================================
  function renderMediaDetails(data) {
    mediaThumbnail.src = data.thumbnail || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800';
    mediaDuration.textContent = data.duration_str || '00:00';
    mediaTitle.textContent = data.title || 'Untitled Media';
    mediaTitle.title = data.title || 'Untitled Media';
    mediaUploader.textContent = data.uploader || 'Unknown Creator';

    if (data.views !== null && data.views !== undefined) {
      mediaViews.textContent = `${Number(data.views).toLocaleString()} views`;
      document.getElementById('meta-views-wrapper').style.display = 'inline-flex';
    } else {
      document.getElementById('meta-views-wrapper').style.display = 'none';
    }

    if (data.upload_date) {
      mediaDate.textContent = data.upload_date;
      document.getElementById('meta-date-wrapper').style.display = 'inline-flex';
    } else {
      document.getElementById('meta-date-wrapper').style.display = 'none';
    }

    if (data.platform) {
      mediaPlatformName.textContent = data.platform.name;
      const iconEl = mediaPlatformBadge.querySelector('i');
      if (iconEl) iconEl.className = data.platform.icon;
    }

    mediaOriginalLink.href = data.webpage_url || data.url;
  }

  // Preview Play button in Media Overview
  if (previewPlayBtn) {
    previewPlayBtn.addEventListener('click', () => {
      if (state.currentMedia) {
        // If has direct playable preview url
        const topQ = (state.currentMedia.video_qualities && state.currentMedia.video_qualities[0]) || null;
        const streamUrl = (topQ && topQ.direct_url) ? topQ.direct_url : null;
        
        if (streamUrl) {
          modalVideoElement.src = streamUrl;
          modalVideoElement.style.display = 'block';
          modalAudioElement.style.display = 'none';
          playerModalTitle.textContent = state.currentMedia.title || 'Stream Preview';
          playerModal.style.display = 'flex';
          modalVideoElement.play().catch(() => {});
        } else {
          // If no direct url, open external link or notify user
          window.open(state.currentMedia.webpage_url || state.currentMedia.url, '_blank');
        }
      }
    });
  }

  // ==========================================================================
  // Render Quality Options (Tabs & Cards)
  // ==========================================================================
  function renderQualitySelectors(data) {
    // 1. Render Video Qualities
    videoQualitiesGrid.innerHTML = '';
    const videoQualities = data.video_qualities || [];
    
    if (videoQualities.length === 0) {
      videoQualitiesGrid.innerHTML = `
        <div class="video-quality-empty-state">
          <i class="fas fa-headphones" style="font-size: 2rem; color: var(--accent-primary); margin-bottom: 8px;"></i>
          <p style="font-weight: 600; color: var(--text-primary);">Audio Stream Detected</p>
          <p style="font-size: 0.85rem; color: var(--text-secondary);">This source does not provide separate video tracks. Please choose an option from the <strong>Audio Only (MP3)</strong> tab.</p>
        </div>
      `;
    } else {
      let defaultSelected = videoQualities.find(v => v.height === 1080) || 
                            videoQualities.find(v => v.height === 720) || 
                            videoQualities[0];

      videoQualities.forEach((vq) => {
        const isSelected = (vq === defaultSelected);
        const card = document.createElement('div');
        card.className = `quality-card ${isSelected ? 'selected' : ''}`;
        card.dataset.mode = 'video';
        
        const qId = (vq.format_id && (vq.format_id.startsWith('http://') || vq.format_id.startsWith('https://')))
          ? vq.format_id
          : (vq.height ? vq.height.toString() : (vq.format_id || 'best').toString());

        card.dataset.qualityId = qId;
        card.dataset.label = vq.label;
        card.dataset.size = vq.filesize_str;

        let badgeClass = 'badge-hd';
        let badgeText = 'HD';
        if (vq.height >= 2160) { badgeClass = 'badge-4k'; badgeText = '4K UHD'; }
        else if (vq.height >= 1080) { badgeClass = 'badge-fhd'; badgeText = '1080p'; }
        else if (vq.height >= 720) { badgeClass = 'badge-hd'; badgeText = '720p'; }
        else { badgeClass = 'badge-fps'; badgeText = `${vq.height || 480}p`; }

        card.innerHTML = `
          <div class="card-select-indicator">
            <i class="fas fa-check"></i>
          </div>
          <div class="card-top">
            <span class="resolution-tag">
              ${vq.height ? `${vq.height}p` : 'HD'}
              <span class="badge-pill ${badgeClass}">${badgeText}</span>
              ${vq.fps >= 50 ? `<span class="badge-pill badge-fps">${Math.round(vq.fps)}fps</span>` : ''}
            </span>
          </div>
          <div class="card-meta-row">
            <span class="card-size">${vq.filesize_str}</span>
            <span class="card-codec">${(vq.vcodec || '').substring(0, 4).toUpperCase() || 'H264'}</span>
          </div>
        `;

        card.addEventListener('click', () => selectQuality(card, 'video', qId, vq.label, vq.filesize_str));
        videoQualitiesGrid.appendChild(card);
      });

      if (defaultSelected) {
        const defaultQId = (defaultSelected.format_id && (defaultSelected.format_id.startsWith('http://') || defaultSelected.format_id.startsWith('https://')))
          ? defaultSelected.format_id
          : (defaultSelected.height ? defaultSelected.height.toString() : (defaultSelected.format_id || 'best').toString());
        selectQuality(null, 'video', defaultQId, defaultSelected.label, defaultSelected.filesize_str);
      }
    }

    // 2. Render Audio Options
    audioQualitiesGrid.innerHTML = '';
    const audioOptions = data.audio_options || [];
    audioOptions.forEach((ao, index) => {
      const isSelected = (!videoQualities.length && index === 0);
      const card = document.createElement('div');
      card.className = `quality-card ${isSelected ? 'selected' : ''}`;
      card.dataset.mode = 'audio';
      card.dataset.qualityId = ao.id;
      card.dataset.label = ao.label;
      card.dataset.size = ao.filesize_str;

      card.innerHTML = `
        <div class="card-select-indicator">
          <i class="fas fa-check"></i>
        </div>
        <div class="card-top">
          <span class="resolution-tag">
            <i class="fas fa-music" style="color: var(--accent-primary);"></i> ${ao.label}
          </span>
        </div>
        <div class="card-meta-row">
          <span class="card-size">${ao.filesize_str}</span>
          <span class="card-codec">${ao.ext.toUpperCase()}</span>
        </div>
      `;

      card.addEventListener('click', () => selectQuality(card, 'audio', ao.id, ao.label, ao.filesize_str));
      audioQualitiesGrid.appendChild(card);
    });

    // 3. Render Raw Stream Inspector
    rawFormatsTbody.innerHTML = '';
    const rawFormats = data.raw_formats || [];
    rawFormats.forEach(rf => {
      const tr = document.createElement('tr');
      const fType = rf.vcodec !== 'none' && rf.acodec !== 'none' ? 'Video + Audio' : (rf.vcodec !== 'none' ? 'Video Only' : 'Audio Only');
      tr.innerHTML = `
        <td><code>${rf.format_id}</code></td>
        <td>${fType}</td>
        <td>${rf.resolution || 'N/A'} • ${rf.ext}</td>
        <td>${rf.fps ? rf.fps + ' fps' : '--'}</td>
        <td style="font-family: var(--font-mono);">${rf.filesize_str}</td>
        <td>
          <button type="button" class="btn-secondary" style="padding: 3px 8px; font-size: 0.78rem;">
            Select
          </button>
        </td>
      `;

      tr.querySelector('button').addEventListener('click', () => {
        selectQuality(null, 'raw', rf.format_id, `Format ${rf.format_id} (${rf.ext})`, rf.filesize_str);
        showToast(`Selected raw format: ${rf.format_id}`, 'info');
      });

      rawFormatsTbody.appendChild(tr);
    });
  }

  function selectQuality(cardEl, mode, qualityId, label, sizeStr) {
    state.selectedMode = mode;
    state.selectedQualityId = qualityId;
    state.selectedLabel = label;
    state.selectedSize = sizeStr;

    selectedQualityBadge.textContent = label;
    selectedSizeBadge.textContent = sizeStr ? `~${sizeStr}` : '';

    document.querySelectorAll('.quality-card').forEach(c => c.classList.remove('selected'));
    if (cardEl) {
      cardEl.classList.add('selected');
    }
  }

  // Tab Switching
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const targetTabId = btn.dataset.tab;
      [videoTab, audioTab, rawTab].forEach(t => {
        if (t) t.style.display = (t.id === targetTabId) ? 'block' : 'none';
      });
    });
  });

  // ==========================================================================
  // Start Download
  // ==========================================================================
  startDownloadBtn.addEventListener('click', async () => {
    if (!state.currentMedia) {
      showError('No Media', 'Please analyze a URL first.');
      return;
    }

    const payload = {
      url: state.currentMedia.url,
      mode: state.selectedMode,
      quality_id: state.selectedQualityId.toString(),
      container: prefContainer.value,
      embed_subtitles: prefSubtitles.checked,
      custom_filename: prefCustomName.value.trim() || null,
      title: state.currentMedia.title,
      thumbnail: state.currentMedia.thumbnail,
      duration_str: state.currentMedia.duration_str,
      uploader: state.currentMedia.uploader
    };

    try {
      startDownloadBtn.disabled = true;
      startDownloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Initializing...';

      const res = await fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const json = await res.json();
      if (!res.ok || !json.success) {
        throw new Error(json.detail || 'Failed to start download.');
      }

      state.activeDownloadId = json.download_id;
      initActiveDownloadUI(payload);
      trackDownloadProgress(json.download_id);
      showToast('Download started in background', 'info');
    } catch (err) {
      console.error(err);
      showToast(err.message, 'error');
    } finally {
      startDownloadBtn.disabled = false;
      startDownloadBtn.innerHTML = '<i class="fas fa-arrow-down-to-bracket"></i> <span>Download Now</span>';
    }
  });

  function initActiveDownloadUI(payload) {
    activeDownloadSection.style.display = 'block';
    progressThumb.src = state.currentMedia.thumbnail || '';
    progressTitle.textContent = state.currentMedia.title || 'Downloading...';
    progressQualityBadge.textContent = state.selectedLabel;
    
    progressStatusBadge.textContent = 'Starting';
    progressStatusBadge.className = 'badge-status';
    progressStage.textContent = 'Connecting to media stream...';
    progressMeterFill.style.width = '0%';

    metricPercent.textContent = '0%';
    metricSpeed.textContent = '-- MB/s';
    metricBytes.textContent = '0 MB';
    metricEta.textContent = '--:--';

    downloadSuccessActions.style.display = 'none';
    activeDownloadSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  // ==========================================================================
  // Real-Time Progress Tracking (WebSocket + Polling Fallback)
  // ==========================================================================
  function trackDownloadProgress(downloadId) {
    if (state.activeSocket) {
      try { state.activeSocket.close(); } catch(e) {}
    }
    if (state.pollingInterval) {
      clearInterval(state.pollingInterval);
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/progress/${downloadId}`;

    let socketConnected = false;
    try {
      const socket = new WebSocket(wsUrl);
      state.activeSocket = socket;

      socket.onopen = () => {
        socketConnected = true;
      };

      socket.onmessage = (event) => {
        try {
          const task = JSON.parse(event.data);
          updateProgressUI(task);
        } catch (e) {
          console.error('Error parsing progress packet:', e);
        }
      };

      socket.onerror = () => {
        if (!socketConnected) startPolling(downloadId);
      };

      socket.onclose = () => {};
    } catch (e) {
      startPolling(downloadId);
    }
  }

  function startPolling(downloadId) {
    if (state.pollingInterval) clearInterval(state.pollingInterval);
    state.pollingInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/progress/${downloadId}`);
        if (!res.ok) return;
        const task = await res.json();
        updateProgressUI(task);
        if (task.status === 'finished' || task.status === 'error') {
          clearInterval(state.pollingInterval);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 500);
  }

  function updateProgressUI(task) {
    if (!task) return;

    if (task.stage) progressStage.textContent = task.stage;
    if (task.title) progressTitle.textContent = task.title;

    const percent = Math.min(Math.max(task.progress || 0, 0), 100);
    progressMeterFill.style.width = `${percent}%`;
    metricPercent.textContent = `${percent.toFixed(1)}%`;

    if (task.speed_str) metricSpeed.textContent = task.speed_str;
    if (task.eta_str) metricEta.textContent = task.eta_str;

    if (task.downloaded_bytes && task.total_bytes) {
      metricBytes.textContent = `${formatBytes(task.downloaded_bytes)} / ${formatBytes(task.total_bytes)}`;
    } else if (task.downloaded_bytes) {
      metricBytes.textContent = formatBytes(task.downloaded_bytes);
    }

    // Status changes
    if (task.status === 'downloading') {
      progressStatusBadge.textContent = 'Downloading';
      progressStatusBadge.className = 'badge-status';
    } else if (task.status === 'processing') {
      progressStatusBadge.textContent = 'Processing (FFmpeg)';
      progressStatusBadge.className = 'badge-status';
    } else if (task.status === 'finished') {
      progressStatusBadge.textContent = 'Completed';
      progressStatusBadge.className = 'badge-status finished';
      progressMeterFill.style.width = '100%';
      metricPercent.textContent = '100%';
      progressStage.textContent = 'Ready! File saved to your downloads folder.';

      // Enable success action buttons
      downloadSuccessActions.style.display = 'flex';
      actionBrowserDownload.href = `/api/file/${task.id}`;
      actionBrowserDownload.setAttribute('download', task.filename || 'download');

      actionPlayBtn.onclick = () => openPlayerModal(task.id, task.title, task.filename);
      actionOpenFileBtn.onclick = () => handleOpenFile(task.filepath, task.id);
      actionShowFolderBtn.onclick = () => handleShowInFolder(task.filepath, task.id);

      showToast('Download completed successfully', 'success');
      loadHistory();
    } else if (task.status === 'error') {
      progressStatusBadge.textContent = 'Failed';
      progressStatusBadge.className = 'badge-status error';
      progressStage.textContent = `Error: ${task.error || 'Download failed'}`;
      showToast(`Download failed: ${task.error || 'Unknown error'}`, 'error');
    }
  }

  // ==========================================================================
  // Windows Explorer & Host File Actions
  // ==========================================================================
  async function handleOpenFile(filepath, downloadId) {
    try {
      const res = await fetch('/api/open-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filepath, download_id: downloadId })
      });
      const json = await res.json();
      if (json.success) {
        showToast('Opening in media player...', 'info');
      } else {
        showToast(json.detail || 'Could not launch media player.', 'error');
      }
    } catch (e) {
      showToast('Error opening file.', 'error');
    }
  }

  async function handleShowInFolder(filepath, downloadId) {
    try {
      const res = await fetch('/api/show-in-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filepath, download_id: downloadId })
      });
      const json = await res.json();
      if (json.success) {
        if (json.opened_file) {
          showToast('Highlighted in Windows Explorer', 'success');
        } else {
          showToast('Opened downloads folder', 'info');
        }
      } else {
        showToast('Could not open Windows Explorer.', 'error');
      }
    } catch (e) {
      showToast('Error opening Windows Explorer.', 'error');
    }
  }

  async function handleOpenDownloadsFolder() {
    try {
      const res = await fetch('/api/open-downloads-folder', { method: 'POST' });
      const json = await res.json();
      if (json.success) {
        showToast('Opened downloads folder in Windows Explorer', 'info');
      }
    } catch (e) {
      showToast('Error opening downloads folder.', 'error');
    }
  }

  if (libraryOpenFolderBtn) libraryOpenFolderBtn.addEventListener('click', handleOpenDownloadsFolder);
  if (headerOpenFolderBtn) headerOpenFolderBtn.addEventListener('click', handleOpenDownloadsFolder);
  if (footerOpenFolderBtn) footerOpenFolderBtn.addEventListener('click', handleOpenDownloadsFolder);

  // ==========================================================================
  // Media Player Modal
  // ==========================================================================
  function openPlayerModal(downloadId, title, filename) {
    playerModalTitle.textContent = title || filename || 'Media Playback';
    const streamUrl = `/api/stream/${downloadId}`;
    const ext = (filename || '').split('.').pop().toLowerCase();

    if (['mp3', 'wav', 'm4a', 'aac', 'flac'].includes(ext)) {
      modalVideoElement.style.display = 'none';
      modalAudioElement.style.display = 'block';
      modalAudioElement.src = streamUrl;
      modalAudioElement.play().catch(() => {});
    } else {
      modalAudioElement.style.display = 'none';
      modalVideoElement.style.display = 'block';
      modalVideoElement.src = streamUrl;
      modalVideoElement.play().catch(() => {});
    }

    playerModal.style.display = 'flex';
  }

  function closePlayerModal() {
    modalVideoElement.pause();
    modalVideoElement.src = '';
    modalAudioElement.pause();
    modalAudioElement.src = '';
    playerModal.style.display = 'none';
  }

  if (playerModalClose) playerModalClose.addEventListener('click', closePlayerModal);
  if (playerModal) {
    playerModal.addEventListener('click', (e) => {
      if (e.target === playerModal) closePlayerModal();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (playerModal && playerModal.style.display === 'flex') closePlayerModal();
      if (deleteConfirmModal && deleteConfirmModal.style.display === 'flex') closeDeleteModal();
      if (clearConfirmModal && clearConfirmModal.style.display === 'flex') closeClearModal();
    }
  });

  // ==========================================================================
  // Download Library / History
  // ==========================================================================
  async function loadHistory() {
    try {
      const res = await fetch('/api/history');
      if (!res.ok) return;
      const data = await res.json();
      renderHistory(data.history || []);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  }

  function renderHistory(items) {
    libraryCountBadge.textContent = `${items.length} item${items.length === 1 ? '' : 's'}`;
    headerHistoryCount.textContent = items.length;

    if (items.length === 0) {
      historyContainer.innerHTML = `
        <div class="history-empty" id="history-empty-state">
          <i class="fas fa-cloud-arrow-down"></i>
          <p>No downloads yet. Enter a link above to get started.</p>
        </div>
      `;
      return;
    }

    historyContainer.innerHTML = '';
    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'history-item';
      
      const fileStatusBadge = item.file_exists !== false
        ? '<span class="history-status-pill exists"><i class="fas fa-check"></i> On Disk</span>'
        : '<span class="history-status-pill missing"><i class="fas fa-triangle-exclamation"></i> Moved</span>';

      let qualityLabel = item.quality || '';
      if (qualityLabel.startsWith('http://') || qualityLabel.startsWith('https://')) {
        const match = qualityLabel.match(/(\d{3,4}p)/i);
        qualityLabel = match ? match[1] : 'Direct Stream';
      } else if (qualityLabel.length > 25) {
        qualityLabel = qualityLabel.substring(0, 22) + '...';
      }

      card.innerHTML = `
        <div class="history-thumb-wrap">
          <img src="${item.thumbnail || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200'}" alt="thumb" class="history-thumb">
        </div>
        <div class="history-info">
          <h4 class="history-title" title="${item.title}">${item.title}</h4>
          <div class="history-meta">
            <span><i class="fas fa-database"></i> <strong>${item.filesize_str || 'File'}</strong></span>
            ${qualityLabel ? `<span><i class="fas fa-sliders"></i> ${qualityLabel}</span>` : ''}
            ${item.uploader ? `<span><i class="fas fa-user"></i> ${item.uploader}</span>` : ''}
            ${fileStatusBadge}
          </div>
        </div>
        <div class="history-actions">
          <button type="button" class="btn-history-icon btn-history-play" title="Play in App">
            <i class="fas fa-play"></i>
          </button>
          <button type="button" class="btn-history-icon btn-history-open" title="Open in Default Player">
            <i class="fas fa-file-video"></i>
          </button>
          <button type="button" class="btn-history-icon btn-history-folder" title="Show in Windows Explorer">
            <i class="fas fa-folder-open"></i>
          </button>
          <a href="/api/file/${item.id}" class="btn-history-icon" title="Save to Browser" download="${item.filename || 'download'}">
            <i class="fas fa-download"></i>
          </a>
          <button type="button" class="btn-history-icon btn-history-delete" title="Delete download">
            <i class="fas fa-trash-can"></i>
          </button>
        </div>
      `;

      card.querySelector('.btn-history-play').onclick = () => openPlayerModal(item.id, item.title, item.filename);
      card.querySelector('.btn-history-open').onclick = () => handleOpenFile(item.filepath, item.id);
      card.querySelector('.btn-history-folder').onclick = () => handleShowInFolder(item.filepath, item.id);
      card.querySelector('.btn-history-delete').onclick = () => promptDeleteItem(item);

      historyContainer.appendChild(card);
    });
  }

  // Delete Item Modal Handlers
  function promptDeleteItem(item) {
    state.pendingDeleteItem = item;
    deleteItemTitleDesc.textContent = `Delete "${item.title}"?`;
    deleteFileCheckbox.checked = true;
    deleteConfirmModal.style.display = 'flex';
  }

  function closeDeleteModal() {
    deleteConfirmModal.style.display = 'none';
    state.pendingDeleteItem = null;
  }

  deleteCancelBtn.addEventListener('click', closeDeleteModal);
  deleteConfirmModal.addEventListener('click', (e) => {
    if (e.target === deleteConfirmModal) closeDeleteModal();
  });

  deleteConfirmBtn.addEventListener('click', async () => {
    if (!state.pendingDeleteItem) return;
    const item = state.pendingDeleteItem;
    const deleteFromDisk = deleteFileCheckbox.checked;

    deleteConfirmBtn.disabled = true;
    try {
      const res = await fetch('/api/history/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: item.id, delete_file: deleteFromDisk })
      });
      const json = await res.json();
      if (json.success) {
        showToast(deleteFromDisk ? 'Deleted file & removed from history' : 'Removed from history', 'info');
        loadHistory();
      } else {
        showToast('Could not delete item.', 'error');
      }
    } catch (e) {
      showToast('Error removing history item', 'error');
    } finally {
      deleteConfirmBtn.disabled = false;
      closeDeleteModal();
    }
  });

  // Clear All History Handlers
  if (libraryClearAllBtn) {
    libraryClearAllBtn.addEventListener('click', () => {
      clearFilesCheckbox.checked = false;
      clearConfirmModal.style.display = 'flex';
    });
  }

  function closeClearModal() {
    clearConfirmModal.style.display = 'none';
  }

  clearCancelBtn.addEventListener('click', closeClearModal);
  clearConfirmModal.addEventListener('click', (e) => {
    if (e.target === clearConfirmModal) closeClearModal();
  });

  clearConfirmBtn.addEventListener('click', async () => {
    const deleteFiles = clearFilesCheckbox.checked;
    clearConfirmBtn.disabled = true;
    try {
      const res = await fetch('/api/history/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delete_files: deleteFiles })
      });
      const json = await res.json();
      if (json.success) {
        showToast(deleteFiles ? 'All files and history deleted' : 'Download history cleared', 'info');
        loadHistory();
      }
    } catch (e) {
      showToast('Error clearing history', 'error');
    } finally {
      clearConfirmBtn.disabled = false;
      closeClearModal();
    }
  });

  libraryRefreshBtn.addEventListener('click', () => {
    loadHistory();
    showToast('Library refreshed', 'info');
  });

  // ==========================================================================
  // Toast Notifications
  // ==========================================================================
  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'fas fa-info-circle';
    if (type === 'success') icon = 'fas fa-check-circle';
    else if (type === 'error') icon = 'fas fa-circle-exclamation';

    toast.innerHTML = `<i class="${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    }, 3500);
  }

  function formatBytes(bytes) {
    if (!bytes || bytes <= 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  // ==========================================================================
  // Supported Platforms Directory Logic
  // ==========================================================================
  let directoryData = null;
  let activeDirCategory = 'all';

  const dirTabs = document.querySelectorAll('.dir-tab-btn:not(.dir-dropdown-trigger)');
  const dirSearchInput = document.getElementById('dir-search-input');
  const dirContainer = document.getElementById('directory-cards-container');
  const dirDropdownContainer = document.getElementById('dir-dropdown-container');
  const dirDropdownBtn = document.getElementById('dir-dropdown-btn');
  const dirActiveNotice = document.getElementById('dir-active-notice');
  const dirNoticeResetBtn = document.getElementById('dir-notice-reset-btn');

  async function loadSupportedPlatforms() {
    try {
      const res = await fetch('/api/supported-platforms');
      if (!res.ok) return;
      directoryData = await res.json();
      renderDirectory();
    } catch (err) {
      console.error('Failed to load platforms directory:', err);
    }
  }

  function renderDirectory() {
    if (!directoryData || !dirContainer) return;

    const query = (dirSearchInput ? dirSearchInput.value : '').trim().toLowerCase();
    let allItems = [];

    // Filter categories:
    let targetCategories = [];
    if (activeDirCategory === 'all') {
      targetCategories = ['video', 'music', 'generic'];
      if (dirActiveNotice) dirActiveNotice.style.display = 'none';
    } else if (activeDirCategory === 'adult') {
      targetCategories = ['adult'];
      if (dirActiveNotice) dirActiveNotice.style.display = 'flex';
    } else if (activeDirCategory === 'all_everything') {
      targetCategories = ['video', 'music', 'generic', 'adult'];
      if (dirActiveNotice) dirActiveNotice.style.display = 'none';
    } else {
      targetCategories = [activeDirCategory];
      if (dirActiveNotice) dirActiveNotice.style.display = 'none';
    }

    targetCategories.forEach(cat => {
      const items = directoryData[cat] || [];
      items.forEach(it => {
        allItems.push({ ...it, category: cat });
      });
    });

    if (query) {
      if (activeDirCategory === 'all') {
        const adultItems = directoryData['adult'] || [];
        adultItems.forEach(it => {
          if (it.name.toLowerCase().includes(query) || it.domain.toLowerCase().includes(query)) {
            allItems.push({ ...it, category: 'adult' });
          }
        });
      }

      allItems = allItems.filter(
        item =>
          item.name.toLowerCase().includes(query) ||
          item.domain.toLowerCase().includes(query) ||
          (item.qualities && item.qualities.toLowerCase().includes(query))
      );
    }

    if (allItems.length === 0) {
      dirContainer.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">
          <i class="fas fa-circle-question" style="font-size: 2rem; margin-bottom: 10px; opacity: 0.5;"></i>
          <p>No platforms matched "${query}". But VDOWN can extract from <strong>any site</strong> with direct video or HTML5 streams.</p>
        </div>
      `;
      return;
    }

    dirContainer.innerHTML = '';
    allItems.forEach(item => {
      const card = document.createElement('div');
      card.className = 'dir-card';

      let catBadgeClass = 'badge-video';
      if (item.category === 'adult') catBadgeClass = 'badge-adult';
      else if (item.category === 'music') catBadgeClass = 'badge-music';
      else if (item.category === 'generic') catBadgeClass = 'badge-generic';

      card.innerHTML = `
        <div class="dir-card-top">
          <div class="dir-card-icon" style="color: ${item.color || 'var(--accent-primary)'};">
            <i class="${item.icon || 'fas fa-globe'}"></i>
          </div>
          <div class="dir-card-names">
            <div class="dir-card-name">${item.name}</div>
            <div class="dir-card-domain">${item.domain}</div>
          </div>
        </div>
        <span class="dir-card-badge ${catBadgeClass}">${item.badge || 'Supported'}</span>
        <div class="dir-card-qualities">
          <i class="fas fa-sliders"></i>
          <span>${item.qualities || 'All Qualities'}</span>
        </div>
      `;

      card.style.cursor = 'pointer';
      card.title = `Click to test ${item.name}`;
      card.onclick = () => {
        if (item.domain && item.domain !== '*') {
          urlInput.value = `https://${item.domain}`;
          urlInput.focus();
          clearBtn.style.display = 'inline-flex';
          updatePlatformIcon(`https://${item.domain}`);
          showToast(`Target set to ${item.name}. Enter a video link!`, 'info');
          document.getElementById('downloader-section').scrollIntoView({ behavior: 'smooth' });
        }
      };

      dirContainer.appendChild(card);
    });
  }

  // Directory Category Tab switching
  dirTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.dir-tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeDirCategory = btn.dataset.category;
      if (dirDropdownContainer) dirDropdownContainer.classList.remove('open');
      renderDirectory();
    });
  });

  // Discreet Directory Dropdown Toggle
  if (dirDropdownBtn && dirDropdownContainer) {
    dirDropdownBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      dirDropdownContainer.classList.toggle('open');
    });

    document.querySelectorAll('.dir-dropdown-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.dir-tab-btn').forEach(b => b.classList.remove('active'));
        dirDropdownBtn.classList.add('active');
        activeDirCategory = item.dataset.category;
        dirDropdownContainer.classList.remove('open');
        renderDirectory();
      });
    });

    document.addEventListener('click', (e) => {
      if (!dirDropdownContainer.contains(e.target)) {
        dirDropdownContainer.classList.remove('open');
      }
    });
  }

  // Return to Mainstream Sites Button
  if (dirNoticeResetBtn) {
    dirNoticeResetBtn.addEventListener('click', () => {
      document.querySelectorAll('.dir-tab-btn').forEach(b => b.classList.remove('active'));
      const defaultTab = document.getElementById('dir-tab-all');
      if (defaultTab) defaultTab.classList.add('active');
      activeDirCategory = 'all';
      renderDirectory();
    });
  }

  if (dirSearchInput) {
    dirSearchInput.addEventListener('input', () => {
      renderDirectory();
    });
  }

  // Initial Load
  loadHistory();
  loadSupportedPlatforms();
});
