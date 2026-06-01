const root = document.getElementById("view-root");
const title = document.getElementById("page-title");
const subtitle = document.getElementById("page-subtitle");

const iconPaths = {
  home: '<path d="M3 10.8 12 3l9 7.8"/><path d="M5 10v10h14V10"/><path d="M9.5 20v-6h5v6"/>',
  light: '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M8 10a4 4 0 1 1 8 0c0 2.8-2 3.6-2 6h-4c0-2.4-2-3.2-2-6Z"/>',
  music: '<path d="M9 18V5l10-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="16" cy="16" r="3"/>',
  car: '<path d="M6 17h12"/><path d="M5 17l1.7-6.2A3 3 0 0 1 9.6 8h4.8a3 3 0 0 1 2.9 2.8L19 17"/><circle cx="7.5" cy="17.5" r="1.5"/><circle cx="16.5" cy="17.5" r="1.5"/>',
  vacuum: '<path d="M5 14a7 7 0 0 1 14 0v2a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4Z"/><path d="M9 14h.01"/><path d="M15 14h.01"/><path d="M9 18h6"/><path d="M12 7V4"/><path d="M8 4h8"/>',
  shield: '<path d="M12 22s8-3.8 8-11V5l-8-3-8 3v6c0 7.2 8 11 8 11Z"/><path d="M9.5 12.2 11.3 14l3.5-4"/>',
  moon: '<path d="M21 14.3A8.3 8.3 0 0 1 9.7 3a7 7 0 1 0 11.3 11.3Z"/>',
  lock: '<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
  robot: '<rect x="5" y="8" width="14" height="11" rx="3"/><path d="M12 8V4"/><path d="M8.5 13h.01"/><path d="M15.5 13h.01"/><path d="M9 17h6"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.9 4.9 1.4 1.4"/><path d="m17.7 17.7 1.4 1.4"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m4.9 19.1 1.4-1.4"/><path d="m17.7 6.3 1.4-1.4"/>',
  film: '<rect x="4" y="5" width="16" height="14" rx="2"/><path d="M8 5v14"/><path d="M16 5v14"/><path d="M4 9h4"/><path d="M16 9h4"/><path d="M4 15h4"/><path d="M16 15h4"/>',
  tv: '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M8 21h8"/><path d="M12 18v3"/>',
  cast: '<path d="M4 7V5h16v14h-3"/><path d="M4 15a6 6 0 0 1 6 6"/><path d="M4 11a10 10 0 0 1 10 10"/><path d="M4 19.5v.5"/>',
  volume: '<path d="M11 5 6 9H3v6h3l5 4Z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18.5 5.5a9 9 0 0 1 0 13"/>',
  play: '<path d="M8 5v14l11-7Z"/>',
  power: '<path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.8 0"/>',
  remote: '<rect x="8" y="2" width="8" height="20" rx="4"/><circle cx="12" cy="7" r="1"/><path d="M10.5 12h3"/><path d="M12 10.5v3"/><path d="M10.5 17h3"/>',
  bed: '<path d="M4 18V7"/><path d="M20 18v-5a3 3 0 0 0-3-3H9v8"/><path d="M4 13h5"/><path d="M4 18h16"/>',
  coffee: '<path d="M6 8h10v5a5 5 0 0 1-5 5H9a3 3 0 0 1-3-3Z"/><path d="M16 9h1.5a2.5 2.5 0 0 1 0 5H16"/><path d="M6 21h12"/>',
  pause: '<path d="M8 5v14"/><path d="M16 5v14"/>',
  mute: '<path d="M11 5 6 9H3v6h3l5 4Z"/><path d="m19 9-6 6"/><path d="m13 9 6 6"/>',
  eye: '<path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
  climate: '<path d="M14 14.8a4 4 0 1 1-4 0V5a2 2 0 1 1 4 0Z"/><path d="M12 8v7"/>',
  box: '<path d="m21 8-9-5-9 5 9 5 9-5Z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/>',
  bolt: '<path d="M13 2 5 14h6l-1 8 8-12h-6l1-8Z"/>',
  door: '<path d="M6 21V4a1 1 0 0 1 1-1h10v18"/><path d="M10 12h.01"/><path d="M4 21h16"/>',
  camera: '<path d="M4 7h4l2-2h4l2 2h4v12H4Z"/><circle cx="12" cy="13" r="3"/>',
  spark: '<path d="M12 2v6"/><path d="M12 16v6"/><path d="M4.2 4.2l4.2 4.2"/><path d="m15.6 15.6 4.2 4.2"/><path d="M2 12h6"/><path d="M16 12h6"/><path d="m4.2 19.8 4.2-4.2"/><path d="m15.6 8.4 4.2-4.2"/>'
};

