import { store as penPaperStore } from "/plugins/a0_pen_paper/webui/workflows-store.js";

function waitForElement(selector, timeoutMs = 5000) {
  const found = document.querySelector(selector);
  if (found) return Promise.resolve(found);
  return new Promise((resolve) => {
    const timeout = globalThis.setTimeout(() => {
      observer.disconnect();
      resolve(document.querySelector(selector));
    }, timeoutMs);
    const observer = new MutationObserver(() => {
      const element = document.querySelector(selector);
      if (!element) return;
      globalThis.clearTimeout(timeout);
      observer.disconnect();
      resolve(element);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  });
}

export default async function registerPenPaperWorkflowsSurface(canvas) {
  canvas.registerSurface({
    id: "pen_paper_workflows",
    title: "Workflows",
    icon: "edit_note",
    order: 25,
    modalPath: "/plugins/a0_pen_paper/webui/main.html",
    async open(payload = {}) {
      const panel = await waitForElement('[data-surface-id="pen_paper_workflows"] .pnpwf-panel');
      if (panel && penPaperStore?.onOpen) {
        await penPaperStore.onOpen(panel, { mode: "canvas", ...payload });
      } else if (penPaperStore?.init) {
        await penPaperStore.init();
      }
    },
    async close() {
      await penPaperStore.cleanup?.();
    },
  });
}
