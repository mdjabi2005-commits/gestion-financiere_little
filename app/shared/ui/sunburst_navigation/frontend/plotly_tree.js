/**
 * Plotly Tree - Streamlit Custom Component
 * Multi-select with visual feedback
 */

// Global state for selections
let selectedCodes = new Set();
let lastResetCounter = 0;  // Track reset requests from Python

// Wait for Streamlit to be available
function initComponent() {
    if (typeof window.Streamlit === 'undefined') {
        console.log('[PLOTLY_TREE] Waiting for Streamlit...');
        setTimeout(initComponent, 100);
        return;
    }

    console.log('[PLOTLY_TREE] Streamlit found!');

    const Streamlit = window.Streamlit;

    function onRenderEvent(event) {
        const data = event.detail;

        if (!data || !data.args) {
            console.error('[PLOTLY_TREE] No data from Python');
            return;
        }

        console.log('[PLOTLY_TREE] Received data:', data.args);

        const hierarchy = data.args.hierarchy;
        const height = data.args.height || 600;
        const resetCounter = data.args.reset_counter || 0;

        // Check if reset was requested from Python
        if (resetCounter > lastResetCounter) {
            console.log('[PLOTLY_TREE] Reset requested! Clearing all selections');
            selectedCodes.clear();
            lastResetCounter = resetCounter;
        }

        renderPlotlyTree(hierarchy, height);

        Streamlit.setFrameHeight(height + 50);
    }

    function renderPlotlyTree(hierarchy, height) {
        console.log('[PLOTLY_TREE] Rendering tree...');

        // Build Plotly data
        const labels = [];
        const parents = [];
        const values = [];
        const colors = [];
        const codes = [];
        const ids = [];

        function addNode(code, parentId = '') {
            if (!hierarchy[code]) return;

            const node = hierarchy[code];
            labels.push(node.label || code);
            parents.push(parentId);
            values.push(Math.abs(node.amount || node.total || 1));

            // Color: purple if selected, original color otherwise
            const isSelected = selectedCodes.has(code);
            const color = isSelected ? '#9333ea' : (node.color || '#64748b');
            colors.push(color);

            codes.push(code);
            ids.push(code);

            if (node.children && node.children.length > 0) {
                node.children.forEach(childCode => addNode(childCode, code));
            }
        }

        addNode('TR');

        console.log('[PLOTLY_TREE] Selected codes:', Array.from(selectedCodes));

        // Create Plotly Sunburst
        const data = [{
            type: 'sunburst',
            labels: labels,
            parents: parents,
            values: values,
            ids: ids,
            marker: {
                colors: colors,
                line: {
                    width: 2,
                    color: '#0f172a'
                }
            },
            textfont: {
                size: 12,
                color: 'white',
                family: 'Arial, sans-serif'
            },
            hovertemplate: '<b>%{label}</b><br>Montant: %{value:.0f} €<br><extra></extra>',
            branchvalues: 'total',
            insidetextorientation: 'radial'
        }];

        const layout = {
            height: height,
            margin: { t: 30, l: 10, r: 10, b: 10 },
            paper_bgcolor: '#0f172a',
            plot_bgcolor: '#0f172a',
            font: { color: 'white', size: 12 }
        };

        // Render Plotly chart
        Plotly.newPlot('plotly-container', data, layout, { responsive: true });

        console.log('[PLOTLY_TREE] Plotly rendered successfully');

        // Detect clicks and toggle selection
        document.getElementById('plotly-container').on('plotly_click', function (eventData) {
            console.log('[PLOTLY_TREE] Click detected!', eventData);

            const pointIndex = eventData.points[0].pointNumber;
            const clickedCode = codes[pointIndex];
            const clickedLabel = labels[pointIndex];

            // Special case: clicking on root (TR / Univers Financier) = RESET ALL
            if (clickedCode === 'TR') {
                console.log('[PLOTLY_TREE] Clicked on root! Clearing all selections');
                selectedCodes.clear();

                // Re-render with cleared selections
                renderPlotlyTree(hierarchy, height);

                // Send empty array to Python
                Streamlit.setComponentValue({
                    codes: [],
                    action: 'reset'
                });

                console.log('[PLOTLY_TREE] All selections cleared!');
                return;
            }

            // Normal behavior: Toggle selection
            if (selectedCodes.has(clickedCode)) {
                selectedCodes.delete(clickedCode);
                console.log('[PLOTLY_TREE] Removed:', clickedCode);
            } else {
                selectedCodes.add(clickedCode);
                console.log('[PLOTLY_TREE] Added:', clickedCode);
            }

            // Re-render with new colors
            renderPlotlyTree(hierarchy, height);

            // Send to Python (array of selected codes)
            Streamlit.setComponentValue({
                codes: Array.from(selectedCodes),
                action: 'multi-select'
            });

            console.log('[PLOTLY_TREE] Selection sent to Python:', Array.from(selectedCodes));
        });
    }

    // Register Streamlit events
    Streamlit.setComponentReady();
    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRenderEvent);
    console.log('[PLOTLY_TREE] Component ready with multi-select!');
}

// Start initialization
initComponent();
