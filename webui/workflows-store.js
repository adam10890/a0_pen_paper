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
const LIVE_POLL_MS = 1500;
const LIVE_SECTIONS = [
    "findings",
    "results",
    "insights",
    "notes",
    "decisions",
    "backtrack",
    "execution_log",
];
const DIAGRAM_TYPES = ["flow", "flow-vertical", "layers", "sequence", "timeline"];
const DIAGRAM_THEMES = ["tech-blue", "morandi", "mint", "terracotta", "indigo"];
const UI_TEXT = {
    he: {
        languageButton: "English",
        dirtyTemplateConfirm: "יש שינויים שלא נשמרו בתבנית. לעבור למצב Live בכל זאת?",
        dirtyLiveConfirm: "יש טקסט שלא נוסף לסשן. לעבור לתבניות בכל זאת?",
        dirtySessionConfirm: "יש טקסט שלא נוסף לסשן. לעבור לסשן אחר בכל זאת?",
        dirtyTemplateSwitchConfirm: "יש שינויים שלא נשמרו. לעבור לתבנית אחרת בכל זאת?",
        chatOtherSessions: "סשנים קיימים בצ'אטים אחרים — בטל 'רק צ'אט זה'",
        staleToast: "הסוכן עדכן את הסשן — רענן ואז הוסף שוב",
        addedToSession: "נוסף לסשן",
        noTextToCopy: "אין טקסט להעתקה",
        copied: "הועתק",
        noLinkedTemplate: "לסשן אין תבנית מקושרת",
        templateNotFound: "תבנית לא נמצאה",
        noSourceForDiagram: "בחר תבנית או סשן לפני יצירת דיאגרמה",
        diagramCreated: "דיאגרמה נוצרה",
        agentUpdatedRefresh: "הסוכן עדכן — רענן או הוסף לסשן",
        agentUpdated: "עודכן מהסוכן",
        unsavedTemplate: "שינויים שלא נשמרו",
        saved: "נשמר",
        createTemplatePrompt: "שם תבנית חדשה (אותיות קטנות, מספרים, קו תחתון):",
        newTemplateDesc: "New workflow template",
        templateCreated: "תבנית נוצרה",
        cannotDeleteSession: "לא ניתן למחוק את תבנית session",
        deleteTemplateConfirm: "למחוק את התבנית",
        templateDeleted: "תבנית נמחקה",
        openCanvasWarning: "פתח את לוח Canvas מימין ובחר Workflows",
        staleBanner: "הסוכן עדכן את הסשן — רענן (טען מחדש) או הוסף את הטקסט שלך לפני שינוי נוסף.",
        refresh: "רענן",
        new: "+ חדש",
        description: "תיאור",
        descriptionHe: "תיאור (עברית)",
        phases: "שלבים (מופרדים בפסיק)",
        triggers: "טריגרים (מופרדים בפסיק)",
        edit: "עריכה",
        preview: "תצוגה",
        revert: "בטל",
        delete: "מחק",
        save: "שמור",
        saving: "שומר...",
        chat: "צ'אט:",
        followAgent: "Follow agent",
        currentChatOnly: "רק צ'אט זה",
        currentChat: "צ'אט זה",
        active: "פעיל",
        untagged: "ללא תג",
        section: "Section",
        copy: "העתק",
        openTemplate: "Open template",
        diagram: "Diagram",
        theme: "Theme",
        diagramPreview: "תצוגת דיאגרמה",
        copyPath: "העתק נתיב",
        download: "הורד",
        openDrawio: "פתח draw.io",
        sendWhiteboard: "שלח ל־Whiteboard",
        sendingWhiteboard: "שולח...",
        sentWhiteboard: "נשלח ל־Whiteboard",
        noDiagramYet: "צור דיאגרמה קודם",
        create: "Create",
        creating: "Creating...",
        addToSession: "הוסף לסשן",
        adding: "מוסיף...",
        emptyTemplates: "אין תבניות. הרץ execute.py install או צור תבנית חדשה.",
        emptyLiveNone: "אין סשנים פעילים. בקש מהסוכן ליצור workspace עם pen_paper.",
        emptyLiveChatOnly: "אין סשנים לצ'אט הזה. בטל «רק צ'אט זה» לראות סשנים מצ'אטים אחרים.",
        emptyLive: "אין סשנים להצגה.",
    },
    en: {
        languageButton: "עברית",
        dirtyTemplateConfirm: "This template has unsaved changes. Switch to Live anyway?",
        dirtyLiveConfirm: "This session has unsaved text. Switch to Templates anyway?",
        dirtySessionConfirm: "This session has unsaved text. Switch sessions anyway?",
        dirtyTemplateSwitchConfirm: "This template has unsaved changes. Switch templates anyway?",
        chatOtherSessions: "Sessions exist in other chats. Turn off 'This chat only'.",
        staleToast: "The agent updated the session. Refresh and add again.",
        addedToSession: "Added to session",
        noTextToCopy: "Nothing to copy",
        copied: "Copied",
        noLinkedTemplate: "This session has no linked template",
        templateNotFound: "Template not found",
        noSourceForDiagram: "Select a template or session before creating a diagram",
        diagramCreated: "Diagram created",
        agentUpdatedRefresh: "Agent updated the session. Refresh or add to session.",
        agentUpdated: "Updated by agent",
        unsavedTemplate: "Unsaved changes",
        saved: "Saved",
        createTemplatePrompt: "New template name (lowercase letters, numbers, underscores):",
        newTemplateDesc: "New workflow template",
        templateCreated: "Template created",
        cannotDeleteSession: "The built-in session template cannot be deleted",
        deleteTemplateConfirm: "Delete template",
        templateDeleted: "Template deleted",
        openCanvasWarning: "Open the right Canvas and choose Workflows",
        staleBanner: "The agent updated this session. Refresh, or add your text before making another change.",
        refresh: "Refresh",
        new: "+ New",
        description: "Description",
        descriptionHe: "Description (Hebrew)",
        phases: "Phases (comma-separated)",
        triggers: "Triggers (comma-separated)",
        edit: "Edit",
        preview: "Preview",
        revert: "Revert",
        delete: "Delete",
        save: "Save",
        saving: "Saving...",
        chat: "Chat:",
        followAgent: "Follow agent",
        currentChatOnly: "This chat only",
        currentChat: "This chat",
        active: "Active",
        untagged: "Untagged",
        section: "Section",
        copy: "Copy",
        openTemplate: "Open template",
        diagram: "Diagram",
        theme: "Theme",
        diagramPreview: "Diagram preview",
        copyPath: "Copy path",
        download: "Download",
        openDrawio: "Open draw.io",
        sendWhiteboard: "Send to Whiteboard",
        sendingWhiteboard: "Sending...",
        sentWhiteboard: "Sent to Whiteboard",
        noDiagramYet: "Create a diagram first",
        create: "Create",
        creating: "Creating...",
        addToSession: "Add to session",
        adding: "Adding...",
        emptyTemplates: "No templates. Run execute.py install or create a new template.",
        emptyLiveNone: "No active sessions. Ask the agent to create a workspace with pen_paper.",
        emptyLiveChatOnly: "No sessions for this chat. Turn off 'This chat only' to see sessions from other chats.",
        emptyLive: "No sessions to show.",
    },
};

