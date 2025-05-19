/**
 * Theme Manager
 *
 * Handles theme switching between light and dark modes
 * and persists the user's preference in localStorage.
 */

class ThemeManager {
    constructor() {
        this.themeKey = 'theme';
        this.darkThemeClass = 'dark-theme';
        this.defaultTheme = 'light';

        // Initialize theme on page load
        this.initTheme();

        // Listen for storage events (for multi-tab support)
        window.addEventListener('storage', (event) => {
            if (event.key === this.themeKey) {
                this.applyTheme(event.newValue);
            }
        });
    }

    /**
     * Initialize theme based on localStorage or system preference
     */
    initTheme() {
        // Check localStorage first
        const savedTheme = localStorage.getItem(this.themeKey);

        if (savedTheme) {
            this.applyTheme(savedTheme);
        } else {
            // Check system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const theme = prefersDark ? 'dark' : 'light';

            // Save and apply theme
            this.saveTheme(theme);
        }
    }

    /**
     * Apply theme to the document
     * @param {string} theme - 'light' or 'dark'
     */
    applyTheme(theme) {
        if (theme === 'dark') {
            document.body.classList.add(this.darkThemeClass);
        } else {
            document.body.classList.remove(this.darkThemeClass);
        }

        // Update any theme toggles on the page
        this.updateToggles(theme);
    }

    /**
     * Save theme preference to localStorage
     * @param {string} theme - 'light' or 'dark'
     */
    saveTheme(theme) {
        localStorage.setItem(this.themeKey, theme);
        this.applyTheme(theme);
    }

    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
        const currentTheme = localStorage.getItem(this.themeKey) || this.defaultTheme;
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.saveTheme(newTheme);
        return newTheme;
    }

    /**
     * Get current theme
     * @returns {string} - 'light' or 'dark'
     */
    getCurrentTheme() {
        return localStorage.getItem(this.themeKey) || this.defaultTheme;
    }

    /**
     * Update any theme toggles on the page
     * @param {string} theme - 'light' or 'dark'
     */
    updateToggles(theme) {
        // Update radio buttons if they exist
        const lightRadio = document.getElementById('lightTheme');
        const darkRadio = document.getElementById('darkTheme');

        if (lightRadio && darkRadio) {
            lightRadio.checked = theme === 'light';
            darkRadio.checked = theme === 'dark';
        }

        // Update theme preview if it exists
        const themePreview = document.getElementById('themePreview');
        if (themePreview) {
            themePreview.className = `theme-preview ${theme}`;
        }
    }
}

// Initialize theme manager
const themeManager = new ThemeManager();

// Make it globally available
window.themeManager = themeManager;

// Theme toggle is only available in the settings page
