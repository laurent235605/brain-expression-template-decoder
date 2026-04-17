/**
 * Inspiration Master - Frontend Logic
 */

// Global state for inspiration feature
let inspirationState = {
    isLoggedIn: false,
    llmConfig: {
        baseUrl: "https://api.moonshot.cn/v1",
        model: "kimi-k2.5",
        apiKey: ""
    },
    options: null,
    selectedDataset: null,
    selectedDatasetCategory: null,
    pipelineTaskId: null,
    pipelineEventSource: null,
    enhanceTaskId: null,
    enhanceDataType: 'MATRIX',
    enhanceMode: 'single',
    activeEnhanceMode: 'single'
};

document.addEventListener('DOMContentLoaded', function() {
    // Restore saved LLM config from localStorage
    const savedUrl = localStorage.getItem('inspire_llm_url');
    const savedModel = localStorage.getItem('inspire_llm_model');
    const savedKey = localStorage.getItem('inspire_llm_key');
    if (savedUrl) document.getElementById('inspire-llm-url').value = savedUrl;
    if (savedModel) document.getElementById('inspire-llm-model').value = savedModel;
    if (savedKey) document.getElementById('inspire-llm-key').value = savedKey;

    // Auto-save LLM config on input change
    document.getElementById('inspire-llm-url').addEventListener('input', function() { localStorage.setItem('inspire_llm_url', this.value); });
    document.getElementById('inspire-llm-model').addEventListener('input', function() { localStorage.setItem('inspire_llm_model', this.value); });
    document.getElementById('inspire-llm-key').addEventListener('input', function() { localStorage.setItem('inspire_llm_key', this.value); });

    const inspirationBtn = document.getElementById('inspirationBtn');
    if (inspirationBtn) {
        inspirationBtn.addEventListener('click', openInspirationModal);
    }

    // Initialize event listeners for the modal
    document.getElementById('inspire-region').addEventListener('change', updateUniversesAndDelays);
    document.getElementById('inspire-search-dataset').addEventListener('click', searchDatasets);
    document.getElementById('inspire-generate').addEventListener('click', generateAlphaTemplates);
    document.getElementById('inspire-download').addEventListener('click', downloadInspirationResult);
    document.getElementById('inspire-new-task').addEventListener('click', resetInspirationTask);
    document.getElementById('inspire-close').addEventListener('click', closeInspirationModal);
    const directBtn = document.getElementById('inspire-direct');
    if (directBtn) {
        directBtn.addEventListener('click', runDirectAlphaPipeline);
    }
    const directDlBtn = document.getElementById('inspire-direct-download');
    if (directDlBtn) {
        directDlBtn.addEventListener('click', downloadPipelineZip);
    }
    
    const testBtn = document.getElementById('inspire-test-llm');
    if (testBtn) {
        testBtn.addEventListener('click', testLLMConnection);
    }
    const enhanceBtn = document.getElementById('inspire-enhance');
    if (enhanceBtn) {
        enhanceBtn.addEventListener('click', () => {
            alert('建议优先上传“直接来点 Alpha”产生的模板 JSON。若文件名不符合规则可切到手动输入。');
            openEnhanceDataTypeModal('single');
        });
    }
    const crossEnhanceBtn = document.getElementById('inspire-cross-enhance');
    if (crossEnhanceBtn) {
        crossEnhanceBtn.addEventListener('click', () => {
            alert('多源模板增强需要上传 2 个及以上 idea JSON 文件。');
            openEnhanceDataTypeModal('cross');
        });
    }
    const enhanceInput = document.getElementById('inspire-idea-file');
    if (enhanceInput) {
        enhanceInput.addEventListener('change', handleEnhanceFile);
    }
    const crossEnhanceInput = document.getElementById('inspire-cross-idea-file');
    if (crossEnhanceInput) {
        crossEnhanceInput.addEventListener('change', handleCrossEnhanceFile);
    }
    const enhanceDlBtn = document.getElementById('inspire-enhance-download');
    if (enhanceDlBtn) {
        enhanceDlBtn.addEventListener('click', downloadEnhanceZip);
    }

    // Enhance data type modal wiring
    const dtypeClose = document.getElementById('enhance-datatype-close');
    if (dtypeClose) dtypeClose.addEventListener('click', closeEnhanceDataTypeModal);
    const dtypeCancel = document.getElementById('enhance-datatype-cancel');
    if (dtypeCancel) dtypeCancel.addEventListener('click', startEnhanceManualAfterDataType);
    const dtypeConfirm = document.getElementById('enhance-datatype-confirm');
    if (dtypeConfirm) dtypeConfirm.addEventListener('click', confirmEnhanceDataType);

    // Enhance manual modal wiring
    const manualClose = document.getElementById('enhance-manual-close');
    if (manualClose) manualClose.addEventListener('click', closeEnhanceManualModal);
    const manualBack = document.getElementById('enhance-manual-back');
    if (manualBack) manualBack.addEventListener('click', () => {
        closeEnhanceManualModal();
        const input = inspirationState.enhanceMode === 'cross'
            ? document.getElementById('inspire-cross-idea-file')
            : document.getElementById('inspire-idea-file');
        if (input) input.click();
    });
    const manualSubmit = document.getElementById('enhance-manual-submit');
    if (manualSubmit) manualSubmit.addEventListener('click', submitEnhanceManual);
    const manualCrossAdd = document.getElementById('enhance-manual-cross-add');
    if (manualCrossAdd) {
        manualCrossAdd.addEventListener('click', () => {
            appendCrossManualEntry();
        });
    }

    // Manual input auto-normalization
    const manualDatasetId = document.getElementById('enhance-manual-datasetId');
    if (manualDatasetId) {
        manualDatasetId.addEventListener('input', () => {
            manualDatasetId.value = String(manualDatasetId.value || '').toLowerCase();
        });
    }
    const manualRegion = document.getElementById('enhance-manual-region');
    if (manualRegion) {
        manualRegion.addEventListener('input', () => {
            manualRegion.value = String(manualRegion.value || '').toUpperCase();
        });
    }
    
    // Initially disable generate button until tested
    const genBtn = document.getElementById('inspire-generate');
    if (genBtn) {
        genBtn.disabled = true;
        genBtn.title = "Please test LLM connection first";
    }
    
    // Initially disable new task button
    const newTaskBtn = document.getElementById('inspire-new-task');
    if (newTaskBtn) {
        newTaskBtn.disabled = true;
        newTaskBtn.style.opacity = '0.5';
        newTaskBtn.style.cursor = 'not-allowed';
    }

    // Check login status periodically or on load to update button state
    checkLoginAndUpdateButton();
});

