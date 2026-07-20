let diagnosis = null;

document.addEventListener('DOMContentLoaded', () => {
    diagnosis = Session.get('diagnosis');

    if (!diagnosis) {
        showMissingReport();
        return;
    }
    if (diagnosis.error) {
        document.getElementById('weakPointsList').innerHTML = `<div class="error-message">${escapeHtml(diagnosis.error)}</div>`;
        return;
    }

    renderScore();
    renderWeakPoints();
    renderNextSteps();
    renderWrongDetails();
});

function cleanLabel(value) {
    const text = String(value || '').trim();
    if (!text || text.includes('?') || text.includes('�')) return '';
    return text;
}

function showMissingReport() {
    document.getElementById('weakPointsList').innerHTML = `
        <div class="error-message">未找到诊断结果，请先完成答题。</div>
        <button class="btn btn-outline" onclick="window.location.href='index.html'">返回首页</button>
    `;
}

function renderScore() {
    const accuracy = Math.round((diagnosis.accuracy || 0) * 100);
    document.getElementById('scoreNumber').textContent = `${accuracy}%`;
    document.getElementById('correctCount').textContent = diagnosis.correct || 0;
    document.getElementById('totalCount').textContent = diagnosis.total || 0;

    const circle = document.querySelector('.score-circle');
    const number = document.getElementById('scoreNumber');
    const color = accuracy >= 80 ? 'var(--success)' : accuracy >= 50 ? 'var(--warning)' : 'var(--danger)';
    circle.style.borderColor = color;
    number.style.color = color;
}

function renderWeakPoints() {
    const container = document.getElementById('weakPointsList');
    const weakPoints = (diagnosis.weak_points || []).filter(point => cleanLabel(point.name));

    if (!weakPoints.length) {
        container.innerHTML = `
            <div class="empty-state">
                <p class="big-symbol">✓</p>
                <p>本次没有检测到明确的薄弱知识点。可以先复盘错题，再继续挑战下一个单元。</p>
            </div>
        `;
        return;
    }

    container.innerHTML = weakPoints.map(point => `
        <article class="weak-point confidence-${escapeHtml(point.confidence)}">
            <div class="kp-name">
                ${escapeHtml(point.name)}
                <span class="confidence-badge">${confidenceText(point.confidence)}</span>
            </div>
            <div class="kp-meta">
                错误 ${point.wrong_count}/${point.total_asked} 题 · 错误率 ${Math.round((point.error_rate || 0) * 100)}%
            </div>
            <p class="diagnosis-reason"><strong>原因：</strong>${escapeHtml(point.reason || '相关题目出现错误，需要回到概念和错题中复盘。')}</p>
            <button class="btn btn-sm btn-primary remediate-btn" data-kp="${encodeURIComponent(point.name)}">
                补这个知识点
            </button>
        </article>
    `).join('');

    container.querySelectorAll('.remediate-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const kpName = decodeURIComponent(btn.dataset.kp);
            Session.set('remediate_kps', [kpName]);
            window.location.href = `remediate.html?kp=${encodeURIComponent(kpName)}`;
        });
    });

    const allBtn = document.getElementById('remediateAllBtn');
    allBtn.disabled = false;
    allBtn.addEventListener('click', () => {
        Session.set('remediate_kps', weakPoints.map(point => point.name));
        window.location.href = 'remediate.html';
    });
}

function renderNextSteps() {
    const container = document.getElementById('nextStepsList');
    const weakPoints = (diagnosis.weak_points || []).filter(point => cleanLabel(point.name));

    if (!weakPoints.length) {
        container.innerHTML = '<p>建议先复盘本次错题，再进入下一个单元。</p>';
        return;
    }

    container.innerHTML = weakPoints.slice(0, 5).map((point, index) => `
        <div class="next-step">
            <span class="step-index">${index + 1}</span>
            <div>
                <strong>${escapeHtml(point.name)}</strong>
                <p>${escapeHtml(point.suggestion || `先复习“${point.name}”的概念，再做同类题巩固。`)}</p>
            </div>
        </div>
    `).join('');
}

function renderWrongDetails() {
    const wrongDetails = diagnosis.wrong_details || [];
    if (!wrongDetails.length) return;

    document.getElementById('wrongDetailsCard').style.display = 'block';
    document.getElementById('wrongDetailsList').innerHTML = wrongDetails.map((detail, index) => {
        const tags = (detail.tags || []).map(cleanLabel).filter(Boolean);
        return `
            <div class="practice-question">
                <p class="wrong-title">错题 ${index + 1}：${escapeHtml(detail.text)}</p>
                <p>你的答案：<span class="danger-text">${escapeHtml(detail.student_answer || '未作答')}</span></p>
                <p>正确答案：<span class="success-text">${escapeHtml(detail.correct_answer)}</span></p>
                ${tags.length ? `<p class="muted">关联知识点：${tags.map(escapeHtml).join('、')}</p>` : ''}
            </div>
        `;
    }).join('');
}

function confidenceText(confidence) {
    if (confidence === 'high') return '高置信度';
    if (confidence === 'medium') return '中置信度';
    return '低置信度';
}

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}
