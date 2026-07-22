$(function () {
    $("#sidebarToggle").on("click", function () {
        document.body.classList.toggle("sidebar-collapsed");
    });

    $("form[data-confirm]").on("submit", function (event) {
        if (!window.confirm($(this).data("confirm"))) {
            event.preventDefault();
        }
    });

    $("#assetFilterForm select").on("change", function () {
        $("#assetFilterForm").trigger("submit");
    });

    if ($("#assetsTable").length) {
        $("#assetsTable").DataTable({
            responsive: true,
            pageLength: 10,
            order: [[0, "asc"]],
        });
    }

    if ($("#employeesTable").length) {
        $("#employeesTable").DataTable({
            responsive: true,
            pageLength: 10,
            order: [[0, "asc"]],
        });
    }

    if ($("#departmentsTable").length) {
        $("#departmentsTable").DataTable({
            responsive: true,
            pageLength: 10,
            order: [[0, "asc"]],
        });
    }

    $("#assetModal").on("hidden.bs.modal", function () {
        const form = this.querySelector("form");
        form.reset();
        $("#asset_id").val("");
        $("#assetModalLabel").text("New Asset");
    });

    $(".edit-asset").on("click", function () {
        const button = $(this);
        $("#assetModalLabel").text("Edit Asset");
        $("#asset_id").val(button.data("id"));
        $("#asset_tag").val(button.data("asset-tag"));
        $("#serial_number").val(button.data("serial-number"));
        $("#category").val(button.data("category"));
        $("#model").val(button.data("model"));
        $("#purchase_date").val(button.data("purchase-date"));
        $("#purchase_value").val(button.data("purchase-value"));
        $("#status").val(button.data("status"));
    });

    $("#employeeModal").on("hidden.bs.modal", function () {
        const form = this.querySelector("form");
        form.reset();
        $("#employee_id").val("");
        $("#employeeModalLabel").text("New Employee");
        $("#employee_is_active").prop("checked", true);
    });

    $(".edit-employee").on("click", function () {
        const button = $(this);
        $("#employeeModalLabel").text("Edit Employee");
        $("#employee_id").val(button.data("id"));
        $("#employee_name").val(button.data("name"));
        $("#employee_department_id").val(button.data("department-id"));
        $("#employee_contact").val(button.data("contact"));
        $("#employee_is_active").prop("checked", String(button.data("is-active")) === "1");
    });

    $("#departmentModal").on("hidden.bs.modal", function () {
        const form = this.querySelector("form");
        form.reset();
        $("#department_id").val("");
        $("#departmentModalLabel").text("New Department");
        $("#department_is_active").prop("checked", true);
    });

    $(".edit-department").on("click", function () {
        const button = $(this);
        $("#departmentModalLabel").text("Edit Department");
        $("#department_id").val(button.data("id"));
        $("#department_name").val(button.data("name"));
        $("#department_cost_center").val(button.data("cost-center"));
        $("#department_is_active").prop("checked", String(button.data("is-active")) === "1");
    });
});