function validateDatasetIdHasLettersAndDigits(datasetId) {
    const v = String(datasetId || '').trim();
    if (!v) return false;
    const hasLetter = /[a-z]/i.test(v);
    const hasDigit = /\d/.test(v);
    return hasLetter && hasDigit;
}

function isValidIdeaFilename(filename) {
    // Expected: <dataset_id>_<region>_<delay>_idea_<timestamp>.json
    const name = (filename || '').trim();
    if (!name) return false;
    const parts = name.split('_');
    if (parts.length < 5) return false;
    if (parts[parts.length - 2] !== 'idea') return false;
    const delayStr = parts[parts.length - 3];
    if (!/^\d+$/.test(delayStr)) return false;
    const region = parts[parts.length - 4];
    if (!region) return false;
    const datasetId = parts.slice(0, parts.length - 4).join('_');
    return !!datasetId;
}

function openEnhanceManualModal(prefill = {}) {
    const modal = document.getElementById('enhanceManualModal');
    if (!modal) {
        alert('缺少手动输入窗口（enhanceManualModal）。');
        return;
    }

    const datasetIdEl = document.getElementById('enhance-manual-datasetId');
    const regionEl = document.getElementById('enhance-manual-region');
    const delayEl = document.getElementById('enhance-manual-delay');
    const universeEl = document.getElementById('enhance-manual-universe');
    const templateEl = document.getElementById('enhance-manual-template');
    const ideaEl = document.getElementById('enhance-manual-idea');
    const crossFields = document.getElementById('enhance-manual-cross-fields');
    const titleEl = document.getElementById('enhance-manual-title');

    const currentRegion = (document.getElementById('inspire-region') || {}).value || '';
    const currentDelay = (document.getElementById('inspire-delay') || {}).value || '';
    const currentUniverse = (document.getElementById('inspire-universe') || {}).value || '';
    const currentDatasetId = inspirationState.selectedDataset || '';

    if (datasetIdEl) datasetIdEl.value = (prefill.datasetId ?? datasetIdEl.value) || currentDatasetId;
    if (regionEl) regionEl.value = (prefill.region ?? regionEl.value) || currentRegion;
    if (delayEl) delayEl.value = (prefill.delay ?? delayEl.value) || currentDelay;
    if (universeEl) universeEl.value = (prefill.universe ?? universeEl.value) || currentUniverse;
    if (templateEl && prefill.template !== undefined) templateEl.value = prefill.template;
    if (ideaEl && prefill.idea !== undefined) ideaEl.value = prefill.idea;

    const isCrossManual = inspirationState.enhanceMode === 'cross';
    if (crossFields) crossFields.style.display = isCrossManual ? 'block' : 'none';
    ensureCrossManualEntries(isCrossManual);
    if (titleEl) titleEl.textContent = isCrossManual
        ? '手动输入 - 多源模板增强'
        : '手动输入 - 增强单个历史模板';

    // Enforce casing rules
    if (datasetIdEl) datasetIdEl.value = String(datasetIdEl.value || '').toLowerCase();
    if (regionEl) regionEl.value = String(regionEl.value || '').toUpperCase();

    modal.style.display = 'block';
}

function closeEnhanceManualModal() {
    const modal = document.getElementById('enhanceManualModal');
    if (modal) modal.style.display = 'none';
}

function buildCrossManualEntry(index, prefill = {}) {
    const wrapper = document.createElement('div');
    wrapper.className = 'enhance-cross-manual-entry';
    wrapper.style.marginBottom = '12px';
    wrapper.style.border = '1px solid #eee';
    wrapper.style.borderRadius = '6px';
    wrapper.style.padding = '10px';

    const title = document.createElement('div');
    title.style.display = 'flex';
    title.style.justifyContent = 'space-between';
    title.style.alignItems = 'center';
    title.style.marginBottom = '8px';

    const label = document.createElement('span');
    label.style.fontSize = '0.9em';
    label.style.color = '#666';
    label.textContent = `第 ${index} 组`;

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-outline';
    removeBtn.classList.add('enhance-cross-manual-remove');
    removeBtn.style.padding = '2px 8px';
    removeBtn.style.fontSize = '12px';
    removeBtn.textContent = '删除';
    removeBtn.addEventListener('click', () => {
        const list = document.getElementById('enhance-manual-cross-list');
        const count = list ? list.querySelectorAll('.enhance-cross-manual-entry').length : 0;
        if (count <= 1) {
            alert('cross 手动模式至少需要 2 组 template/idea，不能再删除了。');
            return;
        }
        wrapper.remove();
        refreshCrossManualEntryLabels();
    });

    title.appendChild(label);
    title.appendChild(removeBtn);

    const templateLabel = document.createElement('label');
    templateLabel.style.display = 'block';
    templateLabel.style.marginBottom = '6px';
    templateLabel.style.fontSize = '0.85em';
    templateLabel.style.color = '#666';
    templateLabel.textContent = 'Alpha模板template（必填）';

    const templateInput = document.createElement('textarea');
    templateInput.className = 'form-input enhance-cross-manual-template';
    templateInput.rows = 3;
    templateInput.style.width = '100%';
    templateInput.style.marginBottom = '8px';
    templateInput.placeholder = '例如 rank(ts_delta({ret}, 5))';
    templateInput.value = String(prefill.template || '');

    const ideaLabel = document.createElement('label');
    ideaLabel.style.display = 'block';
    ideaLabel.style.marginBottom = '6px';
    ideaLabel.style.fontSize = '0.85em';
    ideaLabel.style.color = '#666';
    ideaLabel.textContent = 'Alpha Template idea（可选）';

    const ideaInput = document.createElement('textarea');
    ideaInput.className = 'form-input enhance-cross-manual-idea';
    ideaInput.rows = 2;
    ideaInput.style.width = '100%';
    ideaInput.placeholder = '用中文描述该组 alpha idea';
    ideaInput.value = String(prefill.idea || '');

    wrapper.appendChild(title);
    wrapper.appendChild(templateLabel);
    wrapper.appendChild(templateInput);
    wrapper.appendChild(ideaLabel);
    wrapper.appendChild(ideaInput);
    return wrapper;
}

