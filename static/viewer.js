function getFreeSpace() {
    var url = "/api/freespace";
    var client = new XMLHttpRequest();
    client.open("GET", url, false);
    client.setRequestHeader("Content-Type", "text/plain");
    client.send();
    var response = 0;
    if (client.status == 200) {
        response = JSON.parse(client.responseText);
    }
    return(response.toFixed(2) + " GB");
}


function getHostname() {
    var url = "/api/hostname";
    var client = new XMLHttpRequest();
    client.open("GET", url, false);
    client.setRequestHeader("Content-Type", "text/plain");
    client.send();
    var response = 0;
    if (client.status == 200) {
        response = JSON.parse(client.responseText);
    }
    return(response);
}


function getStatus() {
    var url = "/api/status";
    var client = new XMLHttpRequest();
    client.open("GET", url, false);
    client.setRequestHeader("Content-Type", "text/plain");
    client.send();
    var response = 0;
    if (client.status == 200) {
        response = JSON.parse(client.responseText);
    }
    return(response);
}



function refresh() {
  fn = "preview.jpg?" + new Date().getTime();
  document.getElementById("piclink").href = "/previews/" + fn;
  document.getElementById("previewpic").src = "/previews/" + fn;
  document.getElementById("status").innerHTML = getStatus() + " free space:" + getFreeSpace();
}

hostname = getHostname()
document.getElementById("title").innerHTML = hostname + " cloudberry viewfinder";
document.getElementById("hostname").innerHTML = getHostname();

var refreshInterval = setInterval( "refresh()", 10 * 1000);

//initial values on page load
refresh();
