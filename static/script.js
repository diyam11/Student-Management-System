
const studentForm = document.getElementById("studentForm");
const studentTable = document.getElementById("studentTable");
const messageBox = document.getElementById("message");
const searchInput = document.getElementById("searchInput");
const submitButton = document.getElementById("submitStudent");
const cancelEditButton = document.getElementById("cancelEdit");
const editingStudentId = document.getElementById("editingStudentId");

const menuToggle = document.getElementById("menuToggle");
const sidebar = document.getElementById("sidebar");
const appShell = document.querySelector(".app-shell");

let courseChart = null;
let searchTimer = null;
let messageTimer = null;

const MOBILE_BREAKPOINT = 900;

/* API HELPER */

async function api(url, options = {}) {
    const response = await fetch(url, options);

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            data.error ||
            data.message ||
            `Request failed (${response.status})`
        );
    }

    return data;
}

/* MESSAGES */

function showMessage(message, type = "success") {
    messageBox.textContent = message;
    messageBox.className = `alert-message show ${type}`;

    clearTimeout(messageTimer);

    messageTimer = setTimeout(() => {
        messageBox.className = "alert-message";
        messageBox.textContent = "";
    }, 4500);
}

/* HTML ESCAPING */

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

/* RESET FORM */

function resetForm() {
    studentForm.reset();

    editingStudentId.value = "";

    document.getElementById("formTitle").textContent =
        "Add a student";

    document.getElementById("formSubtitle").textContent =
        "Create a new student record.";

    submitButton.textContent = "＋ Add student";
    cancelEditButton.hidden = true;
    submitButton.disabled = false;
}

/* EDIT STUDENT */

function startEditing(student) {
    editingStudentId.value = student.student_id;

    document.getElementById("name").value = student.name;
    document.getElementById("email").value = student.email;
    document.getElementById("course").value = student.course;
    document.getElementById("marks").value = student.marks;

    document.getElementById("formTitle").textContent =
        "Edit student";

    document.getElementById("formSubtitle").textContent =
        `Updating record #${student.student_id}`;

    submitButton.textContent = "✓ Save changes";
    cancelEditButton.hidden = false;

    document.getElementById("addStudent").scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    document.getElementById("name").focus({
        preventScroll: true
    });
}

/* LOAD STUDENTS */

