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



function scroll_to_bottom(element) {
    element.scrollTop = element.scrollHeight
}







