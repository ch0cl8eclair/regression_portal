window.onload=function() {
    // get tab container
    var container = document.getElementById("tabContainer");
    // set current tab
    var navitem = container.querySelector(".tabs ul li");
    //store which tab we are on
    var ident = navitem.id.split("_")[1];
    navitem.parentNode.setAttribute("data-current",ident);
    //set current tab with class of activetabheader
    navitem.setAttribute("class","tabActiveHeader");

    //this adds click event to tabs
    var tabs = container.querySelectorAll(".tabs ul li a");
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].onclick=updateSelectedTab;
    }
}

// on click of one of tabs
function updateSelectedTab() {
  var tlist = document.getElementById("tab-list");
  var current = tlist.getAttribute("data-current");

  //remove class of activetabheader and hide old contents
  document.getElementById("tabHeader_" + current).removeAttribute("class");

  var ident = this.id.split("_")[1];
  //add class of activetabheader to new active tab and show contents
  document.getElementById("tabHeader_" + ident).setAttribute("class","tabActiveHeader");
  tlist.setAttribute("data-current",ident);
}