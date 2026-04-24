function showSection(sectionId) {
    // Hide all sections
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('clargs-section').style.display = 'none';
    document.getElementById('settings-section').style.display = 'none';

    // Deactivate all links
    document.getElementById('dashboard-link').classList.remove('active');
    document.getElementById('clargs-link').classList.remove('active');
    document.getElementById('settings-link').classList.remove('active');

    // Show the selected section and activate its link
    document.getElementById(sectionId).style.display = 'block';
    document.getElementById(sectionId.replace('-section', '-link')).classList.add('active');
}
