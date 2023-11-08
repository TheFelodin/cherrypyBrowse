function reset_data() {
    // AJAX Request to replace csv file
    $.ajax({
        url: '/reset_data',
        method: 'GET',
        success: function (response) {
            alert('Source successfully reset');
            window.location.assign("/");
        },
        error: function () {
            alert('Source coud not be reset');
        }
    });
}