function refreshCrossManualEntryLabels() {
    const list = document.getElementById('enhance-manual-cross-list');
    if (!list) return;
    const entries = list.querySelectorAll('.enhance-cross-manual-entry');
    entries.forEach((entry, idx) => {
        const label = entry.querySelector('span');
        if (label) label.textContent = `第 ${idx + 2} 组`;
        const removeBtn = entry.querySelector('.enhance-cross-manual-remove');
        if (removeBtn) {
            const canRemove = entries.length > 1;
            removeBtn.disabled = !canRemove;
            removeBtn.style.opacity = canRemove ? '1' : '0.5';
            removeBtn.title = canRemove ? '删除该组' : '至少保留 2 组，当前不可删除';
        }
    });
}

function appendCrossManualEntry(prefill = {}) {
    const list = document.getElementById('enhance-manual-cross-list');
    if (!list) return;
    const index = list.querySelectorAll('.enhance-cross-manual-entry').length + 2;
    list.appendChild(buildCrossManualEntry(index, prefill));
}

function ensureCrossManualEntries(enableCross) {
    const list = document.getElementById('enhance-manual-cross-list');
    if (!list) return;
    if (!enableCross) {
        list.innerHTML = '';
        return;
    }
    if (list.querySelectorAll('.enhance-cross-manual-entry').length === 0) {
        appendCrossManualEntry();
    } else {
        refreshCrossManualEntryLabels();
    }
}

function submitEnhanceManual() {
    const apiKey = document.getElementById('inspire-llm-key').value;
    const baseUrl = document.getElementById('inspire-llm-url').value;
    const model = document.getElementById('inspire-llm-model').value;
    if (!apiKey) {
        alert('请输入 LLM API Key。');
        return;
    }

    const datasetIdRaw = (document.getElementById('enhance-manual-datasetId') || {}).value || '';
    const regionRaw = (document.getElementById('enhance-manual-region') || {}).value || '';
    const delay = (document.getElementById('enhance-manual-delay') || {}).value || '';
    const template = (document.getElementById('enhance-manual-template') || {}).value || '';
    const idea = (document.getElementById('enhance-manual-idea') || {}).value || '';

    const datasetId = String(datasetIdRaw || '').toLowerCase();
    const region = String(regionRaw || '').toUpperCase();

    // Keep UI consistent with enforced casing
    const datasetEl = document.getElementById('enhance-manual-datasetId');
    if (datasetEl) datasetEl.value = datasetId;
    const regionEl = document.getElementById('enhance-manual-region');
    if (regionEl) regionEl.value = region;

    if (!datasetId.trim() || !region.trim() || !String(delay).trim() || !template.trim()) {
        alert('请填写 datasetId / region / delay / template（template 为必填）。');
        return;
    }

    if (!validateDatasetIdHasLettersAndDigits(datasetId)) {
        alert('datasetId 必须同时包含字母和数字，例如 fundamental3。');
        return;
    }

    const isCrossManual = inspirationState.enhanceMode === 'cross';
    let manualTemplates = [{ template, idea }];
    if (isCrossManual) {
        const list = document.getElementById('enhance-manual-cross-list');
        const entries = list ? Array.from(list.querySelectorAll('.enhance-cross-manual-entry')) : [];
        for (const entry of entries) {
            const tEl = entry.querySelector('.enhance-cross-manual-template');
            const iEl = entry.querySelector('.enhance-cross-manual-idea');
            manualTemplates.push({
                template: String((tEl && tEl.value) || '').trim(),
                idea: String((iEl && iEl.value) || '').trim(),
            });
        }
        manualTemplates = manualTemplates.filter(item => String(item.template || '').trim());
        if (manualTemplates.length < 2) {
            alert('多源模板增强手动输入至少需要两组 template。请继续添加并填写。');
            return;
        }
    }

    closeEnhanceManualModal();
    inspirationState.activeEnhanceMode = isCrossManual ? 'cross' : 'single';

    const outputDiv = document.getElementById('inspire-output');
    outputDiv.innerHTML = '<pre id="inspire-enhance-stream" style="white-space: pre-wrap; margin: 0;"></pre>';

    const enhanceBtn = document.getElementById('inspire-enhance');
    const crossBtn = document.getElementById('inspire-cross-enhance');
    if (enhanceBtn) {
        enhanceBtn.disabled = true;
        enhanceBtn.textContent = '处理中...';
    }
    if (crossBtn) {
        crossBtn.disabled = true;
        crossBtn.textContent = '处理中...';
    }
    const enhanceDlBtn = document.getElementById('inspire-enhance-download');
    if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';

    const formData = new FormData();
    formData.append('apiKey', apiKey);
    formData.append('baseUrl', baseUrl);
    formData.append('model', model);
    formData.append('dataType', inspirationState.enhanceDataType || 'MATRIX');
    formData.append('datasetId', datasetId);
    formData.append('region', region);
    formData.append('delay', String(delay));
    formData.append('universe', (document.getElementById('enhance-manual-universe') || {}).value || '');
    formData.append('template', template);
    formData.append('idea', idea);
    if (isCrossManual) {
        formData.append('manualTemplates', JSON.stringify(manualTemplates));
    }

    const endpoint = isCrossManual
        ? '/api/inspiration/cross-enhance-template'
        : '/api/inspiration/enhance-template';

    fetch(endpoint, {
        method: 'POST',
        headers: { 'Session-ID': localStorage.getItem('brain_session_id') || '' },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            outputDiv.innerHTML = '启动失败: ' + (data.error || '未知错误');
            if (enhanceBtn) {
                enhanceBtn.disabled = false;
                enhanceBtn.textContent = '增强单个历史模板';
            }
            if (crossBtn) {
                crossBtn.disabled = false;
                crossBtn.textContent = '多源模板增强';
            }
            return;
        }
        inspirationState.enhanceTaskId = data.taskId;
        startEnhanceStream(data.taskId);
    })
    .catch(err => {
        outputDiv.innerHTML = '启动出错: ' + err;
        if (enhanceBtn) {
            enhanceBtn.disabled = false;
            enhanceBtn.textContent = '增强单个历史模板';
        }
        if (crossBtn) {
            crossBtn.disabled = false;
            crossBtn.textContent = '多源模板增强';
        }
    });
}

