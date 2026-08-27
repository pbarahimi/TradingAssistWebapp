// Sortable tables
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("table").forEach(table => {
        const headers = table.querySelectorAll("th");
        headers.forEach((header, index) => {
            header.style.cursor = "pointer";
            header.addEventListener("click", () => sortTable(table, index));
        });
    });

    // Dark mode
    const btn = document.getElementById("darkToggle");
    btn.addEventListener("click", () => {
        document.body.classList.toggle("dark");
        localStorage.setItem("darkMode", document.body.classList.contains("dark"));
    });

    if (localStorage.getItem("darkMode") === "true") {
        document.body.classList.add("dark");
    }

    // Update PnL column formatting
    formatPnlColumns();
});

function sortTable(table, colIndex) {
    const rows = Array.from(table.querySelectorAll("tbody tr"));
    const isNumeric = rows.every(row => !isNaN(row.children[colIndex].innerText));

    rows.sort((a, b) => {
        const A = a.children[colIndex].innerText;
        const B = b.children[colIndex].innerText;
        return isNumeric ? Number(A) - Number(B) : A.localeCompare(B);
    });

    const tbody = table.querySelector("tbody");
    rows.forEach(row => tbody.appendChild(row));
}

function formatPnlColumns() {
    document.querySelectorAll("table").forEach(table => {

        // Find header cells (works for thead or direct tr)
        const headers = Array.from(table.querySelectorAll("th"));

        // Normalize header text
        const pnlIndex = headers.findIndex(h =>
            h.innerText.replace(/\s+/g, "").toLowerCase() === "pnl"
        );

        if (pnlIndex === -1) return; // No PnL column found

        // Format each row
        table.querySelectorAll("tr").forEach(row => {
            const cell = row.children[pnlIndex];
            if (!cell) return;

            const raw = cell.innerText.trim();

            // Skip non-numeric rows (header rows)
            const num = Number(raw);
            if (isNaN(num)) return;

            cell.innerText = num.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        });
    });
}