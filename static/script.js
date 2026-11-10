document.addEventListener("DOMContentLoaded", () => {
    formatPnlColumns()

    const socket = io({ managerOptions: { debug: true } });
    
    socket.on("file_changed", async (data) => {
       // console.log("FILE_CHANGED RECEIVED:", data);
        
        if (data.page.replaceAll("_", " ").replace(".html", "") !== CURRENT_PAGE) return;
        // console.log("Attempt to replace");
        const res = await fetch(window.location.href, { cache: "no-store" });
        const text = await res.text();

        const parser = new DOMParser();
        const doc = parser.parseFromString(text, "text/html");

        const newTables = doc.querySelectorAll("table");
        const oldTables = document.querySelectorAll("table");

        oldTables.forEach((oldTable, i) => {
            if (newTables[i]) {oldTable.replaceWith(newTables[i]);}
        });

        formatPnlColumns();
        // makeTablesSortable();
    });
});

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
            if (isNaN(num) || raw=="") return;

            cell.innerText = num.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        });
    });
}

/* For Rules Complinace Table - Highlight rows with any breach to Red */ 
document.addEventListener("DOMContentLoaded", function() {
        // Targets the table with id="myTable"
        const rows = document.querySelectorAll("#rulesDataTable tbody tr");
        rows.forEach(row => {
            const cells = row.querySelectorAll("td");
            
            // Specify the target column indices you want to check (Column 7 and Column 8)
            const targetIndices = [6, 7]; 
            let shouldHighlight = false;

            // Check each target column
            for (let index of targetIndices) {
                if (cells[index]) {
                    const cellValue = cells[index].textContent.trim();
                    if (cellValue === "1") {
                        shouldHighlight = true;
                        break; // Exit loop early as soon as a '1' is found
                    }
                }
            }

            // If either column has '1', highlight the entire row
            if (shouldHighlight) {
                console.log(row.id);
                cells.forEach(cell => {
                    cell.style.setProperty("background-color", "#fd4e4eab", "important");
                });
            }
        });
    });