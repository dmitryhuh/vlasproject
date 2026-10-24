document.addEventListener("submit", async event => {
    const form = event.target.closest('form[action*="/like/"], form[action*="/repost/"], form[action*="/bookmark/"]');
    if (!form) return;

    event.preventDefault();
    if (form.dataset.sending === "true") return;

    const button = form.querySelector("button");
    const icon = button?.querySelector("i");
    const token = form.querySelector("[name=csrfmiddlewaretoken]")?.value || getCookie("csrftoken");
    if (!button || !icon) return;

    form.dataset.sending = "true";
    button.disabled = true;

    try {
        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": token,
                "X-Requested-With": "XMLHttpRequest"
            },
            credentials: "same-origin"
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || "Не вдалося оновити реакцію.");

        if (form.action.includes("/like/")) {
            icon.className = data.active ? "bi bi-heart-fill" : "bi bi-heart";
        } else if (form.action.includes("/bookmark/")) {
            icon.className = data.active ? "bi bi-bookmark-fill" : "bi bi-bookmark";
        }
        button.classList.toggle("active", Boolean(data.active));

        const count = button.querySelector(".reaction-count");
        if (count && Number.isFinite(Number(data.count))) {
            count.textContent = String(data.count);
            count.setAttribute("aria-label", String(data.count));
        }
    } catch (error) {
        console.error(error);
    } finally {
        form.dataset.sending = "false";
        button.disabled = false;
    }
});

document.querySelectorAll(".post-delete").forEach(form => {
    form.addEventListener("submit", async event => {
        event.preventDefault();

        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value
            }
        });

        const data = await response.json();

        if (data.ok) {
            const post = form.closest(".post, .profile-post");
            post.classList.add("removing");
            setTimeout(() => post.remove(), 200);
        }
    });
});

document.querySelectorAll(".comment-form").forEach(form => {
    form.addEventListener("submit", async event => {
        event.preventDefault();

        const input = form.querySelector("input[name=text]");
        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value
            },
            body: new URLSearchParams({
                text: input.value
            })
        });

        const data = await response.json();
        if (!data.ok) return;

        input.value = "";

        const comments = form.previousElementSibling;
        const empty = comments.querySelector(".comments-empty");
        if (empty) empty.remove();

        const comment = document.createElement("div");
        comment.className = "comment comment-new";
        comment.dataset.commentId = data.id;

        const avatar = data.avatar
            ? `<img src="${data.avatar}" class="comment-avatar" alt="">`
            : `<div class="comment-avatar avatar-empty">${data.username[0].toUpperCase()}</div>`;

        comment.innerHTML = `
            ${avatar}
            <div class="comment-content">
                <div class="comment-header">
                    <a href="/profile/${data.username}/">@${data.username}</a>
                    <form action="${data.delete_url}" method="post" class="comment-delete-form">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie("csrftoken")}">
                        <button type="submit" title="Видалити">
                            <i class="bi bi-trash"></i>
                        </button>
                    </form>
                </div>
                <div class="comment-text">${data.text}</div>
            </div>
        `;

        comments.appendChild(comment);

        const count = form.closest(".comments-box")
            ?.previousElementSibling
            ?.querySelector(".comments-link .reaction-count");

        if (count) count.textContent = Number(count.textContent) + 1;
    });
});

document.addEventListener("submit", async event => {
    const form = event.target.closest(".comment-delete-form");
    if (!form) return;

    event.preventDefault();

    const response = await fetch(form.action, {
        method: "POST",
        headers: {
            "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value
        }
    });

    const data = await response.json();

    if (data.ok) {
        const comment = form.closest(".comment");
        const comments = comment.parentElement;
        const post = form.closest(".comments-box")?.closest(".post, .profile-post");

        comment.classList.add("removing");

        setTimeout(() => {
            comment.remove();

            const remaining = comments.querySelectorAll(".comment").length;
            if (!remaining) {
                comments.insertAdjacentHTML("beforeend", '<div class="comments-empty">Коментарів ще немає. Будьте першим!</div>');
            }

            const count = post?.querySelector(".comments-link .reaction-count");
            if (count) count.textContent = Math.max(0, Number(count.textContent) - 1);
        }, 180);
    }
});

