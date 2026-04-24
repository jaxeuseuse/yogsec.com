document.querySelector('.hero-btn').addEventListener('click', function(e) {
    e.preventDefault(); // Prevent the default anchor behavior
    const targetId = this.getAttribute('href'); // Get the target ID from the link
    const targetElement = document.querySelector(targetId); // Select the target element

    // Scroll to the target element
    targetElement.scrollIntoView({
        behavior: 'smooth', // This makes the scroll smooth
        block: 'start' // Align to the top of the section
    });
});
function adjustHeaderBackground() {
    const header = document.querySelector('.header');
    if (!header) return;
    const imgEl = header.querySelector('.header-bg');
    if (imgEl) {
        // ensure the decorative image is set (use absolute path)
        imgEl.src = '/static/images/banner.png';
    }
}

window.addEventListener('resize', adjustHeaderBackground);
window.addEventListener('load', adjustHeaderBackground); // Adjust on initial load