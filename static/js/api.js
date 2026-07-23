const API_BASE = '/api';

async function apiGet(path) {
    const resp = await fetch(API_BASE + path, {
        headers: buildHeaders(),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
        throw new Error(data.error || `请求失败：${resp.status}`);
    }
    return data;
}

async function apiPost(path, body) {
    const resp = await fetch(API_BASE + path, {
        method: 'POST',
        headers: buildHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(body),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
        throw new Error(data.error || `请求失败：${resp.status}`);
    }
    return data;
}

function buildHeaders(base = {}) {
    const headers = { ...base };
    const key = Session.get('deepseek_api_key');
    if (key) {
        headers['X-DeepSeek-API-Key'] = key;
    }
    return headers;
}

function fetchSubjects() {
    return apiGet('/subjects');
}

function fetchUnits(subjectId) {
    return apiGet(`/subjects/${subjectId}/units`);
}

function fetchQuestions(subjectId, unitId, count = 20, difficulty = 'mixed') {
    const params = new URLSearchParams({
        count: String(count),
        difficulty: difficulty || 'mixed',
    });
    return apiGet(`/subjects/${subjectId}/units/${unitId}/questions?${params.toString()}`);
}

function submitAnswers(subjectId, unitId, answers, difficulty = 'mixed') {
    return apiPost('/submit', {
        subject: subjectId,
        unit_id: unitId,
        difficulty: difficulty || 'mixed',
        answers,
    });
}

function fetchRemediation(subjectId, weakPoints) {
    return apiPost('/remediate', {
        subject: subjectId,
        weak_points: weakPoints,
    });
}

const Session = {
    set(key, value) {
        sessionStorage.setItem(key, JSON.stringify(value));
    },
    get(key) {
        const val = sessionStorage.getItem(key);
        if (val === null) return null;
        try {
            return JSON.parse(val);
        } catch {
            return val;
        }
    },
    clear() {
        sessionStorage.clear();
    },
};
