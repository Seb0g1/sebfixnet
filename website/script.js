document.getElementById("getKeyBtn")?.addEventListener("click", () => {
  if (typeof gtag !== "undefined") gtag("event", "get_key_click");
});
