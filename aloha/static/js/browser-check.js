$(document).ready(function(){
    if(($.browser.msie) && ($.browser.version <8)){
        window.location="/browser-version"
    }
    if(($.browser.mozilla) && (parseInt($.browser.version) <=5)){
        window.location="/browser-version"
    }
    if(($.browser.webkit) && (parseInt($.browser.version <=530))){
        window.location="/browser-version"
    }
});
