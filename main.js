// 사진변환.py와 같은 규칙: 가운데 기준 1080x1080 정사각형 + 오른쪽 아래 반투명 라벨 로고
const SIZE = 1080;
const LOGO_RATIO = 0.15;
const MARGIN = 40;
const PADDING = 14;
const RADIUS = 14;
const LABEL_ALPHA = 130 / 255;
const LOGO_URL = "자료/로고.png";

const fileInput = document.getElementById("files");
const drop = document.getElementById("drop");
const resultCard = document.getElementById("resultCard");
const grid = document.getElementById("grid");
const logoNote = document.getElementById("logoNote");
const zipBtn = document.getElementById("zipAll");
const clearBtn = document.getElementById("clear");

let logoLabel = null;      // 로고가 들어간 라벨 (캔버스)
let logoReady = null;      // 로고 준비 약속
let results = [];          // { blob, name, url }

function today() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("이미지를 열 수 없어요"));
    img.src = src;
  });
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

async function prepareLogo() {
  try {
    const logo = await loadImage(LOGO_URL);
    const w = Math.round(SIZE * LOGO_RATIO);
    const h = Math.max(1, Math.round((logo.naturalHeight * w) / logo.naturalWidth));
    const label = document.createElement("canvas");
    label.width = w + PADDING * 2;
    label.height = h + PADDING * 2;
    const ctx = label.getContext("2d");
    ctx.imageSmoothingQuality = "high";
    ctx.fillStyle = `rgba(255,255,255,${LABEL_ALPHA})`;
    roundRect(ctx, 0, 0, label.width, label.height, RADIUS);
    ctx.fill();
    ctx.drawImage(logo, PADDING, PADDING, w, h);
    logoLabel = label;
  } catch (e) {
    logoLabel = null;
  }
  logoNote.hidden = logoLabel !== null;
}

async function makePhoto(file) {
  const url = URL.createObjectURL(file);
  try {
    const img = await loadImage(url);
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = SIZE;
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingQuality = "high";
    ctx.fillStyle = "#fff"; // 투명한 png는 흰색 바탕
    ctx.fillRect(0, 0, SIZE, SIZE);
    // 가운데 기준으로 꽉 채우기 (늘리지 않고 비율 유지)
    const scale = Math.max(SIZE / img.naturalWidth, SIZE / img.naturalHeight);
    const w = img.naturalWidth * scale;
    const h = img.naturalHeight * scale;
    ctx.drawImage(img, (SIZE - w) / 2, (SIZE - h) / 2, w, h);
    if (logoLabel) {
      ctx.drawImage(logoLabel, SIZE - MARGIN - logoLabel.width, SIZE - MARGIN - logoLabel.height);
    }
    return await new Promise((resolve, reject) =>
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("저장 실패"))), "image/jpeg", 0.95)
    );
  } finally {
    URL.revokeObjectURL(url);
  }
}

function clearResults() {
  results.forEach((r) => URL.revokeObjectURL(r.url));
  results = [];
  grid.innerHTML = "";
  resultCard.hidden = true;
  fileInput.value = "";
}

async function handleFiles(fileList) {
  const files = [...fileList].filter((f) => /^image\/(jpeg|png)$/.test(f.type));
  if (!files.length) {
    alert("jpg 또는 png 사진을 골라 주세요.");
    return;
  }
  await logoReady;
  resultCard.hidden = false;
  zipBtn.disabled = true;

  const date = today();
  for (const file of files) {
    const n = String(results.length + 1).padStart(2, "0");
    const name = `${date}_${n}.jpg`;
    try {
      const blob = await makePhoto(file);
      const url = URL.createObjectURL(blob);
      results.push({ blob, name, url });
      const item = document.createElement("figure");
      item.className = "shot";
      item.style.margin = "0";
      const img = document.createElement("img");
      img.src = url;
      img.alt = `${name} 미리보기`;
      const bar = document.createElement("div");
      bar.className = "bar";
      const label = document.createElement("span");
      label.textContent = name;
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.textContent = "받기";
      bar.append(label, a);
      item.append(img, bar);
      grid.append(item);
    } catch (e) {
      const msg = document.createElement("p");
      msg.className = "note";
      msg.textContent = `${file.name}: 이 사진은 열 수 없었어요.`;
      grid.append(msg);
    }
  }
  zipBtn.disabled = results.length === 0;
}