function getHeaders() {
    const headers = {'Content-Type': 'application/json'};
    const sessionId = localStorage.getItem('brain_session_id');
    if (sessionId) {
        headers['Session-ID'] = sessionId;
    }
    return headers;
}

function checkLoginAndUpdateButton() {
    fetch('/api/check_login', { headers: getHeaders() })
        .then(response => response.json())
        .then(data => {
            const btn = document.getElementById('inspirationBtn');
            if (data.logged_in) {
                inspirationState.isLoggedIn = true;
                if (btn) {
                    btn.style.opacity = '1';
                    btn.style.cursor = 'pointer';
                    btn.disabled = false;
                }
            } else {
                inspirationState.isLoggedIn = false;
                if (btn) {
                    btn.style.opacity = '0.5';
                    btn.style.cursor = 'not-allowed';
                    btn.disabled = true;
                }
            }
        })
        .catch(err => {
            console.error("Error checking login status:", err);
            const btn = document.getElementById('inspirationBtn');
            if (btn) {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
            }
        });
}

// Expose this function globally so other scripts (like brain.js) can call it after login
window.updateInspirationButtonState = checkLoginAndUpdateButton;

function openInspirationModal() {
    if (!inspirationState.isLoggedIn) {
        // Double check
        fetch('/api/check_login', { headers: getHeaders() })
            .then(response => response.json())
            .then(data => {
                if (data.logged_in) {
                    inspirationState.isLoggedIn = true;
                    document.getElementById('inspirationModal').style.display = 'block';
                    loadInspirationOptions();
                } else {
                    // Trigger Brain Login Modal
                    if (typeof openBrainLoginModal === 'function') {
                        openBrainLoginModal();
                    } else {
                        alert("请先登录 BRAIN。");
                    }
                }
            });
        return;
    }
    document.getElementById('inspirationModal').style.display = 'block';
    loadInspirationOptions();
}
function closeInspirationModal() {
    document.getElementById('inspirationModal').style.display = 'none';
}

function loadInspirationOptions() {
    if (inspirationState.options) return; // Already loaded

    fetch('/api/inspiration/options', { headers: getHeaders() })
        .then(res => res.json())
        .then(data => {
            inspirationState.options = data;
            populateRegionDropdown(data);
        })
        .catch(err => console.error("Failed to load options:", err));
}

function populateRegionDropdown(data) {
    const regionSelect = document.getElementById('inspire-region');
    regionSelect.innerHTML = '<option value="">Select Region</option>';
    
    // Assuming data structure matches what we get from ace_lib
    // Structure: { "EQUITY": { "USA": { ... }, "CHN": { ... } } }
    // We'll focus on EQUITY for now or iterate all
    
    let regions = new Set();
    if (data.EQUITY) {
        Object.keys(data.EQUITY).forEach(r => regions.add(r));
    }
    
    regions.forEach(r => {
        const option = document.createElement('option');
        option.value = r;
        option.textContent = r;
        regionSelect.appendChild(option);
    });
}

function updateUniversesAndDelays() {
    const region = document.getElementById('inspire-region').value;
    const universeSelect = document.getElementById('inspire-universe');
    const delaySelect = document.getElementById('inspire-delay');
    
    universeSelect.innerHTML = '<option value="">Select Universe</option>';
    delaySelect.innerHTML = '<option value="">Select Delay</option>';
    
    if (!region || !inspirationState.options || !inspirationState.options.EQUITY || !inspirationState.options.EQUITY[region]) return;
    
    const data = inspirationState.options.EQUITY[region];
    
    data.universes.forEach(u => {
        const option = document.createElement('option');
        option.value = u;
        option.textContent = u;
        universeSelect.appendChild(option);
    });
    
    data.delays.forEach(d => {
        const option = document.createElement('option');
        option.value = d;
        option.textContent = d;
        delaySelect.appendChild(option);
    });
}

function searchDatasets() {
    const region = document.getElementById('inspire-region').value;
    const delay = document.getElementById('inspire-delay').value;
    const universe = document.getElementById('inspire-universe').value;
    const search = document.getElementById('inspire-dataset-search').value;
    
    if (!region || !delay || !universe) {
        alert("请先选择区域、延迟和股票池。");
        return;
    }
    
    const resultsDiv = document.getElementById('inspire-dataset-results');
    resultsDiv.innerHTML = '正在加载数据集...';
    
    fetch('/api/inspiration/datasets', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ region, delay, universe, search })
    })
    .then(res => res.json())
    .then(data => {
        displayDatasetResults(data);
    })
    .catch(err => {
        resultsDiv.innerHTML = '加载数据集出错: ' + err;
    });
}

