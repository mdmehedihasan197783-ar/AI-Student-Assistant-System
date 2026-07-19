const menuButton = document.querySelector(".mobile-menu");
const navigation = document.querySelector(".main-nav");

menuButton?.addEventListener("click", () => {
    const isOpen = navigation.classList.toggle("open");
    menuButton.setAttribute("aria-expanded", String(isOpen));
});

navigation?.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
        navigation.classList.remove("open");
        menuButton?.setAttribute("aria-expanded", "false");
    });
});

const navLinks = Array.from(document.querySelectorAll(".main-nav a[href^='#']"));
const sections = navLinks
    .map((link) => document.querySelector(link.getAttribute("href")))
    .filter(Boolean);

const setActiveNav = (sectionId) => {
    navLinks.forEach((link) => {
        link.classList.toggle("active", link.getAttribute("href") === `#${sectionId}`);
    });
};

const updateActiveSection = () => {
    const currentSection = sections.reduce((activeSection, section) => {
        const sectionTop = section.getBoundingClientRect().top;
        return sectionTop <= 120 ? section : activeSection;
    }, sections[0]);

    if (currentSection) {
        setActiveNav(currentSection.id);
    }
};

window.addEventListener("scroll", updateActiveSection, { passive: true });
window.addEventListener("load", updateActiveSection);
updateActiveSection();
