// Select the node that will be observed for mutations
// developer.mozilla.org/en-US/docs/Web/API/MutationObserver

//https://stackoverflow.com/questions/3583534/refresh-div-element-generated-by-a-django-template
// function refresh_history() {
//     $.ajax({
//         //https://stackoverflow.com/questions/44291887/django-ajax-wouldnt-work-when-in-separate-file
//         url: window.location.pathname + 'update_messages',
//         success: function(data) {
//             $('#msg_history').html(data);
//         }
//     });
// }

function callback(mutationList, observer) {
  mutationList.forEach((mutation) => {
    switch(mutation.type) {
      case 'childList':
        console.log("Callback Executed");
        scroll_to_bottom(document.querySelector('#msg_history'));
        /* One or more children have been added to and/or removed
           from the tree; see mutation.addedNodes and
           mutation.removedNodes */
        break;
      case 'attributes':
        /* An attribute value changed on the element in
           mutation.target; the attribute name is in
           mutation.attributeName and its previous value is in
           mutation.oldValue */
        break;
    }
  });
}

$( document ).ready(function() {
        //scroll to bottom
        let targetNode = document.querySelector('#msg_history');
        if (targetNode) {
            scroll_to_bottom(targetNode);
            let config = { attributes: true, childList: true, subtree: true};
            let observer = new MutationObserver(callback);
            observer.observe(targetNode, config);
        }


        //send room_name to View to load new room
        // $(document).on('click', '.active_room', function () {
        //     let room_name = $(this).attr('id');
        //
        //     $.ajax({
        //         url: chat_window_url,
        //         type: 'get',
        //         data: {
        //             'element': "roomsList",
        //             'room_name': room_name
        //         },
        //         success: function () {
        //             $(this).attr("background", "orange")
        //         }
        //     });
        // });
    });



function scroll_to_bottom(element) {
    element.scrollTop = element.scrollHeight
}