const pageCopy = {
  home: ["Hearth console", "Quiet night, house steady, El Rocco sipping power."],
  lights: ["Glow rooms", "Cottage warmth with clean scene control."],
  media: ["Signal room", "Screens, Sonos, and room playback."],
  tesla: ["El Rocco", "Charge, climate, locks, and trip status."],
  security: ["Watchtower", "Cameras, alarm state, and quick house modes."],
  house: ["House systems", "Sebastian, cabin climate, and home devices."]
};

const navCopy = {
  home: ["home", "Home"],
  lights: ["light", "Lights"],
  media: ["tv", "Media"],
  tesla: ["car", "Car"],
  security: ["shield", "Security"]
  ,house: ["vacuum", "House"]
};

const views = {
  home: `
    <div class="status-ribbon">
      <strong>Night mode · HA online · cabin linked</strong>
      <div class="status-dots">
        <span class="dot">${icon("shield")}</span>
        <span class="dot">${icon("robot")}</span>
        <span class="dot">${icon("bolt")}</span>
      </div>
    </div>
    <article class="card hero">
      <div class="glyph">${icon("moon")}</div>
      <div>
        <div class="metric">56°</div>
        <div class="caption">Crisp clear night · porch calm · 4 mph wind</div>
      </div>
    </article>
    <section class="row">
      ${tile("car", "El Rocco", "48%", "145 mi · charging", "icon-blue", "live")}
      ${tile("light", "Glow", "2 on", "Bedroom lanterns", "icon-warm")}
      ${tile("shield", "Watch", "Armed", "Front door clear", "icon-green")}
      ${tile("robot", "Sebastian", "Online", "Local helper ready", "icon-violet")}
    </section>
    <div class="pill-row">
      ${pill("light", "Hearth glow", "icon-warm")}
      ${pill("film", "Movie den", "icon-blue")}
      ${pill("sun", "Morning bright", "icon-warm")}
      ${pill("moon", "Sleep cabin", "icon-rose")}
    </div>
  `,
  lights: `
    <div class="section-label">${icon("spark", "icon-warm")} Scene presets</div>
    <div class="pill-row">
      ${pill("spark", "Dreamy dusk", "icon-warm")}
      ${pill("film", "Movie night", "icon-blue")}
      ${pill("sun", "Bright morning", "icon-warm")}
      ${pill("moon", "Wind down", "icon-rose")}
      ${pill("spark", "Sweet dreams", "icon-blue")}
      ${pill("coffee", "Wake up", "icon-warm")}
    </div>
    <div class="section-label">${icon("bed", "icon-blue")} Living room</div>
    <section class="row three">
      ${light("All living room", "off", "resting")}
      ${light("Couch", "off", "resting")}
      ${light("TV", "off", "resting")}
      ${light("TV backlight", "off", "resting")}
      ${light("Ceiling", "off", "resting")}
      ${light("Ceiling back", "off", "resting")}
    </section>
    <div class="section-label">${icon("bed", "icon-rose")} Bedroom</div>
    <section class="row three">
      ${light("All bedroom", "55%", "glowing")}
      ${light("Mike's side", "off", "resting")}
      ${light("Kiara's side", "off", "resting")}
      ${light("Light panels", "off", "resting")}
      ${light("Big lamp", "100%", "glowing")}
    </section>
  `,
  media: `
    <article class="card media-now">
      <div class="media-screen">
        <div class="screen-glow"></div>
        <div class="screen-frame">
          <div class="screen-topline"><span>BEDROOM TV</span><span>YOUTUBE</span></div>
          <div class="screen-title">Ambient playlist</div>
          <div class="screen-subtitle">Playing in bedroom</div>
          <div class="media-progress"><span style="width:42%"></span></div>
        </div>
      </div>
      <div class="media-now-meta">
        <div>
          <div class="media-kicker">Now playing</div>
          <div class="media-title">Bedroom TV</div>
          <div class="caption">YouTube · 42% through · volume 18</div>
        </div>
        <div class="remote-strip">
          ${roundControl("power", "icon-rose")}
          ${roundControl("pause", "icon-warm")}
          ${roundControl("volume", "icon-blue")}
        </div>
      </div>
    </article>
    <section class="media-remote card">
      <button>${icon("play", "icon-warm")} Resume</button>
      <button>${icon("cast", "icon-blue")} Cast</button>
      <button>${icon("mute", "icon-rose")} Mute</button>
    </section>
    <div class="section-label">${icon("tv", "icon-blue")} Screens</div>
    <section class="device-stack">
      ${deviceRow("tv", "Bedroom TV", "Playing", "YouTube · 18 volume", "live", "icon-warm")}
      ${deviceRow("tv", "Living Room TV", "Standby", "LG webOS · ready", "", "icon-blue")}
      ${deviceRow("cast", "Google Cast", "Available", "Bedroom route", "", "icon-green")}
    </section>
    <div class="section-label">${icon("music", "icon-green")} Audio</div>
    <section class="row">
      ${tile("music", "Sonos Den", "Ready", "Era 100", "icon-green")}
      ${tile("music", "Spotify", "Ready", "Mike's Spotify", "icon-green")}
      ${tile("volume", "Echo Dot", "Idle", "Local speaker", "icon-blue")}
      ${tile("pause", "All media", "Quiet", "No active group", "icon-rose")}
    </section>
  `,
  tesla: `
    <article class="card car-image-card">
      <img src="../assets/model-y-juniper-transparent.png" alt="Tesla Model Y Juniper">
      <div class="car-badge">${icon("car", "icon-blue")} Model Y Juniper</div>
    </article>
    <section class="car-stats">
      ${miniStat("48%", "battery")}
      ${miniStat("145 mi", "range")}
      ${miniStat("Locked", "secure")}
    </section>
    <section class="row three">
      ${tile("lock", "Lock", "Locked", "secure", "icon-green")}
      ${tile("eye", "Sentry", "On", "watching", "icon-blue")}
      ${tile("climate", "Climate", "70°", "cabin", "icon-blue")}
      ${tile("box", "Frunk", "Closed", "ready", "icon-warm")}
      ${tile("door", "Trunk", "Closed", "ready", "icon-warm")}
      ${tile("bolt", "Charge", "7 kW", "6 hr left", "icon-warm")}
    </section>
    <div class="pill-row">
      ${pill("climate", "Pre-heat", "icon-warm")}
      ${pill("climate", "Pre-cool", "icon-blue")}
      ${pill("spark", "Flash", "icon-warm")}
      ${pill("sun", "Wake", "icon-warm")}
    </div>
    <article class="card list-card">
      ${line("Inside", "58°F")}
      ${line("Outside", "55°F")}
      ${line("Software", "Up to date")}
    </article>
  `,
  security: `
    <article class="card hero">
      <div class="glyph">${icon("shield", "icon-green")}</div>
      <div>
        <div class="metric">Armed</div>
        <div class="caption">Front door clear · car locked · sentry on</div>
      </div>
    </article>
    <div class="pill-row">
      ${pill("home", "Stand down", "icon-green")}
      ${pill("bed", "Tuck us in", "icon-rose")}
      ${pill("eye", "We're out", "icon-blue")}
    </div>
    <section class="row">
      ${tile("door", "Front door", "Clear", "Blink", "icon-green")}
      ${tile("camera", "Side camera", "Ready", "Driveway", "icon-blue")}
    </section>
    <article class="card list-card">
      ${line("Front door motion", "Clear")}
      ${line("Blink Security", "Armed away")}
      ${line("Last activity", "2 min ago")}
    </article>
  `,
  house: `
    <article class="card hero">
      <div class="glyph">${icon("vacuum", "icon-blue")}</div>
      <div>
        <div class="metric">Ready</div>
        <div class="caption">Roomba not online yet · El Rocco cabin climate available</div>
      </div>
    </article>
    <section class="row">
      ${tile("vacuum", "Roomba", "Offline", "Power on dock to add", "icon-blue")}
      ${tile("climate", "Cabin climate", "70°", "El Rocco", "icon-blue")}
      ${tile("light", "Hue bridge", "14 lights", "Already integrated", "icon-warm")}
      ${tile("robot", "Sebastian", "Online", "Assistant ready", "icon-green")}
    </section>
    <div class="pill-row">
      ${pill("home", "Dock")}
      ${pill("spark", "Clean kitchen")}
      ${pill("pause", "Pause")}
    </div>
  `
};

