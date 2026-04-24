/** @odoo-module **/

document.addEventListener(
    "toggle",
    (event) => {
        const openedDetails = event.target;
        if (
            openedDetails.tagName !== "DETAILS" ||
            !openedDetails.open ||
            !openedDetails.classList.contains("sd_reports_history_details")
        ) {
            return;
        }

        const timeline = openedDetails.closest(".sd_reports_history_timeline");
        if (!timeline) {
            return;
        }

        for (const details of timeline.querySelectorAll(".sd_reports_history_details[open]")) {
            if (details !== openedDetails) {
                details.open = false;
            }
        }
    },
    true
);
