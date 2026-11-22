// Small interaction components shared across pages.
import { config, landmarkName, t } from "../core/config.js";
import { resolveDescription } from "../core/api.js";
import { colorText, floorText } from "../core/format.js";
import { createMap, hasLeaflet, pinIcon } from "../core/map.js";
import { toast } from "../core/toasts.js";

export function copyLink(url) {
  return {
    copied: false,
    async copy() {
      try {
        await navigator.clipboard.writeText(url);
      } catch {
        const field = document.createElement("textarea");
        field.value = url;
        document.body.appendChild(field);
        field.select();
        const ok = document.execCommand && document.execCommand("copy");
        field.remove();
        if (!ok) { toast(t.copyFailed, "error"); return; }
      }
      this.copied = true;
      toast(t.copied, "success", 2200);
      setTimeout(() => { this.copied = false; }, 2000);
    },
  };
}

export function shareLink(url, title) {
  return {
    canShare: typeof navigator.share === "function",
    get whatsapp() { return `https://wa.me/?text=${encodeURIComponent(`${t.shareText} ${title}\n${url}`)}`; },
    async share() {
      try {
        await navigator.share({ title: `${t.shareTitle}: ${title}`, text: t.shareText, url });
      } catch { /* the user closed the share sheet */ }
    },
  };
}

export function confirmDialog() {
  return {
    open() { this.$refs.dialog.showModal(); },
    close() { this.$refs.dialog.close(); },
  };
}

export function menu() {
  return {
    open: false,
    toggle() { this.open = !this.open; },
    close() { this.open = false; },
  };
}

export function lightbox() {
  return {
    src: "",
    show(src) { this.src = src; this.$refs.dialog.showModal(); },
    close() { this.$refs.dialog.close(); },
  };
}

export function siteHeader() {
  return {
    open: false,
    scrolled: false,
    init() {
      const update = () => { this.scrolled = window.scrollY > 8; };
      update();
      window.addEventListener("scroll", update, { passive: true });
    },
  };
}

export function driverMode(stage, landmarkState) {
  return {
    stage,
    landmarkState,
    checked(verdict) {
      this.landmarkState = verdict;
      if (verdict === "confirmed" || verdict === "rejected") setTimeout(() => { this.stage = "entrance"; }, 700);
    },
  };
}

export function landingDemo() {
  return {
    t,
    text: "",
    example: 0,
    loading: false,
    result: null,
    error: "",
    mapFailed: false,
    init() {
      this.examples = [...this.$refs.examples.content.children].map((el) => el.textContent.trim());
      const i18n = this.$root.querySelector(".demo__i18n").dataset;
      this.labels = { floor: i18n.floor, ground: i18n.ground, building: i18n.building };
      this.text = this.examples[config.lang === "ar" ? 2 : 0];
      this.example = config.lang === "ar" ? 2 : 0;
      if (!hasLeaflet()) { this.mapFailed = true; this.resolve(); return; }
      this.map = createMap(this.$refs.canvas, { center: [33.8935, 35.497], zoom: 13 });
      this.layer = window.L.layerGroup().addTo(this.map);
      // Show a real result straight away, so the first thing visitors see is the product working.
      this.resolve();
    },
    get top() { return this.result && this.result.candidates[0]; },
    name: landmarkName,
    floorText(v) { return floorText(v, this.labels); },
    colorText(k) { return colorText(k, this.labels.building); },
    useExample(i) { this.example = i; this.text = this.examples[i]; this.resolve(); },
    async resolve() {
      this.error = "";
      this.loading = true;
      try {
        this.result = await resolveDescription(this.text.trim());
        if (this.map) {
          this.layer.clearLayers();
          const c = this.top;
          if (c) {
            const at = [c.landmark.lat, c.landmark.lng];
            window.L.marker(at, { icon: pinIcon(c.quality === "strong" ? "landmark" : "uncertain", { drop: true }) }).addTo(this.layer);
            this.map.flyTo(at, 16, { duration: 0.9 });
          }
        }
      } catch {
        this.error = t.resolveFailed;
      } finally {
        this.loading = false;
      }
    },
  };
}