function displayDatasetResults(datasets) {
    const resultsDiv = document.getElementById('inspire-dataset-results');
    resultsDiv.innerHTML = '';
    
    if (datasets.length === 0) {
        resultsDiv.innerHTML = '未找到数据集。';
        return;
    }
    
    const table = document.createElement('table');
    table.className = 'dataset-table'; 
    table.style.width = '100%'; // Ensure full width
    table.style.borderCollapse = 'collapse';
    
    table.innerHTML = `
        <thead>
            <tr style="text-align: left; background: #f1f1f1;">
                <th style="padding: 8px; border-bottom: 1px solid #ddd;">ID</th>
                <th style="padding: 8px; border-bottom: 1px solid #ddd;">Name</th>
                <th style="padding: 8px; border-bottom: 1px solid #ddd;">Category</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    
    const tbody = table.querySelector('tbody');
    
    datasets.forEach(ds => {
        const tr = document.createElement('tr');
        tr.dataset.id = ds.id;
        tr.style.cursor = 'pointer';
        tr.style.transition = 'background-color 0.2s';
        
        // Fix [object Object] issue for category
        let category = ds.category;
        if (typeof category === 'object' && category !== null) {
            // Try to find a meaningful string representation
            category = category.name || category.id || JSON.stringify(category);
        }
        
        tr.innerHTML = `
            <td style="padding: 8px; border-bottom: 1px solid #eee; color: #007bff; font-weight: bold;">${ds.id}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">${ds.name}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">${category}</td>
        `;
        
        tr.addEventListener('click', function() {
            selectDataset(ds.id, category);
        });
        
        tr.addEventListener('mouseenter', function() {
            if (inspirationState.selectedDataset !== ds.id) {
                this.style.backgroundColor = '#f8f9fa';
            }
        });
        
        tr.addEventListener('mouseleave', function() {
            if (inspirationState.selectedDataset !== ds.id) {
                this.style.backgroundColor = '';
            }
        });

        tbody.appendChild(tr);
    });
    
    resultsDiv.appendChild(table);
}

function selectDataset(id, category) {
    inspirationState.selectedDataset = id;
    inspirationState.selectedDatasetCategory = category || null;
    const display = document.getElementById('inspire-selected-dataset');
    if (display) {
        display.textContent = "已选数据集: " + id;
        display.style.display = 'block';
    }
    
    // Highlight the selected row
    document.querySelectorAll('.dataset-table tr').forEach(tr => tr.style.backgroundColor = '');
    const row = document.querySelector(`.dataset-table tr[data-id="${id}"]`);
    if (row) {
        row.style.backgroundColor = '#e7f1ff';
    }
}

// Removed toggleAccordion as we are moving to a horizontal layout

function generateAlphaTemplates() {
    if (!inspirationState.selectedDataset) {
        alert("请先选择一个数据集。");
        return;
    }
    
    const apiKey = document.getElementById('inspire-llm-key').value;
    const baseUrl = document.getElementById('inspire-llm-url').value;
    const model = document.getElementById('inspire-llm-model').value;
    
    if (!apiKey) {
        alert("请输入 LLM API Key。");
        return;
    }
    
    const region = document.getElementById('inspire-region').value;
    const delay = document.getElementById('inspire-delay').value;
    const universe = document.getElementById('inspire-universe').value;
    const dataType = (document.getElementById('inspire-data-type') || {}).value || 'MATRIX';
    
    const outputDiv = document.getElementById('inspire-output');
    outputDiv.innerHTML = '正在生成模板... 这可能需要几分钟...';
    
    fetch('/api/inspiration/generate', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            apiKey, baseUrl, model,
            region, delay, universe,
            datasetId: inspirationState.selectedDataset,
            dataType
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            outputDiv.innerHTML = '错误: ' + data.error;
        } else {
            // Render Markdown
            // Assuming marked.js or similar is available, or just text for now
            // If you have a markdown renderer, use it.
            // For now, simple text or basic HTML replacement
            outputDiv.innerHTML = formatMarkdown(data.result);
            inspirationState.lastResult = data.result;
            const dlBtn = document.getElementById('inspire-download');
            if (dlBtn) dlBtn.style.display = 'inline-block';
            
            const newTaskBtn = document.getElementById('inspire-new-task');
            if (newTaskBtn) {
                newTaskBtn.disabled = false;
                newTaskBtn.style.opacity = '1';
                newTaskBtn.style.cursor = 'pointer';
            }
        }
    })
    .catch(err => {
        outputDiv.innerHTML = '生成模板出错: ' + err;
    });
}

function runDirectAlphaPipeline() {
    if (!inspirationState.selectedDataset) {
        alert("请先选择一个数据集。");
        return;
    }

    const region = document.getElementById('inspire-region').value;
    const delay = document.getElementById('inspire-delay').value;
    const universe = document.getElementById('inspire-universe').value;
    const dataType = (document.getElementById('inspire-data-type') || {}).value || 'MATRIX';
    const dataCategory = inspirationState.selectedDatasetCategory;

    if (!region || !delay || !universe) {
        alert("请先选择区域、延迟和股票池。");
        return;
    }

    if (!dataCategory) {
        alert("当前数据集没有可用的分类信息，无法运行。请重新搜索并选择数据集。");
        return;
    }

    const apiKey = document.getElementById('inspire-llm-key').value;
    const baseUrl = document.getElementById('inspire-llm-url').value;
    const model = document.getElementById('inspire-llm-model').value;

    if (!apiKey) {
        alert('请先填写 LLM API Key。');
        return;
    }

    const outputDiv = document.getElementById('inspire-output');
    outputDiv.innerHTML = '<pre id="inspire-stream" style="white-space: pre-wrap; margin: 0;"></pre>';

    const directBtn = document.getElementById('inspire-direct');
    if (directBtn) {
        directBtn.disabled = true;
        directBtn.textContent = '正在运行...';
    }

    const dlBtn = document.getElementById('inspire-direct-download');
    if (dlBtn) dlBtn.style.display = 'none';

    if (inspirationState.pipelineEventSource) {
        inspirationState.pipelineEventSource.close();
        inspirationState.pipelineEventSource = null;
    }

    fetch('/api/inspiration/run-pipeline', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            datasetId: inspirationState.selectedDataset,
            dataCategory,
            region,
            delay,
            universe,
            dataType,
            apiKey,
            baseUrl,
            model
        })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            outputDiv.innerHTML = '启动失败: ' + (data.error || '未知错误');
            if (directBtn) {
                directBtn.disabled = false;
                directBtn.textContent = '直接来点 Alpha';
            }
            return;
        }

        inspirationState.pipelineTaskId = data.taskId;
        startPipelineStream(data.taskId);
    })
    .catch(err => {
        outputDiv.innerHTML = '启动出错: ' + err;
        if (directBtn) {
            directBtn.disabled = false;
            directBtn.textContent = '直接来点 Alpha';
        }
    });
}

function startPipelineStream(taskId) {
    const streamEl = document.getElementById('inspire-stream');
    const outputDiv = document.getElementById('inspire-output');
    if (!streamEl) {
        outputDiv.innerHTML = '<pre id="inspire-stream" style="white-space: pre-wrap; margin: 0;"></pre>';
    }
    const target = document.getElementById('inspire-stream');

    const source = new EventSource(`/api/inspiration/stream-pipeline/${taskId}`);
    inspirationState.pipelineEventSource = source;

    source.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            if (payload && payload.line !== undefined) {
                target.textContent += payload.line + '\n';
                outputDiv.scrollTop = outputDiv.scrollHeight;
            }
        } catch {
            target.textContent += event.data + '\n';
            outputDiv.scrollTop = outputDiv.scrollHeight;
        }
    };

    source.addEventListener('done', (event) => {
        let info = null;
        try {
            info = JSON.parse(event.data);
        } catch {
            info = { success: false };
        }
        const directBtn = document.getElementById('inspire-direct');
        if (directBtn) {
            directBtn.disabled = false;
            directBtn.textContent = '直接来点 Alpha';
        }

        if (info && info.success) {
            target.textContent += '\n✅ 运行完成，可下载结果 ZIP。\n';
            const dlBtn = document.getElementById('inspire-direct-download');
            if (dlBtn) dlBtn.style.display = 'inline-block';
        } else {
            target.textContent += '\n❌ 运行失败，请检查日志。\n';
        }

        source.close();
        inspirationState.pipelineEventSource = null;
    });

    source.addEventListener('error', () => {
        const directBtn = document.getElementById('inspire-direct');
        if (directBtn) {
            directBtn.disabled = false;
            directBtn.textContent = '直接来点 Alpha';
        }
        target.textContent += '\n⚠️ 日志流中断。\n';
        source.close();
        inspirationState.pipelineEventSource = null;
    });
}

function downloadPipelineZip() {
    if (!inspirationState.pipelineTaskId) return;
    window.location.href = `/api/inspiration/download-pipeline/${inspirationState.pipelineTaskId}`;
}

function formatMarkdown(text) {
    if (typeof marked !== 'undefined') {
        // Split text by code blocks (triple backticks or single backticks)
        // We want to escape < and > in normal text, but NOT in code blocks
        const parts = text.split(/(```[\s\S]*?```|`[^`]*`)/g);
        
        const escapedParts = parts.map(part => {
            // If it starts with backtick, it's a code block -> return as is
            if (part.startsWith('`')) {
                return part;
            }
            // Otherwise, escape < and >
            return part.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        });
        
        return marked.parse(escapedParts.join(''));
    }
    
    // Fallback simple formatter
    // Here we DO need to escape because we are building HTML manually
    const escapedText = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    let html = escapedText
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/\n/g, '<br>');
    return html;
}

