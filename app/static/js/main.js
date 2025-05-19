/**
 * General JavaScript for sitewide enhancements.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Example: Add an active class to the current navigation link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => link.pathname === currentPath ? link.classList.add('active') : link.classList.remove('active'));
});
