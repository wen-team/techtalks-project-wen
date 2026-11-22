// Entry point: register Alpine components, then start Alpine.
import Alpine from "../vendor/alpine/alpine.esm.min.js";
import focus from "../vendor/alpine/focus.esm.min.js";

import { registerToasts } from "./core/toasts.js";
import { createFlow } from "./components/create-flow.js";
import { colorPicker, floorPicker, photoPicker, voicePlayer, voiceRecorder } from "./components/inputs.js";
import { editPin, pinMap } from "./components/maps.js";
import { confirmDialog, copyLink, driverMode, landingDemo, lightbox, menu, shareLink, siteHeader } from "./components/ui.js";

window.Alpine = Alpine;
Alpine.plugin(focus);
registerToasts(Alpine);

const components = {
  createFlow, colorPicker, floorPicker, photoPicker, voicePlayer, voiceRecorder,
  editPin, pinMap, confirmDialog, copyLink, driverMode, landingDemo, lightbox, menu, shareLink, siteHeader,
};
Object.entries(components).forEach(([name, fn]) => Alpine.data(name, fn));

Alpine.start();