function testLLMConnection() {
    const apiKey = document.getElementById('inspire-llm-key').value;
    const baseUrl = document.getElementById('inspire-llm-url').value;
    const model = document.getElementById('inspire-llm-model').value;
    const testBtn = document.getElementById('inspire-test-llm');
    const generateBtn = document.getElementById('inspire-generate');
    const enhanceBtn = document.getElementById('inspire-enhance');
    const crossEnhanceBtn = document.getElementById('inspire-cross-enhance');
    const enhanceDlBtn = document.getElementById('inspire-enhance-download');
    
    if (!apiKey) {
        alert("请先输入 API Key。");
        return;
    }
    
    testBtn.textContent = "测试中...";
    testBtn.disabled = true;
    
    fetch('/api/inspiration/test_llm', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ apiKey, baseUrl, model })
    })
    .then(res => res.json())
    .then(data => {
        testBtn.disabled = false;
        if (data.success) {
            testBtn.textContent = "成功";
            testBtn.className = "btn btn-success";
            generateBtn.disabled = false;
            if (enhanceBtn) enhanceBtn.disabled = false;
            if (crossEnhanceBtn) crossEnhanceBtn.disabled = false;
            if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';
            setTimeout(() => { testBtn.textContent = "测试连接"; testBtn.className = "btn btn-secondary"; }, 3000);
        } else {
            testBtn.textContent = "失败";
            testBtn.className = "btn btn-danger";
            alert("连接失败: " + data.error);
            generateBtn.disabled = true;
            if (enhanceBtn) enhanceBtn.disabled = true;
            if (crossEnhanceBtn) crossEnhanceBtn.disabled = true;
            if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';
            setTimeout(() => { testBtn.textContent = "测试连接"; testBtn.className = "btn btn-secondary"; }, 3000);
        }
    })
    .catch(err => {
        testBtn.disabled = false;
        testBtn.textContent = "错误";
        alert("错误: " + err);
        if (enhanceBtn) enhanceBtn.disabled = true;
        if (crossEnhanceBtn) crossEnhanceBtn.disabled = true;
        if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';
    });
}

