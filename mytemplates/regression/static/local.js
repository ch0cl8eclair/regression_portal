function toggleScenariosDisplay() {
        // get a list of all the body elements (there will only be one),
        // and then select the zeroth (or first) such element

        // get the results table
        myTable = document.getElementById("scenarios_table");
        
        myTogBtn = document.getElementById("scenarios_toggle_button");
        if (myTogBtn.firstChild.nodeValue == "Show All") {
             myTogBtn.firstChild.nodeValue = "Show Fail"
        }
        else {
                 myTogBtn.firstChild.nodeValue = "Show All"
        }
        
        myTBody = myTable.getElementsByTagName("tbody")[0];
        
        myRows = myTBody.getElementsByTagName("tr");

        // Iterator through the tables rows
        for (r=0;r<myRows.length;r++)
        {
         if (myRows[r].nodeType == 1 && myRows[r].hasChildNodes() == true) {
                tdElements = myRows[r].childNodes;
                for (tdc = 0; tdc < tdElements.length; tdc++) {
                        if (tdElements[tdc].nodeType == 1 && tdElements[tdc].nodeName == "TD" && 
                            tdElements[tdc].className == "sstatus" && tdElements[tdc].firstChild.nodeValue.indexOf("Failed") == -1) {
                                if (myRows[r].style.display != 'none')
                                     myRows[r].style.display = 'none';
                              else {
                                         myRows[r].style.display = 'table-row';
                                }
                        }				 		
                }
            }								 
        }
        //myTable.style.display = 'block';
    }