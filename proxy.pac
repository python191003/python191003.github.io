function FindProxyForURL(url,host){
     if (shExpMatch(url,"pad.iclass30.com/*")){
           return "PROXY note.ms:80";
     }
      if (shExpMatch(url,"recordlog.iclass30.com/*")){
            return "PROXY note.ms:80";
      }
       if (shExpMatch(url,"*.fundot.info/*")){
             return "PROXY note.ms:80";
       }
        return "DIRECT";
}
