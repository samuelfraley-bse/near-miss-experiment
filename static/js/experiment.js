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
        selfRatedAccuracy: null,
        frustration: null,
        motivation: null,
        luckVsSkill: null
    },
    barRunning: false,
    barPosition: 0,
    barAnimationId: null,
    reelSpinning: false,
    reelHitUsed: false,
    wheelZoneStart: 0,
    wheelZoneEnd: 0
};

// ─── SETUP ────────────────────────────────────────────────────────────────────

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
                if (scale.id === 'confidence-scale')     experimentState.survey.confidenceImpact = value;
                if (scale.id === 'accuracy-scale')       experimentState.survey.selfRatedAccuracy = value;
                if (scale.id === 'frustration-scale')    experimentState.survey.frustration = value;
                if (scale.id === 'motivation-scale')     experimentState.survey.motivation = value;
                if (scale.id === 'luckskill-scale')      experimentState.survey.luckVsSkill = value;
                checkSurveyComplete();
            });
        });
    });

    const params = new URLSearchParams(window.location.search);
    if (params.get('dev') === '1') {
        window._devMode = true;
        const panel = document.getElementById('test-mode-panel');
        if (panel) panel.classList.remove('hidden');
        document.title += ' [DEV]';
    }
});

// ─── UTILITIES ────────────────────────────────────────────────────────────────

function switchScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
}

function checkConsent() {
    const checked = document.getElementById('consent-checkbox').checked;
    document.getElementById('consent-btn').disabled = !checked;
}

function checkDemographicsComplete() {
    const age = document.getElementById('age-input').value;
    const gender = document.querySelector('input[name="gender"]:checked');
    const valid = age && parseInt(age) >= 10 && parseInt(age) <= 100 && gender;
    document.getElementById('demographics-btn').disabled = !valid;
}

function submitDemographicsAndStart() {
    const age = parseInt(document.getElementById('age-input').value);
    const gender = document.querySelector('input[name="gender"]:checked').value;
    window._demographics = { age, gender };
    startExperiment();
}

// ─── SESSION START ────────────────────────────────────────────────────────────

