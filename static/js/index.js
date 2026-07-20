let selectedSubject = null;
let selectedSubjectLabel = '';
let selectedUnit = null;
let selectedUnitTitle = '';

document.addEventListener('DOMContentLoaded', async () => {
    initApiKeyBox();
    await loadSubjects();
    document.getElementById('subjectSelect').addEventListener('change', onSubjectChange);
    document.getElementById('startBtn').addEventListener('click', onStartQuiz);
});

function initApiKeyBox() {
    const input = document.getElementById('apiKeyInput');
    const button = document.getElementById('saveKeyBtn');
    const status = document.getElementById('apiKeyStatus');
    const suggestions = document.getElementById('keySuggestions');
    const saved = Session.get('deepseek_api_key');

    // 内置预设 Key
    const BUILTIN_KEY = 'sk-02168810f6ca444fa3d964cfc332161e';
    const BUILTIN_MASKED = 'sk-0216…161e（内置默认）';

    // 输入框始终从空开始
    // 如果之前保存过 Key，在状态下提示，但不填入输入框
    if (saved) {
        status.textContent = '上次保存过 Key，仍有效。点击输入框可选择或更换。';
    }

    // 构建下拉选项（内置 Key + 之前保存的 Key 如果不同）
    let optionItems = `<li class="key-suggestion-item" data-key="${BUILTIN_KEY}">
        <span class="suggestion-label">${BUILTIN_MASKED}</span>
        <span class="suggestion-hint">点击使用</span>
    </li>`;

    if (saved && saved !== BUILTIN_KEY) {
        const savedMasked = saved.length > 12
            ? saved.slice(0, 7) + '…' + saved.slice(-4) + '（上次保存）'
            : saved + '（上次保存）';
        optionItems += `<li class="key-suggestion-item" data-key="${saved}">
            <span class="suggestion-label">${savedMasked}</span>
            <span class="suggestion-hint">点击使用</span>
        </li>`;
    }

    suggestions.innerHTML = optionItems;

    // 点击输入框 → 如果为空则显示建议列表
    input.addEventListener('focus', () => {
        if (!input.value.trim()) {
            suggestions.style.display = 'block';
        }
    });

    // 点击建议项 → 填入
    suggestions.addEventListener('click', (e) => {
        const item = e.target.closest('.key-suggestion-item');
        if (!item) return;
        input.value = item.dataset.key;
        suggestions.style.display = 'none';
        status.textContent = '已选择 Key，点击"保存"生效。';
    });

    // 用户手动输入时隐藏建议
    input.addEventListener('input', () => {
        suggestions.style.display = 'none';
    });

    // 点击外部关闭建议
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !suggestions.contains(e.target)) {
            suggestions.style.display = 'none';
        }
    });

    button.addEventListener('click', () => {
        const value = input.value.trim();
        if (!value) {
            sessionStorage.removeItem('deepseek_api_key');
            status.textContent = '已清除 Key；系统仍可使用内置默认 Key。';
            return;
        }
        Session.set('deepseek_api_key', value);
        status.textContent = '已保存 Key：仅保存在当前浏览器会话中。';
    });
}

async function loadSubjects() {
    const select = document.getElementById('subjectSelect');
    try {
        const data = await fetchSubjects();
        for (const subject of data.subjects || []) {
            const opt = document.createElement('option');
            opt.value = subject.id;
            opt.textContent = `${subject.name} · 七年级 · ${subject.total_units} 个单元 · ${subject.total_knowledge_points} 个知识点`;
            opt.dataset.name = subject.name;
            select.appendChild(opt);
        }
    } catch (err) {
        select.innerHTML = '<option value="">学科加载失败，请刷新重试</option>';
        console.error(err);
    }
}

async function onSubjectChange() {
    const subjectId = this.value;
    const unitSection = document.getElementById('unitSection');
    const selectedInfo = document.getElementById('selectedInfo');
    const startBtn = document.getElementById('startBtn');

    selectedSubject = subjectId || null;
    selectedSubjectLabel = this.selectedOptions[0]?.dataset?.name || '';
    selectedUnit = null;
    selectedUnitTitle = '';
    startBtn.disabled = true;
    selectedInfo.style.display = 'none';

    if (!subjectId) {
        unitSection.style.display = 'none';
        return;
    }

    unitSection.style.display = 'block';
    document.getElementById('unitList').innerHTML = `
        <div class="loading compact">
            <div class="spinner"></div>
            <p>正在加载单元列表...</p>
        </div>
    `;

    try {
        const data = await fetchUnits(subjectId);
        renderUnitList(data.units || []);
    } catch (err) {
        document.getElementById('unitList').innerHTML = `
            <div class="error-message">单元加载失败：${escapeHtml(err.message)}</div>
        `;
    }
}

function renderUnitList(units) {
    const container = document.getElementById('unitList');
    if (!units.length) {
        container.innerHTML = '<div class="empty-state">暂无单元数据</div>';
        return;
    }

    container.innerHTML = units.map(unit => {
        const title = unit.display_title || buildDisplayTitle(unit);
        return `
            <button class="unit-item" data-unit-id="${escapeHtml(unit.unit_id)}" data-title="${escapeHtml(title)}">
                <div>
                    <div class="unit-name">${escapeHtml(title)}</div>
                    <div class="unit-meta">${escapeHtml(unit.volume || '')} · ${unit.knowledge_point_count || 0} 个知识点</div>
                </div>
            </button>
        `;
    }).join('');

    container.querySelectorAll('.unit-item').forEach(item => {
        item.addEventListener('click', () => {
            container.querySelectorAll('.unit-item').forEach(el => el.classList.remove('selected'));
            item.classList.add('selected');
            selectedUnit = item.dataset.unitId;
            selectedUnitTitle = item.dataset.title;

            document.getElementById('selectedDetail').innerHTML = `
                <p><strong>学科：</strong>${escapeHtml(selectedSubjectLabel)}</p>
                <p><strong>单元：</strong>${escapeHtml(selectedUnitTitle)}</p>
            `;
            document.getElementById('selectedInfo').style.display = 'block';
            document.getElementById('startBtn').disabled = false;
        });
    });
}

function buildDisplayTitle(unit) {
    const subjectName = selectedSubjectLabel || '';
    const unitLabel = selectedSubject === 'english'
        ? `Unit ${unit.unit_no}`
        : `第${unit.unit_no}单元`;
    const name = selectedSubject === 'english' && unit.unit_name_zh
        ? `${unit.unit_name} ${unit.unit_name_zh}`
        : (unit.unit_name_zh || unit.unit_name);
    return `${subjectName} · 七年级${unit.volume} · ${unitLabel}：${name}`;
}

function onStartQuiz() {
    if (!selectedSubject || !selectedUnit) return;
    Session.set('subject', selectedSubject);
    Session.set('subject_label', selectedSubjectLabel);
    Session.set('unit_id', selectedUnit);
    Session.set('unit_title', selectedUnitTitle);
    window.location.href = 'quiz.html';
}

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}
