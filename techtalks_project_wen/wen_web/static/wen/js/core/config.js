// Server-provided settings and translated strings (see wen_web/context_processors.py).
const el = document.getElementById("wen-config");
export const config = el ? JSON.parse(el.textContent) : { t: {}, tiles: {} };
export const t = config.t || {};
export const isArabic = () => (config.lang || "").startsWith("ar");

export function csrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  if (match) return decodeURIComponent(match[1]);
  const input = document.querySelector("input[name=csrfmiddlewaretoken]");
  return input ? input.value : "";
}

export function landmarkName(landmark) {
  if (!landmark) return "";
  return isArabic() && landmark.name_ar ? landmark.name_ar : landmark.name;
}
export function landmarkAltName(landmark) {
  if (!landmark) return "";
  return isArabic() ? landmark.name : landmark.name_ar;
}
export function landmarkArea(landmark) {
  if (!landmark) return "";
  return isArabic() && landmark.area_ar ? landmark.area_ar : landmark.area;
}
