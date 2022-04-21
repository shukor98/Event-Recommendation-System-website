function rsvp(postId){
  const rsvpCount = document.getElementById('rsvps-count-${postId}');
  const rsvpButton = document.getElementById('rsvp-button-${postId}');

  fetch('/rsvp/${postId}', {method: "POST"}).then((res) => res.json()).then((data) =>console.log(data));// {rsvpCount.innerHTML = data["rsvp"]});
  console.log(postId, rsvpCount);
  //console.log(rsvpCount.value)
}
