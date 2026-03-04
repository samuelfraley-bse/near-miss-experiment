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
        improvementConfidence: null,
        learningPotential: null,
        feedbackCredibility: null,
        confidenceImpact: null,
        selfRatedAccuracy: null,
        finalRoundCloseness: null,
        frustration: null,
        motivation: null,
        luckVsSkill: null,
        expectedSuccess: null,
        appDownloadLikelihood: null
    },
    barRunning: false,
    barPosition: 0,
    barAnimationId: null,
    reelSpinning: false,
    reelForcedSide: null,
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
    // Backward-compatible: support both legacy single checkbox and new 4-item consent.
    const legacy = document.getElementById('consent-checkbox');
    const readSheetEl = document.getElementById('consent-read-sheet-checkbox');
    const questionsEl = document.getElementById('consent-questions-checkbox');
    const ageEl = document.getElementById('consent-age-checkbox');
    const voluntaryEl = document.getElementById('consent-voluntary-checkbox');

    let allChecked = false;
    if (readSheetEl && questionsEl && ageEl && voluntaryEl) {
        allChecked = readSheetEl.checked && questionsEl.checked && ageEl.checked && voluntaryEl.checked;
    } else if (legacy) {
        allChecked = legacy.checked;
    }

    document.getElementById('consent-btn').disabled = !allChecked;
}

function checkDemographicsComplete() {
    const age = document.getElementById('age-input').value;
    const gender = document.querySelector('input[name="gender"]:checked');
    const bdmCourseMember = document.querySelector('input[name="bdm_course_member"]:checked');
    const valid = age && parseInt(age) >= 18 && parseInt(age) <= 100 && gender && bdmCourseMember;
    document.getElementById('demographics-btn').disabled = !valid;
}

function submitDemographicsAndStart() {
    const age = parseInt(document.getElementById('age-input').value);
    const gender = document.querySelector('input[name="gender"]:checked').value;
    const bdmCourseMember = document.querySelector('input[name="bdm_course_member"]:checked').value === 'yes';
    window._demographics = { age, gender, bdmCourseMember };
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
                gender: window._demographics?.gender || null,
                bdm_course_member: window._demographics?.bdmCourseMember ?? null
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

let REEL_CELL_W  = 70;
let REEL_VISIBLE = 540;

function updateReelDimensions() {
    var outer = document.getElementById('reel-outer');
    if (!outer) return;
    var w = outer.offsetWidth || 540;
    // aim for ~5 visible cells; clamp between 50 and 70 px per slot
    REEL_CELL_W  = Math.max(50, Math.min(70, Math.floor(w / 5)));
    REEL_VISIBLE = w;
}

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
        cell.style.cssText = 'width:' + (REEL_CELL_W - 6) + 'px;height:110px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1.5em;font-weight:800;border-radius:8px;margin:0 3px;user-select:none;' +
            (inZone
                ? 'background:#14532d;color:#4ade80;border:2px solid #22c55e;box-shadow:0 0 10px rgba(34,197,94,0.3);'
                : 'background:#1e293b;color:#cbd5e0;');
        cell.textContent = v;
        track.appendChild(cell);
    });
    var pointer = document.getElementById('reel-pointer');
    if (pointer) pointer.style.width = (REEL_CELL_W - 6) + 'px';
    setReelPos(0);
}

function setupReelTrial(config) {
    document.getElementById('wheel-trial-num').textContent = experimentState.currentTrial;
    experimentState.wheelZoneStart = Math.floor(Math.random() * 60) + 15;
    experimentState.wheelZoneEnd   = experimentState.wheelZoneStart + 8;
    document.getElementById('wheel-zone-label').textContent =
        'Winning zone: ' + experimentState.wheelZoneStart + '–' + experimentState.wheelZoneEnd;
    updateReelDimensions();
    buildReel();
    document.getElementById('wheel-spin-btn').disabled = false;
    document.getElementById('spin-status').textContent = '';
    switchScreen('wheel-screen');
}

