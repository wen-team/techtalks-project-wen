// The four-step address creation flow (steps 1-3 live on one page, step 4 is a separate page).
import { ApiError, resolveDescription } from "../core/api.js";
import { landmarkAltName, landmarkArea, landmarkName, t } from "../core/config.js";
import { escapeHtml } from "../core/format.js";
import { BEIRUT, createMap, hasLeaflet, pinIcon } from "../core/map.js";
import { toast } from "../core/toasts.js";

export function createFlow(initialStep = 1) {
  const initial = JSON.parse(document.getElementById("create-initial")?.textContent || "{}");
  return {
    t,
    step: initialStep,
    titles: [],
    description: initial.description || "",
    resolution: initial.resolution || null,
    landmarkId: initial.landmark_id || "",
    pin: initial.pin && initial.pin.lat ? initial.pin : null,
    resolving: false,
    submitting: false,
    error: "",
    mapFailed: false,

    init() {
      this.titles = [...this.$refs.titles.content.children].map((el) => el.textContent);
      this.mapHints = [...this.$refs.hints.content.children].map((el) => el.textContent);
      this.$watch("step", (step) => {
        window.scrollTo({ top: 0, behavior: "smooth" });
        if (step === 2) this.$nextTick(() => this.drawMap());
        if (step === 3) this.sendHints();
      });
      if (this.step === 2) this.$nextTick(() => this.drawMap());
    },

    get candidates() { return (this.resolution && this.resolution.candidates) || []; },
    get selected() { return this.candidates.find((c) => c.landmark.id === this.landmarkId) || null; },
    get mapHint() { return this.candidates.length ? this.mapHints[0] : this.mapHints[1]; },
    get highlighted() {
      const text = this.resolution ? this.resolution.text : this.description;
      const match = this.selected && this.selected.matched_text;
      if (!match || !text.includes(match)) return escapeHtml(text);
      const i = text.indexOf(match);
      return escapeHtml(text.slice(0, i)) + "<mark>" + escapeHtml(match) + "</mark>" + escapeHtml(text.slice(i + match.length));
    },
    name: landmarkName,
    altName: landmarkAltName,
    area: landmarkArea,

    example(text) {
      this.description = text;
      this.error = "";
      this.$refs.description.focus();
    },

    async resolve() {
      this.error = "";
      const text = this.description.trim();
      if (text.length < 6) { this.error = t.tooShort; this.$refs.description.focus(); return; }
      this.resolving = true;
      try {
        this.resolution = await resolveDescription(text);
        const first = this.candidates[0];
        if (first) this.select(first, { quiet: true });
        else { this.landmarkId = ""; this.pin = null; }
        this.step = 2;
      } catch (err) {
        this.error = err instanceof ApiError && err.code === "too_short" ? t.tooShort : t.resolveFailed;
      } finally {
        this.resolving = false;
      }
    },

    select(candidate) {
      this.landmarkId = candidate.landmark.id;
      this.pin = { lat: candidate.landmark.lat, lng: candidate.landmark.lng, source: "landmark" };
      this.renderMarkers();
    },

    drawMap() {
      if (!hasLeaflet()) { this.mapFailed = true; return; }
      if (!this.map) {
        const center = this.pin ? [this.pin.lat, this.pin.lng] : BEIRUT;
        this.map = createMap(this.$refs.map, { center, zoom: this.pin ? 16 : 13 });
        this.map.on("click", (e) => this.placeManually(e.latlng));
        this.layer = window.L.layerGroup().addTo(this.map);
      }
      this.renderMarkers(true);
      // The step was hidden a moment ago; re-measure and re-fit once it has a size.
      setTimeout(() => { this.map.invalidateSize(); this.renderMarkers(true); }, 60);
    },

    renderMarkers(fit = false) {
      if (!this.map) return;
      const L = window.L;
      this.layer.clearLayers();
      const points = [];
      this.candidates.forEach((c) => {
        if (c.landmark.id === this.landmarkId) return;
        const at = [c.landmark.lat, c.landmark.lng];
        points.push(at);
        L.marker(at, { icon: pinIcon("candidate"), title: landmarkName(c.landmark) })
          .on("click", () => this.select(c))
          .addTo(this.layer);
      });
      if (this.pin) {
        const at = [this.pin.lat, this.pin.lng];
        points.push(at);
        const kind = this.pin.source !== "landmark" ? "building" : this.selected && this.selected.quality !== "strong" ? "uncertain" : "landmark";
        const marker = L.marker(at, { icon: pinIcon(kind, { drop: true }), draggable: true, autoPan: true, zIndexOffset: 500 }).addTo(this.layer);
        marker.on("dragend", () => {
          const { lat, lng } = marker.getLatLng();
          this.pin = { lat: +lat.toFixed(6), lng: +lng.toFixed(6), source: this.landmarkId ? "adjusted" : "manual" };
          marker.setIcon(pinIcon("building"));
          toast(this.landmarkId ? t.pinMoved : t.pinPlaced, "info");
        });
        if (!fit) this.map.panTo(at);
      }
      if (fit && points.length > 1) this.map.fitBounds(L.latLngBounds(points).pad(0.35), { maxZoom: 16 });
      else if (fit && points.length === 1) this.map.setView(points[0], 16);
    },

    placeManually(latlng) {
      if (this.pin && this.landmarkId) return; // with a landmark, users drag the pin instead
      this.pin = { lat: +latlng.lat.toFixed(6), lng: +latlng.lng.toFixed(6), source: "manual" };
      this.renderMarkers();
    },

    toDetails() {
      if (!this.pin) return;
      this.step = 3;
    },

    sendHints() {
      const hints = (this.resolution && this.resolution.hints) || {};
      window.dispatchEvent(new CustomEvent("wen-hints", { detail: hints }));
    },

    onSubmit(event) {
      if (this.step !== 3) { event.preventDefault(); return; }
      const title = this.$root.querySelector("[name=title]");
      if (title && !title.value.trim()) {
        event.preventDefault();
        title.setAttribute("aria-invalid", "true");
        title.focus();
        return;
      }
      this.submitting = true;
    },
  };
}
