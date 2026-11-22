// Thin wrapper around Leaflet so every map in Wen looks and behaves the same.
import { config } from "./config.js";

export const BEIRUT = [33.8938, 35.5018];

const DROP = "M20 1.5C9.8 1.5 1.5 9.6 1.5 19.7c0 12.6 15.4 26.6 17 28a2.2 2.2 0 0 0 3 0c1.6-1.4 17-15.4 17-28C38.5 9.6 30.2 1.5 20 1.5Z";
const DOT = '<circle class="wen-pin__core" cx="20" cy="19.5" r="6.5"/>';
const DOOR = '<path class="wen-pin__core" d="M14.5 27v-8.5a5.5 5.5 0 0 1 11 0V27Z"/>';

export function hasLeaflet() {
  return typeof window.L !== "undefined";
}

/** kind: landmark | uncertain | confirmed | candidate | building */
export function pinIcon(kind = "landmark", { drop = false } = {}) {
  const core = kind === "building" ? DOOR : DOT;
  const cls = `wen-pin wen-pin--${kind}${drop ? " is-dropping" : ""}`;
  const pulse = kind === "landmark" || kind === "building" ? '<span class="wen-pin-pulse"></span>' : "";
  return window.L.divIcon({
    className: "",
    html: `<div class="${cls}">${pulse}<svg viewBox="0 0 40 52" aria-hidden="true"><path class="wen-pin__drop" d="${DROP}"/>${core}</svg></div>`,
    iconSize: [40, 52],
    iconAnchor: [20, 50],
  });
}

export function createMap(element, { center = BEIRUT, zoom = 15, interactive = true } = {}) {
  const L = window.L;
  const map = L.map(element, {
    center,
    zoom,
    zoomControl: false,
    attributionControl: true,
    scrollWheelZoom: false,
    dragging: interactive,
    tap: interactive,
    touchZoom: interactive,
    doubleClickZoom: interactive,
  });
  L.control.zoom({ position: "bottomright" }).addTo(map);
  map.attributionControl.setPrefix(false);
  const tiles = config.tiles || {};
  if (tiles.url) {
    let loaded = 0;
    let failed = 0;
    const layer = L.tileLayer(tiles.url, {
      attribution: tiles.attribution || "",
      subdomains: "abcd",
      maxZoom: 20,
      detectRetina: false,
    });
    layer.on("tileload", () => { loaded += 1; element.classList.remove("map--no-tiles"); });
    layer.on("tileerror", () => {
      failed += 1;
      if (!loaded && failed > 3) element.closest(".map")?.classList.add("map--no-tiles");
    });
    layer.addTo(map);
  }
  // Maps often start inside hidden steps or flex containers; re-measure once visible.
  const observer = new ResizeObserver(() => map.invalidateSize());
  observer.observe(element);
  map.on("unload", () => observer.disconnect());
  return map;
}

export function readJson(id) {
  const el = document.getElementById(id);
  return el ? JSON.parse(el.textContent) : null;
}