function spinReel() {
    if (experimentState.reelSpinning) return;
    experimentState.reelSpinning = true;
    document.getElementById('wheel-spin-btn').disabled = true;

    var lossFrame    = experimentState.lossFrame;
    var isForcedRound = experimentState.currentTrial >= experimentState.maxTrials - 1;
    var zs = experimentState.wheelZoneStart;
    var ze = experimentState.wheelZoneEnd;

    var shownOutcome;
    if (isForcedRound) {
        shownOutcome = lossFrame;           // 'near_miss' or 'clear_loss' — forced
    } else if (Math.random() < 1/3) {
        shownOutcome = 'hit';               // independent 1/3 per trial, no cap
    } else {
        shownOutcome = 'clear_loss';        // neutral plain loss regardless of condition
    }

    var targetValue;
    if (shownOutcome === 'hit') {
        targetValue = zs + 1 + Math.floor(Math.random() * Math.max(1, ze - zs - 1));
    } else if (shownOutcome === 'near_miss') {
        var side;
        if (isForcedRound) {
            if (experimentState.reelForcedSide === null) {
                side = Math.random() < 0.5 ? 'right' : 'left';
                experimentState.reelForcedSide = side;
            } else {
                side = experimentState.reelForcedSide === 'right' ? 'left' : 'right';
            }
        } else {
            side = Math.random() < 0.5 ? 'right' : 'left';
        }
        if (side === 'right') {
            targetValue = ze + 1;
        } else {
            targetValue = Math.max(0, zs - 1);
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

    if (result.framed_outcome === 'hit') {
        outcomeText.textContent = '🎉 You got it!';
        outcomeText.className   = 'outcome-text outcome-hit';
    } else if (result.framed_outcome === 'near_miss') {
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
    const delay = result.framed_outcome === 'near_miss' ? 2000 : 1200;
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

// ─── POST SURVEY (one question at a time) ────────────────────────────────────

const SURVEY_QUESTIONS = [
    // ─── PRIMARY DV ───
    {
        key: 'desiredRoundsNextTime',
        text: 'How many additional rounds would you like to play?',
        hint: 'Each round takes about 20 seconds.',
        type: 'buttons',
        options: [
            { label: '0', value: 0 }, { label: '1', value: 1 },
            { label: '2', value: 2 }, { label: '3', value: 3 },
            { label: '4', value: 4 }, { label: '5', value: 5 }
        ]
    },
    // ─── MEDIATORS (Rational Updating) ───
    {
        key: 'improvementConfidence',
        text: 'How confident are you that you could do better if you played again?',
        type: 'likert', min: 1, max: 7,
        anchorLeft: 'Not at all', anchorRight: 'Extremely'
    },
    {
        key: 'learningPotential',
        text: 'How much do you think you could improve at this task with more practice?',
        type: 'likert', min: 1, max: 7,
        anchorLeft: 'Not at all', anchorRight: 'Very much'
    },
    // ─── SECONDARY DVs ───
    {
        key: 'expectedSuccess',
        text: 'If you played 10 more rounds, how many times do you think you would hit the target zone?',
        type: 'buttons',
        options: [
            { label: '0', value: 0 }, { label: '1', value: 1 },
            { label: '2', value: 2 }, { label: '3', value: 3 },
            { label: '4', value: 4 }, { label: '5', value: 5 },
            { label: '6', value: 6 }, { label: '7', value: 7 },
            { label: '8', value: 8 }, { label: '9', value: 9 },
            { label: '10', value: 10 }
        ]
    },
    {
        key: 'appDownloadLikelihood',
        text: 'If this game were available as a free app, how likely would you be to download it?',
        type: 'likert', min: 1, max: 7,
        anchorLeft: 'Very unlikely', anchorRight: 'Very likely'
    },
    // ─── MANIPULATION CHECKS ───
    {
        key: 'confidenceImpact',
        text: 'To what extent did you feel that your actions influenced the outcome of each round?',
        type: 'likert', min: 1, max: 7,
        anchorLeft: 'Not at all', anchorRight: 'Completely'
    },
    {
        key: 'feedbackCredibility',
        text: 'How believable was the feedback you received about your performance?',
        type: 'likert', min: 1, max: 7,
        anchorLeft: 'Not at all', anchorRight: 'Completely'
    },
    {
        key: 'selfRatedAccuracy',
        text: 'During the game, I frequently felt like I was very close to winning.',
        type: 'likert', min: 1, max: 7,
        anchorLeft: 'Strongly disagree', anchorRight: 'Strongly agree'
    },
    {
        key: 'finalRoundCloseness',
        text: 'On your final round, how close did you feel you were to winning?',
        type: 'likert', min: 1, max: 7,
        anchorLeft: 'Not at all close', anchorRight: 'Extremely close'
    },
    // ─── COVARIATES ───
    {
        key: 'frustration',
        text: 'How frustrated did you feel during the game?',
        type: 'likert', min: 1, max: 7,
        anchorLeft: 'Not at all', anchorRight: 'Extremely'
    },
    {
        key: 'motivation',
        text: 'How motivated did you feel to keep trying?',
        type: 'likert', min: 1, max: 7,
        anchorLeft: 'Not at all', anchorRight: 'Extremely'
    },
    {
        key: 'luckVsSkill',
        text: 'How much did luck vs. skill determine your results?',
        type: 'likert', min: 1, max: 7,
        anchorLeft: 'All luck', anchorRight: 'All skill'
    }
];

let surveyStep = 0;


function showPostSurvey() {
    experimentState.survey = {
        desiredRoundsNextTime: null, improvementConfidence: null,
        learningPotential: null,    expectedSuccess: null,
        appDownloadLikelihood: null, confidenceImpact: null,
        feedbackCredibility: null,  selfRatedAccuracy: null,
        finalRoundCloseness: null,  frustration: null,
        motivation: null,           luckVsSkill: null
    };
    surveyStep = 0;
    renderSurveyQuestion();
    switchScreen('post-survey-screen');
}

function renderSurveyQuestion() {
    const q       = SURVEY_QUESTIONS[surveyStep];
    const total   = SURVEY_QUESTIONS.length;
    const pct     = Math.round((surveyStep / total) * 100);
    const isLast  = surveyStep === total - 1;

    document.getElementById('survey-progress').textContent = (surveyStep + 1) + ' / ' + total;
    document.getElementById('survey-progress-bar').style.width = pct + '%';
    document.getElementById('survey-question-text').textContent = q.text;

    const hintEl = document.getElementById('survey-question-hint');
    if (q.hint) { hintEl.textContent = q.hint; hintEl.style.display = 'block'; }
    else        { hintEl.style.display = 'none'; }

    const area = document.getElementById('survey-answer-area');
    area.innerHTML = '';

    const nextBtn = document.getElementById('survey-next-btn');
    nextBtn.disabled = true;
    nextBtn.textContent = isLast ? 'Finish' : 'Next';

    if (q.type === 'buttons') {
        // Simple button row (e.g. 0–5)
        const row = document.createElement('div');
        row.className = 'likert-scale';
        q.options.forEach(function(opt) {
            const btn = document.createElement('button');
            btn.className = 'likert-btn';
            btn.textContent = opt.label;
            btn.dataset.value = opt.value;
            btn.addEventListener('click', function() {
                row.querySelectorAll('.likert-btn').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                experimentState.survey[q.key] = opt.value;
                nextBtn.disabled = false;
            });
            row.appendChild(btn);
        });
        area.appendChild(row);
    } else {
        // 1–7 likert with anchors
        const wrap = document.createElement('div');
        wrap.className = 'likert-scale';
        const leftAnchor = document.createElement('span');
        leftAnchor.className = 'likert-anchor';
        leftAnchor.textContent = q.anchorLeft;
        wrap.appendChild(leftAnchor);
        for (let v = q.min; v <= q.max; v++) {
            const btn = document.createElement('button');
            btn.className = 'likert-btn';
            btn.textContent = v;
            btn.dataset.value = v;
            const val = v;
            btn.addEventListener('click', function() {
                wrap.querySelectorAll('.likert-btn').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                experimentState.survey[q.key] = val;
                nextBtn.disabled = false;
            });
            wrap.appendChild(btn);
        }
        const rightAnchor = document.createElement('span');
        rightAnchor.className = 'likert-anchor';
        rightAnchor.textContent = q.anchorRight;
        wrap.appendChild(rightAnchor);
        area.appendChild(wrap);
    }
}

function surveyNext() {
    surveyStep++;
    if (surveyStep < SURVEY_QUESTIONS.length) {
        renderSurveyQuestion();
    } else {
        submitPostSurvey();
    }
}

async function submitPostSurvey() {
    try {
        const s = experimentState.survey;
        const response = await fetch('/api/save-post-survey', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wants_more_rounds:         s.desiredRoundsNextTime >= 1,
                desired_rounds_next_time:  s.desiredRoundsNextTime,
                improvement_confidence:    s.improvementConfidence,
                learning_potential:        s.learningPotential,
                expected_success:          s.expectedSuccess,
                app_download_likelihood:   s.appDownloadLikelihood,
                confidence_impact:         s.confidenceImpact,
                feedback_credibility:      s.feedbackCredibility,
                self_rated_accuracy:       s.selfRatedAccuracy,
                final_round_closeness:     s.finalRoundCloseness,
                frustration:               s.frustration,
                motivation:                s.motivation,
                luck_vs_skill:             s.luckVsSkill
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
