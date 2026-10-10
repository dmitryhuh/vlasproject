(() => {
    const thread = document.getElementById("messageThread");
    const form = document.getElementById("messageForm");

    if (!thread || !form) return;

    const input = form.querySelector("textarea");
    const sendButton = form.querySelector("button");
    const errorBox = document.getElementById("messageError");
    const messagesUrl = thread.dataset.messagesUrl;
    const sendUrl = thread.dataset.sendUrl;
    let lastId = Number(thread.dataset.lastId || 0);
    let loading = false;

    function csrfToken() {
        const field = form.querySelector("[name=csrfmiddlewaretoken]");
        if (field && field.value) return field.value;
        const item = document.cookie.split(";")
            .map(value => value.trim())
            .find(value => value.startsWith("csrftoken="));
        return item ? decodeURIComponent(item.slice("csrftoken=".length)) : "";
    }

    function appendMessage(message) {
        if (thread.querySelector('[data-message-id="' + message.id + '"]')) return;
        lastId = Math.max(lastId, Number(message.id));
        thread.dataset.lastId = String(lastId);

        const empty = document.getElementById("conversationEmpty");
        if (empty) empty.remove();

        const row = document.createElement("div");
        row.className = "message-row " + (message.is_mine ? "own" : "other");
        row.dataset.messageId = String(message.id);
        const bubble = document.createElement("div");
        bubble.className = "message-bubble";

        if (!message.is_mine) {
            const sender = document.createElement("span");
            sender.className = "message-sender";
            sender.textContent = message.sender;
            bubble.appendChild(sender);
        }

        const text = document.createElement("div");
        text.className = "message-text";
        text.textContent = message.text;
        const time = document.createElement("time");
        time.textContent = message.time;
        bubble.append(text, time);
        row.appendChild(bubble);
        thread.appendChild(row);
    }

    async function loadMessages() {
        if (loading || document.hidden) return;
        loading = true;

        try {
            const response = await fetch(messagesUrl + "?after_id=" + lastId);
            if (!response.ok) return;
            const data = await response.json();
            if (data.messages.length) {
                const nearBottom = thread.scrollHeight - thread.scrollTop - thread.clientHeight < 90;
                data.messages.forEach(appendMessage);
                if (nearBottom) thread.scrollTop = thread.scrollHeight;
            }
        } catch (error) {
            console.error("Не вдалося оновити повідомлення", error);
        } finally {
            loading = false;
        }
    }

    form.addEventListener("submit", async event => {
        event.preventDefault();
        const text = input.value.trim();
        if (!text || sendButton.disabled) return;
        errorBox.textContent = "";
        sendButton.disabled = true;

        try {
            const response = await fetch(sendUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken(),
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
                },
                body: new URLSearchParams({ text })
            });
            const data = await response.json();
            if (!response.ok || !data.ok) {
                errorBox.textContent = data.error || "Не вдалося надіслати повідомлення.";
                return;
            }
            input.value = "";
            input.style.height = "auto";
            appendMessage(data.message);
            thread.scrollTop = thread.scrollHeight;
        } catch (error) {
            errorBox.textContent = "Немає з’єднання. Спробуй ще раз.";
        } finally {
            sendButton.disabled = false;
            input.focus();
        }
    });

    input.addEventListener("input", () => {
        input.style.height = "auto";
        input.style.height = Math.min(input.scrollHeight, 120) + "px";
    });

    input.addEventListener("keydown", event => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    thread.scrollTop = thread.scrollHeight;
    window.setInterval(loadMessages, 2500);
})();
