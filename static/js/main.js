// REACTIONS

document.querySelectorAll('form[action*="/like/"]').forEach(form => {
    form.addEventListener("submit", async event => {
        event.preventDefault();

        const button = form.querySelector("button");
        const icon = button.querySelector("i");
        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value
            }
        });
        const data = await response.json();

        icon.className = data.active ? "bi bi-heart-fill" : "bi bi-heart";
        button.classList.toggle("active", data.active);
    });
});

document.querySelectorAll('form[action*="/repost/"]').forEach(form => {
    form.addEventListener("submit", async event => {
        event.preventDefault();

        const button = form.querySelector("button");
        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value
            }
        });
        const data = await response.json();

        button.classList.toggle("active", data.active);

        const text = button.querySelector(".reaction-count");
        if (text) text.textContent = data.count;
    });
});

document.querySelectorAll('form[action*="/bookmark/"]').forEach(form => {
    form.addEventListener("submit", async event => {
        event.preventDefault();

        const button = form.querySelector("button");
        const icon = button.querySelector("i");
        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value
            }
        });
        const data = await response.json();

        icon.className = data.active ? "bi bi-bookmark-fill" : "bi bi-bookmark";
        button.classList.toggle("active", data.active);
    });
});

// DELETE POST

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

// COMMENT

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

// DELETE COMMENT

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

// COMMENTS OPEN

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

// CSRF

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

// AVATAR PREVIEW

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

// CREATE POST PREVIEW

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

// REGISTER STEPS

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

// LIVE SEARCH

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
