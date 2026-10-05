document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.querySelector(".sidebar");
    const buttons = document.querySelectorAll("[data-sidebar-toggle]");
    if (!sidebar || !buttons.length) return;

    const setOpen = (open) => {
        sidebar.classList.toggle("open", open);
        buttons.forEach(button => {
            button.setAttribute("aria-expanded", String(open));
            button.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
            button.textContent = open ? "×" : "☰";
        });
    };

    buttons.forEach(button => button.addEventListener("click", () => {
        setOpen(!sidebar.classList.contains("open"));
    }));

    sidebar.querySelectorAll("a.nav-item").forEach(link => {
        link.addEventListener("click", () => setOpen(false));
    });

    document.addEventListener("click", event => {
        if (sidebar.classList.contains("open") &&
            !sidebar.contains(event.target) &&
            !Array.from(buttons).some(button => button.contains(event.target))) {
            setOpen(false);
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") setOpen(false);
    });
});
