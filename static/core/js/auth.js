document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
        const field = button.closest(".password-field");
        const input = field?.querySelector("input");
        const label = button.querySelector("span");

        if (!input || !label) {
            return;
        }

        const shouldShow = input.type === "password";
        input.type = shouldShow ? "text" : "password";
        label.textContent = shouldShow ? "Hide" : "Show";
        button.classList.toggle("is-visible", shouldShow);
        button.setAttribute("aria-label", shouldShow ? "Hide password" : "Show password");
    });
});
