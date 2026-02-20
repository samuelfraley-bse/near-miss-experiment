let experimentState = {
    participantId: null,
    frameType: null,
    lossFrame: null,
    conditionId: null,
    maxTrials: 5,
    currentTrial: 0,
    completedTrials: 0,
    currentTrialConfig: null,
    lastOutcome: null,
    survey: {
        desiredRoundsNextTime: null,
        confidenceImpact: null,
        selfRatedAccuracy: null
    },
    barRunning: false,
    barPosition: 0,
    barAnimationId: null
};

document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && experimentState.barRunning) {
            e.preventDefault();
            stopBar();
        }
    });

    document.querySelectorAll('.likert-scale').forEach(scale => {
        scale.querySelectorAll('.likert-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                scale.querySelectorAll('.likert-btn').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                const value = parseInt(btn.dataset.value, 10);
                if (scale.id === 'desired-rounds-scale') experimentState.survey.desiredRoundsNextTime = value;
                if (scale.id === 'confidence-scale') experimentState.survey.confidenceImpact = value;
                if (scale.id === 'accuracy-scale') experimentState.survey.selfRatedAccuracy = value;
                checkSurveyComplete();
            });
        });
    });

    const params = new URLSearchParams(window.location.search);
    if (params.get('test') === '1') {
        const panel = document.getElementById('test-mode-panel');
        if (panel) panel.classList.remove('hidden');
    }
});

function switchScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => screen.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
}

async function startExperiment(forceFrameType = null, forceLossFrame = null) {
    try {
        const response = await fetch('/api/start-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                force_frame_type: forceFrameType,
                force_loss_frame: forceLossFrame
            })
        });
        const data = await response.json();

        experimentState.participantId = data.participant_id;
        experimentState.frameType = data.frame_type;
        experimentState.lossFrame = data.loss_frame;
        experimentState.conditionId = data.condition_id;
        experimentState.maxTrials = data.max_trials;
        experimentState.currentTrial = 0;
        experimentState.completedTrials = 0;

        await showFrameIntro();
    } catch (error) {
        console.error('Error starting experiment:', error);
        alert('Could not start the session.');
    }
}

async function showFrameIntro() {
    const response = await fetch('/api/get-frame');
    const frame = await response.json();
    document.getElementById('frame-title').textContent = frame.title;
    document.getElementById('frame-description').textContent = frame.description;
    switchScreen('frame-intro-screen');
}

async function startNextTrial() {
    experimentState.currentTrial += 1;
    document.getElementById('bar-trial-num').textContent = experimentState.currentTrial;

    try {
        const response = await fetch('/api/generate-bar-trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trial_number: experimentState.currentTrial })
        });
        const config = await response.json();
        experimentState.currentTrialConfig = config;
        setupBarTask(config);
        document.getElementById('start-trial-btn').classList.remove('hidden');
        document.getElementById('stop-btn').classList.add('hidden');
        switchScreen('bar-task-screen');
    } catch (error) {
        console.error('Error generating trial:', error);
    }
}

function setupBarTask(config) {
    const targetZone = document.getElementById('target-zone');
    targetZone.style.left = config.target_zone_start + '%';
    targetZone.style.width = config.target_zone_width + '%';
    const bar = document.getElementById('moving-bar');
    bar.style.left = '0%';
}

function beginTrial() {
    document.getElementById('start-trial-btn').classList.add('hidden');
    document.getElementById('stop-btn').classList.remove('hidden');
    startBarAnimation();
}

