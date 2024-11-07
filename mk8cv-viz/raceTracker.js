class RaceTracker {
    constructor(containerId, options = {}) {
        this.container = d3.select(`#${containerId}`);
        this.width = options.width || 128;
        this.height = options.height || 400;
        this.margin = options.margin || { top: 20, right: 20, bottom: 20, left: 20 };
        this.circleRadius = options.circleRadius || 24;
        this.circleSpacing = options.circleSpacing || 56;

        this.positions = [
            { id: 'P7', position: 1 },
            { id: 'P4', position: 2 },
            { id: 'P1', position: 3 },
            { id: 'P3', position: 4 },
            { id: 'P11', position: 5 },
            { id: 'P9', position: 6 },
            { id: 'P12', position: 7 }
        ];

        this.colors = {
            'P1': '#ef4444',
            'P3': '#3b82f6',
            'P4': '#22c55e',
            'P7': '#eab308',
            'P9': '#ec4899',
            'P11': '#8b5cf6',
            'P12': '#f97316'
        };

        this.initializeSVG();
        this.drawPositions();
    }

    initializeSVG() {
        this.svg = this.container
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height);
    }

    drawPositions() {
        const positions = this.svg.selectAll('g')
            .data(this.positions, d => d.id)
            .enter()
            .append('g')
            .attr('transform', (d, i) =>
                `translate(${this.width/2}, ${this.margin.top + i * this.circleSpacing})`);

        positions.append('circle')
            .attr('r', this.circleRadius)
            .style('fill', d => this.colors[d.id] || '#6b7280');

        positions.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.3em')
            .attr('fill', 'white')
            .attr('font-weight', 'bold')
            .style('font-size', '14px')
            .text(d => d.id);
    }

    updatePositions(newPositions) {
        const transition = d3.transition()
            .duration(500)
            .ease(d3.easeBackOut);

        const positions = this.svg.selectAll('g')
            .data(newPositions, d => d.id);

        positions.transition(transition)
            .attr('transform', (d, i) =>
                `translate(${this.width/2}, ${this.margin.top + i * this.circleSpacing})`);

        // Update the stored positions
        this.positions = newPositions;
    }
}