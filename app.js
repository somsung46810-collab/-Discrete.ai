const gallery = [
  ['Celestial Passage','#59d6ff','#5530ae',330,20,25,135],['Chrome Bloom','#ff62c6','#331a50',245,65,22,40],['Desert Oracle','#ffc45c','#552842',390,55,30,150],['Azure Monument','#62e4ff','#17294b',280,40,22,180],['Glass Leviathan','#98ffea','#54339a',360,70,25,25],['Solar Garden','#ffef74','#c03b81',250,30,30,120],['Dream Circuit','#8b7cff','#122542',315,45,18,160],['Emerald Archive','#5dffc4','#16363c',370,63,35,20]
];

const grid = document.getElementById('galleryGrid');
gallery.forEach(([title,c1,c2,h,x,y,angle],i) => {
  const el = document.createElement('article');
  el.className = 'art-card';
  el.innerHTML = `<div class="art" style="--h:${h}px;--c1:${c1};--c2:${c2};--x:${x}%;--y:${y}%;--angle:${angle}deg"></div><div class="overlay"><h4>${title}</h4><span>by @discrete_creator_${i+1}</span></div>`;
  grid.appendChild(el);
});

const canvas = document.getElementById('cyglobsCanvas');
const renderer = new CyGlobsGLRenderer(canvas);
const prompt = document.getElementById('prompt');
const style = document.getElementById('style');
const mode = document.getElementById('mode');
const aspect = document.getElementById('aspect');
const toast = document.getElementById('toast');

async function callFramework(operation, payload = {}) {
  const response = await fetch('/rpc', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ protocol_version: '1.0', operation, payload })
  });
  if (!response.ok) throw new Error(`RPC request failed: ${response.status}`);
  const envelope = await response.json();
  if (envelope.status !== 'ok') throw new Error(envelope.error || 'CyGlobs framework error');
  return envelope.result;
}

function applyAspect() {
  const preview = document.querySelector('.preview-art');
  const ratio = aspect.value.split(' ')[0];
  preview.dataset.aspect = ratio;
  preview.style.aspectRatio = ratio === '16:9' ? '16 / 9' : ratio === '9:16' ? '9 / 16' : '1 / 1';
  renderer.resize();
}

async function renderArtwork() {
  const button = document.getElementById('generate');
  button.disabled = true;
  button.innerHTML = '<span>◌</span> Validating CyGlobs directives...';

  const localResult = renderer.generate({ prompt: prompt.value.trim(), style: style.value, mode: mode.value });
  let frameworkStatus = 'local fallback';

  try {
    const manifest = await callFramework('render_manifest', {
      prompt: prompt.value.trim(),
      style: style.value,
      mode: mode.value,
      aspect_ratio: aspect.value.split(' ')[0]
    });
    frameworkStatus = manifest.pipeline.join(' → ');
    toast.textContent = 'CyGlobs RPC validated; framebuffer rendered locally';
  } catch (error) {
    console.info('CyGlobs server unavailable; continuing with local renderer.', error);
    toast.textContent = 'Local CyGlobsGL render complete; RPC server offline';
  }

  document.getElementById('previewTitle').textContent = prompt.value.trim().split(/[,.]/)[0] || 'CyGlobsGL Creation';
  document.getElementById('previewMeta').textContent = `CyGlobsGL • ${mode.value} • radius 0.62`;
  document.getElementById('packetHex').textContent = `${localResult.packet} · ${frameworkStatus}`;
  toast.classList.add('show');

  setTimeout(() => {
    button.disabled = false;
    button.innerHTML = '<span>✦</span> Render with CyGlobsGL <kbd>Ctrl ↵</kbd>';
    toast.classList.remove('show');
  }, 1100);
}

document.querySelectorAll('[data-add]').forEach((button) => button.addEventListener('click', () => {
  prompt.value = `${prompt.value.trim().replace(/,+$/, '')}, ${button.dataset.add}`;
  prompt.focus();
}));

document.getElementById('generate').addEventListener('click', renderArtwork);
document.getElementById('downloadRender').addEventListener('click', () => renderer.download());
aspect.addEventListener('change', applyAspect);
mode.addEventListener('change', renderArtwork);
style.addEventListener('change', renderArtwork);
document.addEventListener('keydown', (event) => {
  if (event.ctrlKey && event.key === 'Enter') renderArtwork();
});

applyAspect();
renderArtwork();
