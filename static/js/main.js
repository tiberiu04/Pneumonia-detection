document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("upload-form");
  const themeToggleHeader = document.getElementById("theme-toggle");
  const themeToggleSettings = document.getElementById("themeToggle");
  const hist = document.getElementById("history");

  if (form) {
    form.addEventListener("submit", () => {
      document.getElementById("loading-overlay").style.display = "flex";
    });
  }

  if (localStorage.getItem("theme") === "dark") {
    enableDarkMode();
  }

  if (themeToggleHeader) {
    themeToggleHeader.addEventListener("click", toggleTheme);
  }

  if (themeToggleSettings) {
    themeToggleSettings.addEventListener("change", toggleTheme);
  }

  if (hist) {
    const saved = JSON.parse(localStorage.getItem('history') || '[]');
    saved.forEach(text => {
      const li = document.createElement('li');
      li.textContent = text;
      li.classList.add('list-group-item');
      hist.appendChild(li);
    });
  }

  const resultDiv = document.querySelector('.alert-info');
  if (resultDiv) {
    const text = resultDiv.textContent.trim();
    const li = document.createElement('li');
    li.textContent = text;
    li.classList.add('list-group-item');
    hist.appendChild(li);

    const saved = JSON.parse(localStorage.getItem('history') || '[]');
    saved.push(text);
    localStorage.setItem('history', JSON.stringify(saved));
  }

  const ctx = document.getElementById('historyChart')?.getContext('2d');
  if (ctx) {
    const labels = Array.from({length: 20}, (_, i) => `Prediction ${i+1}`);
    const data = labels.map(() => Math.random() * 0.4 + 0.6);

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(79,172,254,0.5)');
    gradient.addColorStop(1, 'rgba(0,242,254,0.1)');

    new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Pneumonia Confidence',
          data,
          fill: true,
          backgroundColor: gradient,
          borderColor: '#4facfe',
          pointBackgroundColor: '#00f2fe',
          pointRadius: 4,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        animation: { duration: 2000, easing: 'easeOutBounce' },
        scales: { y: { beginAtZero: true, max: 1 } }
      }
    });
  }

  function enableDarkMode() {
    document.body.classList.add("dark-mode");
    localStorage.setItem("theme", "dark");
  }

  function disableDarkMode() {
    document.body.classList.remove("dark-mode");
    localStorage.setItem("theme", "light");
  }

  function toggleTheme() {
    if (document.body.classList.contains("dark-mode")) {
      disableDarkMode();
    } else {
      enableDarkMode();
    }
  }
});
