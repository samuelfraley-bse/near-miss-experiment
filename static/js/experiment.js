// Experiment state
let experimentState = {
    participantId: null,
    game1Type: null,
    game2Type: null,
    currentGame: 1,
    currentGameType: null,
    currentTrial: 0,
    isPracticeTrial: false,
    practiceCompletedGame1: false,
    practiceCompletedGame2: false,
    game1Trials: [],
    game2Trials: [],
    score: 0,
    bankroll: 0,
    startingBankroll: 20,
    maxWager: 5,
    currentWager: 0,
    maxTrials: 15,
    // Bar game state
    barRunning: false,
    barPosition: 0,
    barAnimationId: null,
    targetZoneStart: 0,
    targetZoneWidth: 0,
    barSpeed: 0,
    barDuration: 0,
    // Slot game state
    slotTrialData: null,
    // Outcome & timing
    lastOutcome: null,
    outcomeShownAt: null,
    pendingNextAction: null,
    pendingNextActionData: null,
    // Self-report tracking
    selfReportRatings: { closeness: null, control: null, urge: null },
    selfReportInterval: 5
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Keyboard support
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && experimentState.barRunning) {
            e.preventDefault();
            stopBar();
        }
    });

    // Likert button handlers
    document.querySelectorAll('.likert-scale').forEach(scale => {
        scale.querySelectorAll('.likert-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                // Deselect siblings
                scale.querySelectorAll('.likert-btn').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                // Store rating
                const scaleId = scale.id;
                const value = parseInt(btn.dataset.value);
                if (scaleId === 'closeness-scale') experimentState.selfReportRatings.closeness = value;
                if (scaleId === 'control-scale') experimentState.selfReportRatings.control = value;
                if (scaleId === 'urge-scale') experimentState.selfReportRatings.urge = value;
                // Enable submit if all answered
                checkSelfReportComplete();
            });
        });
    });

    // Show test mode panel if ?test=1 in URL
    if (new URLSearchParams(window.location.search).get('test') === '1') {
        document.getElementById('test-mode-panel').classList.remove('hidden');
    }
});

function checkSelfReportComplete() {
    const r = experimentState.selfReportRatings;
    const allAnswered = r.closeness !== null && r.control !== null && r.urge !== null;
    document.getElementById('submit-self-report-btn').disabled = !allAnswered;
}

// --- Session & Flow ---

async function startExperiment(forceGameType) {
    try {
        const response = await fetch('/api/start-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                participant_id: null,
                force_game_type: forceGameType || null
            })
        });

        const data = await response.json();
        experimentState.participantId = data.participant_id;
        experimentState.game1Type = data.game1_type;
        experimentState.game2Type = data.game2_type;
        experimentState.currentGame = 1;
        experimentState.score = data.score || 0;
        experimentState.bankroll = data.bankroll || 0;
        experimentState.startingBankroll = data.starting_bankroll || 20;
        experimentState.maxWager = data.max_wager || 5;
        experimentState.maxTrials = data.max_trials;
        experimentState.practiceCompletedGame1 = false;
        experimentState.practiceCompletedGame2 = false;
        experimentState.isPracticeTrial = false;

        // Start with game 1
        experimentState.currentGameType = data.game1_type;
        showFrameIntro(data.game1_type);
    } catch (error) {
        console.error('Error starting experiment:', error);
        alert('Error starting experiment');
    }
}

async function showFrameIntro(gameType) {
    experimentState.currentGameType = gameType;
    experimentState.currentTrial = 0;

    try {
        const response = await fetch(`/api/get-frame/${gameType}`);
        const frame = await response.json();

        document.getElementById('frame-title').textContent = frame.title;
        document.getElementById('frame-description').textContent = frame.description;

        switchScreen('frame-intro-screen');
    } catch (error) {
        console.error('Error loading frame:', error);
    }
}

function proceedToGame() {
    if (isPracticeDoneForCurrentGame()) {
        showWagerScreen();
    } else {
        startPracticeTrial();
    }
}

function isPracticeDoneForCurrentGame() {
    return experimentState.currentGame === 1
        ? experimentState.practiceCompletedGame1
        : experimentState.practiceCompletedGame2;
}

function markPracticeDoneForCurrentGame() {
    if (experimentState.currentGame === 1) {
        experimentState.practiceCompletedGame1 = true;
    } else {
        experimentState.practiceCompletedGame2 = true;
    }
}

function startPracticeTrial() {
    experimentState.isPracticeTrial = true;
    experimentState.currentWager = 0;

    if (experimentState.currentGameType === 'luck') {
        playNextSlotTrial(true);
    } else {
        playNextBarTrial(true);
    }
}

