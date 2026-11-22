import { t } from "./config.js";

export function floorText(value, labels) {
  if (value === undefined || value === null || value === "") return "";
  if (String(value) === "0") return labels.ground;
  return /^\d+$/.test(String(value)) ? labels.floor.replace("{n}", value) : String(value);
}

export function colorText(key, template) {
  const name = (t.colors && t.colors[key]) || key;
  return template.replace("{color}", name);
}

export function clock(seconds) {
  const s = Math.max(0, Math.floor(seconds || 0));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}