async function loadStudents() {
    const search = encodeURIComponent(searchInput.value.trim());

    const students = await api(`/api/students?search=${search}`);

    studentTable.innerHTML = "";

    if (students.length === 0) {
        const row = document.createElement("tr");

        const cell = document.createElement("td");
        cell.colSpan = 5;
        cell.className = "empty-state";

        cell.textContent = searchInput.value.trim()
            ? "No students match your search."
            : "No student records yet. Add your first student.";

        row.appendChild(cell);
        studentTable.appendChild(row);
    }

    students.forEach(student => {
        const marks = Number(student.marks);

        const performance = marks >= 75
            ? ["Excellent", "excellent"]
            : marks >= 50
                ? ["Good", "good"]
                : ["Needs support", "needs-support"];

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>
                <div class="student-cell">
                    <div class="student-avatar">
                        ${escapeHTML(
                            student.name.trim().charAt(0).toUpperCase() || "S"
                        )}
                    </div>

                    <div>
                        <div class="student-name">
                            ${escapeHTML(student.name)}
                        </div>
                        <div class="student-email">
                            ${escapeHTML(student.email)}
                        </div>
                        <div class="student-id">
                            ID #${Number(student.student_id)}
                        </div>
                    </div>
                </div>
            </td>

            <td>
                <span class="course-pill">
                    ${escapeHTML(student.course)}
                </span>
            </td>

            <td>
                <div class="marks-cell">
                    <strong>${marks.toFixed(2)}</strong>
                    <div class="marks-track">
                        <span style="width:${Math.max(
                            0, Math.min(100, marks)
                        )}%"></span>
                    </div>
                </div>
            </td>

            <td>
                <span class="performance-pill ${performance[1]}">
                    ${performance[0]}
                </span>
            </td>

            <td>
                <div class="action-buttons">
                    <button
                        type="button"
                        class="action-btn view-btn"
                        data-action="view"
                        data-id="${Number(student.student_id)}"
                    >View</button>

                    <button
                        type="button"
                        class="action-btn edit-btn"
                        data-action="edit"
                        data-id="${Number(student.student_id)}"
                    >Edit</button>

                    <button
                        type="button"
                        class="action-btn delete-btn"
                        data-action="delete"
                        data-id="${Number(student.student_id)}"
                        data-name="${escapeHTML(student.name)}"
                    >Delete</button>
                </div>
            </td>
        `;

        studentTable.appendChild(row);
    });

    document.getElementById("recordCount").textContent =
        `${students.length} ${
            students.length === 1 ? "record" : "records"
        }`;

    document.getElementById("tableFooterText").textContent =
        `Showing ${students.length} ${
            students.length === 1 ? "student" : "students"
        }`;
}

/* LOAD ANALYTICS */

async function loadAnalytics() {
    const data = await api("/api/analytics");
    const summary = data.summary;

    document.getElementById("totalStudents").textContent =
        summary.total_students;

    document.getElementById("averageMarks").textContent =
        Number(summary.average_marks).toFixed(2);

    document.getElementById("highestMarks").textContent =
        Number(summary.highest_marks).toFixed(2);

    document.getElementById("totalCourses").textContent =
        summary.total_courses;

    const labels = data.courses.map(item => item.course);
    const values = data.courses.map(
        item => Number(item.average_marks || 0)
    );

    const ctx = document.getElementById("courseChart");

    if (courseChart) {
        courseChart.destroy();
    }

    courseChart = new Chart(ctx, {
        type: "bar",

        data: {
            labels,
            datasets: [{
                label: "Average marks",
                data: values,

                backgroundColor: labels.map((_, index) => [
                    "#7755d9",
                    "#9a82e8",
                    "#b8a8f1",
                    "#6e91e8",
                    "#65b7a2",
                    "#f0b66b"
                ][index % 6]),

                borderRadius: 7,
                borderSkipped: false,
                maxBarThickness: 38
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    display: false
                },

                tooltip: {
                    callbacks: {
                        label: item =>
                            ` ${item.parsed.y.toFixed(2)} / 100`
                    }
                }
            },

            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,

                    grid: {
                        color: "#f0eef7"
                    },

                    ticks: {
                        stepSize: 20
                    },

                    border: {
                        display: false
                    }
                },

                x: {
                    grid: {
                        display: false
                    },

                    border: {
                        display: false
                    }
                }
            }
        }
    });

    const courseStats = document.getElementById("courseStats");

    if (data.courses.length) {
        courseStats.innerHTML = data.courses.map(item => `
            <div class="course-stat">
                <span>${escapeHTML(item.course)}</span>
                <strong>
                    ${Number(item.average_marks).toFixed(1)}%
                </strong>
                <small>
                    ${Number(item.student_count)}
                    student${Number(item.student_count) === 1 ? "" : "s"}
                </small>
            </div>
        `).join("");
    } else {
        courseStats.innerHTML = `
            <p class="course-empty">
                Course analytics will appear when you add student records.
            </p>
        `;
    }
}

/* REFRESH DASHBOARD */

async function refreshDashboard() {
    try {
        await Promise.all([
            loadStudents(),
            loadAnalytics()
        ]);
    } catch (error) {
        showMessage(
            error.message || "Could not load dashboard data.",
            "danger"
        );
    }
}

/* ADD OR UPDATE STUDENT */

studentForm.addEventListener("submit", async event => {
    event.preventDefault();

    const student = {
        name: document.getElementById("name").value.trim(),
        email: document.getElementById("email").value.trim(),
        course: document.getElementById("course").value.trim(),
        marks: document.getElementById("marks").value
    };

    const id = editingStudentId.value;
    const isEditing = Boolean(id);

    submitButton.disabled = true;
    submitButton.textContent = isEditing
        ? "Saving..."
        : "Adding...";

    try {
        const result = await api(
            isEditing ? `/api/students/${id}` : "/api/students",
            {
                method: isEditing ? "PUT" : "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(student)
            }
        );

        resetForm();

        showMessage(
            result.message ||
            (isEditing
                ? "Student updated successfully."
                : "Student added successfully.")
        );

        await refreshDashboard();
    } catch (error) {
        showMessage(error.message, "danger");
    } finally {
        submitButton.disabled = false;
    }
});

/* CANCEL EDIT */

cancelEditButton.addEventListener("click", resetForm);

/* VIEW, EDIT, DELETE STUDENT */

studentTable.addEventListener("click", async event => {
    const button = event.target.closest("button[data-action]");

    if (!button) {
        return;
    }

    const id = button.dataset.id;
    const action = button.dataset.action;

    try {
        if (action === "view") {
            const student = await api(`/api/students/${id}`);

            alert(
                `STUDENT DETAILS\n\n` +
                `ID: ${student.student_id}\n` +
                `Name: ${student.name}\n` +
                `Email: ${student.email}\n` +
                `Course: ${student.course}\n` +
                `Marks: ${Number(student.marks).toFixed(2)} / 100`
            );

        } else if (action === "edit") {
            const student = await api(`/api/students/${id}`);
            startEditing(student);

        } else if (action === "delete") {
            const name = button.dataset.name || "this student";

            if (!confirm(
                `Are you sure you want to delete ${name}'s record?`
            )) {
                return;
            }

            button.disabled = true;

            const result = await api(`/api/students/${id}`, {
                method: "DELETE"
            });

            if (editingStudentId.value === id) {
                resetForm();
            }

            showMessage(
                result.message || "Student deleted successfully."
            );

            await refreshDashboard();
        }
    } catch (error) {
        showMessage(error.message, "danger");
        button.disabled = false;
    }
});