function updateWagerButtons() {
    const maxAllowedWager = Math.min(experimentState.maxWager, experimentState.bankroll);
    document.querySelectorAll('.wager-btn').forEach(btn => {
        const value = parseInt(btn.dataset.wager, 10);
        btn.disabled = experimentState.bankroll < 1 || value > maxAllowedWager;
    });
}

// --- Wager ---

function showWagerScreen() {
    experimentState.isPracticeTrial = false;
    const nextTrial = experimentState.currentTrial + 1;
    document.getElementById('wager-trial-num').textContent = nextTrial;
    document.getElementById('wager-score').textContent = experimentState.bankroll;
    updateWagerButtons();
    switchScreen('wager-screen');
}

function placeWager(amount) {
    const maxAllowedWager = Math.min(experimentState.maxWager, experimentState.bankroll);
    if (amount < 1 || amount > maxAllowedWager) {
        return;
    }

    experimentState.currentWager = amount;

    if (experimentState.currentGameType === 'luck') {
        playNextSlotTrial(false);
    } else {
        playNextBarTrial(false);
    }
}

// --- Bar Task ---

async function playNextBarTrial(isPractice = false) {
    if (!isPractice) {
        experimentState.currentTrial += 1;
    }
    const trialNumber = isPractice ? 0 : experimentState.currentTrial;

    try {
        const response = await fetch('/api/generate-bar-trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trial_number: trialNumber })
        });

        const trialConfig = await response.json();

        experimentState.barSpeed = trialConfig.bar_speed;
        experimentState.barDuration = trialConfig.duration;
        experimentState.targetZoneStart = trialConfig.target_zone_start;
        experimentState.targetZoneWidth = trialConfig.target_zone_width;

        // Update status bar
        document.getElementById('bar-trial-num').textContent = isPractice ? 'Practice' : experimentState.currentTrial;
        document.getElementById('bar-wager').textContent = experimentState.currentWager;
        document.getElementById('bar-score').textContent = experimentState.bankroll;

        // Set up bar visually
        setupBarTask(trialConfig);

        // Show start button, hide stop button
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

    document.getElementById('bar-instructions').innerHTML =
        'The red bar will move from left to right. Try to stop it inside the <strong>green target zone</strong>.<br>' +
        'Press <strong>SPACE</strong> or click <strong>STOP</strong> when the bar is inside the zone.';
}

function beginTrial() {
    document.getElementById('start-trial-btn').classList.add('hidden');
    document.getElementById('stop-btn').classList.remove('hidden');

    document.getElementById('bar-instructions').innerHTML =
        'Press <strong>SPACE</strong> or click <strong>STOP</strong> to stop the bar';

    startBarAnimation();
}

function startBarAnimation() {
    const bar = document.getElementById('moving-bar');
    const startTime = Date.now();
    const duration = experimentState.barDuration || 1500;

    experimentState.barRunning = true;

    const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);

        const basePosition = progress * 100;
        const randomness = experimentState.barSpeed;
        const position = basePosition + (Math.sin(elapsed / 100) * randomness * 5);

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

    evaluateBarTrial();
}

async function evaluateBarTrial() {
    try {
        const response = await fetch('/api/evaluate-trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                bar_position: experimentState.barPosition,
                target_zone_start: experimentState.targetZoneStart,
                target_zone_width: experimentState.targetZoneWidth,
                trial_number: experimentState.currentTrial,
                wager: experimentState.currentWager,
                is_practice: experimentState.isPracticeTrial
            })
        });

        const result = await response.json();
        if (!response.ok || result.success === false) {
            throw new Error(result.error || 'Failed to evaluate trial');
        }

        experimentState.score = result.score;
        experimentState.bankroll = result.bankroll;
        experimentState.lastOutcome = result;
        if (!result.is_practice && experimentState.currentGame === 1) {
            experimentState.game1Trials.push(result);
        } else if (!result.is_practice) {
            experimentState.game2Trials.push(result);
        }

        showOutcome(result);
    } catch (error) {
        console.error('Error evaluating trial:', error);
    }
}

// --- Slot Machine ---

const ALL_SLOT_EMOJIS = ['🍒', '🍋', '🍊', '🍇', '🔔', '7️⃣'];

