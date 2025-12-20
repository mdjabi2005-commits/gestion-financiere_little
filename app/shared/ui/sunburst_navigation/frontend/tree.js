/**
 * Dynamic Tree - Simplified D3.js Implementation
 * Minimal fractal tree visualization with Streamlit integration
 */

// Global state
let hierarchyData = null;
let currentNode = 'TR';
let navigationStack = ['TR'];
let svg, g, tooltip;
let width = 800;
let height = 600;

// Streamlit Component Integration
function onRender(event) {
    const data = event.detail;

    if (!data || !data.args) {
        console.error('No data received from Python');
        return;
    }

    console.log('Received data from Python:', data.args);
    hierarchyData = data.args.hierarchy;
    height = data.args.height || 600;

    // Initialize or update visualization
    if (!svg) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => init());
        } else {
            init();
        }
    } else {
        updateVisualization();
    }

    // Update Streamlit frame height
    window.Streamlit.setFrameHeight(height + 150);
}

// Register Streamlit events
if (window.Streamlit) {
    window.Streamlit.setComponentReady();
    window.Streamlit.events.addEventListener(window.Streamlit.RENDER_EVENT, onRender);
} else {
    console.error('Streamlit not found');
}

function init() {
    console.log('Dynamic Tree: Initializing...');

    const container = d3.select('#tree-container');
    width = container.node().clientWidth || 800;

    // Create SVG
    svg = container.append('svg')
        .attr('width', width)
        .attr('height', height);

    g = svg.append('g');

    // Create tooltip
    tooltip = container.append('div')
        .attr('class', 'tooltip');

    // Create controls
    const controls = container.append('div').attr('class', 'controls');
    controls.append('button').attr('class', 'control-btn').attr('id', 'back-btn')
        .text('← Retour').on('click', handleBack);
    controls.append('button').attr('class', 'control-btn').attr('id', 'reset-btn')
        .text('⟲ Reset').on('click', handleReset);

    // Create breadcrumb
    container.append('div').attr('class', 'breadcrumb')
        .html('<span id="breadcrumb-path">Transactions</span>');

    // Initial render
    updateVisualization();
}

function updateVisualization() {
    if (!hierarchyData || !hierarchyData[currentNode]) {
        console.error('No data for node:', currentNode);
        return;
    }

    const node = hierarchyData[currentNode];
    updateBreadcrumb();
    updateButtons();
    renderTree(node);
}

function renderTree(node) {
    g.selectAll('*').remove();

    if (!node.children || node.children.length === 0) {
        showLeafMessage(node);
        return;
    }

    // Simple horizontal layout
    const childrenData = node.children.map(code => hierarchyData[code]).filter(n => n);
    const totalValue = childrenData.reduce((sum, child) => sum + (child.amount || child.total || 0), 0);

    const y = 100;
    const totalWidth = width * 0.8;
    const startX = (width - totalWidth) / 2;
    let currentX = startX;

    childrenData.forEach((child, i) => {
        const value = child.amount || child.total || 0;
        const proportion = value / totalValue;
        const rectWidth = Math.max(60, totalWidth * proportion - 10);
        const rectHeight = 80;

        const rect = g.append('rect')
            .attr('x', currentX)
            .attr('y', y)
            .attr('width', 0)
            .attr('height', rectHeight)
            .attr('rx', 6)
            .style('fill', child.color || '#10b981')
            .style('stroke', '#fff')
            .style('stroke-width', 2)
            .style('cursor', 'pointer')
            .on('click', () => {
                const clickedCode = node.children[i];

                // Navigate in tree
                currentNode = clickedCode;
                navigationStack.push(currentNode);
                updateVisualization();

                // Send to Python via Streamlit Component API
                if (window.Streamlit) {
                    window.Streamlit.setComponentValue({
                        code: clickedCode,
                        action: 'select',
                        label: child.label
                    });
                }
            })
            .on('mouseenter', function () {
                d3.select(this).style('filter', 'brightness(1.3)');
                tooltip.html(`<div>${child.label}</div><div>${formatCurrency(value)}</div>`)
                    .style('left', (currentX + rectWidth / 2) + 'px')
                    .style('top', (y - 20) + 'px')
                    .classed('visible', true);
            })
            .on('mouseleave', function () {
                d3.select(this).style('filter', 'brightness(1)');
                tooltip.classed('visible', false);
            });

        rect.transition().duration(500).attr('width', rectWidth);

        // Label
        g.append('text')
            .attr('x', currentX + rectWidth / 2)
            .attr('y', y + 40)
            .attr('text-anchor', 'middle')
            .style('fill', 'white')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .text(truncate(child.label, rectWidth));

        currentX += rectWidth + 10;
    });
}

function handleBack() {
    if (navigationStack.length <= 1) return;
    navigationStack.pop();
    currentNode = navigationStack[navigationStack.length - 1];
    updateVisualization();

    // Notify Python
    if (window.Streamlit) {
        window.Streamlit.setComponentValue({
            code: currentNode,
            action: 'back'
        });
    }
}

function handleReset() {
    navigationStack = ['TR'];
    currentNode = 'TR';
    updateVisualization();

    // Notify Python
    if (window.Streamlit) {
        window.Streamlit.setComponentValue({
            code: 'TR',
            action: 'reset'
        });
    }
}

function updateBreadcrumb() {
    const path = navigationStack.map(code => {
        const node = hierarchyData[code];
        return node ? node.label : code;
    }).join(' → ');
    d3.select('#breadcrumb-path').text(path);
}

function updateButtons() {
    d3.select('#back-btn').property('disabled', navigationStack.length <= 1);
    d3.select('#reset-btn').property('disabled', currentNode === 'TR');
}

function showLeafMessage(node) {
    g.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .style('fill', '#10b981')
        .style('font-size', '20px')
        .text(node.label + ' - Feuille terminale');
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(Math.abs(amount));
}

function truncate(text, maxWidth) {
    if (!text) return '';
    const maxChars = Math.floor(maxWidth / 8);
    return text.length > maxChars ? text.substring(0, maxChars - 3) + '...' : text;
}
