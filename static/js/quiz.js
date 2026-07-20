let questions = [];
let answers = {};

document.addEventListener('DOMContentLoaded', async () => {
    const subjectId = Session.get('subject');
    const unitId = Session.get('unit_id');
    const unitTitle = Session.get('unit_title') || `${subjectId} · ${unitId}`;

    document.getElementById('breadcrumb').textContent = unitTitle;

    if (!subjectId || !unitId) {
        showError('还没有选择学科或单元，请返回首页重新选择。');
        return;
    }

    await loadQuestions(subjectId, unitId);
});

async function loadQuestions(subjectId, unitId) {
    const loadingArea = document.getElementById('loadingArea');
    const loadingText = document.getElementById('loadingText');
    const quizArea = document.getElementById('quizArea');
    const sourceMsg = document.getElementById('questionSourceMsg');

    try {
        loadingArea.style.display = 'block';
        loadingText.textContent = '正在生成诊断题...';

        const data = await fetchQuestions(subjectId, unitId);
        if (!data.questions || data.questions.length === 0) {
            showError(data.error || '生成失败，请重试。');
            return;
        }

        questions = data.questions;
        loadingArea.style.display = 'none';
        quizArea.style.display = 'block';

        sourceMsg.style.display = 'block';
        sourceMsg.textContent = data.from_cache ? '已使用缓存题库' : '已生成新的诊断题';

        renderQuestions();
        updateProgress();
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = false;
        submitBtn.addEventListener('click', onSubmit);
    } catch (err) {
        showError(`生成失败，请重试：${err.message}`);
    }
}

function cleanTags(tags) {
    return (tags || [])
        .map(tag => String(tag || '').trim())
        .filter(tag => tag && !tag.includes('?') && !tag.includes('�'));
}

function renderQuestions() {
    const container = document.getElementById('questionsContainer');
    container.innerHTML = questions.map((q, index) => {
        const tags = cleanTags(q.tags);
        const tagHtml = tags.length
            ? `<span class="tag-list">${tags.map(escapeHtml).join('、')}</span>`
            : '';
        return `
            <section class="card question-card">
                <div class="q-header">
                    <span class="q-number">第 ${index + 1} 题</span>
                    ${tagHtml}
                </div>
                <div class="q-text">${escapeHtml(q.text)}</div>
                <div class="options" data-qid="${escapeHtml(q.id)}">
                    ${(q.options || []).map((opt, optIndex) => {
                        const letter = String.fromCharCode(65 + optIndex);
                        return `
                            <label class="option">
                                <input type="radio" name="q_${escapeHtml(q.id)}" value="${letter}">
                                <span class="option-text">${escapeHtml(opt)}</span>
                            </label>
                        `;
                    }).join('')}
                </div>
            </section>
        `;
    }).join('');

    container.querySelectorAll('.options').forEach(group => {
        group.addEventListener('change', event => {
            if (event.target.matches('input[type="radio"]')) {
                const qId = group.dataset.qid;
                answers[qId] = event.target.value;
                group.querySelectorAll('.option').forEach(item => item.classList.remove('selected'));
                event.target.closest('.option').classList.add('selected');
                updateProgress();
            }
        });
    });
}

function updateProgress() {
    const answered = Object.keys(answers).length;
    const total = questions.length;
    const pct = total ? Math.round((answered / total) * 100) : 0;
    document.getElementById('progressFill').style.width = `${pct}%`;
    document.getElementById('progressText').textContent = `已答：${answered} / ${total} 题`;
}

async function onSubmit() {
    const subjectId = Session.get('subject');
    const unitId = Session.get('unit_id');
    const submitBtn = document.getElementById('submitBtn');
    const answerList = questions.map(q => ({
        q_id: q.id,
        student_answer: answers[q.id] || '',
    }));

    submitBtn.disabled = true;
    submitBtn.textContent = '正在提交并诊断...';

    try {
        const result = await submitAnswers(subjectId, unitId, answerList);
        Session.set('diagnosis', result);
        window.location.href = 'report.html';
    } catch (err) {
        submitBtn.disabled = false;
        submitBtn.textContent = '提交失败，点击重试';
        alert(`提交失败：${err.message}`);
    }
}

function showError(message) {
    document.getElementById('loadingArea').style.display = 'none';
    document.getElementById('quizArea').style.display = 'none';
    document.getElementById('errorArea').style.display = 'block';
    document.getElementById('errorMsg').textContent = message;
}

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}