async function playNextSlotTrial(isPractice = false) {
    if (!isPractice) {
        experimentState.currentTrial += 1;
    }
    const trialNumber = isPractice ? 0 : experimentState.currentTrial;

    try {
        const response = await fetch('/api/generate-slot-trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trial_number: trialNumber })
        });

        const trialConfig = await response.json();
        experimentState.slotTrialData = trialConfig;

        // Update status bar
        document.getElementById('slot-trial-num').textContent = isPractice ? 'Practice' : experimentState.currentTrial;
        document.getElementById('slot-wager').textContent = experimentState.currentWager;
        document.getElementById('slot-score').textContent = experimentState.bankroll;

        // Reset reels
        for (let i = 0; i < 3; i++) {
            const reel = document.getElementById('reel-' + i);
            reel.querySelector('.reel-inner').innerHTML = '<span class="reel-symbol">?</span>';
            reel.classList.remove('stopped', 'spinning');
        }

        document.getElementById('spin-btn').classList.remove('hidden');
        document.getElementById('spin-btn').disabled = false;

        switchScreen('slot-task-screen');
    } catch (error) {
        console.error('Error generating slot trial:', error);
    }
}

async function spinSlots() {
    const trialConfig = experimentState.slotTrialData;
    const finalEmojis = trialConfig.reel_emojis;
    const spinDurations = trialConfig.spin_durations;

    document.getElementById('spin-btn').disabled = true;

    for (let i = 0; i < 3; i++) {
        const reel = document.getElementById('reel-' + i);
        reel.classList.add('spinning');
        startReelSpin(i);
    }

    for (let i = 0; i < 3; i++) {
        const waitTime = i === 0 ? spinDurations[0] : spinDurations[i] - spinDurations[i - 1];
        await delay(waitTime);
        stopReel(i, finalEmojis[i]);
    }

    await delay(500);
    await evaluateSlotTrial();
}

function startReelSpin(reelIndex) {
    const reelInner = document.querySelector('#reel-' + reelIndex + ' .reel-inner');
    let currentIndex = 0;

    const intervalId = setInterval(() => {
        currentIndex = (currentIndex + 1) % ALL_SLOT_EMOJIS.length;
        reelInner.innerHTML = '<span class="reel-symbol">' + ALL_SLOT_EMOJIS[currentIndex] + '</span>';
    }, 80);

    document.getElementById('reel-' + reelIndex).dataset.spinInterval = intervalId;
}

function stopReel(reelIndex, finalEmoji) {
    const reel = document.getElementById('reel-' + reelIndex);
    const reelInner = reel.querySelector('.reel-inner');

    clearInterval(parseInt(reel.dataset.spinInterval));

    reelInner.innerHTML = '<span class="reel-symbol">' + finalEmoji + '</span>';
    reel.classList.remove('spinning');
    reel.classList.add('stopped');
}

async function evaluateSlotTrial() {
    const trialConfig = experimentState.slotTrialData;

    try {
        const response = await fetch('/api/evaluate-slot-trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                reels: trialConfig.reels,
                trial_number: experimentState.currentTrial,
                wager: experimentState.currentWager,
                is_practice: experimentState.isPracticeTrial
            })
        });

        const result = await response.json();
        if (!response.ok || result.success === false) {
            throw new Error(result.error || 'Failed to evaluate slot trial');
        }

        experimentState.score = result.score;
        experimentState.bankroll = result.bankroll;
        experimentState.lastOutcome = result;
        if (!result.is_practice && experimentState.currentGame === 1) {
            experimentState.game1Trials.push(result);
        } else if (!result.is_practice) {
            experimentState.game2Trials.push(result);
        }

        showOutcome(result);
    } catch (error) {
        console.error('Error evaluating slot trial:', error);
    }
}

// --- Outcome & Decision ---

function showOutcome(result) {
    // Display outcome
    const outcomeText = document.getElementById('outcome-text');
    const outcomePoints = document.getElementById('outcome-points');
    const decisionTitle = document.getElementById('decision-title');
    const continueText = document.getElementById('continue-choice-text');
    const switchBtn = document.getElementById('switch-btn');

    if (result.is_practice) {
        outcomeText.textContent = result.is_hit ? 'Practice hit!' : (result.is_near_miss ? 'Practice near-miss' : 'Practice miss');
        outcomeText.className = 'outcome-text ' + (result.is_hit ? 'outcome-hit' : (result.is_near_miss ? 'outcome-near-miss' : 'outcome-miss'));
        outcomePoints.textContent = 'Practice trial: no points won or lost';
        outcomePoints.className = 'outcome-points points-zero';
        decisionTitle.textContent = 'Practice complete. Start real trials?';
        continueText.textContent = 'Start real trials';
        switchBtn.classList.add('hidden');
    } else if (result.is_hit) {
        outcomeText.textContent = 'You made it!';
        outcomeText.className = 'outcome-text outcome-hit';
        outcomePoints.textContent = '+' + result.points_delta + ' points';
        outcomePoints.className = 'outcome-points points-gained';
    } else if (result.is_near_miss) {
        outcomeText.textContent = 'Almost made it!';
        outcomeText.className = 'outcome-text outcome-near-miss';
        outcomePoints.textContent = '-' + experimentState.currentWager + ' points';
        outcomePoints.className = 'outcome-points points-lost';
    } else {
        outcomeText.textContent = 'Missed it!';
        outcomeText.className = 'outcome-text outcome-miss';
        outcomePoints.textContent = '-' + experimentState.currentWager + ' points';
        outcomePoints.className = 'outcome-points points-lost';
    }

    if (!result.is_practice) {
        decisionTitle.textContent = 'What would you like to do?';
        continueText.textContent = 'Play again';
        switchBtn.classList.remove('hidden');
    }

    document.getElementById('outcome-score').textContent = result.bankroll;

    // Start reaction time clock
    experimentState.outcomeShownAt = Date.now();

    switchScreen('outcome-screen');
}

