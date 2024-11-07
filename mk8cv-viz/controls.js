class RaceControls {
    constructor(containerId, onStart, onStop, onScenario, onSpeedChange) {
        this.container = document.getElementById(containerId);
        this.isRacing = false;
        this.currentScenario = 'normal';
        this.currentSpeed = 1000; // Default speed (ms)
        this.onStart = onStart;
        this.onStop = onStop;
        this.onScenario = onScenario;
        this.onSpeedChange = onSpeedChange;

        this.initializeControls();
    }

    initializeControls() {
        // Start/Stop button
        const startStopButton = document.createElement('button');
        startStopButton.className = 'btn btn-start';
        startStopButton.textContent = 'Start Race';
        startStopButton.onclick = () => this.toggleRace();

        // Scenarios container
        const scenariosContainer = document.createElement('div');
        scenariosContainer.style.marginTop = '16px';

        const scenarioTitle = document.createElement('div');
        scenarioTitle.textContent = 'Race Scenarios';
        scenarioTitle.style.color = 'white';
        scenarioTitle.style.fontWeight = 'bold';
        scenarioTitle.style.textAlign = 'center';
        scenarioTitle.style.marginBottom = '8px';

        const scenarios = ['normal', 'blueShell', 'catchup', 'breakaway'];
        const scenarioButtons = scenarios.map(scenario => {
            const button = document.createElement('button');
            button.className = `btn btn-scenario ${scenario === this.currentScenario ? 'active' : ''}`;
            button.textContent = scenario.charAt(0).toUpperCase() + scenario.slice(1);
            button.onclick = () => this.setScenario(scenario, scenarioButtons);
            return button;
        });

        this.startStopButton = startStopButton;

        this.container.appendChild(startStopButton);
        this.container.appendChild(scenariosContainer);
        scenariosContainer.appendChild(scenarioTitle);
        scenarioButtons.forEach(button => scenariosContainer.appendChild(button));
                // Add speed control
        const speedControl = document.createElement('div');
        speedControl.className = 'speed-control';

        const speedTitle = document.createElement('div');
        speedTitle.textContent = 'Simulation Speed';
        speedTitle.style.fontWeight = 'bold';
        speedTitle.style.textAlign = 'center';
        speedTitle.style.marginBottom = '8px';

        const speedLabel = document.createElement('div');
        speedLabel.className = 'speed-label';
        speedLabel.innerHTML = '<span>Slower</span><span>Faster</span>';

        const speedSlider = document.createElement('input');
        speedSlider.type = 'range';
        speedSlider.className = 'speed-slider';
        speedSlider.min = '100';
        speedSlider.max = '2000';
        speedSlider.step = '100';
        speedSlider.value = this.currentSpeed;

        speedSlider.oninput = (e) => {
            this.currentSpeed = parseInt(e.target.value);
            this.onSpeedChange(2100 - this.currentSpeed); // Invert the value so sliding right makes it faster
        };

        speedControl.appendChild(speedTitle);
        speedControl.appendChild(speedSlider);
        speedControl.appendChild(speedLabel);

        this.container.appendChild(speedControl);
    }

    toggleRace() {
        this.isRacing = !this.isRacing;
        if (this.isRacing) {
            this.startStopButton.className = 'btn btn-stop';
            this.startStopButton.textContent = 'Stop Race';
            this.onStart();
        } else {
            this.startStopButton.className = 'btn btn-start';
            this.startStopButton.textContent = 'Start Race';
            this.onStop();
        }
    }

    setScenario(scenario, buttons) {
        this.currentScenario = scenario;
        buttons.forEach(button => {
            button.className = `btn btn-scenario ${button.textContent.toLowerCase() === scenario ? 'active' : ''}`;
        });
        this.onScenario(scenario);
    }
}