document.addEventListener("click", event => {
    const button = event.target.closest(".comments-link");
    if (!button) return;

    const comments = document.getElementById(button.dataset.commentsTarget);
    if (!comments) return;

    const icon = button.querySelector("i");

    comments.open = !comments.open;
    button.classList.toggle("active", comments.open);

    if (icon) {
        icon.className = comments.open
            ? "bi bi-chat-fill"
            : "bi bi-chat";
    }
});

function getCookie(name) {
    const cookies = document.cookie.split(";");

    for (const cookie of cookies) {
        const item = cookie.trim();
        if (item.startsWith(name + "=")) {
            return decodeURIComponent(item.substring(name.length + 1));
        }
    }

    return "";
}

const avatarInput = document.getElementById("avatarInput");
const avatarPreview = document.getElementById("avatarPreview");

if (avatarInput && avatarPreview) {
    avatarInput.addEventListener("change", () => {
        const file = avatarInput.files[0];
        if (!file) return;

        const image = document.createElement("img");
        image.src = URL.createObjectURL(file);
        image.className = "edit-profile-avatar";
        image.id = "avatarPreview";

        avatarPreview.replaceWith(image);
    });
}

const imageInput = document.getElementById("image-input");
const imagePreview = document.getElementById("image-preview");

if (imageInput && imagePreview) {
    let files = [];

    imageInput.addEventListener("change", () => {
        files = [...files, ...imageInput.files];
        updateImagePreview();
    });

    function updateImagePreview() {
        imagePreview.innerHTML = "";
        const dataTransfer = new DataTransfer();

        files.forEach((file, index) => {
            dataTransfer.items.add(file);

            const item = document.createElement("div");
            item.className = "preview-item";

            const image = document.createElement("img");
            image.src = URL.createObjectURL(file);

            const button = document.createElement("button");
            button.type = "button";
            button.className = "preview-remove";
            button.innerHTML = '<i class="bi bi-x"></i>';

            button.addEventListener("click", () => {
                files.splice(index, 1);
                updateImagePreview();
            });

            item.append(image, button);
            imagePreview.appendChild(item);
        });

        imageInput.files = dataTransfer.files;
    }
}

const registerForm = document.getElementById("register-form");

if (registerForm) {
    const steps = registerForm.querySelectorAll(".register-step");
    const dots = document.querySelectorAll(".register-dot");
    const next = registerForm.querySelector(".register-next");
    const back = registerForm.querySelector(".register-back");
    const firstName = registerForm.querySelector("[name=first_name]");
    const birthday = registerForm.querySelector("[name=birthday]");
    const activeStep = registerForm.querySelector(".register-step.active");
    let current = Number(activeStep?.dataset.step || 1);

    next?.setAttribute("type", "button");
    back?.setAttribute("type", "button");

    function showStep(step) {
        current = step;

        steps.forEach(item => {
            const active = Number(item.dataset.step) === step;
            item.classList.toggle("active", active);
            item.hidden = !active;

            if (active) {
                requestAnimationFrame(() => {
                    item.animate(
                        [
                            { opacity: 0, transform: "translateX(18px)" },
                            { opacity: 1, transform: "translateX(0)" }
                        ],
                        { duration: 220, easing: "ease-out" }
                    );
                });
            }
        });

        dots.forEach((dot, index) => {
            dot.classList.toggle("active", index < step);
        });
    }

    next?.addEventListener("click", () => {
        if (!firstName?.value.trim()) {
            firstName?.focus();
            return;
        }

        if (!birthday?.value) {
            birthday?.focus();
            return;
        }

        showStep(2);
    });

    back?.addEventListener("click", () => showStep(1));
    showStep(current);
}

let searchTimer;

document.addEventListener("input", event => {
    if (!event.target.matches('.search-box input[name="q"]')) return;

    clearTimeout(searchTimer);

    searchTimer = setTimeout(async () => {
        const input = event.target;
        const query = input.value.trim();
        const url = `/search/?q=${encodeURIComponent(query)}`;

        try {
            const response = await fetch(url);
            const html = await response.text();
            const parser = new DOMParser();
            const page = parser.parseFromString(html, "text/html");
            const newResults = page.querySelector(".search-results");
            const currentResults = document.querySelector(".search-results");

            if (newResults && currentResults) {
                currentResults.innerHTML = newResults.innerHTML;
            }

            history.replaceState(null, "", url);
        } catch (error) {
            console.error(error);
        }
    }, 100);
});

