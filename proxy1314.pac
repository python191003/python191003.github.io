function FindProxyForURL(url,host){
     if (shExpMatch(host,"learningmachine.iclass30.com")){
           return "PROXY 82.156.242.74:8080";
     }
     if (shExpMatch(host,"recordlog.iclass30.com")){
           return "PROXY 192.168.100.1:80";
     }
     if (shExpMatch(host,"*.fundot.info")){
           return "PROXY 192.168.100.1:80";
     }
     return "DIRECT";
}
