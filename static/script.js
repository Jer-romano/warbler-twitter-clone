const BASE_URL = "http://127.0.0.1:5000";

$(document).ready(function() {
    axios.defaults.headers.common["X-CSRFToken"] = "{{ form.csrf_token() }}";
    
    // Select all like buttons with the class "btn" and "btn-primary" or "btn-secondary"
    var likeButtons = $('.btn.btn-primary, .btn.btn-secondary');
    
    // Now you can work with the selected like buttons
    
    async function likeMessage(evt) {
        evt.preventDefault();
        var button = $(this);
        var msgId = button.closest('.list-group-item').data('msg-id');
        try {
            let response = await axios.post(`${BASE_URL}/users/add_like/${msgId}`)
            .then(function(response) {
                if (response.data.action === "add") {
                    button.removeClass('btn-secondary').addClass('btn-primary');
                } else if (response.data.action === "remove") {
                    button.removeClass('btn-primary').addClass('btn-secondary');
                }
            });
        } catch(err) {
            console.error("likeMessage function failed: ", err);
        }
    }
    likeButtons.click(likeMessage);

    $("#new-message").click(function() {
        console.log("In here");
        $("#new-message-div").toggle();
    });

    async function createMessage(evt) {
        evt.preventDefault()
        try {
            let formData = {
                text: $("#message-content").val(),
                token: $("#new-message-form input").val()
            };
            console.log(formData["text"])
            let response = await axios.post(`${BASE_URL}/messages/new`,
            formData, { headers: { 'Content-Type': 'application/json',
                                    'X-CSRFToken': formData['token']}
                       });
        
        } catch(err) {
            console.error("createMessage function failed: ", err)
        }
      }
      
      $("#new-message-form").on("submit", createMessage);

});


  