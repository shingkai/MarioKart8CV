export class RaceTracker {
    constructor(containerId, options = {}) {
        this.container = d3.select(`#${containerId}`);
        this.width = options.width || 800;
        this.height = options.height || 400;
        this.margin = options.margin || { top: 20, right: 20, bottom: 20, left: 20 };
        this.circleRadius = options.circleRadius || 24;
        this.timeWindowSize = options.timeWindowSize || 20;
        
        // Initialize data storage for time series
        this.timeSeriesData = new Map();
        this.timeIndex = 0;
        
        this.initializeSVG();
        this.setupScales();
        this.setupAxes();
    }

    initializeSVG() {
        this.svg = this.container
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height);

        this.mainGroup = this.svg
            .append('g')
            .attr('transform', `translate(${this.margin.left},${this.margin.top})`);
    }

    setupScales() {
        this.innerWidth = this.width - this.margin.left - this.margin.right;
        this.innerHeight = this.height - this.margin.top - this.margin.bottom;

        // X scale for time, with extra space for one more tick
        this.xScale = d3.scaleLinear()
            .range([0, this.innerWidth]);

        // Y scale for positions (fixed from 1 to 12, inverted)
        this.yScale = d3.scaleLinear()
            .domain([1, 12])
            .range([0, this.innerHeight]);
        
        // Line generator
        this.line = d3.line()
            .x(d => this.xScale(d.time))
            .y(d => this.yScale(d.position));
    }

    setupAxes() {
        const axisColor = '#9CA3AF';

        // Create and style x-axis
        this.xAxis = this.mainGroup.append('g')
            .attr('class', 'x-axis')
            .attr('transform', `translate(0,${this.innerHeight})`);

        // Create and style y-axis
        this.yAxis = this.mainGroup.append('g')
            .attr('class', 'y-axis')
            .call(d3.axisLeft(this.yScale)
                .ticks(12)
                .tickFormat(d3.format('d')));

        // Style both axes
        this.svg.selectAll('.x-axis, .y-axis')
            .attr('color', axisColor)
            .selectAll('line, path')
            .attr('stroke', axisColor);
    }

    updateScales() {
        // Update x scale domain to include one extra tick
        const maxTime = this.timeIndex;
        if (maxTime < this.timeWindowSize) {
            this.xScale.domain([0, maxTime + 1]);
        } else {
            this.xScale.domain([maxTime - this.timeWindowSize, maxTime + 1]);
        }

        // Update x-axis
        this.xAxis.call(d3.axisBottom(this.xScale)
            .ticks(maxTime < this.timeWindowSize ? maxTime + 1 : this.timeWindowSize + 1)
            .tickFormat(""));
        
        // Maintain axis styling after update
        const axisColor = '#9CA3AF';
        this.svg.selectAll('.x-axis')
            .attr('color', axisColor)
            .selectAll('line, path')
            .attr('stroke', axisColor);
        
        this.svg.selectAll('.x-axis text')
            .attr('fill', axisColor);
    }

    updatePositions(newPositions) {
        this.timeIndex++;
        
        // Update time series data
        newPositions.forEach((racer, index) => {
            if (!this.timeSeriesData.has(racer.id)) {
                this.timeSeriesData.set(racer.id, []);
            }
            
            const racerData = this.timeSeriesData.get(racer.id);
            racerData.push({
                time: this.timeIndex,
                position: racer.position,
                coins: racer.coins,
                items: [racer.item1, racer.item2].filter(item => item && item !== 'NONE')
            });
            if (racerData.length > this.timeWindowSize) {
                racerData.shift()
            }
        });

        this.drawTimeSeries();
    }

    drawTimeSeries() {
        this.updateScales();

        // Create color scale for racers
        const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

        // Draw lines
        const lines = this.mainGroup.selectAll('.racer-line')
            .data(Array.from(this.timeSeriesData.entries()), d => d[0]);

        // Update existing lines
        lines.select('path')
            .attr('d', d => this.line(d[1]));

        // Enter new lines
        const linesEnter = lines.enter()
            .append('g')
            .attr('class', 'racer-line');

        linesEnter.append('path')
            .attr('fill', 'none')
            .attr('stroke', (d, i) => colorScale(i))
            .attr('stroke-width', 2)
            .attr('d', d => this.line(d[1]));

        // Update markers (circles) for current position
        const markers = this.mainGroup.selectAll('.current-position')
            .data(Array.from(this.timeSeriesData.entries()), d => d[0]);

        markers.enter()
            .append('g')
            .attr('class', 'current-position')
            .merge(markers)
            .each((d, i, nodes) => {
                const g = d3.select(nodes[i]);
                const currentData = d[1][d[1].length - 1];

                // Remove existing elements
                g.selectAll('*').remove();

                // Add background circle
                g.append('circle')
                    .attr('r', this.circleRadius)
                    .attr('cx', this.xScale(currentData.time))
                    .attr('cy', this.yScale(currentData.position))
                    .attr('fill', '#1f2937')
                    .attr('stroke', '#374151')
                    .attr('stroke-width', 2);

                // Add character image
                g.append('image')
                    .attr('x', this.xScale(currentData.time) - this.circleRadius)
                    .attr('y', this.yScale(currentData.position) - this.circleRadius)
                    .attr('width', this.circleRadius * 2)
                    .attr('height', this.circleRadius * 2)
                    .attr('href', () => {
                        const charName = this.characterMap.get(d[0]);
                        return charName ? 
                            `mario_kart_8_images/Character select icons/${charName}.png` : '';
                    })
                    .attr('clip-path', 'circle()');

                // Add coins
                if (currentData.coins) {
                    const coinGroup = g.append('g')
                        .attr('transform', 
                            `translate(${this.xScale(currentData.time) + this.circleRadius * 1.2},
                            ${this.yScale(currentData.position) - this.circleRadius * 0.5})`);
                    
                    coinGroup.append('circle')
                        .attr('r', 12)
                        .attr('fill', '#fbbf24');
                    
                    coinGroup.append('text')
                        .attr('text-anchor', 'middle')
                        .attr('dy', '0.35em')
                        .attr('fill', 'black')
                        .attr('font-weight', 'bold')
                        .attr('font-size', '12px')
                        .text(currentData.coins);
                }

                // Add items
                currentData.items.forEach((item, idx) => {
                    g.append('image')
                        .attr('x', this.xScale(currentData.time) - this.circleRadius * 1.8)
                        .attr('y', this.yScale(currentData.position) - this.circleRadius * 0.75 + 
                            idx * this.circleRadius * 1.1)
                        .attr('width', this.circleRadius)
                        .attr('height', this.circleRadius)
                        .attr('href', `mario_kart_8_images/Items/${item}.png`);
                });
            });

        // Remove old markers
        markers.exit().remove();
    }
}