async function downloadZip() {
  if (!results.length) return;
  zipBtn.disabled = true;
  const original = zipBtn.textContent;
  zipBtn.textContent = "묶는 중...";
  try {
    if (typeof JSZip === "undefined") throw new Error("zip 도구를 불러오지 못했어요");
    const zip = new JSZip();
    results.forEach((r) => zip.file(r.name, r.blob));
    const blob = await zip.generateAsync({ type: "blob" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${today()}_홍보사진.zip`;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (e) {
    alert("한 번에 받기가 안 돼요. 사진마다 '받기' 버튼을 눌러 주세요.");
  } finally {
    zipBtn.textContent = original;
    zipBtn.disabled = false;
  }
}

// ---- 문구 영역 ----
function makeBox(labelText, text, rows) {
  const box = document.createElement("div");
  box.className = "box";
  const label = document.createElement("label");
  label.textContent = labelText;
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.rows = rows;
  ta.setAttribute("aria-label", labelText);
  const row = document.createElement("div");
  row.className = "row";
  const count = document.createElement("span");
  count.className = "count";
  const btn = document.createElement("button");
  btn.type = "button";
  btn.textContent = "복사";
  const refresh = () => (count.textContent = `${ta.value.length}자`);
  ta.addEventListener("input", refresh);
  refresh();
  btn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(ta.value);
    } catch (e) {
      ta.select();
      document.execCommand("copy");
    }
    btn.textContent = "복사됐어요";
    setTimeout(() => (btn.textContent = "복사"), 1500);
  });
  row.append(count, btn);
  box.append(label, ta, row);
  return box;
}

function makeGroup(title, sub, boxes) {
  const g = document.createElement("div");
  g.className = "group";
  const h = document.createElement("h3");
  h.textContent = title;
  if (sub) {
    const s = document.createElement("small");
    s.textContent = sub;
    h.append(s);
  }
  g.append(h, ...boxes);
  return g;
}

function renderCopy() {
  const area = document.getElementById("copyArea");
  const rowsFor = (t) => Math.max(3, t.split("\n").length + 1);

  area.append(
    makeGroup(
      "인스타그램",
      "3가지 중에 골라 쓰세요",
      [
        ...COPY.insta.map((c) => makeBox(c.name, c.text, rowsFor(c.text))),
        makeBox("해시태그 10개", COPY.hashtags, 3),
      ]
    ),
    makeGroup("네이버 블로그", "", [
      makeBox("제목", COPY.blogTitle, 2),
      makeBox("본문", COPY.blogBody, 18),
      makeBox("해시태그", COPY.hashtags, 3),
    ]),
    makeGroup("카카오톡 단골 공지", "3줄", [makeBox("공지", COPY.kakao, 4)])
  );
}

// ---- 연결 ----
logoReady = prepareLogo();
renderCopy();

fileInput.addEventListener("change", () => handleFiles(fileInput.files));
["dragenter", "dragover"].forEach((ev) =>
  drop.addEventListener(ev, (e) => {
    e.preventDefault();
    drop.classList.add("over");
  })
);
["dragleave", "drop"].forEach((ev) =>
  drop.addEventListener(ev, (e) => {
    e.preventDefault();
    drop.classList.remove("over");
  })
);
drop.addEventListener("drop", (e) => handleFiles(e.dataTransfer.files));
zipBtn.addEventListener("click", downloadZip);
clearBtn.addEventListener("click", clearResults);
