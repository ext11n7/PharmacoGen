import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';

const canvas = document.querySelector('#heroCanvas');
if (!canvas) throw new Error('Hero canvas is missing');

const visual = canvas.closest('.hero-visual');
const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(34, 1, .1, 100);
camera.position.set(0, 0, 4.4);

const group = new THREE.Group();
scene.add(group);

const count = 760;
const positions = new Float32Array(count * 3);
const seeds = new Float32Array(count * 4);
for (let index = 0; index < count; index += 1) {
  seeds[index * 4] = Math.random();
  seeds[index * 4 + 1] = Math.random();
  seeds[index * 4 + 2] = Math.random();
  seeds[index * 4 + 3] = Math.random();
}

const particlesGeometry = new THREE.BufferGeometry();
particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
const particleMaterial = new THREE.PointsMaterial({ size: .025, transparent: true, opacity: .78, depthWrite: false, blending: THREE.AdditiveBlending });
const particles = new THREE.Points(particlesGeometry, particleMaterial);
group.add(particles);

const core = new THREE.Mesh(
  new THREE.IcosahedronGeometry(.82, 2),
  new THREE.MeshBasicMaterial({ wireframe: true, transparent: true, opacity: .18 })
);
group.add(core);

const rings = [
  new THREE.Mesh(new THREE.TorusGeometry(1.12, .006, 8, 96), new THREE.MeshBasicMaterial({ transparent: true, opacity: .42 })),
  new THREE.Mesh(new THREE.TorusGeometry(1.35, .004, 8, 96), new THREE.MeshBasicMaterial({ transparent: true, opacity: .24 })),
  new THREE.Mesh(new THREE.TorusGeometry(.58, .004, 8, 96), new THREE.MeshBasicMaterial({ transparent: true, opacity: .28 }))
];
rings[0].rotation.set(.8, .15, .3);
rings[1].rotation.set(-.2, .9, -.45);
rings[2].rotation.set(1.1, -.6, .1);
rings.forEach((ring) => group.add(ring));

const pointer = { x: 0, y: 0, tx: 0, ty: 0 };
const clock = new THREE.Clock();

function isLightTheme() {
  return document.body.classList.contains('light');
}

function updatePalette() {
  const color = isLightTheme() ? 0x09090b : 0xfafafa;
  particleMaterial.color.setHex(color);
  core.material.color.setHex(color);
  rings.forEach((ring) => ring.material.color.setHex(color));
}

function resize() {
  const width = visual.clientWidth;
  const height = visual.clientHeight;
  renderer.setSize(width, height, false);
  camera.aspect = width / Math.max(height, 1);
  camera.updateProjectionMatrix();
}

function animate() {
  const elapsed = clock.getElapsedTime();
  const position = particlesGeometry.attributes.position.array;
  const morph = (Math.sin(elapsed * .68) + 1) * .5;

  for (let index = 0; index < count; index += 1) {
    const seed = index * 4;
    const theta = seeds[seed] * Math.PI * 2 + elapsed * .08;
    const phi = Math.acos(2 * seeds[seed + 1] - 1);
    const pulse = 1 + Math.sin(elapsed * 1.25 + seeds[seed + 2] * 9) * .08;
    const radius = (1.02 + seeds[seed + 3] * .24) * pulse;
    const sphereX = Math.sin(phi) * Math.cos(theta) * radius;
    const sphereY = Math.cos(phi) * radius;
    const sphereZ = Math.sin(phi) * Math.sin(theta) * radius;
    const wave = theta * 2.4 + seeds[seed + 2] * 3;
    const waveRadius = .78 + Math.sin(wave * 2 + elapsed) * .22;
    const waveX = Math.cos(wave) * waveRadius;
    const waveY = Math.sin(wave * 1.7) * .82;
    const waveZ = Math.sin(wave) * waveRadius;
    position[index * 3] = THREE.MathUtils.lerp(sphereX, waveX, morph * .36);
    position[index * 3 + 1] = THREE.MathUtils.lerp(sphereY, waveY, morph * .36);
    position[index * 3 + 2] = THREE.MathUtils.lerp(sphereZ, waveZ, morph * .36);
  }
  particlesGeometry.attributes.position.needsUpdate = true;
  pointer.x += (pointer.tx - pointer.x) * .035;
  pointer.y += (pointer.ty - pointer.y) * .035;
  group.rotation.y = elapsed * .11 + pointer.x * .24;
  group.rotation.x = Math.sin(elapsed * .23) * .08 + pointer.y * .14;
  core.rotation.y = -elapsed * .17;
  core.rotation.x = elapsed * .09;
  rings[0].rotation.z += .0025;
  rings[1].rotation.x -= .0017;
  rings[2].rotation.y += .0032;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

visual.addEventListener('pointermove', (event) => {
  const rect = visual.getBoundingClientRect();
  pointer.tx = ((event.clientX - rect.left) / rect.width - .5) * 2;
  pointer.ty = ((event.clientY - rect.top) / rect.height - .5) * -2;
});
visual.addEventListener('pointerleave', () => { pointer.tx = 0; pointer.ty = 0; });
new ResizeObserver(resize).observe(visual);
new MutationObserver(updatePalette).observe(document.body, { attributes: true, attributeFilter: ['class'] });
updatePalette();
resize();
animate();
