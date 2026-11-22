// Toast notifications. Server messages arrive as <template data-initial-toast>.
let nextId = 1;

export function registerToasts(Alpine) {
  Alpine.store("toasts", {
    items: [],
    push(text, level = "info", timeout = 4200) {
      const id = nextId++;
      this.items.push({ id, text, level });
      if (timeout) setTimeout(() => this.dismiss(id), timeout);
      return id;
    },
    dismiss(id) {
      this.items = this.items.filter((item) => item.id !== id);
    },
  });

  Alpine.data("toaster", () => ({
    init() {
      this.$el.querySelectorAll("template[data-initial-toast]").forEach((tpl) => {
        const level = tpl.dataset.level.includes("error") ? "error" : tpl.dataset.level.includes("success") ? "success" : "info";
        Alpine.store("toasts").push(tpl.innerHTML.trim(), level, 5200);
      });
    },
  }));

  // Server-side HTMX responses can send HX-Trigger: {"wen-toast": {"text": "...", "level": "success"}}
  document.body.addEventListener("wen-toast", (event) => {
    const { text, level } = event.detail || {};
    if (text) Alpine.store("toasts").push(text, level);
  });
}

export const toast = (text, level) => window.Alpine && window.Alpine.store("toasts").push(text, level);