document.addEventListener("submit", event => {
    if (event.target.matches(".search-box")) {
        event.preventDefault();
    }
});

(() => {
    let images = [];
    let currentIndex = 0;
    let overlay;
    let stageImage;
    let closeButton;
    let previousButton;
    let nextButton;
    let countLabel;

    function buildOverlay() {
        if (overlay) return;
        overlay = document.createElement("div");
        overlay.className = "made-lightbox";
        overlay.setAttribute("role", "dialog");
        overlay.setAttribute("aria-modal", "true");
        overlay.setAttribute("aria-label", "Перегляд зображення");

        const wrap = document.createElement("div");
        wrap.className = "made-lightbox-image-wrap";
        stageImage = document.createElement("img");
        stageImage.className = "made-lightbox-image";
        stageImage.alt = "";
        wrap.appendChild(stageImage);

        closeButton = makeButton("made-lightbox-control made-lightbox-close", "bi bi-x-lg", "Закрити");
        previousButton = makeButton("made-lightbox-control made-lightbox-prev", "bi bi-chevron-left", "Попереднє фото");
        nextButton = makeButton("made-lightbox-control made-lightbox-next", "bi bi-chevron-right", "Наступне фото");
        countLabel = document.createElement("div");
        countLabel.className = "made-lightbox-count";

        closeButton.addEventListener("click", closeLightbox);
        previousButton.addEventListener("click", () => showImage(currentIndex - 1));
        nextButton.addEventListener("click", () => showImage(currentIndex + 1));
        overlay.addEventListener("click", event => {
            if (event.target === overlay) closeLightbox();
        });

        overlay.append(wrap, closeButton, previousButton, nextButton, countLabel);
        document.body.appendChild(overlay);
    }

    function makeButton(className, iconName, label) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = className;
        button.setAttribute("aria-label", label);
        const icon = document.createElement("i");
        icon.className = "bi " + iconName;
        button.appendChild(icon);
        return button;
    }

    function showImage(index) {
        if (!images.length) return;
        currentIndex = (index + images.length) % images.length;
        const source = images[currentIndex];
        stageImage.src = source.currentSrc || source.src;
        stageImage.alt = source.alt || "Зображення";
        const multiple = images.length > 1;
        previousButton.hidden = !multiple;
        nextButton.hidden = !multiple;
        countLabel.hidden = !multiple;
        countLabel.textContent = (currentIndex + 1) + " / " + images.length;
    }

    function openLightbox(image) {
        const group = image.dataset.group;
        images = Array.from(document.querySelectorAll(".js-lightbox-image")).filter(item => {
            return group ? item.dataset.group === group : item === image;
        });
        if (!images.length) images = [image];
        currentIndex = Math.max(0, images.indexOf(image));
        buildOverlay();
        showImage(currentIndex);
        overlay.classList.add("open");
        document.body.classList.add("lightbox-open");
        closeButton.focus();
    }

    function closeLightbox() {
        if (!overlay) return;
        overlay.classList.remove("open");
        document.body.classList.remove("lightbox-open");
        stageImage.removeAttribute("src");
    }

    document.addEventListener("click", event => {
        const image = event.target.closest(".js-lightbox-image");
        if (!image) return;
        event.preventDefault();
        openLightbox(image.tagName === "IMG" ? image : image.querySelector("img") || image);
    });

    document.addEventListener("keydown", event => {
        if (!overlay || !overlay.classList.contains("open")) return;
        if (event.key === "Escape") closeLightbox();
        if (event.key === "ArrowLeft" && images.length > 1) showImage(currentIndex - 1);
        if (event.key === "ArrowRight" && images.length > 1) showImage(currentIndex + 1);
    });
})();

document.querySelectorAll(".auth-box form").forEach(form => {
    form.addEventListener("submit", () => {
        const button = form.querySelector('button[type="submit"]');
        if (!button || button.disabled) return;
        const original = button.textContent.trim();
        button.disabled = true;
        button.classList.add("is-loading");
        const label = form.id === "register-form" ? "Створюємо акаунт..." : "Входимо...";
        button.textContent = label;
        button.setAttribute("aria-busy", "true");
        button.dataset.originalText = original;
    });
});
