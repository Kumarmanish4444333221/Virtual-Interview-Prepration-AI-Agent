/**
 * Auto-scroll functionality for Chainlit chat
 * Only scrolls when user clicks setup option buttons (company, role, experience, etc.)
 */

(function() {
    'use strict';
    
    /**
     * Find the main scrollable chat container
     */
    function findScrollContainer() {
        const containers = Array.from(document.querySelectorAll('div')).filter(el => {
            const style = window.getComputedStyle(el);
            return (style.overflowY === 'auto' || style.overflowY === 'scroll') && 
                   el.scrollHeight > el.clientHeight + 100;
        });
        
        let bestContainer = null;
        let maxDiff = 0;
        
        for (const container of containers) {
            const diff = container.scrollHeight - container.clientHeight;
            if (diff > maxDiff) {
                maxDiff = diff;
                bestContainer = container;
            }
        }
        
        return bestContainer;
    }
    
    /**
     * Scroll to the bottom of the chat container
     */
    function scrollToBottom() {
        const container = findScrollContainer();
        if (container) {
            container.scrollTo({
                top: container.scrollHeight,
                behavior: 'smooth'
            });
        }
    }
    
    /**
     * Check if button is a setup option button (company, role, experience, questions)
     */
    function isSetupOptionButton(button) {
        const buttonText = button.textContent || '';
        
        // Setup option patterns - these are the selection buttons during setup
        const setupPatterns = [
            // Company selection
            '🔍 Google', '📦 Amazon', '💻 Microsoft', '👥 Meta', '🍎 Apple', 
            '🎬 Netflix', '🚀 Startup', '🏢 Other',
            // Experience levels
            '🌱 Fresher', '📈 Junior', '💼 Mid-Level', '🎯 Senior', '👑 Lead',
            // Role categories
            '💻 Engineering', '📊 Data & AI', '🔧 Specialized', '👔 Management',
            // Specific roles (start with 💼)
            '💼 ',
            // Question count options
            '⚡ Quick', '📝 Standard', '📚 Thorough', '🎯 Comprehensive'
        ];
        
        return setupPatterns.some(pattern => buttonText.includes(pattern));
    }
    
    /**
     * Add click listeners to setup option buttons only
     */
    function setupActionButtonListeners() {
        document.addEventListener('click', (event) => {
            const target = event.target;
            const button = target.closest('button');
            
            if (button && isSetupOptionButton(button)) {
                // Only scroll for setup option buttons
                setTimeout(scrollToBottom, 200);
                setTimeout(scrollToBottom, 500);
            }
        }, true);
    }
    
    /**
     * Initialize
     */
    function init() {
        console.log('[AutoScroll] Initialized (setup options only)');
        setupActionButtonListeners();
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
