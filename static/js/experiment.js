// Experiment state
let experimentState = {
    participantId: null,
    gameOrder: null,
    currentGameType: null,
    currentTrial: 0,
    trials: [],
    barRunning: false,
    barPosition: 0,
    barAnimationId: null,
    targetZoneStart: 0,
    targetZoneWidth: 0,
    barSpeed: 0,
    slotTrialData: null
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

    // Rating slider update
    const slider = document.getElementById('willingness-slider');
    if (slider) {
        slider.addEventListener('input', (e) => {
            document.getElementById('rating-value').textContent = e.target.value;
        });
    }

    // Show test mode panel if ?test=1 in URL
    if (new URLSearchParams(window.location.search).get('test') === '1') {
        document.getElementById('test-mode-panel').classList.remove('hidden');
    }
});

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
        experimentState.gameOrder = data.game_order;
        
        // Determine which game to show first
        const firstGame = data.game_order === 'dartboard_first' ? 'luck' : 'skill';
        showFrameIntro(firstGame);
    } catch (error) {
        console.error('Error starting experiment:', error);
        alert('Error starting experiment');
    }
}

async function showFrameIntro(gameType) {
    experimentState.currentGameType = gameType;
    
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
    experimentState.currentTrial = 0;
    experimentState.trials = [];

    if (experimentState.currentGameType === 'luck') {
        playNextSlotTrial();
    } else {
        playNextTrial();
    }
}

async function playNextTrial() {
    experimentState.currentTrial += 1;

    if (experimentState.currentTrial > 5) {
        showResults();
        return;
    }

    try {
        // Generate bar trial parameters
        const response = await fetch('/api/generate-bar-trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trial_number: experimentState.currentTrial })
        });

        const trialConfig = await response.json();

        // Store config for evaluation
        experimentState.barSpeed = trialConfig.bar_speed;
        experimentState.targetZoneStart = trialConfig.target_zone_start;
        experimentState.targetZoneWidth = trialConfig.target_zone_width;

        // Update UI
        document.getElementById('current-trial').textContent = experimentState.currentTrial;

        // Set up bar task visually (bar visible but not moving)
        setupBarTask(trialConfig);

        // Hide feedback, show start button, hide stop button
        document.getElementById('trial-feedback').classList.add('hidden');
        document.getElementById('start-trial-btn').classList.remove('hidden');
        document.getElementById('stop-btn').classList.add('hidden');

        switchScreen('bar-task-screen');
    } catch (error) {
        console.error('Error generating trial:', error);
    }
}

function beginTrial() {
    // Hide start button, show stop button
    document.getElementById('start-trial-btn').classList.add('hidden');
    document.getElementById('stop-btn').classList.remove('hidden');

    // Update instructions to the short reminder
    document.getElementById('bar-instructions').innerHTML =
        'Press <strong>SPACE</strong> or click <strong>STOP</strong> to stop the bar';

    // Start bar animation
    startBarAnimation();
}

function setupBarTask(config) {
    const targetZone = document.getElementById('target-zone');
    targetZone.style.left = config.target_zone_start + '%';
    targetZone.style.width = config.target_zone_width + '%';

    const bar = document.getElementById('moving-bar');
    bar.style.left = '0%';

    // Reset to full instructions
    document.getElementById('bar-instructions').innerHTML =
        'The red bar will move from left to right. Try to stop it inside the <strong>green target zone</strong>.<br>' +
        'Press <strong>SPACE</strong> or click <strong>STOP</strong> when the bar is inside the zone.';
}

function startBarAnimation() {
    const bar = document.getElementById('moving-bar');
    const startTime = Date.now();
    const duration = 2000; // 2 seconds
    
    experimentState.barRunning = true;
    
    const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Position: 0 to 100 with some randomness based on speed
        const basePosition = progress * 100;
        const randomness = experimentState.barSpeed;
        const position = basePosition + (Math.sin(elapsed / 100) * randomness * 5);
        
        experimentState.barPosition = Math.max(0, Math.min(position, 100));
        bar.style.left = experimentState.barPosition + '%';
        
        if (progress < 1 && experimentState.barRunning) {
            experimentState.barAnimationId = requestAnimationFrame(animate);
        } else if (progress >= 1 && experimentState.barRunning) {
            // Auto-stop if timer expires
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
    try {
        const response = await fetch('/api/evaluate-trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                bar_position: experimentState.barPosition,
                target_zone_start: experimentState.targetZoneStart,
                target_zone_width: experimentState.targetZoneWidth,
                trial_number: experimentState.currentTrial
            })
        });
        
        const result = await response.json();
        
        // Store trial result
        experimentState.trials.push({
            trial_number: experimentState.currentTrial,
            is_hit: result.is_hit,
            is_near_miss: result.is_near_miss,
            position: result.bar_position
        });
        
        // Show feedback
        showTrialFeedback(result.feedback);
    } catch (error) {
        console.error('Error evaluating trial:', error);
    }
}

