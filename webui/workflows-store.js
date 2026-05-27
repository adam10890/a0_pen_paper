import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { renderSafeMarkdown } from "/js/safe-markdown.js";
import {
    toastFrontendError,
    toastFrontendSuccess,
    toastFrontendWarning,
} from "/components/notifications/notification-store.js";

const API = "/plugins/a0_pen_paper";
const POLL_MS = 2500;

export const store = createStore("penPaperWorkflows", {
    templates: [],
    baseWorkflows: null,
    runtimeDir: "",
    selected: "",
    content: "",
    description: "",
    descriptionHe: "",
    phasesText: "",
    triggersText: "",
    previewHtml: "",
    tab: "edit",
    loading: false,
    saving: false,
    dirty: false,
    serverMtime: 0,
    status: "",
    _initialized: false,
    _pollTimer: null,
    _snapshot: null,

    async init() {
        if (this._initialized) return;
        this._initialized = true;
        await this.refreshList();
        if (!this._pollTimer) {
            this._pollTimer = setInterval(() => this._pollRemoteChanges(), POLL_MS);
        }
    },

    async refreshList() {
        this.loading = true;
        try {
            const r = await callJsonApi(`${API}/workflows_list`, {});
            if (!r?.ok) throw new Error(r?.error || "list failed");
            this.templates = r.templates || [];
            this.baseWorkflows = r.base_workflows || null;
            this.runtimeDir = r.runtime_dir || "";
            if (!this.selected && this.templates.length) {
                await this.select(this.templates[0].name);
            } else if (this.selected) {
                const still = this.templates.some((t) => t.name === this.selected);
                if (!still && this.templates.length) {
                    await this.select(this.templates[0].name);
                }
            }
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        } finally {
            this.loading = false;
        }
    },

    async select(name) {
        if (this.dirty && this.selected && this.selected !== name) {
            const ok = confirm("יש שינויים שלא נשמרו. לעבור לתבנית אחרת בכל זאת?");
            if (!ok) return;
        }
        this.loading = true;
        try {
            const r = await callJsonApi(`${API}/workflows_get`, { template_name: name });
            if (!r?.ok) throw new Error(r?.error || "load failed");
            const t = r.template;
            this.selected = t.name;
            this.content = t.content || "";
            this.description = t.description || "";
            this.descriptionHe = t.description_he || "";
            this.phasesText = (t.phases || []).join(", ");
            this.triggersText = (t.triggers || []).join(", ");
            this.serverMtime = t.mtime || 0;
            this.dirty = false;
            this._snapshot = this._capture();
            await this._renderPreview();
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        } finally {
            this.loading = false;
        }
    },

    markDirty() {
        this.dirty = true;
        this.status = "שינויים שלא נשמרו";
    },

    async onContentInput() {
        this.markDirty();
        await this._renderPreview();
    },

    async _renderPreview() {
        try {
            this.previewHtml = await renderSafeMarkdown(this.content || "");
        } catch (_) {
            this.previewHtml = "";
        }
    },

    _capture() {
        return JSON.stringify({
            content: this.content,
            description: this.description,
            descriptionHe: this.descriptionHe,
            phasesText: this.phasesText,
            triggersText: this.triggersText,
        });
    },

    _metadataPayload() {
        const phases = this.phasesText
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean);
        const triggers = this.triggersText
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean);
        return {
            description: this.description,
            description_he: this.descriptionHe,
            phases,
            triggers,
        };
    },

    async save() {
        if (!this.selected) return;
        this.saving = true;
        try {
            const r = await callJsonApi(`${API}/workflows_save`, {
                template_name: this.selected,
                content: this.content,
                metadata: this._metadataPayload(),
            });
            if (!r?.ok) throw new Error(r?.error || "save failed");
            this.dirty = false;
            this._snapshot = this._capture();
            this.status = "נשמר";
            toastFrontendSuccess(`תבנית '${this.selected}' נשמרה`, "Pen & Paper");
            await this.refreshList();
            const g = await callJsonApi(`${API}/workflows_get`, { template_name: this.selected });
            if (g?.ok) this.serverMtime = g.template?.mtime || 0;
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        } finally {
            this.saving = false;
        }
    },

    revert() {
        if (!this._snapshot) return;
        const s = JSON.parse(this._snapshot);
        this.content = s.content;
        this.description = s.description;
        this.descriptionHe = s.descriptionHe;
        this.phasesText = s.phasesText;
        this.triggersText = s.triggersText;
        this.dirty = false;
        this.status = "";
        this._renderPreview();
    },

    async createNew() {
        const name = prompt("שם תבנית חדשה (אותיות קטנות, מספרים, קו תחתון):");
        if (!name) return;
        try {
            const r = await callJsonApi(`${API}/workflows_create`, {
                template_name: name.trim(),
                description: "New workflow template",
            });
            if (!r?.ok) throw new Error(r?.error || "create failed");
            toastFrontendSuccess(`תבנית '${name}' נוצרה`, "Pen & Paper");
            await this.refreshList();
            await this.select(name.trim());
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        }
    },

    async deleteSelected() {
        if (!this.selected) return;
        if (this.selected === "session") {
            toastFrontendWarning("לא ניתן למחוק את תבנית session", "Pen & Paper");
            return;
        }
        if (!confirm(`למחוק את התבנית '${this.selected}'?`)) return;
        try {
            const r = await callJsonApi(`${API}/workflows_delete`, {
                template_name: this.selected,
            });
            if (!r?.ok) throw new Error(r?.error || "delete failed");
            toastFrontendSuccess(`תבנית '${this.selected}' נמחקה`, "Pen & Paper");
            this.selected = "";
            this.content = "";
            await this.refreshList();
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        }
    },

    async _pollRemoteChanges() {
        if (!this.selected || this.dirty || this.saving) return;
        try {
            const r = await callJsonApi(`${API}/workflows_get`, {
                template_name: this.selected,
            });
            if (!r?.ok) return;
            const m = r.template?.mtime || 0;
            if (m && m !== this.serverMtime) {
                this.serverMtime = m;
                const t = r.template;
                this.content = t.content || "";
                this.description = t.description || "";
                this.descriptionHe = t.description_he || "";
                this.phasesText = (t.phases || []).join(", ");
                this.triggersText = (t.triggers || []).join(", ");
                this._snapshot = this._capture();
                this.status = "עודכן מהסוכן";
                await this._renderPreview();
            }
        } catch (_) {}
    },

    async onOpen(_panel, _opts = {}) {
        await this.init();
    },

    cleanup() {
        // Keep polling alive while the surface is registered; canvas close is UI-only.
    },

    openInCanvas() {
        const rc = typeof Alpine !== "undefined" ? Alpine.store("rightCanvas") : null;
        if (rc && typeof rc.open === "function") {
            rc.open("pen_paper_workflows");
            return;
        }
        toastFrontendWarning("פתח את לוח Canvas מימין ובחר Workflows", "Pen & Paper");
    },
});
