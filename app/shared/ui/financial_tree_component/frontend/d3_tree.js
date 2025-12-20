/**
 * D3.js Interactive Financial Tree - Full Drag & Drop
 * 
 * Features:
 * - Drag rectangles to reorganize categories
 * - Drop on empty space to create new category
 * - Drop on trash zone to delete category
 * - Intelligent layout to avoid overlapping
 */

// Global state
let hierarchyData = null;
let svg = null;
let draggedNode = null;
let dropZone = null;

// Constants
const NODE_WIDTH = 140;
const NODE_HEIGHT = 50;
const VERTICAL_SPACING = 100;
const HORIZONTAL_SPACING = 20;

// Colors
const REVENUE_COLOR = '#10b981'; // Green
const EXPENSE_COLOR = '#ef4444'; // Red
const SELECTED_COLOR = '#9333ea'; // Purple
const DRAG_COLOR = '#f59e0b'; // Orange

// Wait for Streamlit
function initD3Tree() {
    if (typeof window.Streamlit === 'undefined') {
        console.log('[D3_TREE] Waiting for Streamlit...');
        setTimeout(initD3Tree, 100);
        return;
    }

    console.log('[D3_TREE] Streamlit ready!');
    const Streamlit = window.Streamlit;

    function onRenderEvent(event) {
        const data = event.detail;

        if (!data || !data.args) {
            console.error('[D3_TREE] No data from Python');
            return;
        }

        console.log('[D3_TREE] Received data:', data.args);

        hierarchyData = data.args.hierarchy;
        const height = data.args.height || 900;

        renderTree(hierarchyData, height);

        Streamlit.setFrameHeight(height + 100);
    }

    function renderTree(hierarchy, containerHeight) {
        // Clear previous
        d3.select('#tree-container').selectAll('*').remove();

        // Convert to D3 hierarchy
        const root = convertToD3Hierarchy(hierarchy);

        // Use tree layout with more spacing
        const width = window.innerWidth || 1200;
        const treeLayout = d3.tree()
            .size([width - 300, containerHeight - 250])
            .separation((a, b) => {
                // More separation for siblings
                return (a.parent === b.parent ? 1.5 : 2);
            });

        // Compute positions
        const treeData = treeLayout(root);

        // Create SVG
        svg = d3.select('#tree-container')
            .append('svg')
            .attr('width', width)
            .attr('height', containerHeight)
            .style('background', 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)')
            .append('g')
            .attr('transform', 'translate(150, 80)');

        // Add delete zone at bottom
        addDeleteZone(width, containerHeight);

        // Draw links (branches)
        const links = svg.selectAll('.link')
            .data(treeData.links())
            .enter()
            .append('path')
            .attr('class', 'link')
            .attr('d', d3.linkVertical()
                .x(d => d.x)
                .y(d => d.y)
            )
            .attr('fill', 'none')
            .attr('stroke', '#60a5fa')  // Brighter blue for better visibility
            .attr('stroke-width', 3)  // Thicker lines
            .attr('opacity', 0.8);  // More opaque

        console.log(`[D3_TREE] Drew ${treeData.links().length} links/branches`);

        // Draw nodes as draggable rectangles
        const nodes = svg.selectAll('.node')
            .data(treeData.descendants())
            .enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.x}, ${d.y})`)
            .call(d3.drag()
                .on('start', dragStarted)
                .on('drag', dragging)
                .on('end', dragEnded)
            )
            .on('dblclick', handleDoubleClick);

        // Node rectangles
        nodes.append('rect')
            .attr('x', -NODE_WIDTH / 2)
            .attr('y', -NODE_HEIGHT / 2)
            .attr('width', NODE_WIDTH)
            .attr('height', NODE_HEIGHT)
            .attr('rx', 8)
            .attr('fill', d => getNodeColor(d.data))
            .attr('stroke', '#cbd5e1')
            .attr('stroke-width', 2)
            .style('cursor', d => d.data.code === 'TR' ? 'default' : 'grab')
            .style('filter', 'drop-shadow(0 4px 6px rgba(0,0,0,0.3))')
            .on('mouseenter', function (event, d) {
                if (d.data.code !== 'TR') {
                    d3.select(this)
                        .attr('stroke', '#fbbf24')  // Yellow highlight
                        .attr('stroke-width', 4);
                }
            })
            .on('mouseleave', function (event, d) {
                if (d.data.code !== 'TR') {
                    d3.select(this)
                        .attr('stroke', '#cbd5e1')
                        .attr('stroke-width', 2);
                }
            });

        console.log(`[D3_TREE] Drew ${treeData.descendants().length} nodes/rectangles`);

        // Node emoji
        nodes.append('text')
            .attr('dy', -8)
            .attr('text-anchor', 'middle')
            .style('font-size', '20px')
            .style('pointer-events', 'none')
            .text(d => getCategoryEmoji(d.data.label));

        // Node label
        nodes.append('text')
            .attr('dy', 8)
            .attr('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('font-weight', 'bold')
            .style('fill', '#ffffff')
            .style('pointer-events', 'none')
            .text(d => {
                const label = d.data.label || d.data.code;
                return label.length > 15 ? label.substring(0, 15) + '...' : label;
            });

        // Node amount
        nodes.append('text')
            .attr('dy', 22)
            .attr('text-anchor', 'middle')
            .style('font-size', '11px')
            .style('fill', '#22d3ee')
            .style('font-weight', 'bold')
            .style('pointer-events', 'none')
            .text(d => {
                const amount = d.data.amount || d.data.total || 0;
                return `${Math.abs(amount).toLocaleString('fr-FR')} €`;
            });
    }

    function addDeleteZone(width, height) {
        dropZone = svg.append('g')
            .attr('class', 'delete-zone')
            .attr('transform', `translate(${width / 2 - 150}, ${height - 150})`);

        dropZone.append('rect')
            .attr('width', 200)
            .attr('height', 60)
            .attr('rx', 10)
            .attr('fill', '#dc2626')
            .attr('opacity', 0.3)
            .attr('stroke', '#ef4444')
            .attr('stroke-width', 3)
            .attr('stroke-dasharray', '10,5');

        dropZone.append('text')
            .attr('x', 100)
            .attr('y', 35)
            .attr('text-anchor', 'middle')
            .style('font-size', '16px')
            .style('fill', '#ffffff')
            .style('font-weight', 'bold')
            .style('pointer-events', 'none')
            .text('🗑️ Supprimer');
    }

    function dragStarted(event, d) {
        // Don't allow dragging root
        if (d.data.code === 'TR') return;

        draggedNode = d;
        d3.select(this).raise();

        // Change cursor
        d3.select(this).style('cursor', 'grabbing');

        // Highlight being dragged
        d3.select(this).select('rect')
            .attr('fill', DRAG_COLOR)
            .attr('stroke-width', 4);

        // Highlight delete zone
        dropZone.select('rect')
            .attr('opacity', 0.7)
            .attr('stroke-width', 5);

        console.log('[DRAG] Started:', d.data.label);
    }

    function dragging(event, d) {
        if (d.data.code === 'TR') return;

        // Move the node
        d3.select(this)
            .attr('transform', `translate(${event.x}, ${event.y})`);
    }

    function dragEnded(event, d) {
        if (d.data.code === 'TR') return;

        draggedNode = null;

        // Reset delete zone
        dropZone.select('rect')
            .attr('opacity', 0.3)
            .attr('stroke-width', 3);

        // Check if dropped on delete zone
        const dropX = event.x;
        const dropY = event.y;

        // Get delete zone bounds (rough check)
        const deleteZoneBounds = dropZone.node().getBBox();
        const transform = dropZone.attr('transform');
        const match = transform.match(/translate\(([^,]+),([^)]+)\)/);
        const deleteX = parseFloat(match[1]);
        const deleteY = parseFloat(match[2]);

        if (dropX >= deleteX && dropX <= deleteX + 200 &&
            dropY >= deleteY && dropY <= deleteY + 60) {
            // Dropped on delete zone!
            console.log('[DELETE] Category:', d.data.label);
            handleDeleteCategory(d.data.code, d.data.label);
            return;
        }

        // Otherwise, check if reparenting
        handleReparentCategory(d, event.x, event.y);
    }

    function handleDoubleClick(event, d) {
        // Double-click to add subcategory
        if (d.data.code === 'TR') return;

        console.log('[CREATE] Add subcategory to:', d.data.label);

        // Ask for subcategory name in JavaScript
        const subcatName = prompt(`Créer une sous-catégorie sous "${d.data.label}":\n\nNom de la sous-catégorie:`, '');

        if (subcatName && subcatName.trim() !== '') {
            // Send to Python with name
            Streamlit.setComponentValue({
                action: 'create_subcategory',
                parent_code: d.data.code,
                parent_label: d.data.label,
                subcategory_name: subcatName.trim()
            });
        }
    }

    function handleDeleteCategory(code, label) {
        // Confirm deletion
        if (confirm(`Supprimer "${label}" et toutes ses transactions ?`)) {
            Streamlit.setComponentValue({
                action: 'delete_category',
                code: code,
                label: label
            });
        } else {
            // Cancelled - re-render to reset position
            renderTree(hierarchyData, 900);
        }
    }

    function handleReparentCategory(node, newX, newY) {
        // Find closest node to drop position
        const allNodes = svg.selectAll('.node').data();
        let closestNode = null;
        let minDist = Infinity;

        allNodes.forEach(n => {
            if (n === node || n.data.code === 'TR') return;

            const dist = Math.sqrt(
                Math.pow(n.x - newX, 2) + Math.pow(n.y - newY, 2)
            );

            if (dist < minDist && dist < 150) {
                minDist = dist;
                closestNode = n;
            }
        });

        if (closestNode) {
            console.log('[REPARENT] Move', node.data.label, 'to', closestNode.data.label);

            Streamlit.setComponentValue({
                action: 'reparent_category',
                code: node.data.code,
                label: node.data.label,
                new_parent_code: closestNode.data.code,
                new_parent_label: closestNode.data.label
            });
        } else {
            // No valid drop target - reset position
            renderTree(hierarchyData, 900);
        }
    }

    function getNodeColor(data) {
        // Color based on transaction type
        if (data.label === 'Revenus' || data.label === 'Salaire') {
            return REVENUE_COLOR;
        } else if (data.label === 'Dépenses') {
            return EXPENSE_COLOR;
        }

        // Check if it's under revenus or dépenses
        if (data.color === REVENUE_COLOR || data.color === '#10b981') {
            return REVENUE_COLOR;
        } else if (data.color === EXPENSE_COLOR || data.color === '#ef4444') {
            return EXPENSE_COLOR;
        }

        // Default
        return '#64748b';
    }

    function getCategoryEmoji(label) {
        const emojiMap = {
            'Revenus': '💼',
            'Dépenses': '🛒',
            'Salaire': '💵',
            'Freelance': '🖥️',
            'Alimentation': '🍔',
            'Supermarché': '🛒',
            'Restaurant': '🍽️',
            'Transport': '🚗',
            'Logement': '🏠',
            'Santé': '⚕️',
            'Loisirs': '🎮',
            'Education': '📚',
            'Uca': '🎓'
        };

        return emojiMap[label] || '📁';
    }

    function convertToD3Hierarchy(flatHierarchy) {
        const buildNode = (code) => {
            if (!flatHierarchy[code]) return null;

            const node = flatHierarchy[code];
            const children = (node.children || [])
                .map(childCode => buildNode(childCode))
                .filter(child => child !== null);

            return {
                code: code,
                label: node.label,
                color: node.color,
                amount: node.amount || node.total,
                level: node.level,
                children: children.length > 0 ? children : undefined
            };
        };

        const treeData = buildNode('TR');
        return d3.hierarchy(treeData);
    }

    // Register Streamlit events
    Streamlit.setComponentReady();
    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRenderEvent);
    console.log('[D3_TREE] Component ready with drag & drop!');
}

// Start
initD3Tree();
