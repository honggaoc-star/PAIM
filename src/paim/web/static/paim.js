"use strict";

for (const form of document.querySelectorAll("form[data-submit-lock]")) {
  form.addEventListener("submit", () => {
    const button = form.querySelector("button[type='submit']");
    if (button) {
      button.disabled = true;
      button.setAttribute("aria-disabled", "true");
    }
  });
}