function handleEnhanceFile(event) {
    const files = event.target.files ? Array.from(event.target.files) : [];
    if (files.length === 0) return;

    // If filenames are not parseable by backend/script, switch to manual mode.
    const invalid = files.filter(f => !isValidIdeaFilename(f.name));
    if (invalid.length > 0) {
        const first = files[0];
        // Try prefill template/idea from the first JSON.
        const reader = new FileReader();
        reader.onload = () => {
            let prefill = {};
            try {
                const obj = JSON.parse(String(reader.result || ''));
                if (obj && typeof obj === 'object') {
                    prefill = {
                        template: obj.template || '',
                        idea: obj.idea || ''
                    };
                }
            } catch {
                prefill = {};
            }
            alert('你选择的 idea JSON 文件名不符合规则，已切换到手动输入模式。');
            openEnhanceManualModal(prefill);
        };
        reader.onerror = () => {
            alert('你选择的 idea JSON 文件名不符合规则，已切换到手动输入模式。');
            openEnhanceManualModal({});
        };
        reader.readAsText(first);
        event.target.value = '';
        return;
    }

    const apiKey = document.getElementById('inspire-llm-key').value;
    const baseUrl = document.getElementById('inspire-llm-url').value;
    const model = document.getElementById('inspire-llm-model').value;
    if (!apiKey) {
        alert("请输入 LLM API Key。");
        return;
    }

    const outputDiv = document.getElementById('inspire-output');
    outputDiv.innerHTML = '<pre id="inspire-enhance-stream" style="white-space: pre-wrap; margin: 0;"></pre>';
    inspirationState.activeEnhanceMode = 'single';

    const enhanceBtn = document.getElementById('inspire-enhance');
    if (enhanceBtn) {
        enhanceBtn.disabled = true;
        enhanceBtn.textContent = '处理中...';
    }
    const enhanceDlBtn = document.getElementById('inspire-enhance-download');
    if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';

    const formData = new FormData();
    files.forEach(file => formData.append('ideaFiles', file));
    formData.append('apiKey', apiKey);
    formData.append('baseUrl', baseUrl);
    formData.append('model', model);
    formData.append('dataType', inspirationState.enhanceDataType || 'MATRIX');

    fetch('/api/inspiration/enhance-template', {
        method: 'POST',
        headers: { 'Session-ID': localStorage.getItem('brain_session_id') || '' },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            if (data && data.errorCode === 'NEED_MANUAL_INPUT') {
                outputDiv.innerHTML = '需要手动输入 dataset/template/idea。请在弹窗中填写后继续。';
                openEnhanceManualModal({});
            } else {
                outputDiv.innerHTML = '启动失败: ' + (data.error || '未知错误');
            }
            if (enhanceBtn) {
                enhanceBtn.disabled = false;
                enhanceBtn.textContent = '增强单个历史模板';
            }
            return;
        }
        inspirationState.enhanceTaskId = data.taskId;
        startEnhanceStream(data.taskId);
    })
    .catch(err => {
        outputDiv.innerHTML = '启动出错: ' + err;
        if (enhanceBtn) {
            enhanceBtn.disabled = false;
            enhanceBtn.textContent = '增强单个历史模板';
        }
    })
    .finally(() => {
        event.target.value = '';
    });
}

function handleCrossEnhanceFile(event) {
    const files = event.target.files ? Array.from(event.target.files) : [];
    if (files.length === 0) return;

    if (files.length < 2) {
        alert('多源模板增强至少需要上传 2 个 idea JSON 文件。');
        event.target.value = '';
        return;
    }

    const apiKey = document.getElementById('inspire-llm-key').value;
    const baseUrl = document.getElementById('inspire-llm-url').value;
    const model = document.getElementById('inspire-llm-model').value;
    if (!apiKey) {
        alert('请输入 LLM API Key。');
        event.target.value = '';
        return;
    }

    const outputDiv = document.getElementById('inspire-output');
    outputDiv.innerHTML = '<pre id="inspire-enhance-stream" style="white-space: pre-wrap; margin: 0;"></pre>';
    inspirationState.activeEnhanceMode = 'cross';
    const crossStyleEl = document.getElementById('inspire-cross-style');
    const crossStyle = crossStyleEl ? String(crossStyleEl.value || 'balanced').trim() : 'balanced';

    const crossBtn = document.getElementById('inspire-cross-enhance');
    if (crossBtn) {
        crossBtn.disabled = true;
        crossBtn.textContent = '处理中...';
    }
    const enhanceDlBtn = document.getElementById('inspire-enhance-download');
    if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';

    const formData = new FormData();
    files.forEach(file => formData.append('ideaFiles', file));
    formData.append('apiKey', apiKey);
    formData.append('baseUrl', baseUrl);
    formData.append('model', model);
    formData.append('dataType', inspirationState.enhanceDataType || 'MATRIX');
    formData.append('crossStyle', crossStyle || 'balanced');

    fetch('/api/inspiration/cross-enhance-template', {
        method: 'POST',
        headers: { 'Session-ID': localStorage.getItem('brain_session_id') || '' },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            outputDiv.innerHTML = '启动失败: ' + (data.error || '未知错误');
            if (crossBtn) {
                crossBtn.disabled = false;
                crossBtn.textContent = '多源模板增强';
            }
            return;
        }
        inspirationState.enhanceTaskId = data.taskId;
        startEnhanceStream(data.taskId);
    })
    .catch(err => {
        outputDiv.innerHTML = '启动出错: ' + err;
        if (crossBtn) {
            crossBtn.disabled = false;
            crossBtn.textContent = '多源模板增强';
        }
    })
    .finally(() => {
        event.target.value = '';
    });
}

function openEnhanceDataTypeModal(mode = 'single') {
    inspirationState.enhanceMode = mode === 'cross' ? 'cross' : 'single';
    const modal = document.getElementById('enhanceDataTypeModal');
    if (!modal) {
        // Fallback: if modal missing, proceed with default.
        const input = inspirationState.enhanceMode === 'cross'
            ? document.getElementById('inspire-cross-idea-file')
            : document.getElementById('inspire-idea-file');
        if (input) input.click();
        return;
    }

    // Default to MATRIX each time unless user already picked.
    const sel = document.getElementById('inspire-enhance-data-type');
    if (sel) sel.value = inspirationState.enhanceDataType || 'MATRIX';
    const crossStyleRow = document.getElementById('enhance-cross-style-row');
    if (crossStyleRow) crossStyleRow.style.display = inspirationState.enhanceMode === 'cross' ? 'block' : 'none';
    const crossStyleSel = document.getElementById('inspire-cross-style');
    if (crossStyleSel && !crossStyleSel.value) crossStyleSel.value = 'balanced';
    modal.style.display = 'block';
}

