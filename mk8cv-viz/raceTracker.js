// raceTracker.js
export class RaceTracker {
    constructor(containerId, options = {}) {
        this.container = d3.select(`#${containerId}`);
        this.width = options.width || 400;
        this.height = options.height || 700;
        this.margin = options.margin || { top: 20, right: 20, bottom: 20, left: 20 };
        this.circleRadius = options.circleRadius || 32;
        this.circleSpacing = options.circleSpacing || 72;

        // Updated character map to work with P1-P12 format
        this.characterMap = new Map([
            ['P1', 'Mario'],
            ['P2', 'Luigi']
        ]);

        this.positions = [
            { id: 'P1', position: 1, coins: 0, item1: null, item2: null },
            { id: 'P2', position: 2, coins: 0, item1: null, item2: null },
        ];

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
        // Clear existing content
        this.svg.selectAll('*').remove();

        // Add debug logging
        // console.log('Drawing positions:', this.positions);

        // Create group for each racer
        const racerGroups = this.svg.selectAll('g')
            .data(this.positions, d => d.id)
            .enter()
            .append('g')
            .attr('transform', (d, i) =>
                `translate(${this.width/2}, ${this.margin.top + i * this.circleSpacing})`);

        // Add background circle
        racerGroups.append('circle')
            .attr('r', this.circleRadius)
            .attr('fill', '#1f2937')
            .attr('stroke', '#374151')
            .attr('stroke-width', 2);

        console.log(this.characterMap)

        // Add character images with debug logging
        racerGroups.append('image')
            .attr('x', -this.circleRadius)
            .attr('y', -this.circleRadius)
            .attr('width', this.circleRadius * 2)
            .attr('height', this.circleRadius * 2)
            .attr('href', d => {
                console.log('Processing player:', d);
                const charName = this.characterMap.get(d.id);
                console.log(this.characterMap)
                console.log(charName)
                if (!charName) {
                    console.warn(`No character mapping found for player ${d.id}`);
                    return ''; // Return empty string to prevent 404
                }
                const imagePath = `mario_kart_8_images/Character select icons/${charName}.png`;
                // console.log('Image path:', imagePath);
                return imagePath;
            })
            .attr('clip-path', 'circle()');

        // Add coin count
        racerGroups.append('g')
            .attr('transform', `translate(${this.circleRadius * 1.2}, ${-this.circleRadius * 0.5})`)
            .call(g => {
                g.append('circle')
                    .attr('r', 12)
                    .attr('fill', '#fbbf24');
                g.append('text')
                    .attr('text-anchor', 'middle')
                    .attr('dy', '0.35em')
                    .attr('fill', 'black')
                    .attr('font-weight', 'bold')
                    .attr('font-size', '12px')
                    .text(d => d.coins || 0);
            });

        // Add items with adjusted naming
        racerGroups.each((d, i, nodes) => {
            const g = d3.select(nodes[i]);

            // Item 1
            if (d.item1 && d.item1 !== 'NONE') {
                const item1Name = d.item1; // Remove spaces from item names
                g.append('image')
                    .attr('x', -this.circleRadius * 1.8)
                    .attr('y', -this.circleRadius * 0.75)
                    .attr('width', this.circleRadius)
                    .attr('height', this.circleRadius)
                    .attr('href', `mario_kart_8_images/Items/${item1Name}.png`);
            }

            // Item 2
            if (d.item2 && d.item2 !== 'NONE') {
                const item2Name = d.item2; // Remove spaces from item names
                g.append('image')
                    .attr('x', -this.circleRadius * 1.8)
                    .attr('y', -this.circleRadius * 0.75 + this.circleRadius * 1.1)
                    .attr('width', this.circleRadius)
                    .attr('height', this.circleRadius)
                    .attr('href', `mario_kart_8_images/Items/${item2Name}.png`);
            }
        });
    }

    updatePositions(newPositions) {
        // console.log('Updating positions with:', newPositions);

        this.positions = newPositions;

        const transition = d3.transition()
            .duration(500)
            .ease(d3.easeBackOut);

        const groups = this.svg.selectAll('g')
            .data(newPositions, d => d.id);

        groups.transition(transition)
            .attr('transform', (d, i) =>
                `translate(${this.width/2}, ${this.margin.top + i * this.circleSpacing})`);

        // Redraw everything to update coins and items
        this.drawPositions();
    }
}