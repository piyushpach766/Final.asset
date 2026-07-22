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
});
