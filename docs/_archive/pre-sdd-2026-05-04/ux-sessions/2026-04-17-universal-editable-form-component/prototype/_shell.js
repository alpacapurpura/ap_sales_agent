// Shared helpers for all variants: sidebar mock, copilot panel, focus bar sim
window.renderShell = function ({ variantName, centerHtml }) {
  const shellHtml = `
  <div class="flex h-screen overflow-hidden bg-slate-50">
    <!-- LEFT: app sidebar mock -->
    <aside class="w-56 bg-slate-900 text-slate-100 flex flex-col shrink-0">
      <div class="p-4 border-b border-slate-800">
        <div class="text-xs text-slate-500 uppercase tracking-wide">Tenant</div>
        <div class="font-bold">Visionarias</div>
      </div>
      <nav class="flex-1 p-2 text-sm">
        <div class="mb-2 text-xs uppercase text-slate-500 px-2 pt-2">Studios</div>
        <a class="block px-3 py-1.5 rounded bg-purple-600/30 text-purple-200 font-medium">Brand</a>
        <a class="block px-3 py-1.5 rounded hover:bg-slate-800 text-slate-400">Offer</a>
        <a class="block px-3 py-1.5 rounded hover:bg-slate-800 text-slate-400">Growth</a>
        <a class="block px-3 py-1.5 rounded hover:bg-slate-800 text-slate-400">Sales</a>
        <a class="block px-3 py-1.5 rounded hover:bg-slate-800 text-slate-400">Connections</a>
      </nav>
      <div class="p-3 border-t border-slate-800 text-xs text-slate-500">
        <a href="index.html" class="hover:text-white">← Volver al índice</a>
      </div>
    </aside>

    <!-- MIDDLE: brand section (variant-specific) -->
    <main class="flex-1 overflow-hidden flex flex-col min-w-0">
      <header class="border-b bg-white px-6 py-3 flex items-center justify-between">
        <div>
          <div class="text-xs text-slate-500">Brand Studio › Esencia</div>
          <h1 class="font-bold text-slate-900">Identidad de marca</h1>
        </div>
        <div class="text-xs px-2 py-1 rounded bg-purple-50 text-purple-700 font-medium border border-purple-200">
          ${variantName}
        </div>
      </header>
      <div class="flex-1 overflow-auto">${centerHtml}</div>
    </main>

    <!-- RIGHT: copilot panel -->
    <aside class="w-80 bg-white border-l border-slate-200 flex flex-col shrink-0">
      <div id="focus-bar" class="flex items-center gap-2 border-b border-slate-200 bg-purple-50 px-3 py-2">
        <svg class="h-4 w-4 text-purple-600" fill="currentColor" viewBox="0 0 20 20"><path d="M4 3a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H4zm0 2h12v10H4V5z"/></svg>
        <span class="text-xs font-medium text-purple-800 min-w-0 truncate">
          Brand › <span id="fb-domain">Identidad</span> <span class="text-purple-400">›</span> <span id="fb-field" class="italic">Ningún campo</span>
        </span>
        <div class="ml-auto flex gap-0.5">
          <div class="h-1.5 w-1.5 rounded-full bg-green-500"></div>
          <div class="h-1.5 w-1.5 rounded-full bg-green-500"></div>
          <div class="h-1.5 w-1.5 rounded-full animate-pulse bg-purple-500"></div>
          <div class="h-1.5 w-1.5 rounded-full bg-slate-300"></div>
          <div class="h-1.5 w-1.5 rounded-full bg-slate-300"></div>
        </div>
      </div>

      <div class="flex-1 overflow-auto p-4 space-y-3 text-sm">
        <div class="bg-slate-100 rounded-lg p-3">
          <div class="text-xs text-slate-500 mb-1">Copilot</div>
          Hola 👋 Estoy viendo tu <b>Identidad de marca</b>. Contame de vos y lo voy llenando.
        </div>
        <div class="bg-purple-600 text-white rounded-lg p-3 ml-6">
          Mi misión es ayudar a creadores a vivir de su contenido
        </div>
        <div class="bg-slate-100 rounded-lg p-3">
          <div class="text-xs text-slate-500 mb-1">Copilot</div>
          Perfecto, actualizo <b>Misión</b>. <button onclick="simulateAiUpdate()" class="text-purple-600 underline">[ver cambio]</button>
        </div>
        <div class="bg-purple-50 border border-purple-200 text-purple-900 rounded-lg p-3 text-xs">
          💡 Click en un campo del centro → FocusBar arriba se actualiza. El copilot siempre sabe dónde estás.
        </div>
      </div>

      <div class="border-t p-3">
        <div class="flex gap-2">
          <input class="flex-1 rounded border border-slate-300 px-3 py-2 text-sm" placeholder="Decile algo al copilot…" />
          <button class="rounded bg-purple-600 text-white px-3 text-sm">→</button>
        </div>
      </div>
    </aside>
  </div>`;
  document.body.innerHTML = shellHtml;

  document.querySelectorAll('[data-field-id]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      const label = el.getAttribute('data-field-label') || el.getAttribute('data-field-id');
      const domain = el.getAttribute('data-field-domain') || 'Identidad';
      document.getElementById('fb-domain').textContent = domain;
      document.getElementById('fb-field').textContent = label;
      document.getElementById('fb-field').classList.remove('italic');
      document.querySelectorAll('[data-field-id]').forEach(f => f.classList.remove('ring-2','ring-purple-400','ring-offset-2'));
      el.classList.add('ring-2','ring-purple-400','ring-offset-2');
    });
  });
};

window.simulateAiUpdate = function() {
  const mision = document.querySelector('[data-field-id="mission"]');
  if (!mision) return;
  mision.classList.add('ring-2','ring-green-400','bg-green-50');
  const badge = document.createElement('span');
  badge.textContent = 'IA';
  badge.className = 'absolute -top-2 -left-2 rounded-full bg-purple-600 text-white text-[9px] px-1.5 py-0.5 font-bold shadow z-10';
  mision.style.position = 'relative';
  mision.appendChild(badge);
  setTimeout(() => {
    mision.classList.remove('ring-green-400','bg-green-50');
    badge.remove();
  }, 3000);
};
