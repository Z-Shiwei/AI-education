let allSubjects = [];
let selectedGrade = null;
let selectedSubject = null;
let selectedSubjectLabel = '';
let selectedUnit = null;
let selectedUnitTitle = '';

document.addEventListener('DOMContentLoaded', async () => {
    initApiKeyBox();
    await loadSubjects();
    document.getElementById('gradeSelect').addEventListener('change', onGradeChange);
    document.getElementById('subjectSelect').addEventListener('change', onSubjectChange);
    document.getElementById('startBtn').addEventListener('click', onStartQuiz);
});

function initApiKeyBox() {
    const input = document.getElementById('apiKeyInput');
    const button = document.getElementById('saveKeyBtn');
    const status = document.getElementById('apiKeyStatus');
    const suggestions = document.getElementById('keySuggestions');
    const saved = Session.get('deepseek_api_key');

    const BUILTIN_KEY = 'sk-02168810f6ca444fa3d964cfc332161e';
    const BUILTIN_MASKED = 'sk-0216...161e（内置默认）';

    if (saved) {
        status.textContent = '已保存个人 Key，本次会话优先使用个人 Key。';
    }

    let optionItems = `<li class="key-suggestion-item" data-key="${BUILTIN_KEY}">
        <span class="suggestion-label">${BUILTIN_MASKED}</span>
        <span class="suggestion-hint">点击使用</span>
    </li>`;

    if (saved && saved !== BUILTIN_KEY) {
        const savedMasked = saved.length > 12
            ? `${saved.slice(0, 7)}...${saved.slice(-4)}（上次保存）`
            : `${saved}（上次保存）`;
        optionItems += `<li class="key-suggestion-item" data-key="${escapeHtml(saved)}">
            <span class="suggestion-label">${escapeHtml(savedMasked)}</span>
            <span class="suggestion-hint">点击使用</span>
        </li>`;
    }

    suggestions.innerHTML = optionItems;

    input.addEventListener('focus', () => {
        if (!input.value.trim()) suggestions.style.display = 'block';
    });

    suggestions.addEventListener('click', (e) => {
        const item = e.target.closest('.key-suggestion-item');
        if (!item) return;
        input.value = item.dataset.key;
        suggestions.style.display = 'none';
        status.textContent = '已选择 Key，点击“保存”后生效。';
    });

    input.addEventListener('input', () => {
        suggestions.style.display = 'none';
    });

    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !suggestions.contains(e.target)) {
            suggestions.style.display = 'none';
        }
    });

    button.addEventListener('click', () => {
        const value = input.value.trim();
        if (!value) {
            sessionStorage.removeItem('deepseek_api_key');
            status.textContent = '已清除个人 Key；系统会使用内置默认 Key。';
            return;
        }
        Session.set('deepseek_api_key', value);
        status.textContent = '已保存 Key：仅保存在当前浏览器会话中。';
    });
}

async function loadSubjects() {
    const gradeSelect = document.getElementById('gradeSelect');
    try {
        const data = await fetchSubjects();
        allSubjects = data.subjects || [];
        const grades = [...new Set(allSubjects.map(subject => subject.grade))].sort((a, b) => a - b);
        for (const grade of grades) {
            const opt = document.createElement('option');
            opt.value = String(grade);
            opt.textContent = `${grade}年级`;
            gradeSelect.appendChild(opt);
        }
    } catch (err) {
        gradeSelect.innerHTML = '<option value="">年级加载失败，请刷新重试</option>';
        console.error(err);
    }
}

function onGradeChange() {
    selectedGrade = this.value ? Number(this.value) : null;
    selectedSubject = null;
    selectedSubjectLabel = '';
    selectedUnit = null;
    selectedUnitTitle = '';

    document.getElementById('unitSection').style.display = 'none';
    document.getElementById('selectedInfo').style.display = 'none';
    document.getElementById('startBtn').disabled = true;

    const subjectSection = document.getElementById('subjectSection');
    const subjectSelect = document.getElementById('subjectSelect');
    subjectSelect.innerHTML = '<option value="">请选择学科</option>';

    if (!selectedGrade) {
        subjectSection.style.display = 'none';
        return;
    }

    const subjects = allSubjects.filter(subject => subject.grade === selectedGrade);
    for (const subject of subjects) {
        const opt = document.createElement('option');
        opt.value = subject.id;
        opt.textContent = `${subject.name} · ${subject.total_units} 个单元 · ${subject.total_knowledge_points} 个知识点`;
        opt.dataset.name = subject.name;
        opt.dataset.grade = subject.grade;
        subjectSelect.appendChild(opt);
    }
    subjectSection.style.display = 'block';
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
                <p><strong>年级：</strong>${escapeHtml(selectedGrade ? `${selectedGrade}年级` : '')}</p>
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
    const unitLabel = subjectName === '英语'
        ? `Unit ${unit.unit_no}`
        : `第${unit.unit_no}单元`;
    const name = subjectName === '英语' && unit.unit_name_zh
        ? `${unit.unit_name} ${unit.unit_name_zh}`
        : (unit.unit_name_zh || unit.unit_name);
    return `${subjectName} · ${selectedGrade}年级 · ${unit.volume} · ${unitLabel}：${name}`;
}

function onStartQuiz() {
    if (!selectedSubject || !selectedUnit) return;
    const questionCount = Number(document.getElementById('questionCountSelect')?.value || 20);
    const difficulty = document.getElementById('difficultySelect')?.value || 'mixed';
    Session.set('grade', selectedGrade);
    Session.set('subject', selectedSubject);
    Session.set('subject_label', selectedSubjectLabel);
    Session.set('unit_id', selectedUnit);
    Session.set('unit_title', selectedUnitTitle);
    Session.set('question_count', questionCount);
    Session.set('difficulty', difficulty);
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
