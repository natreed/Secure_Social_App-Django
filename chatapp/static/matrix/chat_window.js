// Select the node that will be observed for mutations
// developer.mozilla.org/en-US/docs/Web/API/MutationObserver

//https://stackoverflow.com/questions/3583534/refresh-div-element-generated-by-a-django-template
// function refresh_history() {
//     console.log('refresh');
//     $.ajax({
//         //https://stackoverflow.com/questions/44291887/django-ajax-wouldnt-work-when-in-separate-file
//         url: window.location,
//         success: function(data) {
//             console.log("success");
//             $('#msg_history').html(data);
//         }
//     });
// }

function callback(mutationList, observer) {
  mutationList.forEach((mutation) => {
    switch(mutation.type) {
      case 'childList':
        console.log("Callback Executed");
        scroll_to_bottom();
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

function scroll_to_bottom() {
    let history = $(#msg_history)
    $('#msg_history').scrollTop = $('#msg_history').scrollHeight
}

$( document ).ready(function() {
    //scroll to bottom
    let targetNode = $('#msg_history');
    scroll_to_bottom();
    let config = { attributes: true, childList: true, subtree: true};
    let observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
});


// interval = setInterval(function() {
//         refresh_history();
// }, 1000);
//
//
// window.onbeforeunload = closingCode;
// function closingCode(){
//     clearInterval(interval)
// }