async function handleTrialDecision(decision) {
    if (experimentState.isPracticeTrial) {
        markPracticeDoneForCurrentGame();
        experimentState.isPracticeTrial = false;
        showWagerScreen();
        return;
    }

    const reactionTime = experimentState.outcomeShownAt ? (Date.now() - experimentState.outcomeShownAt) : 0;

    document.querySelectorAll('#outcome-screen .choice-btn').forEach(btn => {
        btn.disabled = true;
    });

    try {
        const response = await fetch('/api/save-trial-decision', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                decision: decision,
                reaction_time_ms: reactionTime,
                trial_number: experimentState.currentTrial
            })
        });

        const result = await response.json();
        experimentState.score = result.score;
        experimentState.bankroll = result.bankroll;

        // Check if self-report is due (every 5 trials)
        if (experimentState.currentTrial % experimentState.selfReportInterval === 0) {
            showSelfReport();
            // After self-report, we'll route based on result.next_action
            experimentState.pendingNextAction = result.next_action;
            experimentState.pendingNextActionData = result;
            return;
        }

        // Route based on next action
        routeNextAction(result.next_action, result);
    } catch (error) {
        console.error('Error saving decision:', error);
        document.querySelectorAll('#outcome-screen .choice-btn').forEach(btn => {
            btn.disabled = false;
        });
    }
}

function routeNextAction(nextAction, result) {
    if (typeof result.bankroll === 'number') {
        experimentState.bankroll = result.bankroll;
    }

    if (nextAction === 'continue') {
        showWagerScreen();
    } else if (nextAction === 'switch_to_game2') {
        switchToGame2(result.game2_type, result.bankroll);
    } else if (nextAction === 'end') {
        showSummary();
    }

    document.querySelectorAll('#outcome-screen .choice-btn').forEach(btn => {
        btn.disabled = false;
    });
}

function switchToGame2(game2Type, bankroll) {
    experimentState.currentGame = 2;
    experimentState.currentGameType = game2Type;
    if (typeof bankroll === 'number') {
        experimentState.bankroll = bankroll;
    }
    experimentState.currentTrial = 0;
    showFrameIntro(game2Type);
}

// --- Self-Report ---

function showSelfReport() {
    // Reset selections
    experimentState.selfReportRatings = { closeness: null, control: null, urge: null };
    document.querySelectorAll('.likert-btn').forEach(btn => btn.classList.remove('selected'));
    document.getElementById('submit-self-report-btn').disabled = true;

    switchScreen('self-report-screen');
}

async function submitSelfReport() {
    try {
        await fetch('/api/save-self-report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                after_trial: experimentState.currentTrial,
                closeness: experimentState.selfReportRatings.closeness,
                control: experimentState.selfReportRatings.control,
                urge: experimentState.selfReportRatings.urge
            })
        });

        // Route to pending action
        const pendingAction = experimentState.pendingNextAction || 'continue';
        const pendingData = experimentState.pendingNextActionData || {};
        experimentState.pendingNextAction = null;
        experimentState.pendingNextActionData = null;

        routeNextAction(pendingAction, pendingData);
    } catch (error) {
        console.error('Error saving self-report:', error);
    }
}

// --- Summary ---

async function showSummary() {
    try {
        const response = await fetch('/api/get-summary');
        const summary = await response.json();

        document.getElementById('summary-score').textContent = summary.total_score + ' pts';
        document.getElementById('summary-game1-label').textContent =
            (summary.game1_type === 'skill' ? 'Skill Game' : 'Luck Game');
        document.getElementById('summary-game1-trials').textContent =
            summary.game1_trials_played + ' trials';
        document.getElementById('summary-game2-label').textContent =
            (summary.game2_type === 'skill' ? 'Skill Game' : 'Luck Game');
        document.getElementById('summary-game2-trials').textContent =
            summary.game2_trials_played + ' trials';

        switchScreen('summary-screen');
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}

// --- Utilities ---

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function switchScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');
}
