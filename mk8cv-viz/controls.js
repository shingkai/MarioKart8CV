export class RaceControls {
    constructor(containerId, onStart, onStop) {
        this.container = document.getElementById(containerId);
        this.isRacing = false;
        this.onStart = onStart;
        this.onStop = onStop;

        this.initializeControls();
    }

    cleanup() {
        // Remove event listeners and clean up any resources
        if (this.startStopButton) {
            this.startStopButton.onclick = null;
        }
        if (this.container) {
            this.container.innerHTML = '';
        }
    }

    initializeControls() {
        // Clear existing content
        if (this.container) {
            this.container.innerHTML = '';
        }

        // Start/Stop button
        const startStopButton = document.createElement('button');
        startStopButton.className = 'btn btn-start';
        startStopButton.textContent = 'Start Race';
        startStopButton.onclick = () => this.toggleRace();
        this.startStopButton = startStopButton;
        this.container.appendChild(startStopButton);

        // RaceID input field
        const raceIDInput = document.createElement('input');
        raceIDInput.type = 'text';
        raceIDInput.id = "raceIDInput";
        raceIDInput.placeholder = "Enter Race ID";
        raceIDInput.name = "raceIDInput";
        this.raceIDInput = raceIDInput;
        this.container.appendChild(raceIDInput);
    }

    toggleRace() {
        console.log(`toggleRace: ${this.isRacing}`);
        if (this.isRacing) {
            this.startStopButton.className = 'btn btn-stop';
            this.startStopButton.textContent = 'Stop Race';
            this.onStart(this.raceIDInput.value);
            this.isRacing = !this.isRacing;
        } else {
            this.startStopButton.className = 'btn btn-start';
            this.startStopButton.textContent = 'Start Race';
            if (this.raceIDInput.value) {
                this.onStop();
                this.isRacing = !this.isRacing;
            } else {
                alert('Race ID is required');
            }
        }
    }

}