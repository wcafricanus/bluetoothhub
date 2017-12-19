 var scannedDeviceContainer = document.getElementById("listbox");
 var connectedDeviceContainer = document.getElementById("connectedlist")
 var eventSource = new EventSource("/stream");
 var prev_scanned = new Object();
 var prev_connected = new Object();
 function onButtonClick(e) {
                e.preventDefault();
                var url=$(this).attr('name'),
                data=$(this).closest('form').serialize();
                $.ajax({
                    url:url,
                    type:'post',
                    data:data,
                    success:function(){
                       //whatever you wanna do after the form is successfully submitted
                    }
                });
                return false;
            }
 $("#connectButton").on("click", onButtonClick);
 $("#disconnectButton").on("click", onButtonClick);
 $("#startHrButton").on("click", onButtonClick);
 $("#stopHrButton").on("click", onButtonClick);

 eventSource.onmessage = function(e) {
    console.log(e.data);
    fullData = JSON.parse(e.data);
    scannedDevicesObj = fullData["scanned"]
    var equals = Object.keys(prev_scanned).join("").localeCompare(Object.keys(scannedDevicesObj).join("")) == 0;// element-wise compare
    if(!equals){
        prev_scanned = scannedDevicesObj;
        var str = '';
        Object.keys(scannedDevicesObj).forEach(function(key) {
            str += '<option value="'+key+'">'+scannedDevicesObj[key]['name']+'</option>';
        })
        scannedDeviceContainer.innerHTML = str;
    }
    connectedDevicesObj = fullData["connected"]
    equals = Object.keys(prev_connected).join("").localeCompare(Object.keys(connectedDevicesObj).join("")) == 0;
    if(!equals){
        prev_connected = connectedDevicesObj;
        var str = '';
        Object.keys(connectedDevicesObj).forEach(function(key) {
            str += '<option value="'+key+'">'+connectedDevicesObj[key]['name']+'</option>';
        })
        connectedDeviceContainer.innerHTML = str;
    }

    // Heart Rate Monitoring
    heartRateObj = fullData["heart_rate"]
    var heartRateDisplayContainer = document.getElementById("heartRateDisplay")
    var deviceKeyArray = Object.keys(heartRateObj)

    // Remove heart rate rows of de-registered devices
    var children = heartRateDisplayContainer.childNodes;
    var idsPendingRemoval = [];
    for (var i = 0; i < children.length; i++) {
      var pChild = children[i];
      var found = deviceKeyArray.indexOf(pChild.id.split("-")[1]);
      if(found===-1)
        idsPendingRemoval.push(pChild.id);
    }
    for(var i = 0; i < idsPendingRemoval.length; i++){
        document.getElementById(idsPendingRemoval[i]).remove();
    }

    // Add or update heart rate rows
    Object.keys(heartRateObj).forEach(function(key) {
            var p_element = document.getElementById("HR-"+key);
            if(p_element == null){
                p_element = document.createElement("p");
                p_element.id = "HR-"+key;
                heartRateDisplayContainer.appendChild(p_element);
                }
            var str = '';
            heartrate = heartRateObj[key]
            if (heartrate != null)
                str += '<i class="fa fa-heart-o" style="font-size:48px;color:red">'+heartrate+'</i>';
            else
                str += '<i class="fa fa-circle-o-notch fa-spin" style="font-size:48px;color:red"></i>';
            if(p_element.innerHTML !== str)
                p_element.innerHTML = str;
    });
 };