/* SEARCH STUDENTS */

searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);

    searchTimer = setTimeout(() => {
        loadStudents().catch(error => {
            showMessage(error.message, "danger");
        });
    }, 250);
});

/* SIDEBAR CONTROLS */

function closeMobileSidebar() {
    sidebar.classList.remove("sidebar-open");
    menuToggle.setAttribute("aria-expanded", "false");
}

function setSidebarForScreenSize() {
    if (window.innerWidth <= MOBILE_BREAKPOINT) {
        // Mobile: sidebar starts hidden and opens over the page.
        appShell.classList.remove("sidebar-closed");
        closeMobileSidebar();
    } else {
        // Desktop: sidebar is visible unless the user closes it.
        closeMobileSidebar();
        appShell.classList.remove("sidebar-closed");
        menuToggle.setAttribute("aria-expanded", "true");
    }
}

menuToggle.addEventListener("click", event => {
    event.stopPropagation();

    if (window.innerWidth <= MOBILE_BREAKPOINT) {
        const isOpen = sidebar.classList.toggle("sidebar-open");

        menuToggle.setAttribute("aria-expanded", String(isOpen));
    } else {
        const isClosed = appShell.classList.toggle("sidebar-closed");

        menuToggle.setAttribute("aria-expanded", String(!isClosed));
    }
});

// Close the mobile sidebar when clicking outside it.
document.addEventListener("click", event => {
    if (
        window.innerWidth <= MOBILE_BREAKPOINT &&
        sidebar.classList.contains("sidebar-open") &&
        !sidebar.contains(event.target) &&
        !menuToggle.contains(event.target)
    ) {
        closeMobileSidebar();
    }
});

// Close the mobile sidebar after selecting a navigation link.
sidebar.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", () => {
        if (window.innerWidth <= MOBILE_BREAKPOINT) {
            closeMobileSidebar();
        }
    });
});

// Reset sidebar state when switching between desktop and mobile layouts.
let previousScreenMode =
    window.innerWidth <= MOBILE_BREAKPOINT ? "mobile" : "desktop";

window.addEventListener("resize", () => {
    const currentScreenMode =
        window.innerWidth <= MOBILE_BREAKPOINT ? "mobile" : "desktop";

    if (currentScreenMode !== previousScreenMode) {
        setSidebarForScreenSize();
        previousScreenMode = currentScreenMode;
    }
});

/* START DASHBOARD */

setSidebarForScreenSize();
refreshDashboard();
