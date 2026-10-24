document.addEventListener("DOMContentLoaded", () => {
    const thread = document.getElementById("messageThread");
    const form = document.getElementById("messageForm");
    if (!thread || !form) return;

    const input = form.querySelector('textarea[name="text"]');
    const sendButton = form.querySelector('button[type="submit"]');
    const errorBox = document.getElementById("messageError");
    const userId = Number(thread.dataset.userId);
    let socket;
    let reconnectTimer;
    let closing = false;

    function showError(message) {
        errorBox.textContent = message;
    }

    function appendMessage(message) {
        if (thread.querySelector(`[data-message-id="${message.id}"]`)) return;

        const empty = document.getElementById("conversationEmpty");
        if (empty) empty.remove();

        const own = Number(message.sender_id) === userId;
        const row = document.createElement("div");
        row.className = `message-row ${own ? "own" : "other"}`;
        row.dataset.messageId = String(message.id);
        if (own && message.delete_url) row.dataset.deleteUrl = message.delete_url;

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";

        if (!own) {
            const sender = document.createElement("span");
            sender.className = "message-sender";
            sender.textContent = message.sender;
            bubble.appendChild(sender);
        }

        const text = document.createElement("div");
        text.className = "message-text";
        text.textContent = message.text;
        bubble.appendChild(text);

        const meta = document.createElement("div");
        meta.className = "message-meta";
        const time = document.createElement("time");
        time.textContent = message.time;
        meta.appendChild(time);

        if (own) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "message-delete-button";
            button.title = "Видалити повідомлення";
            button.setAttribute("aria-label", "Видалити повідомлення");
            const icon = document.createElement("i");
            icon.className = "bi bi-trash3";
            button.appendChild(icon);
            meta.appendChild(button);
        }

        bubble.appendChild(meta);
        row.appendChild(bubble);
        thread.appendChild(row);
        thread.scrollTop = thread.scrollHeight;
    }

    function showEmptyState() {
        if (thread.querySelector(".message-row")) return;
        if (document.getElementById("conversationEmpty")) return;
        const empty = document.createElement("div");
        empty.className = "conversation-empty";
        empty.id = "conversationEmpty";
        const title = document.createElement("h2");
        title.textContent = "Почніть розмову";
        const description = document.createElement("p");
        description.textContent = "Напишіть перше повідомлення.";
        empty.append(title, description);
        thread.appendChild(empty);
    }

    function removeMessage(id) {
        thread.querySelector(`[data-message-id="${id}"]`)?.remove();
        showEmptyState();
    }

    function connect() {
        if (closing) return;
        const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
        socket = new WebSocket(`${scheme}//${window.location.host}${thread.dataset.wsPath}`);

        socket.addEventListener("open", () => {
            sendButton.disabled = false;
            showError("");
        });

        socket.addEventListener("message", event => {
            let data;
            try {
                data = JSON.parse(event.data);
            } catch {
                return;
            }

            if (data.type === "message") {
                appendMessage(data);
            } else if (data.type === "delete") {
                removeMessage(data.id);
            } else if (data.type === "error") {
                showError(data.message);
            }
        });

        socket.addEventListener("close", event => {
            sendButton.disabled = true;
            if (closing) return;
            if (event.code === 4403) {
                closing = true;
                showError("Немає доступу до цього чату.");
                return;
            }
            showError("З'єднання втрачено. Підключення повториться автоматично.");
            reconnectTimer = window.setTimeout(connect, 1500);
        });

        socket.addEventListener("error", () => socket.close());
    }

    function csrfToken() {
        const field = form.querySelector("[name=csrfmiddlewaretoken]");
        if (field) return field.value;
        const cookie = document.cookie.split(";").map(item => item.trim())
            .find(item => item.startsWith("csrftoken="));
        return cookie ? decodeURIComponent(cookie.slice("csrftoken=".length)) : "";
    }

    form.addEventListener("submit", event => {
        event.preventDefault();
        const text = input.value.trim();
        if (!text || !socket || socket.readyState !== WebSocket.OPEN) {
            if (text) showError("Немає з'єднання з чатом.");
            return;
        }

        socket.send(JSON.stringify({ text }));
        input.value = "";
        input.style.height = "auto";
        showError("");
        input.focus();
    });

    input.addEventListener("input", () => {
        input.style.height = "auto";
        input.style.height = `${Math.min(input.scrollHeight, 125)}px`;
    });

    input.addEventListener("keydown", event => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    document.addEventListener("click", async event => {
        const button = event.target.closest(".message-delete-button");
        if (!button) return;
        const row = button.closest(".message-row");
        const deleteUrl = row?.dataset.deleteUrl;
        if (!row || !deleteUrl || button.disabled) return;
        if (!window.confirm("Видалити це повідомлення?")) return;

        button.disabled = true;
        const messageId = row.dataset.messageId;
        try {
            const response = await fetch(deleteUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "same-origin",
            });
            const data = await response.json();
            if (!response.ok || !data.ok) throw new Error(data.error || "Не вдалося видалити повідомлення.");
            removeMessage(messageId);
        } catch (error) {
            button.disabled = false;
            showError(error.message || "Не вдалося видалити повідомлення.");
        }
    });

    window.addEventListener("beforeunload", () => {
        closing = true;
        window.clearTimeout(reconnectTimer);
        if (socket) socket.close();
    });

    thread.scrollTop = thread.scrollHeight;
    connect();
});