function showTrialFeedback(feedback) {
    const feedbackBox = document.getElementById('trial-feedback');
    document.getElementById('feedback-message').textContent = feedback;
    feedbackBox.classList.remove('hidden');
}

function nextTrial() {
    if (experimentState.currentGameType === 'luck') {
        playNextSlotTrial();
    } else {
        playNextTrial();
    }
}

async function showResults() {
    try {
        const response = await fetch('/api/get-results', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const results = await response.json();
        
        document.getElementById('win-rate').textContent = results.win_rate + '%';
        document.getElementById('hits-detail').textContent = `${results.hits} out of ${results.total_trials} hits`;
        
        switchScreen('results-screen');
    } catch (error) {
        console.error('Error getting results:', error);
    }
}

async function makeDecision(decision) {
    const willingness = parseInt(document.getElementById('willingness-slider').value);
    
    try {
        const response = await fetch('/api/save-decision', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                decision: decision,
                willingness_rating: willingness,
                game_type: experimentState.currentGameType,
                win_rate: parseFloat(document.getElementById('win-rate').textContent)
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show end screen
            switchScreen('end-screen');
        }
    } catch (error) {
        console.error('Error saving decision:', error);
        alert('Error saving data');
    }
}

// --- Slot Machine Functions ---

const ALL_SLOT_EMOJIS = ['🍒', '🍋', '🍊', '🍇', '🔔', '7️⃣'];

async function playNextSlotTrial() {
    experimentState.currentTrial += 1;

    if (experimentState.currentTrial > 5) {
        showResults();
        return;
    }

    try {
        const response = await fetch('/api/generate-slot-trial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trial_number: experimentState.currentTrial })
        });

        const trialConfig = await response.json();
        experimentState.slotTrialData = trialConfig;

        // Update trial counter
        document.getElementById('slot-current-trial').textContent = experimentState.currentTrial;

        // Reset reels to "?" display
        for (let i = 0; i < 3; i++) {
            const reel = document.getElementById('reel-' + i);
            reel.querySelector('.reel-inner').innerHTML = '<span class="reel-symbol">?</span>';
            reel.classList.remove('stopped', 'spinning');
        }

        // Show spin button, hide feedback
        document.getElementById('spin-btn').classList.remove('hidden');
        document.getElementById('spin-btn').disabled = false;
        document.getElementById('slot-feedback').classList.add('hidden');

        switchScreen('slot-task-screen');
    } catch (error) {
        console.error('Error generating slot trial:', error);
    }
}

async function spinSlots() {
    const trialConfig = experimentState.slotTrialData;
    const finalEmojis = trialConfig.reel_emojis;
    const spinDurations = trialConfig.spin_durations;

    // Disable spin button
    document.getElementById('spin-btn').disabled = true;

    // Start all reels spinning
    for (let i = 0; i < 3; i++) {
        const reel = document.getElementById('reel-' + i);
        reel.classList.add('spinning');
        startReelSpin(i);
    }

    // Stop each reel at staggered times
    for (let i = 0; i < 3; i++) {
        const waitTime = i === 0 ? spinDurations[0] : spinDurations[i] - spinDurations[i - 1];
        await delay(waitTime);
        stopReel(i, finalEmojis[i]);
    }

    // Brief pause after last reel, then evaluate
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
                trial_number: experimentState.currentTrial
            })
        });

        const result = await response.json();

        experimentState.trials.push({
            trial_number: experimentState.currentTrial,
            is_hit: result.is_hit,
            is_near_miss: result.is_near_miss,
            reels: trialConfig.reels
        });

        // Show feedback
        document.getElementById('slot-feedback-message').textContent = result.feedback;
        document.getElementById('slot-feedback').classList.remove('hidden');
        document.getElementById('spin-btn').classList.add('hidden');
    } catch (error) {
        console.error('Error evaluating slot trial:', error);
    }
}

function nextSlotTrial() {
    playNextSlotTrial();
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function switchScreen(screenId) {
    // Hide all screens
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Show target screen
    document.getElementById(screenId).classList.add('active');
}
