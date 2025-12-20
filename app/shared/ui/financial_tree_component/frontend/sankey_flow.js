/**
 * D3.js Sankey Flow Visualization - Draggable Transaction Lines
 * 
 * Features:
 * - Fixed node rectangles positioned in columns by level
 * - Curved lines representing individual transactions
 * - Line width proportional to transaction amount
 * - Drag lines to change transaction category
 */

// Global state
let nodesData = [];
let transactionsData = [];
let svg = null;
let nodeElements = null;
let linkElements = null;

// Constants - Optimized for mental map view
const NODE_WIDTH = 120;
const NODE_HEIGHT = 55;  // Slightly larger for readability in compact view
const MARGIN = { top: 40, right: 30, bottom: 40, left: 30 };

// Colors
const REVENUE_COLOR = '#10b981'; // Green
const EXPENSE_COLOR = '#ef4444'; // Red
const NEUTRAL_COLOR = '#64748b'; // Gray
const DRAG_COLOR = '#f59e0b'; // Orange

// Wait for Streamlit
function initSankeyFlow() {
    if (typeof window.Streamlit === 'undefined') {
        console.log('[SANKEY_FLOW] Waiting for Streamlit...');
        setTimeout(initSankeyFlow, 100);
        return;
    }

    console.log('[SANKEY_FLOW] Streamlit ready!');
    const Streamlit = window.Streamlit;

    function onRenderEvent(event) {
        const data = event.detail;

        if (!data || !data.args) {
            console.error('[SANKEY_FLOW] No data from Python');
            return;
        }

        console.log('[SANKEY_FLOW] Received data:', data.args);

        nodesData = data.args.nodes || [];
        transactionsData = data.args.transactions || [];
        const height = data.args.height || 2500;  // Compact mental map height

        if (nodesData.length === 0) {
            console.warn('[SANKEY_FLOW] No nodes to display');
            return;
        }

        renderSankeyFlow(nodesData, transactionsData, height);
    }

    function renderSankeyFlow(nodes, transactions, containerHeight) {
        // Clear previous
        d3.select('#tree-container').selectAll('*').remove();

        const width = window.innerWidth || 1200;
        const height = containerHeight - MARGIN.top - MARGIN.bottom;
        const innerWidth = width - MARGIN.left - MARGIN.right;

        // Create SVG
        svg = d3.select('#tree-container')
            .append('svg')
            .attr('width', width)
            .attr('height', containerHeight)
            .style('background', 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)')
            .append('g')
            .attr('transform', `translate(${MARGIN.left}, ${MARGIN.top})`);

        // Calculate layout
        let layout = calculateLayout(nodes, innerWidth, height);

        // Calculate anchor points for bundling
        layout = calculateLinkAnchors(layout, transactions);

        // Draw links (transaction flows) FIRST (so they're behind nodes)
        drawTransactionLinks(layout, transactions);

        // Draw nodes (categories)
        drawNodes(layout);

        console.log(`[SANKEY_FLOW] Rendered ${nodes.length} nodes and ${transactions.length} transaction links`);

        // Set frame height AFTER rendering is complete
        Streamlit.setFrameHeight(containerHeight + 100);
    }

    function calculateLayout(nodes, width, height) {
        // Group nodes by level
        const nodesByLevel = d3.group(nodes, d => d.level);
        const maxLevel = d3.max(nodes, d => d.level);

        // Calculate column positions (X)
        const columnWidth = width / (maxLevel + 1);

        // Position each node
        const layout = {};

        nodesByLevel.forEach((nodesInLevel, level) => {
            const x = level * columnWidth + columnWidth / 2;

            // SORT nodes by type within each level (revenus first, then dépenses)
            // This prevents green and red rectangles from mixing
            const sortedNodes = [...nodesInLevel].sort((a, b) => {
                if (a.type === 'revenu' && b.type === 'dépense') return -1;
                if (a.type === 'dépense' && b.type === 'revenu') return 1;
                // If same type or both neutral, sort by label
                return (a.label || '').localeCompare(b.label || '');
            });

            // Reduce vertical spacing multiplier to fit more nodes
            const spacing = (height / (sortedNodes.length + 1)) * 1.2;  // Reduced from 1.8 to 1.2

            sortedNodes.forEach((node, index) => {
                layout[node.id] = {
                    ...node,
                    x: x,
                    y: (index + 1) * spacing,
                    // Track incoming and outgoing links for bundling
                    incomingLinks: [],
                    outgoingLinks: []
                };
            });
        });

        return layout;
    }

    function calculateLinkAnchors(layout, transactions) {
        // Count connections for each node
        transactions.forEach(tx => {
            const path = tx.path;
            if (!path || path.length < 2) return;

            for (let i = 0; i < path.length - 1; i++) {
                const sourceId = path[i];
                const targetId = path[i + 1];

                if (layout[sourceId] && layout[targetId]) {
                    layout[sourceId].outgoingLinks.push(tx);
                    layout[targetId].incomingLinks.push(tx);
                }
            }
        });

        // Calculate anchor points for each node
        Object.values(layout).forEach(node => {
            const nodeHeight = NODE_HEIGHT;
            // Use nodeHeight directly - don't multiply to avoid overflow
            const anchorSpacing = nodeHeight * 0.8;  // Stay well within bounds

            // SORT outgoing links by type (revenus first, then dépenses)
            // This prevents green and red lines from mixing
            node.outgoingLinks.sort((a, b) => {
                if (a.type === 'revenu' && b.type === 'dépense') return -1;
                if (a.type === 'dépense' && b.type === 'revenu') return 1;
                return 0;
            });

            // Distribute outgoing connections along right edge within bounds
            const outCount = node.outgoingLinks.length;
            node.outgoingAnchors = {};
            node.outgoingLinks.forEach((tx, i) => {
                const offset = (i + 1) * anchorSpacing / (outCount + 1) - anchorSpacing / 2;
                node.outgoingAnchors[tx.id] = { x: NODE_WIDTH / 2, y: offset };
            });

            // SORT incoming links by type (revenus first, then dépenses)
            node.incomingLinks.sort((a, b) => {
                if (a.type === 'revenu' && b.type === 'dépense') return -1;
                if (a.type === 'dépense' && b.type === 'revenu') return 1;
                return 0;
            });

            // Distribute incoming connections along left edge within bounds
            const inCount = node.incomingLinks.length;
            node.incomingAnchors = {};
            node.incomingLinks.forEach((tx, i) => {
                const offset = (i + 1) * anchorSpacing / (inCount + 1) - anchorSpacing / 2;
                node.incomingAnchors[tx.id] = { x: -NODE_WIDTH / 2, y: offset };
            });
        });

        return layout;
    }

    function drawNodes(layout) {
        const layoutArray = Object.values(layout);

        nodeElements = svg.selectAll('.node')
            .data(layoutArray)
            .enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.x}, ${d.y})`);

        // Node rectangles
        nodeElements.append('rect')
            .attr('x', -NODE_WIDTH / 2)
            .attr('y', -NODE_HEIGHT / 2)
            .attr('width', NODE_WIDTH)
            .attr('height', NODE_HEIGHT)
            .attr('rx', 8)
            .attr('fill', d => getNodeColor(d))
            .attr('stroke', '#cbd5e1')
            .attr('stroke-width', 2)
            .style('filter', 'drop-shadow(0 4px 6px rgba(0,0,0,0.3))');

        // Node labels
        nodeElements.append('text')
            .attr('dy', 0)
            .attr('text-anchor', 'middle')
            .style('font-size', '13px')
            .style('font-weight', 'bold')
            .style('fill', '#ffffff')
            .style('pointer-events', 'none')
            .text(d => {
                const label = d.label || d.id;
                return label.length > 12 ? label.substring(0, 12) + '...' : label;
            });

        // Node amounts
        nodeElements.append('text')
            .attr('dy', 15)
            .attr('text-anchor', 'middle')
            .style('font-size', '11px')
            .style('fill', '#22d3ee')
            .style('font-weight', 'bold')
            .style('pointer-events', 'none')
            .text(d => {
                const amount = d.total || 0;
                return `${Math.abs(amount).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} €`;
            });
    }

    function drawTransactionLinks(layout, transactions) {
        // Prepare link data
        const links = [];

        transactions.forEach(tx => {
            const path = tx.path;
            if (!path || path.length < 2) return;

            // Create links for each segment of the path
            for (let i = 0; i < path.length - 1; i++) {
                const sourceId = path[i];
                const targetId = path[i + 1];

                const source = layout[sourceId];
                const target = layout[targetId];

                if (source && target) {
                    links.push({
                        source: source,
                        target: target,
                        transaction: tx,
                        amount: tx.amount,
                        type: tx.type
                    });
                }
            }
        });

        // FIXED WIDTH - all lines have the same size
        const LINK_WIDTH = 4;  // Épaisseur fixe des lignes
        const GRAB_WIDTH = 20; // Zone de grab fixe

        // Draw links with DOUBLE layer: invisible wide stroke for grabbing + visible stroke
        linkElements = svg.selectAll('.link-group')
            .data(links)
            .enter()
            .append('g')
            .attr('class', 'link-group');

        // Invisible wider stroke for easier grabbing
        linkElements.append('path')
            .attr('class', 'link-grab-area')
            .attr('d', d => createCurvePath(d.source, d.target, d.transaction))
            .attr('fill', 'none')
            .attr('stroke', 'transparent')
            .attr('stroke-width', GRAB_WIDTH)
            .style('cursor', 'grab');

        // Visible stroke - FIXED WIDTH
        const visibleLinks = linkElements.append('path')
            .attr('class', 'link-visible')
            .attr('d', d => createCurvePath(d.source, d.target, d.transaction))
            .attr('fill', 'none')
            .attr('stroke', d => d.type === 'revenu' ? REVENUE_COLOR : EXPENSE_COLOR)
            .attr('stroke-width', LINK_WIDTH)  // Largeur fixe
            .attr('opacity', 0.6)
            .style('pointer-events', 'none');  // Events handled by grab-area

        // Apply interactions to the GROUP
        linkElements
            .on('mouseenter', function (event, d) {
                // Highlight on hover
                d3.select(this).select('.link-visible')
                    .attr('opacity', 1)
                    .attr('stroke-width', LINK_WIDTH * 1.8)  // Un peu plus épais au hover
                    .attr('stroke', DRAG_COLOR)
                    .style('filter', 'drop-shadow(0 0 8px ' + DRAG_COLOR + ')');  // Glow effect

                // Show tooltip
                showTooltip(event, d.transaction);
            })
            .on('mouseleave', function (event, d) {
                d3.select(this).select('.link-visible')
                    .attr('opacity', 0.6)
                    .attr('stroke-width', LINK_WIDTH)
                    .attr('stroke', d.type === 'revenu' ? REVENUE_COLOR : EXPENSE_COLOR)
                    .style('filter', 'none');

                hideTooltip();
            })
            .call(d3.drag()
                .on('start', function (event, d) { dragLinkStarted.call(this, event, d); })
                .on('drag', function (event, d) { dragLinkDragging.call(this, event, d); })
                .on('end', function (event, d) { dragLinkEnded.call(this, event, d); })
            );

        console.log(`[SANKEY_FLOW] Drew ${links.length} transaction link segments`);
    }

    function createCurvePath(source, target, transaction) {
        // Get anchor points if available
        const sourceAnchor = source.outgoingAnchors && source.outgoingAnchors[transaction.id];
        const targetAnchor = target.incomingAnchors && target.incomingAnchors[transaction.id];

        // Calculate start and end points with anchors
        const startX = source.x + (sourceAnchor ? sourceAnchor.x : 0);
        const startY = source.y + (sourceAnchor ? sourceAnchor.y : 0);
        const endX = target.x + (targetAnchor ? targetAnchor.x : 0);
        const endY = target.y + (targetAnchor ? targetAnchor.y : 0);

        // Cubic Bezier curve with control points at 40% distance
        const controlDistance = (endX - startX) * 0.4;

        return `M${startX},${startY} 
                C${startX + controlDistance},${startY} 
                 ${endX - controlDistance},${endY} 
                 ${endX},${endY}`;
    }

    function dragLinkStarted(event, d) {
        const LINK_WIDTH = 4;

        d3.select(this).select('.link-visible')
            .attr('stroke', DRAG_COLOR)
            .attr('opacity', 1)
            .attr('stroke-width', LINK_WIDTH * 2)  // Deux fois plus épais pendant le drag
            .style('filter', 'drop-shadow(0 0 12px ' + DRAG_COLOR + ')');

        d3.select(this).select('.link-grab-area')
            .style('cursor', 'grabbing');

        console.log('[DRAG] Started dragging transaction:', d.transaction.id);
    }

    function dragLinkDragging(event, d) {
        const [mouseX, mouseY] = d3.pointer(event, svg.node());

        // Find closest node to current mouse position
        const closestNode = findClosestNode(mouseX, mouseY);

        // Clear any previous preview highlights
        svg.selectAll('.node rect').attr('stroke-width', 2).attr('stroke', '#cbd5e1');

        // Show preview of target node
        if (closestNode && closestNode.id !== d.source.id && closestNode.id !== d.target.id) {
            // Highlight the target node
            svg.selectAll('.node')
                .filter(node => node.id === closestNode.id)
                .select('rect')
                .attr('stroke', '#f59e0b')
                .attr('stroke-width', 4);

            // Show preview tooltip with new path
            showPreviewTooltip(event, d.transaction, closestNode);
        } else {
            hidePreviewTooltip();
        }
    }

    function showPreviewTooltip(event, transaction, targetNode) {
        let tooltip = d3.select('#preview-tooltip');
        if (tooltip.empty()) {
            tooltip = d3.select('body')
                .append('div')
                .attr('id', 'preview-tooltip')
                .style('position', 'absolute')
                .style('background', 'rgba(245, 158, 11, 0.95)')
                .style('color', '#fff')
                .style('padding', '8px 12px')
                .style('border-radius', '6px')
                .style('font-size', '12px')
                .style('pointer-events', 'none')
                .style('z-index', '10001')
                .style('font-weight', 'bold')
                .style('box-shadow', '0 4px 8px rgba(0,0,0,0.3)');
        }

        const newCategory = extractCategoryFromNode(targetNode);
        tooltip
            .html(`
                🎯 Nouveau chemin:<br/>
                <span style="font-size: 11px;">${newCategory.category}${newCategory.subcategory ? ' → ' + newCategory.subcategory : ''}</span>
            `)
            .style('left', (event.pageX + 15) + 'px')
            .style('top', (event.pageY + 20) + 'px')
            .style('opacity', 1);
    }

    function hidePreviewTooltip() {
        d3.select('#preview-tooltip').style('opacity', 0);
    }

    function dragLinkEnded(event, d) {
        const LINK_WIDTH = 4;
        const [mouseX, mouseY] = d3.pointer(event, svg.node());

        // Hide preview tooltip
        hidePreviewTooltip();

        // Reset all node highlights
        svg.selectAll('.node rect').attr('stroke-width', 2).attr('stroke', '#cbd5e1');

        // Find closest node to drop position
        const closestNode = findClosestNode(mouseX, mouseY);

        if (closestNode && closestNode.id !== d.source.id && closestNode.id !== d.target.id) {
            console.log('[DROP] Transaction', d.transaction.id, 'dropped on', closestNode.label);

            // Extract category info from node
            const newCategory = extractCategoryFromNode(closestNode);

            // Send update to Python
            Streamlit.setComponentValue({
                action: 'update_transaction',
                transaction_id: d.transaction.id,
                new_category: newCategory.category,
                new_subcategory: newCategory.subcategory
            });
        } else {
            // Reset visual
            d3.select(this).select('.link-visible')
                .attr('stroke', d.type === 'revenu' ? REVENUE_COLOR : EXPENSE_COLOR)
                .attr('opacity', 0.6)
                .attr('stroke-width', LINK_WIDTH)
                .style('filter', 'none');

            d3.select(this).select('.link-grab-area')
                .style('cursor', 'grab');
        }
    }

    function findClosestNode(mouseX, mouseY) {
        let closestNode = null;
        let minDist = Infinity;

        Object.values(nodeElements.data()).forEach(node => {
            const dist = Math.sqrt(
                Math.pow(node.x - mouseX, 2) + Math.pow(node.y - mouseY, 2)
            );

            if (dist < minDist && dist < 100) { // 100px threshold
                minDist = dist;
                closestNode = node;
            }
        });

        return closestNode;
    }

    function extractCategoryFromNode(node) {
        // Extract category and subcategory from node ID
        // Examples:
        // CAT_DEPENSES_ALIMENTATION => category: "Alimentation", subcategory: null
        // SUBCAT_DEPENSES_ALIMENTATION_SUPERMARCHE => category: "Alimentation", subcategory: "Supermarché"

        if (node.id.startsWith('SUBCAT_')) {
            // Format: SUBCAT_TYPE_CATEGORY_SUBCATEGORY
            const parts = node.id.split('_');
            if (parts.length >= 4) {
                const category = parts[2].charAt(0) + parts[2].slice(1).toLowerCase();
                const subcategory = parts.slice(3).join(' ');
                const subcatFormatted = subcategory.split('_').map(w =>
                    w.charAt(0) + w.slice(1).toLowerCase()
                ).join(' ');

                return {
                    category: category,
                    subcategory: subcatFormatted
                };
            }
        } else if (node.id.startsWith('CAT_')) {
            // Format: CAT_TYPE_CATEGORY
            const parts = node.id.split('_');
            if (parts.length >= 3) {
                const category = parts.slice(2).join(' ');
                const catFormatted = category.split('_').map(w =>
                    w.charAt(0) + w.slice(1).toLowerCase()
                ).join(' ');

                return {
                    category: catFormatted,
                    subcategory: null
                };
            }
        }

        return { category: node.label, subcategory: null };
    }

    function getNodeColor(node) {
        if (node.type === 'revenu') return REVENUE_COLOR;
        if (node.type === 'dépense') return EXPENSE_COLOR;
        return NEUTRAL_COLOR;
    }

    function showTooltip(event, transaction) {
        // Create tooltip if it doesn't exist
        let tooltip = d3.select('#sankey-tooltip');
        if (tooltip.empty()) {
            tooltip = d3.select('body')
                .append('div')
                .attr('id', 'sankey-tooltip')
                .style('position', 'absolute')
                .style('background', 'rgba(0, 0, 0, 0.95)')
                .style('color', '#fff')
                .style('padding', '12px 16px')
                .style('border-radius', '8px')
                .style('font-size', '13px')
                .style('pointer-events', 'none')
                .style('z-index', '10000')
                .style('box-shadow', '0 6px 12px rgba(0,0,0,0.4)')
                .style('border', '2px solid #f59e0b')
                .style('max-width', '350px');
        }

        // Build path display
        const pathLabels = transaction.path ? transaction.path.map(nodeId => {
            const node = nodesData.find(n => n.id === nodeId);
            return node ? node.label : nodeId;
        }) : [];

        const pathHTML = pathLabels.length > 0
            ? `<div style="font-size: 11px; color: #94a3b8; margin-top: 8px; padding-top: 8px; border-top: 1px solid #475569;">
                📍 <strong>Chemin actuel:</strong><br/>
                ${pathLabels.join(' → ')}
               </div>`
            : '';

        tooltip
            .html(`
                <div style="font-weight: bold; font-size: 14px; margin-bottom: 4px;">${transaction.description}</div>
                <div style="color: #22d3ee; font-size: 16px; font-weight: bold; margin: 6px 0;">${transaction.amount.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} €</div>
                <div style="font-size: 11px; color: #cbd5e1;">${transaction.date || ''}</div>
                ${pathHTML}
                <div style="font-size: 10px; color: #64748b; margin-top: 8px; font-style: italic;">💡 Glissez pour changer de catégorie</div>
            `)
            .style('left', (event.pageX + 15) + 'px')
            .style('top', (event.pageY - 30) + 'px')
            .style('opacity', 1);
    }

    function hideTooltip() {
        d3.select('#sankey-tooltip').style('opacity', 0);
    }

    // Register Streamlit events
    Streamlit.setComponentReady();
    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRenderEvent);
    console.log('[SANKEY_FLOW] Component ready with drag & drop transactions!');
}

// Start
initSankeyFlow();