function icon(name, className = "") {
  return `<svg class="icon ${className}" viewBox="0 0 24 24" aria-hidden="true">${iconPaths[name]}</svg>`;
}

function tile(iconName, name, value, note, iconClass = "icon-warm", className = "") {
  return `<article class="card tile ${className}"><div class="iconline">${icon(iconName, iconClass)}<strong>${name}</strong></div><div><div class="big">${value}</div><div class="caption">${note}</div></div></article>`;
}

function light(name, value, note) {
  return tile("light", name, value, note, value === "off" ? "icon-blue" : "icon-warm");
}

function pill(iconName, text, iconClass = "icon-warm") {
  return `<span class="pill">${icon(iconName, iconClass)}${text}</span>`;
}

function roundControl(iconName, iconClass = "icon-blue") {
  return `<span class="round-control">${icon(iconName, iconClass)}</span>`;
}

function deviceRow(iconName, name, value, note, statusClass = "", iconClass = "icon-blue") {
  return `<article class="card device-row ${statusClass}">
    <div class="device-icon">${icon(iconName, iconClass)}</div>
    <div class="device-main"><strong>${name}</strong><span>${note}</span></div>
    <div class="device-state">${value}</div>
  </article>`;
}

function line(label, value) {
  return `<div class="list-line"><span>${label}</span><strong>${value}</strong></div>`;
}

function miniStat(value, label) {
  return `<div class="mini-stat"><strong>${value}</strong><span>${label}</span></div>`;
}

function setView(name) {
  if (!views[name]) name = "home";
  const copy = pageCopy[name];
  title.textContent = copy[0];
  subtitle.textContent = copy[1];
  root.innerHTML = views[name];
  if (window.location.hash.slice(1) !== name) {
    history.replaceState(null, "", `#${name}`);
  }
  window.scrollTo({ top: 0, behavior: "instant" });
  document.querySelectorAll(".nav").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === name);
  });
}

document.querySelectorAll(".nav").forEach((button) => {
  const [iconName, label] = navCopy[button.dataset.view];
  button.innerHTML = `${icon(iconName)}<span>${label}</span>`;
    button.addEventListener("click", () => setView(button.dataset.view));
});

window.addEventListener("hashchange", () => setView(window.location.hash.slice(1) || "home"));

setView(window.location.hash.slice(1) || "home");
