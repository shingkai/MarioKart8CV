export class RaceControls {
    constructor(containerId, onStart, onStop) {
        this.container = document.getElementById(containerId);
        this.isRacing = false;
        this.onStart = onStart;
        this.onStop = onStop;

        this.initializeControls();
    }

    initializeControls() {
        // Start/Stop button
        const startStopButton = document.createElement('button');
        startStopButton.className = 'btn btn-start';
        startStopButton.textContent = 'Start Race';
        startStopButton.onclick = () => this.toggleRace();


        this.startStopButton = startStopButton;

        this.container.appendChild(startStopButton);
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

}