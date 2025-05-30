document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {  // Solo para usuarios autenticados
        const themeIcon = themeToggle.querySelector('i');
        const themeCss = document.getElementById('theme-css');
        
        // Cargar el tema guardado o usar light por defecto
        const savedTheme = localStorage.getItem('theme') || 'light';
        applyTheme(savedTheme);

        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            localStorage.setItem('theme', newTheme);
        });

        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            if (theme === 'dark') {
                themeCss.href = 'https://bootswatch.com/5/darkly/bootstrap.min.css';
                themeIcon.className = 'bi bi-moon-fill';
                document.body.classList.remove('light-theme');
                document.body.classList.add('dark-theme');
            } else {
                themeCss.href = 'https://bootswatch.com/5/flatly/bootstrap.min.css';
                themeIcon.className = 'bi bi-sun-fill';
                document.body.classList.remove('dark-theme');
                document.body.classList.add('light-theme');
            }
        }
    } else {
        // Si no hay botón (usuario no autenticado), forzar tema claro
        document.documentElement.setAttribute('data-theme', 'light');
        document.body.classList.add('light-theme');
    }
});
