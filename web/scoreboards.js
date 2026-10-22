"use strict";
const search = document.getElementById("test-search"), filter = document.getElementById("test-filter");
if (search && filter) {
  const rows = [...document.querySelectorAll("tbody tr")];
  function render() {
    let count = 0;
    for (const row of rows) {
      const matches = row.dataset.name.includes(search.value.toLowerCase()) &&
        (filter.value === "all" || (filter.value === "mismatch" ? row.dataset.mismatch === "true" : row.dataset.state === filter.value));
      row.hidden = !matches;
      if (matches) count++;
    }
    document.getElementById("test-count").textContent = `${count} of ${rows.length} tests shown`;
  }
  search.addEventListener("input", render); filter.addEventListener("change", render); render();
}
