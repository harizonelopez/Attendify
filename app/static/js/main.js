document.addEventListener("DOMContentLoaded", function () {
    // Automatically dismiss flash messages after 5 seconds.
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const closeButton = alert.querySelector(".btn-close");
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });

    // Highlight the active sidebar navigation link.
    const currentPath = window.location.pathname;
    document.querySelectorAll(".sidebar-link").forEach(function (link) {
        if (!link.href) return;
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath) {
            link.classList.add("active");
        }
    });

    // Confirm before performing destructive actions.
    document.querySelectorAll("[data-confirm]").forEach(function (element) {
        element.addEventListener("click", function (event) {
            const message = element.dataset.confirm;
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });

    // Search/filter table rows.
    document.querySelectorAll("[data-table-search]").forEach(function (input) {
        const table = document.querySelector(input.dataset.tableSearch);
        if (!table) return;
        input.addEventListener("input", function () {
            const searchTerm = input.value.toLowerCase().trim();
            table.querySelectorAll("tbody tr").forEach(function (row) {
                row.style.display = row.textContent.toLowerCase().includes(searchTerm)
                    ? ""
                    : "none";
            });
        });
    });

    /* ---- ATTENDANCE PAGE INTERACTIONS ---- */
    const attendanceForm = document.getElementById("attendanceForm");
    // Run attendance interactions only on the attendance page.
    if (attendanceForm) {
        const attendanceTable = document.getElementById("attendanceTable");
        const studentSearch = document.getElementById("studentSearch");
        const presentCount = document.getElementById("presentCount");
        const absentCount = document.getElementById("absentCount");
        const totalCount = document.getElementById("totalCount");
        if (attendanceTable) {
            const rows = attendanceTable.querySelectorAll(".attendance-row");
            // Update attendance summary counters.
            function updateAttendanceSummary() {
                let present = 0;
                let absent = 0;

                rows.forEach(function (row) {
                    const selected = row.querySelector(
                        'input[type="radio"]:checked'
                    );

                    if (selected) {
                        if (selected.value === "present") {
                            present++;
                        } else if (selected.value === "absent") {
                            absent++;
                        }
                    }
                });

                if (presentCount) presentCount.textContent = present;
                if (absentCount) absentCount.textContent = absent;
                if (totalCount) totalCount.textContent = rows.length;
            }

            // Update counters whenever attendance is selected.
            attendanceForm.addEventListener("change", function (event) {
                if (event.target.classList.contains("attendance-radio")) {
                    updateAttendanceSummary();
                }
            });

            // Search students by name or username.
            if (studentSearch) {
                studentSearch.addEventListener("input", function () {
                    const searchTerm = studentSearch.value.toLowerCase().trim();

                    rows.forEach(function (row) {
                        const studentDetails = row.textContent.toLowerCase();

                        row.style.display = studentDetails.includes(searchTerm)
                            ? ""
                            : "none";
                    });
                });
            }

            // Validate attendance before submission.
            attendanceForm.addEventListener("submit", function (event) {
                let unmarked = 0;
                rows.forEach(function (row) {
                    const selected = row.querySelector(
                        'input[type="radio"]:checked'
                    );
                    if (!selected) {
                        unmarked++;
                    }
                });
                if (unmarked > 0) {
                    event.preventDefault();
                    alert(
                        `Please assign an attendance status to all students. ${unmarked} student(s) remain unmarked.`
                    );

                    return;
                }

                if (!confirm("Are you sure you want to save this attendance record?")) {
                    event.preventDefault();
                }
            });

            // Initialize attendance counters.
            updateAttendanceSummary();
        }
    }

    // Show/hide password fields
    document.querySelectorAll(".password-toggle").forEach(button => {
        button.addEventListener("click", () => {
            const input = document.getElementById(button.dataset.target);
            const icon = button.querySelector("i");

            if (!input || !icon) return;

            const isPassword = input.type === "password";

            input.type = isPassword ? "text" : "password";
            icon.classList.toggle("bi-eye", !isPassword);
            icon.classList.toggle("bi-eye-slash", isPassword);
        });
    });

    // Automatically dismiss global flash notifications
    document.querySelectorAll(".global-flash-container .alert").forEach(alert => {
        setTimeout(() => {
            alert.classList.remove("show");

            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 4000);
    });
});
