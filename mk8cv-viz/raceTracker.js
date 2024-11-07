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
        this.characterMap = {
            'P1': 'Mario',
            'P2': 'Luigi',
            'P3': 'Peach',
            'P4': 'Yoshi',
            'P5': 'Bowser',
            'P6': 'Donkey Kong',
            'P7': 'Toad',
            'P8': 'Dry Bones',
            'P9': 'Daisy',
            'P10': 'Waluigi',
            'P11': 'Rosalina',
            'P12': 'Metal Mario'
        };

        this.positions = [
            { id: 'P1', position: 1, coins: 5, item1: 'Banana', item2: 'Green Shell' },
            { id: 'P2', position: 2, coins: 3, item1: 'Red Shell', item2: null },
            { id: 'P3', position: 3, coins: 8, item1: 'Star', item2: null },
            { id: 'P4', position: 4, coins: 2, item1: null, item2: null },
            { id: 'P5', position: 5, coins: 6, item1: 'Mushroom', item2: 'Mushroom' },
            { id: 'P6', position: 6, coins: 4, item1: 'Spiny Shell', item2: null },
            { id: 'P7', position: 7, coins: 1, item1: null, item2: null },
            { id: 'P8', position: 8, coins: 7, item1: 'Lightning', item2: null },
            { id: 'P9', position: 9, coins: 0, item1: null, item2: null },
            { id: 'P10', position: 10, coins: 9, item1: 'Banana', item2: 'Banana' },
            { id: 'P11', position: 11, coins: 4, item1: null, item2: null },
            { id: 'P12', position: 12, coins: 2, item1: 'Green Shell', item2: null },
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

        // Add character images with debug logging
        racerGroups.append('image')
            .attr('x', -this.circleRadius)
            .attr('y', -this.circleRadius)
            .attr('width', this.circleRadius * 2)
            .attr('height', this.circleRadius * 2)
            .attr('href', d => {
                // console.log('Processing player:', d);
                const charName = this.characterMap[d.id];
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
            if (d.item1 && d.item1 !== 'None') {
                const item1Name = d.item1; // Remove spaces from item names
                g.append('image')
                    .attr('x', -this.circleRadius * 1.8)
                    .attr('y', -this.circleRadius * 0.75)
                    .attr('width', this.circleRadius)
                    .attr('height', this.circleRadius)
                    .attr('href', `mario_kart_8_images/Items/${item1Name}.png`);
            }

            // Item 2
            if (d.item2 && d.item2 !== 'None') {
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