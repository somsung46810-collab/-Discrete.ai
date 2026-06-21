class CyGlobsGLRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d', { alpha: false });
    this.angle = 0;
    this.frame = 0;
    this.config = { prompt: '', style: 'Cinematic', mode: 'Wireframe', radius: 0.62 };
    this.resize();
    addEventListener('resize', () => this.resize());
    requestAnimationFrame((t) => this.loop(t));
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = Math.min(devicePixelRatio || 1, 2);
    this.canvas.width = Math.max(1, Math.round(rect.width * dpr));
    this.canvas.height = Math.max(1, Math.round(rect.height * dpr));
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.width = rect.width;
    this.height = rect.height;
  }

  seed(text) {
    let value = 2166136261;
    for (const char of text) {
      value ^= char.charCodeAt(0);
      value = Math.imul(value, 16777619);
    }
    return value >>> 0;
  }

  directivePacket(opcode, objectId, x, y, z) {
    const packet = new Uint8Array(8);
    packet[0] = (opcode & 0x0f) << 4;
    packet[1] = objectId & 0xff;
    const values = [x, y, z].map((v) => Math.max(-32768, Math.min(32767, Math.round(v * 256))));
    values.forEach((value, index) => {
      packet[2 + index * 2] = (value >> 8) & 0xff;
      packet[3 + index * 2] = value & 0xff;
    });
    return Array.from(packet, (byte) => byte.toString(16).padStart(2, '0')).join('');
  }

  generate({ prompt, style, mode }) {
    this.config = { prompt, style, mode, radius: 0.62 };
    this.angle += 0.45;
    return {
      packet: this.directivePacket(0x3, 7, this.angle, this.config.radius, 0),
      renderer: 'CyGlobsGL browser MVP renderer',
    };
  }

  rotate([x, y, z], ax, ay) {
    const cy = Math.cos(ay), sy = Math.sin(ay);
    const cx = Math.cos(ax), sx = Math.sin(ax);
    const x1 = x * cy - z * sy;
    const z1 = x * sy + z * cy;
    return [x1, y * cx - z1 * sx, y * sx + z1 * cx];
  }

  project(vertex) {
    const [x, y, z] = this.rotate(vertex, -0.34, this.angle);
    const depth = 4.2 + z;
    const scale = Math.min(this.width, this.height) * 0.56 / depth;
    return [this.width / 2 + x * scale, this.height / 2 + y * scale, depth];
  }

  palette() {
    const seed = this.seed(this.config.prompt + this.config.style);
    const hue = seed % 360;
    return {
      primary: `hsl(${hue} 92% 68%)`,
      secondary: `hsl(${(hue + 72) % 360} 90% 64%)`,
      dark: `hsl(${(hue + 24) % 360} 55% 8%)`,
    };
  }

  scene() {
    const r = this.config.radius;
    const vertices = [
      [-r, r, -r], [r, r, -r], [r, -r, -r], [-r, -r, -r],
      [-r, r, r], [r, r, r], [r, -r, r], [-r, -r, r],
      [0, -1.4 * r, 0], [0, 1.7 * r, 0],
    ];
    const edges = [
      [0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],
      [0,4],[1,5],[2,6],[3,7],[3,8],[2,8],[6,8],[7,8],
      [0,9],[1,9],[4,9],[5,9]
    ];
    return { vertices, edges };
  }

  drawBackground(colors) {
    const gradient = this.ctx.createRadialGradient(this.width * .5, this.height * .48, 0, this.width * .5, this.height * .5, this.width * .68);
    gradient.addColorStop(0, colors.secondary);
    gradient.addColorStop(.17, colors.primary.replace('68%', '28%'));
    gradient.addColorStop(.55, colors.dark);
    gradient.addColorStop(1, '#05060b');
    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(0, 0, this.width, this.height);

    this.ctx.strokeStyle = 'rgba(145,120,255,.16)';
    this.ctx.lineWidth = 1;
    const horizon = this.height * .66;
    for (let y = horizon; y < this.height; y += 28) {
      this.ctx.beginPath(); this.ctx.moveTo(0, y); this.ctx.lineTo(this.width, y); this.ctx.stroke();
    }
    for (let x = -this.width; x < this.width * 2; x += 48) {
      this.ctx.beginPath(); this.ctx.moveTo(this.width / 2, horizon); this.ctx.lineTo(x, this.height); this.ctx.stroke();
    }
  }

  drawObject(colors) {
    const { vertices, edges } = this.scene();
    const points = vertices.map((v) => this.project(v));
    const mode = this.config.mode;
    this.ctx.lineJoin = 'round';
    this.ctx.lineCap = 'round';

    if (mode === 'Triangles') {
      const faces = [[0,1,9],[1,5,9],[5,4,9],[4,0,9],[3,2,8],[2,6,8],[6,7,8],[7,3,8]];
      faces.forEach((face, index) => {
        const g = this.ctx.createLinearGradient(points[face[0]][0], points[face[0]][1], points[face[2]][0], points[face[2]][1]);
        g.addColorStop(0, index % 2 ? `${colors.primary}aa` : `${colors.secondary}99`);
        g.addColorStop(1, 'rgba(15,10,35,.25)');
        this.ctx.fillStyle = g;
        this.ctx.beginPath();
        face.forEach((idx, i) => i ? this.ctx.lineTo(points[idx][0], points[idx][1]) : this.ctx.moveTo(points[idx][0], points[idx][1]));
        this.ctx.closePath(); this.ctx.fill();
      });
    }

    this.ctx.shadowBlur = 16;
    this.ctx.shadowColor = colors.primary;
    this.ctx.strokeStyle = mode === 'Contingency' ? 'rgba(96,255,180,.92)' : colors.primary;
    this.ctx.lineWidth = 1.8;
    edges.forEach(([a,b], index) => {
      if (mode === 'Contingency' && index % 2) this.ctx.setLineDash([7,6]); else this.ctx.setLineDash([]);
      this.ctx.beginPath(); this.ctx.moveTo(points[a][0], points[a][1]); this.ctx.lineTo(points[b][0], points[b][1]); this.ctx.stroke();
    });
    this.ctx.setLineDash([]);
    this.ctx.shadowBlur = 0;

    points.forEach(([x,y], index) => {
      this.ctx.fillStyle = index > 7 ? '#fff' : colors.secondary;
      this.ctx.beginPath(); this.ctx.arc(x, y, index > 7 ? 3.4 : 2.1, 0, Math.PI * 2); this.ctx.fill();
    });
  }

  loop() {
    this.angle += 0.0035;
    const colors = this.palette();
    this.drawBackground(colors);
    this.drawObject(colors);
    this.frame += 1;
    requestAnimationFrame(() => this.loop());
  }

  download(filename = 'cyglobsgl-render.png') {
    const link = document.createElement('a');
    link.download = filename;
    link.href = this.canvas.toDataURL('image/png');
    link.click();
  }
}

window.CyGlobsGLRenderer = CyGlobsGLRenderer;
