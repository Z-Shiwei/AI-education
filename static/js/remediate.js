let remediationData = null;

document.addEventListener('DOMContentLoaded', async () => {
    const subjectId = Session.get('subject');
    const urlParams = new URLSearchParams(window.location.search);
    const urlKp = urlParams.get('kp');
    const kpNames = urlKp
        ? [decodeURIComponent(urlKp)]
        : (Session.get('remediate_kps') || []);

    if (urlKp) {
        Session.set('remediate_kps', kpNames);
    }

    if (!subjectId || !kpNames.length) {
        showError('没有薄弱知识点信息，请先完成诊断。');
        return;
    }

    await loadRemediation(subjectId, kpNames);
});

async function loadRemediation(subjectId, kpNames) {
    try {
        document.getElementById('loadingMsg').textContent = `正在为 ${kpNames.length} 个薄弱点准备补习内容...`;
        const data = await fetchRemediation(subjectId, kpNames);
        remediationData = data;
        document.getElementById('loadingArea').style.display = 'none';

        if (data.error) {
            showError(data.error);
            return;
        }

        if (data.upstream_summary) {
            document.getElementById('summaryCard').style.display = 'block';
            document.getElementById('summaryText').textContent = data.upstream_summary;
        }

        renderRemediations(data.remediations || []);
    } catch (err) {
        showError(`补习内容加载失败：${err.message}`);
    }
}

function renderRemediations(remediations) {
    const container = document.getElementById('remediationContainer');
    if (!remediations.length) {
        container.innerHTML = '<section class="card empty-state">暂时没有生成补习内容，请稍后重试。</section>';
        return;
    }

    container.innerHTML = remediations.map((rem, i) => `
        <section class="card">
            <h2 class="remediate-title">补习 ${i + 1}：${escapeHtml(rem.kp_name)}</h2>
            <div class="micro-lesson">
                <h3>微课讲解</h3>
                <p>${escapeHtml(rem.micro_lesson)}</p>
            </div>
            <h3 class="section-subtitle">强化练习</h3>
            ${(rem.practice_questions || []).map((pq, j) => renderPractice(pq, i, j)).join('')}
        </section>
    `).join('');

    container.querySelectorAll('.check-btn').forEach(btn => {
        btn.addEventListener('click', checkPracticeAnswer);
    });
}

function renderPractice(pq, i, j) {
    return `
        <div class="practice-question" data-i="${i}" data-j="${j}">
            <p class="practice-title">练习 ${j + 1}：${escapeHtml(pq.question)}</p>
            <div class="options">
                ${(pq.options || []).map((opt, k) => {
                    const letter = String.fromCharCode(65 + k);
                    return `
                        <label class="option">
                            <input type="radio" name="pq_${i}_${j}" value="${letter}">
                            <span>${escapeHtml(opt)}</span>
                        </label>
                    `;
                }).join('')}
            </div>
            <button class="btn btn-sm btn-primary check-btn" data-i="${i}" data-j="${j}" data-answer="${escapeHtml(pq.answer || '')}">
                提交验证
            </button>
            <div class="pq-result" style="display:none;"></div>
        </div>
    `;
}

function checkPracticeAnswer() {
    const i = this.dataset.i;
    const j = this.dataset.j;
    const correctAnswer = this.dataset.answer;
    const selected = document.querySelector(`input[name="pq_${i}_${j}"]:checked`);

    if (!selected) {
        alert('请先选择一个选项');
        return;
    }

    const resultDiv = document.querySelector(`.practice-question[data-i="${i}"][data-j="${j}"] .pq-result`);
    const question = remediationData.remediations[i].practice_questions[j];
    const isCorrect = selected.value === correctAnswer;
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = `
        <div class="${isCorrect ? 'success-text' : 'danger-text'}">
            ${isCorrect ? '正确！' : `还不对。正确答案是：${escapeHtml(correctAnswer)}`}
        </div>
        <div class="muted">${escapeHtml(question.explanation || '')}</div>
    `;

    this.disabled = true;
    this.textContent = '已提交';
}

function showError(message) {
    document.getElementById('loadingArea').style.display = 'none';
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