function startBarAnimation() {
    const bar = document.getElementById('moving-bar');
    const startTime = Date.now();
    const duration = experimentState.currentTrialConfig.duration || 1500;
    const barSpeed = experimentState.currentTrialConfig.bar_speed || 0.7;
    experimentState.barRunning = true;

    const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const basePosition = progress * 100;
        const position = basePosition + (Math.sin(elapsed / 100) * barSpeed * 5);
        experimentState.barPosition = Math.max(0, Math.min(position, 100));
        bar.style.left = experimentState.barPosition + '%';

        if (progress < 1 && experimentState.barRunning) {
            experimentState.barAnimationId = requestAnimationFrame(animate);
        } else if (progress >= 1 && experimentState.barRunning) {
            stopBar();
        }
    };

    experimentState.barAnimationId = requestAnimationFrame(animate);
}

function stopBar() {
    if (!experimentState.barRunning) return;
    experimentState.barRunning = false;
    cancelAnimationFrame(experimentState.barAnimationId);
    document.getElementById('stop-btn').classList.add('hidden');
    evaluateTrial();
}

async function evaluateTrial() {
    const config = experimentState.currentTrialConfig;
    try {
        const response = await fetch('/api/evaluate-trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                bar_position: experimentState.barPosition,
                target_zone_start: config.target_zone_start,
                target_zone_width: config.target_zone_width,
                trial_number: experimentState.currentTrial
            })
        });
        const result = await response.json();
        experimentState.lastOutcome = result;
        experimentState.completedTrials = result.trial_count;
        showOutcome(result);
    } catch (error) {
        console.error('Error evaluating trial:', error);
    }
}

function showOutcome(result) {
    const outcomeText = document.getElementById('outcome-text');
    const outcomeFeedback = document.getElementById('outcome-feedback');
    const nextBtn = document.getElementById('next-round-btn');

    if (result.is_hit) {
        outcomeText.textContent = 'Hit!';
        outcomeText.className = 'outcome-text outcome-hit';
    } else if (result.is_near_miss) {
        outcomeText.textContent = 'So close!';
        outcomeText.className = 'outcome-text outcome-near-miss';
    } else {
        outcomeText.textContent = 'You lost this round.';
        outcomeText.className = 'outcome-text outcome-miss';
    }

    outcomeFeedback.textContent = result.feedback;
    nextBtn.textContent = result.done ? 'Continue to final questions' : 'Next round';
    switchScreen('outcome-screen');
}

function advanceFromOutcome() {
    if (experimentState.lastOutcome && experimentState.lastOutcome.done) {
        showPostSurvey();
    } else {
        startNextTrial();
    }
}

function showPostSurvey() {
    experimentState.survey = {
        desiredRoundsNextTime: null,
        confidenceImpact: null,
        selfRatedAccuracy: null
    };
    document.querySelectorAll('.likert-btn').forEach(btn => btn.classList.remove('selected'));
    document.getElementById('submit-survey-btn').disabled = true;
    switchScreen('post-survey-screen');
}

function checkSurveyComplete() {
    const s = experimentState.survey;
    const complete =
        s.desiredRoundsNextTime !== null &&
        s.confidenceImpact !== null &&
        s.selfRatedAccuracy !== null;
    document.getElementById('submit-survey-btn').disabled = !complete;
}

async function submitPostSurvey() {
    try {
        const response = await fetch('/api/save-post-survey', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                desired_rounds_next_time: experimentState.survey.desiredRoundsNextTime,
                confidence_impact: experimentState.survey.confidenceImpact,
                self_rated_accuracy: experimentState.survey.selfRatedAccuracy
            })
        });
        const result = await response.json();
        if (!response.ok || result.success === false) {
            throw new Error(result.error || 'Failed to save survey');
        }
        await showSummary();
    } catch (error) {
        console.error('Error saving survey:', error);
        alert('Could not save final responses.');
    }
}

async function showSummary() {
    try {
        const response = await fetch('/api/get-summary');
        const summary = await response.json();
        document.getElementById('summary-condition').textContent = summary.condition_id || '';
        document.getElementById('summary-hits').textContent = String(summary.hits || 0);
        document.getElementById('summary-near-misses').textContent = String(summary.near_misses || 0);
        switchScreen('summary-screen');
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}
