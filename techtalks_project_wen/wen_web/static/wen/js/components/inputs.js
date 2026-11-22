// Form inputs for the address details: colour, floor, photos, voice note.
import { t } from "../core/config.js";
import { clock } from "../core/format.js";
import { resizeImage, setInputFiles } from "../core/media.js";
import { toast } from "../core/toasts.js";

const PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_PHOTO_BYTES = 8 * 1024 * 1024;

export function colorPicker(initial, keys) {
  return {
    value: initial || "",
    custom: !!initial && !keys.includes(initial),
    fromHint: false,
    pick(key) { this.value = this.value === key && !this.custom ? "" : key; this.custom = false; this.fromHint = false; },
    other() { this.custom = true; this.value = keys.includes(this.value) ? "" : this.value; this.$nextTick(() => this.$refs.custom.focus()); },
    hint(hints) {
      if (!this.value && hints && hints.building_color && keys.includes(hints.building_color)) {
        this.value = hints.building_color;
        this.fromHint = true;
      }
    },
  };
}

export function floorPicker(initial) {
  return {
    value: initial || "",
    fromHint: false,
    init() { this.$watch("value", () => { this.fromHint = false; }); },
    hint(hints) {
      if (!this.value && hints && hints.floor !== undefined) {
        this.value = String(hints.floor);
        this.$nextTick(() => { this.fromHint = true; });
      }
    },
  };
}

export function photoPicker({ max = 4, existing = 0 } = {}) {
  return {
    items: [],        // { file, url }
    removed: [],      // ids of existing photos marked for removal
    existing,
    over: false,
    busy: false,
    get remaining() { return max - (this.existing - this.removed.length) - this.items.length; },
    async add(fileList) {
      const files = [...(fileList || [])];
      if (!files.length) return;
      this.busy = true;
      for (const file of files) {
        if (this.remaining <= 0) { toast(t.tooManyPhotos, "error"); break; }
        if (!PHOTO_TYPES.includes(file.type)) { toast(t.photoType, "error"); continue; }
        const ready = await resizeImage(file);
        if (ready.size > MAX_PHOTO_BYTES) { toast(t.photoTooBig, "error"); continue; }
        this.items.push({ file: ready, url: URL.createObjectURL(ready) });
      }
      this.busy = false;
      this.sync();
    },
    remove(index) {
      URL.revokeObjectURL(this.items[index].url);
      this.items.splice(index, 1);
      this.sync();
    },
    toggleExisting(id, checked) {
      this.removed = checked ? [...this.removed, id] : this.removed.filter((x) => x !== id);
    },
    sync() { setInputFiles(this.$refs.payload, this.items.map((i) => i.file)); },
  };
}

function pickMimeType() {
  if (!window.MediaRecorder) return null;
  return ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"].find((m) => MediaRecorder.isTypeSupported(m)) || "";
}

export function voiceRecorder({ maxSeconds = 120 } = {}) {
  return {
    state: "idle", // idle | recording | ready
    url: "",
    seconds: 0,
    levels: Array(18).fill(4),
    get clock() { return `${clock(this.seconds)} / ${clock(maxSeconds)}`; },

    async start() {
      const mimeType = pickMimeType();
      if (mimeType === null || !navigator.mediaDevices) { toast(t.micUnsupported, "error"); return; }
      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch {
        toast(t.micDenied, "error");
        return;
      }
      this.clear();
      this.stream = stream;
      this.chunks = [];
      this.recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      this.recorder.ondataavailable = (e) => e.data.size && this.chunks.push(e.data);
      this.recorder.onstop = () => this.finish();
      this.recorder.start(250);
      this.state = "recording";
      this.seconds = 0;
      this.startedAt = Date.now();
      this.meter(stream);
      this.timer = setInterval(() => {
        this.seconds = (Date.now() - this.startedAt) / 1000;
        if (this.seconds >= maxSeconds) { toast(t.voiceTooLong, "info"); this.stop(); }
      }, 200);
    },

    meter(stream) {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 64;
        ctx.createMediaStreamSource(stream).connect(analyser);
        const data = new Uint8Array(analyser.frequencyBinCount);
        const tick = () => {
          if (this.state !== "recording") { ctx.close(); return; }
          analyser.getByteFrequencyData(data);
          this.levels = this.levels.map((_, i) => 4 + Math.round((data[i + 2] || 0) / 255 * 24));
          requestAnimationFrame(tick);
        };
        tick();
      } catch { /* level meter is decorative */ }
    },

    stop() {
      clearInterval(this.timer);
      if (this.recorder && this.recorder.state !== "inactive") this.recorder.stop();
      if (this.stream) this.stream.getTracks().forEach((track) => track.stop());
    },

    finish() {
      const type = (this.recorder.mimeType || "audio/webm").split(";")[0];
      const ext = type.includes("mp4") ? "m4a" : type.includes("ogg") ? "ogg" : "webm";
      const file = new File(this.chunks, `voice-note.${ext}`, { type });
      this.useFile(file);
    },

    useFile(file) {
      if (!file) return;
      if (this.url) URL.revokeObjectURL(this.url);
      setInputFiles(this.$refs.payload, [file]);
      this.url = URL.createObjectURL(file);
      this.state = "ready";
    },

    clear() {
      if (this.url) URL.revokeObjectURL(this.url);
      this.url = "";
      this.state = "idle";
      if (this.$refs.payload) setInputFiles(this.$refs.payload, []);
    },
  };
}

export function voicePlayer() {
  return {
    playing: false,
    progress: 0,
    label: "0:00",
    init() {
      const audio = this.$refs.audio;
      if (audio.readyState >= 1 && isFinite(audio.duration)) this.label = clock(audio.duration);
      audio.addEventListener("loadedmetadata", () => { if (isFinite(audio.duration)) this.label = clock(audio.duration); });
      audio.addEventListener("timeupdate", () => {
        const d = isFinite(audio.duration) ? audio.duration : 0;
        this.progress = d ? (audio.currentTime / d) * 100 : 0;
        this.label = clock(audio.currentTime);
      });
      audio.addEventListener("ended", () => { this.playing = false; this.progress = 0; });
      audio.addEventListener("pause", () => { this.playing = false; });
      audio.addEventListener("play", () => { this.playing = true; });
    },
    toggle() {
      const audio = this.$refs.audio;
      if (audio.paused) {
        document.querySelectorAll("audio").forEach((other) => other !== audio && other.pause());
        audio.play().catch(() => toast(t.networkError, "error"));
      } else audio.pause();
    },
    seek(event) {
      const audio = this.$refs.audio;
      const rect = event.currentTarget.getBoundingClientRect();
      if (isFinite(audio.duration)) audio.currentTime = ((event.clientX - rect.left) / rect.width) * audio.duration;
    },
    skip(seconds) {
      const audio = this.$refs.audio;
      audio.currentTime = Math.max(0, audio.currentTime + seconds);
    },
  };
}