export const store = createStore("penPaperWorkflows", {
    uiLang: "he",
    mode: "templates",
    templates: [],
    sessions: [],
    baseWorkflows: null,
    runtimeDir: "",
    selected: "",
    selectedSession: "",
    selectedSection: "notes",
    followAgent: true,
    liveChatOnly: true,
    currentChatId: "",
    chatFocus: null,
    sessionTotalCount: 0,
    sessionEtag: "",
    sessionStale: false,
    sessionMetadata: null,
    diagramTypes: DIAGRAM_TYPES,
    diagramThemes: DIAGRAM_THEMES,
    diagramType: "flow",
    diagramTheme: "tech-blue",
    diagramPath: "",
    diagramXml: "",
    diagramSketch: "",
    diagramMeta: null,
    sendingWhiteboard: false,
    generatingDiagram: false,
    userDraft: false,
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
        this.uiLang = this._loadUiLang();
        if (this.mode === "live") {
            await this.refreshSessions();
        } else {
            await this.refreshList();
        }
        this._resetPollTimer();
    },

    _loadUiLang() {
        try {
            const saved = localStorage.getItem("a0_pen_paper.workflow_ui_lang");
            return saved === "en" ? "en" : "he";
        } catch (_) {
            return "he";
        }
    },

    t(key) {
        return UI_TEXT[this.uiLang]?.[key] || UI_TEXT.en[key] || key;
    },

    toggleUiLang() {
        this.uiLang = this.uiLang === "en" ? "he" : "en";
        try {
            localStorage.setItem("a0_pen_paper.workflow_ui_lang", this.uiLang);
        } catch (_) {}
    },

    _resetPollTimer() {
        if (this._pollTimer) clearInterval(this._pollTimer);
        const ms = this.mode === "live" ? LIVE_POLL_MS : POLL_MS;
        this._pollTimer = setInterval(() => this._pollTick(), ms);
    },

    _pollTick() {
        if (this.mode === "live") {
            this._pollSessionChanges();
        } else {
            this._pollRemoteChanges();
        }
    },

    async setMode(next) {
        if (next === this.mode) return;
        if (this.mode === "templates" && this.dirty) {
            const ok = confirm(this.t("dirtyTemplateConfirm"));
            if (!ok) return;
        }
        if (this.mode === "live" && this.userDraft) {
            const ok = confirm(this.t("dirtyLiveConfirm"));
            if (!ok) return;
        }
        this.mode = next;
        this.status = "";
        this.sessionStale = false;
        this.userDraft = false;
        this._resetPollTimer();
        if (next === "live") {
            await this.refreshSessions();
        } else {
            await this.refreshList();
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

    _getCurrentChatId() {
        try {
            const chats = typeof Alpine !== "undefined" ? Alpine.store("chats") : null;
            if (chats?.selectedContext?.id) return String(chats.selectedContext.id);
            if (typeof globalThis.getContext === "function") {
                const id = globalThis.getContext();
                if (id) return String(id);
            }
            if (window.currentContextId) return String(window.currentContextId);
        } catch (_) {}
        return "";
    },

    async refreshSessions() {
        this.loading = true;
        try {
            const chatId = this._getCurrentChatId();
            this.currentChatId = chatId;
            const r = await callJsonApi(`${API}/sessions_list`, {
                chat_id: chatId || undefined,
                chat_only: this.liveChatOnly,
            });
            if (!r?.ok) throw new Error(r?.error || "sessions list failed");
            this.sessions = r.sessions || [];
            this.sessionTotalCount = r.total_count ?? this.sessions.length;
            this.chatFocus = r.focus || null;
            if (this.followAgent) {
                this._applyAgentFocusFromPayload(r.focus);
            }
            if (!this.selectedSession && this.sessions.length) {
                const preferred =
                    this.sessions.find((s) => s.is_chat_focus) ||
                    this.sessions.find((s) => s.is_current_chat) ||
                    this.sessions[0];
                await this.selectSession(preferred.name);
            } else if (this.selectedSession) {
                const still = this.sessions.some((s) => s.name === this.selectedSession);
                if (!still && this.sessions.length) {
                    const preferred =
                        this.sessions.find((s) => s.is_chat_focus) ||
                        this.sessions.find((s) => s.is_current_chat) ||
                        this.sessions[0];
                    await this.selectSession(preferred.name);
                } else if (still) {
                    await this.loadSessionSection();
                }
            }
            if (chatId && this.liveChatOnly && !this.sessions.length && this.sessionTotalCount > 0) {
                this.status = this.t("chatOtherSessions");
            }
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        } finally {
            this.loading = false;
        }
    },

    _applyAgentFocusFromPayload(focus) {
        if (!focus?.workspace) return;
        const { workspace, section } = focus;
        if (workspace && this.sessions.some((s) => s.name === workspace)) {
            this.selectedSession = workspace;
            if (section && LIVE_SECTIONS.includes(section)) {
                this.selectedSection = section;
            }
        }
    },

    async _applyAgentFocus() {
        try {
            const r = await callJsonApi(`${API}/sessions_focus`, {
                chat_id: this.currentChatId || this._getCurrentChatId() || undefined,
            });
            if (!r?.ok) return;
            this.chatFocus = r.focus || null;
            this._applyAgentFocusFromPayload(r.focus);
        } catch (_) {}
    },

    async selectSession(name) {
        if (this.userDraft && this.selectedSession && this.selectedSession !== name) {
            const ok = confirm(this.t("dirtySessionConfirm"));
            if (!ok) return;
        }
        this.selectedSession = name;
        this.userDraft = false;
        this.sessionStale = false;
        await this.loadSessionSection();
    },

    async loadSessionSection() {
        if (!this.selectedSession) return;
        this.loading = true;
        try {
            const r = await callJsonApi(`${API}/sessions_get`, {
                workspace: this.selectedSession,
                section: this.selectedSection,
            });
            if (!r?.ok) throw new Error(r?.error || "session load failed");
            const s = r.session;
            this.sessionEtag = s.etag || "";
            this.sessionMetadata = s.metadata || null;
            this.content = s.text || "";
            this.userDraft = false;
            this.sessionStale = false;
            await this._renderPreview();
            this.status = "";
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        } finally {
            this.loading = false;
        }
    },

    onSessionInput() {
        this.userDraft = true;
        this.sessionStale = false;
        this._renderPreview();
    },

    async saveSessionNote() {
        if (!this.selectedSession || !this.content?.trim()) return;
        this.saving = true;
        try {
            const r = await callJsonApi(`${API}/sessions_append`, {
                workspace: this.selectedSession,
                section: this.selectedSection,
                content: this.content,
                etag: this.sessionEtag,
            });
            if (r?.error === "stale") {
                this.sessionStale = true;
                if (r.current_etag) this.sessionEtag = r.current_etag;
                toastFrontendWarning(this.t("staleToast"), "Pen & Paper");
                await this.loadSessionSection();
                return;
            }
            if (!r?.ok) throw new Error(r?.error || r?.message || "append failed");
            this.sessionEtag = r.etag || this.sessionEtag;
            this.userDraft = false;
            this.sessionStale = false;
            this.content = "";
            toastFrontendSuccess(this.t("addedToSession"), "Pen & Paper");
            await this.loadSessionSection();
            await this.refreshSessions();
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        } finally {
            this.saving = false;
        }
    },

    async copySessionText() {
        const text = this.content || "";
        if (!text) {
            toastFrontendWarning(this.t("noTextToCopy"), "Pen & Paper");
            return;
        }
        try {
            await navigator.clipboard.writeText(text);
            toastFrontendSuccess(this.t("copied"), "Pen & Paper");
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        }
    },

    async openTemplateFromSession() {
        const tpl = this.sessionMetadata?.template;
        if (!tpl) {
            toastFrontendWarning(this.t("noLinkedTemplate"), "Pen & Paper");
            return;
        }
        await this.setMode("templates");
        if (this.templates.some((t) => t.name === tpl)) {
            await this.select(tpl);
        } else {
            toastFrontendWarning(`${this.t("templateNotFound")}: ${tpl}`, "Pen & Paper");
        }
    },

    async generateDiagram() {
        const sourceType = this.mode === "live" ? "session" : "template";
        const sourceId = sourceType === "session" ? this.selectedSession : this.selected;
        if (!sourceId) {
            toastFrontendWarning(this.t("noSourceForDiagram"), "Pen & Paper");
            return;
        }
        this.generatingDiagram = true;
        try {
            const r = await callJsonApi(`${API}/diagrams_generate`, {
                source_type: sourceType,
                source_id: sourceId,
                diagram_type: this.diagramType,
                theme: this.diagramTheme,
            });
            if (!r?.ok) throw new Error(r?.error || "diagram generation failed");
            this.diagramPath = r.path || "";
            this.diagramXml = r.xml || "";
            this.diagramSketch = r.sketch || "";
            this.diagramMeta = r;
            this.status = `Diagram: ${r.nodes || 0} nodes`;
            toastFrontendSuccess(this.t("diagramCreated"), "Pen & Paper");
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        } finally {
            this.generatingDiagram = false;
        }
    },

    async copyDiagramPath() {
        if (!this.diagramPath) {
            toastFrontendWarning(this.t("noDiagramYet"), "Pen & Paper");
            return;
        }
        try {
            await navigator.clipboard.writeText(this.diagramPath);
            toastFrontendSuccess(this.t("copied"), "Pen & Paper");
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        }
    },

    downloadDiagram() {
        if (!this.diagramXml) {
            toastFrontendWarning(this.t("noDiagramYet"), "Pen & Paper");
            return;
        }
        const name = (this.diagramPath || "pen-paper-diagram.drawio").split(/[\\/]/).pop();
        const blob = new Blob([this.diagramXml], { type: "application/xml;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = name || "pen-paper-diagram.drawio";
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    },

    openDrawio() {
        window.open("https://app.diagrams.net/", "_blank", "noopener,noreferrer");
    },

    async sendDiagramToWhiteboard() {
        const sourceType = this.mode === "live" ? "session" : "template";
        const sourceId = sourceType === "session" ? this.selectedSession : this.selected;
        if (!sourceId) {
            toastFrontendWarning(this.t("noSourceForDiagram"), "Pen & Paper");
            return;
        }
        this.sendingWhiteboard = true;
        try {
            const r = await callJsonApi(`${API}/diagrams_send_whiteboard`, {
                source_type: sourceType,
                source_id: sourceId,
                diagram_type: this.diagramType,
                theme: this.diagramTheme,
            });
            if (!r?.ok) throw new Error(r?.error || "whiteboard bridge failed");
            toastFrontendSuccess(`${this.t("sentWhiteboard")}: ${r.board_name}`, "Pen & Paper");
            const rc = typeof Alpine !== "undefined" ? Alpine.store("rightCanvas") : null;
            if (rc && typeof rc.open === "function") {
                rc.open("whiteboard");
            }
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        } finally {
            this.sendingWhiteboard = false;
        }
    },

    async _pollSessionChanges() {
        if (this.saving) return;
        const chatId = this._getCurrentChatId();
        if (chatId !== this.currentChatId) {
            this.currentChatId = chatId;
            await this.refreshSessions();
            return;
        }
        if (!this.selectedSession) return;
        try {
            if (this.followAgent) {
                await this._applyAgentFocus();
            }
            const r = await callJsonApi(`${API}/sessions_get`, {
                workspace: this.selectedSession,
                section: this.selectedSection,
            });
            if (!r?.ok) return;
            const etag = r.session?.etag || "";
            if (!etag || etag === this.sessionEtag) return;
            const prevEtag = this.sessionEtag;
            this.sessionEtag = etag;
            if (this.userDraft) {
                this.sessionStale = true;
                this.status = this.t("agentUpdatedRefresh");
                await this._renderPreview();
                return;
            }
            const text = r.session?.text || "";
            if (text !== this.content) {
                this.content = text;
                this.status = prevEtag ? this.t("agentUpdated") : "";
                await this._renderPreview();
            }
        } catch (_) {}
    },

    async select(name) {
        if (this.dirty && this.selected && this.selected !== name) {
            const ok = confirm(this.t("dirtyTemplateSwitchConfirm"));
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
        this.status = this.t("unsavedTemplate");
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
            this.status = this.t("saved");
            toastFrontendSuccess(`${this.t("saved")}: ${this.selected}`, "Pen & Paper");
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
        const name = prompt(this.t("createTemplatePrompt"));
        if (!name) return;
        try {
            const r = await callJsonApi(`${API}/workflows_create`, {
                template_name: name.trim(),
                description: this.t("newTemplateDesc"),
            });
            if (!r?.ok) throw new Error(r?.error || "create failed");
            toastFrontendSuccess(`${this.t("templateCreated")}: ${name}`, "Pen & Paper");
            await this.refreshList();
            await this.select(name.trim());
        } catch (e) {
            toastFrontendError(String(e.message || e), "Pen & Paper");
        }
    },

    async deleteSelected() {
        if (!this.selected) return;
        if (this.selected === "session") {
            toastFrontendWarning(this.t("cannotDeleteSession"), "Pen & Paper");
            return;
        }
        if (!confirm(`${this.t("deleteTemplateConfirm")} '${this.selected}'?`)) return;
        try {
            const r = await callJsonApi(`${API}/workflows_delete`, {
                template_name: this.selected,
            });
            if (!r?.ok) throw new Error(r?.error || "delete failed");
            toastFrontendSuccess(`${this.t("templateDeleted")}: ${this.selected}`, "Pen & Paper");
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
                this.status = this.t("agentUpdated");
                await this._renderPreview();
            }
        } catch (_) {}
    },

    async onOpen(_panel, opts = {}) {
        if (opts.mode === "live") {
            this.mode = "live";
        } else if (opts.mode === "templates") {
            this.mode = "templates";
        }
        await this.init();
        if (opts.workspace && this.mode === "live") {
            this.followAgent = false;
            this.selectedSession = opts.workspace;
            if (opts.section) this.selectedSection = opts.section;
            await this.loadSessionSection();
        }
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
        toastFrontendWarning(this.t("openCanvasWarning"), "Pen & Paper");
    },
});
