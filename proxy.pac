function FindProxyForURL(url,host){
     if (shExpMatch(host,"pad.iclass30.com")){
           return "PROXY note.ms:80";
     }
     if (shExpMatch(host,"recordlog.iclass30.com")){
           return "PROXY note.ms:80";
     }
     if (shExpMatch(host,"*.fundot.info")){
           return "PROXY note.ms:80";
     }
     return "DIRECT";
}
