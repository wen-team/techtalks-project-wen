import { t } from "../core/config.js";
import { createMap, hasLeaflet, pinIcon, readJson } from "../core/map.js";

/** Read-only map for an address card or driver mode. */
export function pinMap(dataId) {
  return {
    failed: false,
    init() {
      const data = readJson(dataId);
      if (!data || !hasLeaflet()) { this.failed = true; return; }
      const { pin, landmark, quality } = data;
      const here = [pin.lat, pin.lng];
      const map = createMap(this.$refs.canvas, { center: here, zoom: 16 });
      const L = window.L;
      if (pin.source === "landmark") {
        const kind = quality && quality !== "strong" ? "uncertain" : "landmark";
        L.marker(here, { icon: pinIcon(kind), keyboard: false, title: landmark ? landmark.name : "" }).addTo(map);
      } else {
        L.marker(here, { icon: pinIcon("building"), keyboard: false, title: t.yourBuilding }).addTo(map);
        if (landmark) {
          const lm = [landmark.lat, landmark.lng];
          L.marker(lm, { icon: pinIcon("candidate"), keyboard: false, title: landmark.name }).addTo(map);
          L.polyline([lm, here], { color: "#13869f", weight: 3, dashArray: "2 8", lineCap: "round" }).addTo(map);
          map.fitBounds(L.latLngBounds([lm, here]).pad(0.6), { maxZoom: 17 });
        }
      }
    },
  };
}

/** Draggable pin on the edit page. */
export function editPin(dataId) {
  const data = readJson(dataId) || {};
  return {
    pin: { ...(data.pin || { lat: 33.8938, lng: 35.5018, source: "manual" }) },
    landmark: data.landmark,
    mapFailed: false,
    submitting: false,
    init() {
      if (!hasLeaflet()) { this.mapFailed = true; return; }
      const map = createMap(this.$refs.map, { center: [this.pin.lat, this.pin.lng], zoom: 16 });
      this.marker = window.L.marker([this.pin.lat, this.pin.lng], {
        icon: pinIcon(this.pin.source === "landmark" ? "landmark" : "building"),
        draggable: true,
        autoPan: true,
      }).addTo(map);
      this.marker.on("dragend", () => {
        const { lat, lng } = this.marker.getLatLng();
        this.pin = { lat: +lat.toFixed(6), lng: +lng.toFixed(6), source: this.landmark ? "adjusted" : "manual" };
        this.marker.setIcon(pinIcon("building"));
      });
      this.map = map;
    },
    resetToLandmark() {
      if (!this.landmark) return;
      this.pin = { lat: this.landmark.lat, lng: this.landmark.lng, source: "landmark" };
      this.marker.setLatLng([this.pin.lat, this.pin.lng]).setIcon(pinIcon("landmark"));
      this.map.panTo([this.pin.lat, this.pin.lng]);
    },
  };
}