function closeEnhanceDataTypeModal() {
    const modal = document.getElementById('enhanceDataTypeModal');
    if (modal) modal.style.display = 'none';
}

function confirmEnhanceDataType() {
    const sel = document.getElementById('inspire-enhance-data-type');
    const dt = sel ? sel.value : 'MATRIX';
    inspirationState.enhanceDataType = (dt === 'VECTOR') ? 'VECTOR' : 'MATRIX';
    closeEnhanceDataTypeModal();
    const input = inspirationState.enhanceMode === 'cross'
        ? document.getElementById('inspire-cross-idea-file')
        : document.getElementById('inspire-idea-file');
    if (input) input.click();
}

function startEnhanceManualAfterDataType() {
    const sel = document.getElementById('inspire-enhance-data-type');
    const dt = sel ? sel.value : 'MATRIX';
    inspirationState.enhanceDataType = (dt === 'VECTOR') ? 'VECTOR' : 'MATRIX';
    closeEnhanceDataTypeModal();
    openEnhanceManualModal({});
}

function startEnhanceStream(taskId) {
    const outputDiv = document.getElementById('inspire-output');
    const streamEl = document.getElementById('inspire-enhance-stream');
    if (!streamEl) {
        outputDiv.innerHTML = '<pre id="inspire-enhance-stream" style="white-space: pre-wrap; margin: 0;"></pre>';
    }
    const target = document.getElementById('inspire-enhance-stream');

    const source = new EventSource(`/api/inspiration/stream-enhance/${taskId}`);
    source.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            if (payload && payload.type === 'file_done') {
                target.textContent += `\n• 子任务完成: ${payload.file || ''} (${payload.success ? '成功' : '失败'})\n`;
                outputDiv.scrollTop = outputDiv.scrollHeight;
                return;
            }
            if (payload && payload.line !== undefined) {
                const prefix = payload.file ? `[${payload.file}] ` : '';
                target.textContent += prefix + payload.line + '\n';
                outputDiv.scrollTop = outputDiv.scrollHeight;
            }
        } catch {
            target.textContent += event.data + '\n';
            outputDiv.scrollTop = outputDiv.scrollHeight;
        }
    };

    source.addEventListener('done', (event) => {
        let info = null;
        try {
            info = JSON.parse(event.data);
        } catch {
            info = { success: false };
        }
        const enhanceBtn = document.getElementById('inspire-enhance');
        const crossBtn = document.getElementById('inspire-cross-enhance');
        const enhanceDlBtn = document.getElementById('inspire-enhance-download');
        if (enhanceBtn) {
            enhanceBtn.disabled = false;
            enhanceBtn.textContent = '增强单个历史模板';
        }
        if (crossBtn) {
            crossBtn.disabled = false;
            crossBtn.textContent = '多源模板增强';
        }
        if (enhanceDlBtn) {
            enhanceDlBtn.style.display = info && info.success ? 'inline-block' : 'none';
        }
        if (info && info.success) {
            target.textContent += '\n✅ 已完成 1/1\n';
        } else {
            target.textContent += '\n❌ 执行失败 0/1\n';
            if (info && info.error) {
                target.textContent += `错误: ${info.error}\n`;
            }
        }
        outputDiv.scrollTop = outputDiv.scrollHeight;
        source.close();
    });

    source.addEventListener('error', () => {
        const enhanceBtn = document.getElementById('inspire-enhance');
        const crossBtn = document.getElementById('inspire-cross-enhance');
        const enhanceDlBtn = document.getElementById('inspire-enhance-download');
        if (enhanceBtn) {
            enhanceBtn.disabled = false;
            enhanceBtn.textContent = '增强单个历史模板';
        }
        if (crossBtn) {
            crossBtn.disabled = false;
            crossBtn.textContent = '多源模板增强';
        }
        if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';
        target.textContent += '\n⚠️ 日志流中断。\n';
        source.close();
    });
}

function downloadEnhanceZip() {
    if (!inspirationState.enhanceTaskId) return;
    window.location.href = `/api/inspiration/download-enhance/${inspirationState.enhanceTaskId}`;
}

function downloadInspirationResult() {
    if (!inspirationState.lastResult) return;
    
    const blob = new Blob([inspirationState.lastResult], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `alpha_inspiration_${inspirationState.selectedDataset}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function resetInspirationTask() {
    inspirationState.selectedDataset = null;
    inspirationState.selectedDatasetCategory = null;
    const display = document.getElementById('inspire-selected-dataset');
    if (display) {
        display.textContent = "";
        display.style.display = 'none';
    }
    document.getElementById('inspire-output').innerHTML = "";
    document.getElementById('inspire-dataset-results').innerHTML = "";
    
    const dlBtn = document.getElementById('inspire-download');
    if (dlBtn) dlBtn.style.display = 'none';

    const directDlBtn = document.getElementById('inspire-direct-download');
    if (directDlBtn) directDlBtn.style.display = 'none';

    const enhanceDlBtn = document.getElementById('inspire-enhance-download');
    if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';
    const enhanceBtn = document.getElementById('inspire-enhance');
    if (enhanceBtn) {
        enhanceBtn.disabled = false;
        enhanceBtn.textContent = '增强单个历史模板';
    }
    const crossBtn = document.getElementById('inspire-cross-enhance');
    if (crossBtn) {
        crossBtn.disabled = false;
        crossBtn.textContent = '多源模板增强';
    }
    inspirationState.enhanceTaskId = null;

    if (inspirationState.pipelineEventSource) {
        inspirationState.pipelineEventSource.close();
        inspirationState.pipelineEventSource = null;
    }
    inspirationState.pipelineTaskId = null;
    
    const newTaskBtn = document.getElementById('inspire-new-task');
    if (newTaskBtn) {
        newTaskBtn.disabled = true;
        newTaskBtn.style.opacity = '0.5';
        newTaskBtn.style.cursor = 'not-allowed';
    }
    // Keep LLM config and Region/Universe selections
}

function toggleInspireColumn(colId) {
    const col = document.getElementById(colId);
    if (col) {
        col.classList.toggle('collapsed');
    }
}