async function startExperiment(forceFrameType = null, forceLossFrame = null) {
    try {
        const response = await fetch('/api/start-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                force_frame_type: forceFrameType,
                force_loss_frame: forceLossFrame,
                is_dev: window._devMode || false,
                age: window._demographics?.age || null,
                gender: window._demographics?.gender || null
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

// ─── COUNTDOWN ────────────────────────────────────────────────────────────────

function showCountdown(callback) {
    switchScreen('countdown-screen');
    const el = document.getElementById('countdown-number');
    let count = 3;
    el.textContent = count;
    el.classList.remove('countdown-pop');

    const tick = () => {
        // trigger pop animation
        el.classList.remove('countdown-pop');
        void el.offsetWidth; // reflow to restart animation
        el.classList.add('countdown-pop');

        if (count <= 0) {
            callback();
            return;
        }
        el.textContent = count;
        count--;
        setTimeout(tick, 900);
    };

    tick();
}

// ─── TRIAL ROUTING ────────────────────────────────────────────────────────────

async function startNextTrial() {
    experimentState.currentTrial += 1;

    try {
        const response = await fetch('/api/generate-bar-trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trial_number: experimentState.currentTrial })
        });
        const config = await response.json();
        experimentState.currentTrialConfig = config;

        showCountdown(() => {
            if (experimentState.frameType === 'luck') {
                setupReelTrial(config);
            } else {
                setupBarTrial(config);
            }
        });
    } catch (error) {
        console.error('Error generating trial:', error);
    }
}

// ─── BAR GAME ─────────────────────────────────────────────────────────────────

const BAR_BOUNCE_PERIOD = 280; // ms per one-way pass

function setupBarTrial(config) {
    document.getElementById('bar-trial-num').textContent = experimentState.currentTrial;

    const targetZone = document.getElementById('target-zone');
    targetZone.style.left  = config.target_zone_start + '%';
    targetZone.style.width = config.target_zone_width + '%';

    const bar = document.getElementById('moving-bar');
    bar.style.left = '2%';

    // Bar launches immediately — no Start button
    document.getElementById('start-trial-btn').classList.add('hidden');
    document.getElementById('stop-btn').classList.remove('hidden');

    switchScreen('bar-task-screen');
    startBarAnimation();
}

function startBarAnimation() {
    const bar = document.getElementById('moving-bar');
    const startTime = Date.now();
    experimentState.barRunning = true;

    const animate = () => {
        const elapsed = Date.now() - startTime;
        // Ping-pong triangle wave: bounces 0->100->0->100...
        const period  = BAR_BOUNCE_PERIOD * 2;
        const t       = (elapsed % period) / period;
        const phase   = t < 0.5 ? t * 2 : 2 - t * 2;
        const position = phase * 96 + 2; // 2-98% to keep small margins

        experimentState.barPosition = position;
        bar.style.left = position + '%';

        if (experimentState.barRunning) {
            experimentState.barAnimationId = requestAnimationFrame(animate);
        }
    };

    experimentState.barAnimationId = requestAnimationFrame(animate);
}

function stopBar() {
    if (!experimentState.barRunning) return;
    experimentState.barRunning = false;
    cancelAnimationFrame(experimentState.barAnimationId);
    document.getElementById('stop-btn').classList.add('hidden');

    // Immediately blank the screen so participant never sees where bar stopped
    switchScreen('countdown-screen');
    document.getElementById('countdown-number').textContent = '';

    evaluateTrial(experimentState.barPosition);
}

// --- REEL GAME ---

const REEL_CELL_W  = 70;
const REEL_VISIBLE = 540;

function buildSequence() {
    var seq = [];
    for (var rep = 0; rep < 6; rep++)
        for (var v = 0; v < 100; v++) seq.push(v);
    return seq;
}
var REEL_SEQUENCE = buildSequence();

function setReelPos(offset) {
    var track   = document.getElementById('reel-track');
    var centerX = REEL_VISIBLE / 2 - REEL_CELL_W / 2;
    track.style.transform = 'translateX(' + (centerX - offset * REEL_CELL_W) + 'px)';
}

function buildReel() {
    var track = document.getElementById('reel-track');
    track.innerHTML = '';
    var zs = experimentState.wheelZoneStart;
    var ze = experimentState.wheelZoneEnd;
    REEL_SEQUENCE.forEach(function(v) {
        var cell   = document.createElement('div');
        var inZone = v >= zs && v <= ze;
        cell.style.cssText = 'width:64px;height:110px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1.5em;font-weight:800;border-radius:8px;margin:0 3px;user-select:none;' +
            (inZone
                ? 'background:#14532d;color:#4ade80;border:2px solid #22c55e;box-shadow:0 0 10px rgba(34,197,94,0.3);'
                : 'background:#1e293b;color:#cbd5e0;');
        cell.textContent = v;
        track.appendChild(cell);
    });
    setReelPos(0);
}

function setupReelTrial(config) {
    document.getElementById('wheel-trial-num').textContent = experimentState.currentTrial;
    experimentState.wheelZoneStart = Math.floor(Math.random() * 60) + 15;
    experimentState.wheelZoneEnd   = experimentState.wheelZoneStart + 8;
    document.getElementById('wheel-zone-label').textContent =
        'Winning zone: ' + experimentState.wheelZoneStart + '–' + experimentState.wheelZoneEnd;
    buildReel();
    document.getElementById('wheel-spin-btn').disabled = false;
    document.getElementById('spin-status').textContent = '';
    switchScreen('wheel-screen');
}

function spinReel() {
    if (experimentState.reelSpinning) return;
    experimentState.reelSpinning = true;
    document.getElementById('wheel-spin-btn').disabled = true;

    var lossFrame   = experimentState.lossFrame;
    var isLastRound = experimentState.currentTrial >= experimentState.maxTrials;
    var zs = experimentState.wheelZoneStart;
    var ze = experimentState.wheelZoneEnd;

    var shownOutcome;
    if (isLastRound) {
        shownOutcome = lossFrame;
    } else if (!experimentState.reelHitUsed && experimentState.currentTrial >= 2 && Math.random() < 0.4) {
        shownOutcome = 'hit';
    } else {
        shownOutcome = Math.random() < 0.80
            ? lossFrame
            : (lossFrame === 'near_miss' ? 'clear_loss' : 'near_miss');
    }
    if (shownOutcome === 'hit') experimentState.reelHitUsed = true;

    var targetValue;
    if (shownOutcome === 'hit') {
        targetValue = zs + 1 + Math.floor(Math.random() * Math.max(1, ze - zs - 1));
    } else if (shownOutcome === 'near_miss') {
        if (Math.random() < 0.5) {
            targetValue = ze + 1 + Math.floor(Math.random() * 5);
        } else {
            targetValue = zs - 1 - Math.floor(Math.random() * 5);
        }
    } else {
        targetValue = ze + 28 + Math.floor(Math.random() * 20);
    }
    targetValue = ((targetValue % 100) + 100) % 100;

    var baseIdx   = 200 + targetValue;
    var duration  = 5500;
    var startTime = Date.now();

    var statusEl = document.getElementById('spin-status');
    statusEl.textContent = '';
    var t1 = setTimeout(function() { statusEl.textContent = 'Drawing...'; }, 400);
    var t2 = setTimeout(function() { statusEl.textContent = 'Slowing down...'; }, 3800);

    function easeOut(p) {
        if (p < 0.55) return p * (0.75 / 0.55);
        var r = (p - 0.55) / 0.45;
        return 0.75 + 0.25 * (1 - Math.pow(1 - r, 4));
    }

    function animate() {
        var elapsed  = Date.now() - startTime;
        var progress = Math.min(elapsed / duration, 1);
        setReelPos(baseIdx * easeOut(progress));
        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            clearTimeout(t1); clearTimeout(t2);
            statusEl.textContent = '';
            experimentState.reelSpinning = false;
            evaluateTrial(targetValue, shownOutcome);
        }
    }

    requestAnimationFrame(animate);
}

// ─── TRIAL EVALUATION ─────────────────────────────────────────────────────────

async function evaluateTrial(position, shownOutcome) {
    const config = experimentState.currentTrialConfig;
    try {
        const response = await fetch('/api/evaluate-trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                bar_position: position,
                target_zone_start: config.target_zone_start,
                target_zone_width: config.target_zone_width,
                trial_number: experimentState.currentTrial,
                wheel_zone_start: experimentState.wheelZoneStart,
                wheel_zone_end: experimentState.wheelZoneEnd,
                shown_outcome: shownOutcome || null
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

// ─── OUTCOME SCREEN ───────────────────────────────────────────────────────────

function showOutcome(result) {
    const outcomeText     = document.getElementById('outcome-text');
    const outcomeFeedback = document.getElementById('outcome-feedback');
    const nextBtn         = document.getElementById('next-round-btn');

    // Hide the next button initially
    nextBtn.classList.add('hidden');

    if (result.is_hit) {
        outcomeText.textContent = '🎉 You got it!';
        outcomeText.className   = 'outcome-text outcome-hit';
    } else if (result.is_near_miss) {
        outcomeText.textContent = 'SO close!!';
        outcomeText.className   = 'outcome-text outcome-near-miss';
    } else {
        outcomeText.textContent = 'Not this time.';
        outcomeText.className   = 'outcome-text outcome-miss';
    }

    outcomeFeedback.textContent = result.feedback;
    nextBtn.textContent = result.done ? 'Continue to questions' : 'Next round';

    switchScreen('outcome-screen');

    // Delay showing the Next button so participants actually read the feedback
    // Clear-loss gets a shorter delay (message is brief), near-miss gets longer
    const delay = result.is_near_miss ? 2000 : 1200;
    setTimeout(() => {
        nextBtn.classList.remove('hidden');
    }, delay);
}

function advanceFromOutcome() {
    if (experimentState.lastOutcome && experimentState.lastOutcome.done) {
        showPostSurvey();
    } else {
        startNextTrial();
    }
}

// ─── POST SURVEY ──────────────────────────────────────────────────────────────

function showPostSurvey() {
    experimentState.survey = {
        desiredRoundsNextTime: null,
        confidenceImpact: null,
        selfRatedAccuracy: null,
        frustration: null,
        motivation: null,
        luckVsSkill: null
    };
    document.querySelectorAll('.likert-btn').forEach(btn => btn.classList.remove('selected'));
    document.getElementById('submit-survey-btn').disabled = true;
    switchScreen('post-survey-screen');
}

function checkSurveyComplete() {
    const s = experimentState.survey;
    const complete =
        s.desiredRoundsNextTime !== null &&
        s.confidenceImpact      !== null &&
        s.selfRatedAccuracy     !== null &&
        s.frustration           !== null &&
        s.motivation            !== null &&
        s.luckVsSkill           !== null;
    document.getElementById('submit-survey-btn').disabled = !complete;
}

async function submitPostSurvey() {
    try {
        const response = await fetch('/api/save-post-survey', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wants_more_rounds: experimentState.survey.desiredRoundsNextTime >= 3,
                desired_rounds_next_time: experimentState.survey.desiredRoundsNextTime,
                confidence_impact:        experimentState.survey.confidenceImpact,
                self_rated_accuracy:      experimentState.survey.selfRatedAccuracy,
                frustration:              experimentState.survey.frustration,
                motivation:               experimentState.survey.motivation,
                luck_vs_skill:            experimentState.survey.luckVsSkill
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

// ─── SUMMARY ──────────────────────────────────────────────────────────────────

async function showSummary() {
    try {
        await fetch('/api/get-summary');
        switchScreen('summary-screen');
    } catch (error) {
        switchScreen('summary-screen');
    }
}