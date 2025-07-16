document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("upload-form");
  if (form) {
    form.addEventListener("submit", () => {
      document.getElementById("loading-overlay").style.display = "flex";
    });
  }

  const themeToggleHeader = document.getElementById("theme-toggle");
  const themeToggleSettings = document.getElementById("themeToggle");

  if (localStorage.getItem("theme") === "dark") {
    enableDarkMode();
  } else {
    disableDarkMode();
  }
  syncToggles();

  if (themeToggleHeader) {
    themeToggleHeader.addEventListener("click", () => {
      toggleTheme();
    });
  }

  if (themeToggleSettings) {
    themeToggleSettings.addEventListener("change", () => {
      toggleTheme();
    });
  }

  function toggleTheme() {
    const isDark = document.body.classList.contains("dark-mode");
    if (isDark) {
      disableDarkMode();
      localStorage.setItem("theme", "light");
    } else {
      enableDarkMode();
      localStorage.setItem("theme", "dark");
    }
    syncToggles();
  }

  function enableDarkMode() {
    document.body.classList.add("dark-mode");
  }

  function disableDarkMode() {
    document.body.classList.remove("dark-mode");
  }

  function syncToggles() {
    const isDark = document.body.classList.contains("dark-mode");

    if (themeToggleHeader) {
      if (isDark) {
        themeToggleHeader.classList.add("btn-dark");
        themeToggleHeader.classList.remove("btn-light");
      } else {
        themeToggleHeader.classList.add("btn-light");
        themeToggleHeader.classList.remove("btn-dark");
      }
    }

    if (themeToggleSettings) {
      themeToggleSettings.checked = isDark;
    }
  }

  const hist = document.getElementById('history');
  if (!hist) return;

  const saved = JSON.parse(localStorage.getItem('history') || '[]');
  saved.forEach(text => {
    const li = document.createElement('li');
    li.textContent = text;
    li.classList.add('list-group-item');
    hist.appendChild(li);
  });

  const resultDiv = document.querySelector('.alert-info');
  if (resultDiv) {
    const text = resultDiv.textContent.trim();
    const li = document.createElement('li');
    li.textContent = text;
    li.classList.add('list-group-item');
    hist.appendChild(li);

    saved.push(text);
    localStorage.setItem('history', JSON.stringify(saved));
  }

  const ctx = document.getElementById('historyChart')?.getContext('2d');
  if (!ctx) return;

  const labels = saved.map((_, i) => `Prediction ${i + 1}`);
  const data = saved.map(x => parseFloat(x.match(/\(([^)]+)\)/)?.[1] || 0));

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Pneumonia Confidence',
        data: data,
        fill: true,
        borderColor: '#4facfe',
        backgroundColor: 'rgba(79,172,254,0.2)'
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true, max: 1 }
      }
    }
  });
});
