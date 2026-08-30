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

for (const sourceType of document.querySelectorAll("select[data-provider-source]")) {
  const other = document.querySelector("[data-provider-other]");
  if (!other) {
    continue;
  }
  const refreshOther = () => {
    other.hidden = sourceType.value !== "Other";
  };
  sourceType.addEventListener("change", refreshOther);
  refreshOther();
}
