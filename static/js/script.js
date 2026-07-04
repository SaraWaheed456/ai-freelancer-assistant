document.addEventListener('DOMContentLoaded', () => {

  // Login form
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      window.location.href = 'dashboard.html';
    });
  }

  // Register form
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const password = document.getElementById('password').value;
      const confirmPassword = document.getElementById('confirmPassword').value;
      if (password !== confirmPassword) {
        alert("Passwords don't match. Please check and try again.");
        return;
      }
      window.location.href = 'dashboard.html';
    });
  }

  // Forgot password form
  const forgotForm = document.getElementById('forgotForm');
  if (forgotForm) {
    forgotForm.addEventListener('submit', (e) => {
      e.preventDefault();
      document.getElementById('infoBox').style.display = 'block';
      forgotForm.reset();
    });
  }

  // Apply saved theme on every page load
  const savedTheme = localStorage.getItem('theme') || 'dark';
  if (savedTheme === 'light') {
    document.body.classList.add('light-theme');
  }

});

// Toggle theme function
function toggleTheme(theme) {
  if (theme === 'light') {
    document.body.classList.add('light-theme');
    localStorage.setItem('theme', 'light');
  } else {
    document.body.classList.remove('light-theme');
    localStorage.setItem('theme', 'dark');
  }
}